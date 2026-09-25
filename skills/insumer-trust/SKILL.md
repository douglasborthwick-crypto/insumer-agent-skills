---
name: insumer-trust
description: >
  InsumerAPI wallet trust profile: a curated multi-dimensional condition-based
  access bundle for a single wallet. 45 base checks across 26 chains in 5
  dimensions (stablecoins, governance, NFTs, staking, institutional
  stablecoins), plus optional Solana, XRPL, Bitcoin and Tron dimensions (up to
  50 checks across 28 chains in 9 dimensions). Use when the user wants an InsumerAPI
  trust profile, a pre-built signed wallet snapshot rather than conditions
  specified one by one (for example an InsumerAPI pre-transaction trust check). The profile is signed once, as a whole. Carry it unchanged:
  never re-sign or wrap it.
metadata:
  version: "0.2.0"
  author: InsumerAPI
---

# InsumerAPI Wallet Trust Profile

A curated condition bundle for a single wallet. Same primitive as `insumer-attest` (read → evaluate → sign), but the conditions are pre-defined — 45 base checks across 26 chains in 5 dimensions, with optional cross-chain extensions. **Boolean, not balance, on every check.**

Pick this skill when the developer wants a snapshot. Pick `insumer-attest` when they want to specify their own conditions.

## What you get

- **45 base checks** across **26 chains** in **5 dimensions**:
  - **Stablecoins** (27) — USDC and USDT balances across 22 EVM chains, including USDC on Arc
  - **Governance** (4) — UNI and AAVE on Ethereum, ARB on Arbitrum, OP on Optimism
  - **NFTs** (3) — BAYC, Pudgy Penguins, Wrapped CryptoPunks
  - **Staking** (3) — stETH, rETH, cbETH
  - **Institutional stablecoins** (8) — EURCV, USDCV, USDC, and BENJI across Ethereum, Solana, XRPL, Stellar, and Sui. Always present; the Solana, XRPL, Stellar and Sui entries are evaluated only when the matching wallet is supplied, and are otherwise marked `evaluated: false`
- **Optional extensions** (when extra wallet addresses are provided):
  - **Solana USDC** — pass `solanaWallet`
  - **XRPL stablecoins** — pass `xrplWallet` (RLUSD + USDC checks)
  - **Bitcoin holdings** — pass `bitcoinWallet` (native BTC balance)
  - **Tron USDT** — pass `tronWallet` (USDT-TRC20)
  - **Stellar / Sui** — pass `stellarWallet` / `suiWallet`. These add no checks and no dimension; they let the Stellar and Sui entries in institutional stablecoins be evaluated
- Up to 50 total checks across 28 chains in 9 dimensions when all extensions are included
- Each check returns its own boolean; the response includes per-dimension and overall summaries
- 3 credits standard, 6 credits with `proof: "merkle"`

## Architectural property to preserve

The whole trust profile is signed once by InsumerAPI: one `sig` under `kid: insumer-trust-v2` (plus the post-quantum companion `pqSig` / `pqKid`) covers the entire `trust` object. There are no per-dimension or per-check signatures. **Do not add an orchestrator-layer wrap.** If you build a multi-issuer trust envelope that includes this profile, carry the signed object exactly as issued, beside the other issuers' signed objects, and never re-sign it or wrap it under a new envelope signature. Verifiers should be able to check InsumerAPI's signature directly against its JWKS.

## Setup

```bash
export INSUMER_API_KEY='insr_live_...'
```

## Reference values

- **Endpoint**: `POST https://api.insumermodel.com/v1/trust`
- **Cost**: 3 credits standard, 6 credits with `proof: "merkle"`
- **Wallet pattern**: `wallet` is required (EVM, `0x` + 40 hex chars). `solanaWallet`, `xrplWallet`, `bitcoinWallet`, `tronWallet`, `stellarWallet` (G-address) and `suiWallet` (`0x` + 64 hex chars) are optional add-ons.
- **Trust profile ID format**: `TRST-XXXXX` (returned in `data.trust.id`)

## Usage

### Example 1: EVM-only profile

```bash
curl -X POST https://api.insumermodel.com/v1/trust \
  -H "X-API-Key: $INSUMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
  }'
```

Response shape (abbreviated):

```json
{
  "ok": true,
  "data": {
    "trust": {
      "id": "TRST-A1B2C",
      "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
      "conditionSetVersion": "v2",
      "dimensions": {
        "stablecoins":               { "checks": [...], "passCount": 3, "failCount": 24, "notEvaluatedCount": 0, "total": 27 },
        "governance":                { "checks": [...], "passCount": 2, "failCount": 2,  "notEvaluatedCount": 0, "total": 4 },
        "nfts":                      { "checks": [...], "passCount": 0, "failCount": 3,  "notEvaluatedCount": 0, "total": 3 },
        "staking":                   { "checks": [...], "passCount": 1, "failCount": 2,  "notEvaluatedCount": 0, "total": 3 },
        "institutional_stablecoins": { "checks": [...], "passCount": 0, "failCount": 2,  "notEvaluatedCount": 6, "total": 8 }
      },
      "summary": { "totalChecks": 45, "totalPassed": 6, "totalFailed": 33, "totalNotEvaluated": 6, "dimensionsWithActivity": 3, "dimensionsChecked": 5 },
      "profiledAt": "...",
      "expiresAt": "..."
    },
    "sig": "...",
    "kid": "insumer-trust-v2",
    "pqSig": "...",
    "pqKid": "insumer-trust-pq1"
  },
  "meta": {
    "creditsRemaining": ...,
    "creditsCharged": 3
  }
}
```

### Example 2: With Solana USDC

```bash
curl -X POST https://api.insumermodel.com/v1/trust \
  -H "X-API-Key: $INSUMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "solanaWallet": "5xY...solanaAddress"
  }'
```

### Example 3: Multi-chain profile (EVM + Solana + XRPL + Bitcoin)

```bash
curl -X POST https://api.insumermodel.com/v1/trust \
  -H "X-API-Key: $INSUMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "solanaWallet": "5xY...solanaAddress",
    "xrplWallet": "rN7n3473SaZBCG4dFL83w7p1W9cgPJqKro",
    "bitcoinWallet": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
  }'
```

Each provided Solana, XRPL, Bitcoin or Tron wallet adds its dimension to the response. A Stellar or Sui wallet (`stellarWallet`, `suiWallet`) adds no dimension; it lets the matching institutional-stablecoin entries be evaluated instead of marked `evaluated: false`.

### Example 4: Merkle proofs (advanced)

```bash
curl -X POST https://api.insumermodel.com/v1/trust \
  -H "X-API-Key: $INSUMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "proof": "merkle"
  }'
```

EIP-1186 proofs on every EVM token check (stablecoins, governance, staking, and the EVM institutional rows) where the chain supports proofs; none for NFTs or non-EVM chains. **Costs 6 credits** instead of 3, or 3 if no proof could be delivered, and reveals raw on-chain balances. Only opt in if the consumer explicitly needs the raw balances.

## When to use trust profile vs. custom attest

| User asks for... | Use |
|---|---|
| "Verify this wallet holds X on chain Y" | `insumer-attest` |
| "Gate by USDC balance on Base" | `insumer-attest` |
| "Pre-transaction trust check" | `insumer-trust` |
| "Show me what this wallet holds across chains" | `insumer-trust` |
| "Multi-dimensional wallet profile" | `insumer-trust` |
| "Should I transact with this wallet" | `insumer-trust` |

For multiple wallets in one call, use `insumer-trust-batch`.

## Code emission rules

1. **Read the API key from an env var.** Never inline.
2. **Verify the signature offline.** Use `insumer-jwks-verify`. The signed boolean(s) is the product.
3. **Don't re-sign or wrap the profile.** One InsumerAPI signature covers the whole `trust` object; placing it under a new envelope signature defeats the verification chain. A check whose wallet was not supplied is marked `evaluated: false` and counted in `totalNotEvaluated`, never as a failure.
4. **Don't cache the verdict.** Cache the JWKS, not the trust profile result. Wallet state changes.
5. **Backend only.** The API key is a backend credential.

## Helper script

`scripts/trust.py` — Python helper that wraps `POST /v1/trust`. Reads `INSUMER_API_KEY` from env, accepts `--wallet`, `--solana`, `--xrpl`, `--bitcoin`, `--tron`, `--stellar`, `--sui`, `--proof merkle`.

```bash
python scripts/trust.py --wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

## Error handling

| Status | Cause | Fix |
|---|---|---|
| `400` | Missing `wallet` or invalid format | EVM wallet `^0x[a-fA-F0-9]{40}$` is required |
| `401` | Missing/invalid API key | See `insumer-auth` |
| `402` | Out of credits | Top up via Path 4 in `insumer-auth` |
| `503` | Upstream blockchain data source unavailable | Retryable; no credits charged |

## Related skills

| Skill | Purpose |
|---|---|
| `insumer-auth` | API key creation, top-up |
| `insumer-attest` | Custom condition (pick this if not using the curated bundle) |
| `insumer-trust-batch` | Same primitive for multiple wallets in one call |
| `insumer-jwks-verify` | Offline ES256 verification |

## References

- [InsumerAPI OpenAPI spec](https://insumermodel.com/openapi.yaml)
- [Public JWKS](https://insumermodel.com/.well-known/jwks.json)
- [Developer docs — trust profile](https://insumermodel.com/developers/trust/)
