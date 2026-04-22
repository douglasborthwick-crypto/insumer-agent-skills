---
name: insumer-auth
description: >
  InsumerAPI wallet auth — get an API key, configure environment, top up credits.
  Use when the user asks to set up InsumerAPI, get a key, configure
  INSUMER_API_KEY, check remaining credits, top up credits, or debug 401/402/429
  errors. Covers all four key paths: free (human, email), paid (human, Stripe),
  agent first key (on-chain, no human), and agent top-up of existing key
  (on-chain, no human).
allowed-tools: Bash
metadata:
  version: "0.1.0"
  author: InsumerAPI
---

# InsumerAPI Authentication

Wallet auth via InsumerAPI starts with an API key. The key authenticates the *caller*; the signing key that produces the boolean response stays with the issuer and never leaves. **Read → evaluate → sign.**

There are **four** ways to get or extend a key. Pick the one that matches the caller and stop — don't push upsell copy into emitted code.

## Pick the right path

| Who's getting the key? | What they want | Path | Endpoint |
| ----- | ----- | ----- | ----- |
| **Human**, building or testing | Free starter access (10 credits + 100 calls/day) | **Path 1: Free** | `POST /v1/keys/create` |
| **Human**, wants Pro/Enterprise tier | Higher limits, bulk credits, monthly billing | **Path 2: Paid (Stripe)** | <https://insumermodel.com/developers/account/> |
| **Agent**, no human in the loop, **first key** | Bootstrap with no email, sender wallet = identity | **Path 3: Agent onboarding (crypto)** | `POST /v1/keys/buy` |
| **Agent or human**, **already has a key** | Top up credits, keep the key/history/integrations | **Path 4: Top-up (crypto)** | `POST /v1/credits/buy` |

**Decision rule for agents:** if the agent has no key yet → Path 3. If it has one and ran out of credits → Path 4. Path 4 is the only continuous-identity upgrade path; it preserves history, tier, and integrations.

## Reference values (do not hallucinate)

- **API base**: `https://api.insumermodel.com`
- **Auth header**: `X-API-Key: insr_live_...`
- **Platform wallet — EVM**: `0xAd982CB19aCCa2923Df8F687C0614a7700255a23`
- **Platform wallet — Solana**: `6a1mLjefhvSJX1sEX8PTnionbE9DqoYjU6F6bNkT4Ydr`
- **Platform wallet — Bitcoin**: `bc1qg7qnerdhlmdn899zemtez5tcx2a2snc0dt9dt0`
- **Volume discounts** (paths 3 and 4): $5–$99 → $0.04/call, $100–$499 → $0.03/call (25% off), $500+ → $0.02/call (50% off)
- **Supported payment chains**: USDC/USDT on any major EVM chain or Solana, BTC on Bitcoin (1 confirmation, market-rate USD conversion)

---

## Path 1: Free key (human, no payment)

Free tier is 10 starter credits + 100 `/v1/attest` calls per day, no signup beyond email.

```bash
curl -s -X POST https://api.insumermodel.com/v1/keys/create \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","appName":"my-app","tier":"free"}'
```

Response:

```json
{
  "success": true,
  "key": "insr_live_...",
  "name": "my-app",
  "tier": "free",
  "dailyLimit": 100,
  "apiKeyCredits": 10
}
```

Constraints:
- One free key per email (returns `409` if a free key already exists)
- Maximum 3 keys per IP per 24 hours (returns `429` on exceeded)
- Free tier only — paid tiers go through Path 2

Tell the user to set:

```bash
export INSUMER_API_KEY='insr_live_...'
```

---

## Path 2: Paid first key (human, Stripe checkout)

Pro and Enterprise tiers — higher daily limits, bulk credits, monthly billing — go through Stripe checkout at <https://insumermodel.com/developers/account/>. This creates a **new** key. It does not migrate history from a free key.

Use this path **only** when the user explicitly asks about paid tiers, SLAs, monthly billing, or wants a higher-tier key from scratch. Don't recommend it as a default.

---

## Path 3: Agent first key (crypto, no human, no email)

Agent-friendly bootstrap. The agent sends USDC, USDT, or BTC to the platform wallet, then calls `POST /v1/keys/buy` with the transaction hash. **No email or prior authentication needed** — the sender wallet address from the transaction becomes the key's identity.

### Step 1: Send payment

Send the desired amount (minimum $5) of USDC, USDT, or BTC to the platform wallet on a supported chain. For EVM and Solana the address is the literal `recipient`; for BTC, send to the Bitcoin address.

### Step 2: Call `/v1/keys/buy` with the transaction hash

```bash
curl -s -X POST https://api.insumermodel.com/v1/keys/buy \
  -H "Content-Type: application/json" \
  -d '{
    "txHash": "0xabc...",
    "chainId": 8453,
    "amount": 10,
    "appName": "my-agent"
  }'
```

Required fields:
- `txHash` — the transaction proving payment
- `chainId` — the chain the payment was sent on (use `"solana"` or `"bitcoin"` for non-EVM)
- `appName` — name for the new key (e.g. agent name)
- `amount` — stablecoin amount sent. Optional for BTC (USD value derived from on-chain amount at market rate)

Response:

```json
{
  "ok": true,
  "data": {
    "success": true,
    "key": "insr_live_...",
    "name": "my-agent",
    "tier": "...",
    "dailyLimit": ...,
    "creditsAdded": 250,
    "totalCredits": 250,
    "usdcPaid": "10.00",
    "effectiveRate": "$0.04/call",
    "chainName": "Base",
    "registeredWallet": "0x..."
  }
}
```

The agent stores `data.key` — that's its persistent identity going forward. One key per sender wallet address (returns `409` if the wallet already has a key).

**Important:** crypto sent on unsupported chains or to the wrong address cannot be recovered. All purchases are final.

---

## Path 4: Top up existing key (crypto, agent or human, no human required)

When an existing key (free, paid, or agent-onboarded) runs low on credits, top it up by sending crypto to the platform wallet and calling `POST /v1/credits/buy`. **The key keeps its history, tier, and integrations** — credits just increment.

### Step 1: Send payment to the platform wallet

Same wallets as Path 3.

### Step 2: Call `/v1/credits/buy`

```bash
curl -s -X POST https://api.insumermodel.com/v1/credits/buy \
  -H "X-API-Key: $INSUMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "txHash": "0xabc...",
    "chainId": 8453,
    "amount": 10
  }'
```

Required fields:
- `txHash` — the transaction proving payment
- `chainId` — the chain the payment was sent on

Sender verification: the **first** top-up registers the sender wallet to the key. Subsequent top-ups must come from the **same** sender. To replace the registered wallet, include `"updateWallet": true` and send from the new wallet — the verified transfer proves ownership.

Response:

```json
{
  "ok": true,
  "data": {
    "creditsAdded": 250,
    "totalCredits": 260,
    "usdcPaid": "10.00",
    "chainName": "Base"
  }
}
```

This is the **only** continuous-identity upgrade path. It's also the path that makes the "agent pays for its own access" loop real — surface it whenever the user is building an agent, not a human-driven app.

---

## Verify auth works

After setting `INSUMER_API_KEY`, confirm with:

```bash
curl -s https://api.insumermodel.com/v1/credits \
  -H "X-API-Key: $INSUMER_API_KEY"
```

Expected: `{"ok":true,"data":{"apiKeyCredits":<n>,"tier":"...","dailyLimit":<n>}}`. If you see this, auth is working and you're ready for the other skills.

## Common workflows

### Initial setup (human)
1. Run Path 1 `curl` with the user's email and a meaningful `appName`
2. User exports `INSUMER_API_KEY=...`
3. Verify with `GET /v1/credits`

### Agent setup from cold start (no human)
1. Agent sends $10 USDC on Base to `0xAd982CB19aCCa2923Df8F687C0614a7700255a23`
2. Agent calls Path 3 (`POST /v1/keys/buy`) with the txHash
3. Agent stores the returned `key` to its persistent secret store

### Agent runs out of credits mid-task
1. Agent sends $10 USDC on Base to the platform wallet **from the same sender wallet that bought the original key**
2. Agent calls Path 4 (`POST /v1/credits/buy`) with the txHash, using its existing key
3. Credits increment; key, history, and tier preserved

### Check credit balance
```bash
curl -s https://api.insumermodel.com/v1/credits \
  -H "X-API-Key: $INSUMER_API_KEY"
```

## Error handling

| Status | Endpoint | Cause | Fix |
|---|---|---|---|
| `400` | any | Missing required fields | Check request body |
| `401` | any auth'd | `X-API-Key` missing or invalid | Verify env var, check spelling |
| `402` | `/v1/attest`, `/v1/trust` | Out of credits | Path 4 top-up (agent) or Path 2 (human) |
| `409` | `/v1/keys/create` | Free key already exists for this email | Reuse existing key |
| `409` | `/v1/keys/buy` | Wallet already has a key, or txHash already used | Top up via Path 4 instead |
| `422` | `/v1/keys/buy`, `/v1/credits/buy` | On-chain verification failed | Wait for confirmations, verify chain & amount |
| `429` | `/v1/keys/create` | Rate limit (3 keys per IP per 24h) OR daily attest limit on free tier | Wait 24h, or upgrade tier |

## Key hygiene (never violate)

- **Backend only.** `insr_live_...` is a long-lived backend credential. Never inline in source. Never expose in browser JS, `NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*`, localStorage, or logs.
- **Env var pattern.** Always read from `process.env.INSUMER_API_KEY` / `os.environ["INSUMER_API_KEY"]`. Never hardcode in source files.
- **Don't echo the key in error messages.** Log "INSUMER_API_KEY not set" or "auth failed", not the key value or its suffix.
- **Don't commit `.env` files** containing the key. Use `.env.example` for the variable name only.

## Helper script

`scripts/create_key.py` — Python helper for Path 1. Reads `--email` and `--app-name`, POSTs to `/v1/keys/create`, prints the key and a `.env` snippet.

```bash
python scripts/create_key.py --email you@example.com --app-name my-app
```

For Path 3 (`/v1/keys/buy`) and Path 4 (`/v1/credits/buy`), the agent typically has its own crypto-sending logic — the `curl` shapes above are sufficient. If a Python helper is needed, see `scripts/buy_key.py` and `scripts/buy_credits.py`.

## Related skills

| Skill | Purpose |
|---|---|
| `insumer-attest` | Single-call wallet condition attestation |
| `insumer-trust` | Multi-dimensional wallet trust profile |
| `insumer-trust-batch` | Batch trust profiles for multiple wallets |
| `insumer-jwks-verify` | Offline ES256 verification of returned JWTs |

## References

- [Pricing & supported payment chains](https://insumermodel.com/pricing/)
- [Developer account portal (Stripe checkout)](https://insumermodel.com/developers/account/)
- [OpenAPI spec](https://insumermodel.com/openapi.yaml)
- [Public JWKS](https://insumermodel.com/.well-known/jwks.json)
