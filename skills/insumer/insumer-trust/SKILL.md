---
name: insumer-trust
description: >
  InsumerAPI wallet trust profile — curated multi-dimensional condition-based
  access bundle for a single wallet. 36 base checks across 4 dimensions
  (stablecoins, governance, NFTs, staking) on EVM, plus optional Solana USDC,
  XRPL stablecoins, and Bitcoin holdings. Use when the user wants a pre-built
  wallet snapshot rather than specifying conditions one-by-one — e.g.
  pre-transaction trust check, KYC-of-state, "tell me what this wallet holds
  across chains." Each dimension's signature retains its original issuer; no
  orchestrator wrap.
allowed-tools: Bash
metadata:
  version: "0.1.0"
  author: InsumerAPI
---

# InsumerAPI Wallet Trust Profile

A curated condition bundle for a single wallet. Same primitive as `insumer-attest` (read → evaluate → sign), but the conditions are pre-defined — 36 base checks across 4 dimensions, with optional cross-chain extensions. **Boolean, not balance, on every check.**

Pick this skill when the developer wants a snapshot. Pick `insumer-attest` when they want to specify their own conditions.

## What you get

- **36 base checks** across **4 dimensions** on EVM:
  - **Stablecoins** — USDC and USDT balances on each major EVM chain
  - **Governance** — major governance token holdings
  - **NFTs** — collection holdings
  - **Staking** — staked balances on major staking protocols
- **Optional extensions** (when extra wallet addresses are provided):
  - **Solana USDC** — pass `solanaWallet`
  - **XRPL stablecoins** — pass `xrplWallet` (RLUSD + USDC checks)
  - **Bitcoin holdings** — pass `bitcoinWallet` (native BTC balance)
- Up to 39 total checks when all extensions are included
- Each check returns its own boolean; the response includes per-dimension and overall summaries
- 3 credits standard, 6 credits with `proof: "merkle"`

## Architectural property to preserve

Each dimension's check is signed with its original issuer's signature. **There is no orchestrator-layer wrap** over the aggregated response. If you build a multi-issuer trust envelope using this output, preserve that property — combine the per-dimension attestations as separate signed objects, never re-sign or wrap them under a single envelope signature.

## Setup

```bash
export INSUMER_API_KEY='insr_live_...'
```

## Reference values

- **Endpoint**: `POST https://api.insumermodel.com/v1/trust`
- **Cost**: 3 credits standard, 6 credits with `proof: "merkle"`
- **Wallet pattern**: `wallet` is required (EVM, `0x` + 40 hex chars). Solana / XRPL / Bitcoin wallets are optional add-ons.
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
      "conditionSetVersion": "v1",
      "dimensions": {
        "stablecoins": { "summary": "...", "checks": [...] },
        "governance":  { "summary": "...", "checks": [...] },
        "nfts":        { "summary": "...", "checks": [...] },
        "staking":     { "summary": "...", "checks": [...] }
      }
    },
    "sig": "...",
    "kid": "insumer-attest-v1"
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

Each provided wallet adds its dimension to the response.

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

EIP-1186 Merkle storage proofs on stablecoin and governance checks. **Costs 6 credits** instead of 3, and reveals raw on-chain balances. Only opt in if the consumer explicitly needs the raw balances.

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
3. **Don't re-sign or wrap the dimension attestations.** Each dimension carries its own issuer signature; aggregating them under a new envelope sig defeats the verification chain.
4. **Don't cache the verdict.** Cache the JWKS, not the trust profile result. Wallet state changes.
5. **Backend only.** The API key is a backend credential.

## Helper script

`scripts/trust.py` — Python helper that wraps `POST /v1/trust`. Reads `INSUMER_API_KEY` from env, accepts `--wallet`, `--solana`, `--xrpl`, `--bitcoin`, `--proof merkle`.

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
