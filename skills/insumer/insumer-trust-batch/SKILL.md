---
name: insumer-trust-batch
description: >
  InsumerAPI batch wallet trust profiles — same curated bundle as insumer-trust,
  but for multiple wallets in a single call. Use when the user needs trust
  profiles for a list of wallets (airdrop eligibility, allowlist scoring, batch
  pre-transaction checks). Each wallet's dimensions are returned with their
  original issuer signatures intact — no orchestrator wrap.
allowed-tools: Bash
metadata:
  version: "0.1.0"
  author: InsumerAPI
---

# InsumerAPI Batch Wallet Trust Profile

Same curated condition-based access bundle as `insumer-trust`, but accepts an array of wallets in one request. Useful for airdrop eligibility scoring, allowlist evaluation, batch pre-transaction checks, or any flow that needs `N` profiles at once.

Each wallet's per-dimension attestations retain their original issuer signatures. **No orchestrator wrap.**

## Setup

```bash
export INSUMER_API_KEY='insr_live_...'
```

## Reference values

- **Endpoint**: `POST https://api.insumermodel.com/v1/trust/batch`
- **Cost**: 3 credits per wallet standard, 6 credits per wallet with `proof: "merkle"`
- **Wallet limit**: see OpenAPI spec for the current per-call cap
- **Profile ID format per wallet**: `TRST-XXXXX`

## Usage

### Example 1: Two EVM wallets

```bash
curl -X POST https://api.insumermodel.com/v1/trust/batch \
  -H "X-API-Key: $INSUMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "wallets": [
      "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
      "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"
    ]
  }'
```

Response shape (abbreviated):

```json
{
  "ok": true,
  "data": {
    "trust": [
      {
        "id": "TRST-A1B2C",
        "wallet": "0xd8dA...",
        "dimensions": { ... },
        "sig": "...",
        "kid": "insumer-attest-v1"
      },
      {
        "id": "TRST-D3E4F",
        "wallet": "0xAb58...",
        "dimensions": { ... },
        "sig": "...",
        "kid": "insumer-attest-v1"
      }
    ]
  },
  "meta": {
    "creditsRemaining": ...,
    "creditsCharged": 6
  }
}
```

Each entry in `data.trust` carries its own signature — verify them independently with `insumer-jwks-verify`.

### Example 2: Batch with Merkle proofs

```bash
curl -X POST https://api.insumermodel.com/v1/trust/batch \
  -H "X-API-Key: $INSUMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "wallets": ["0x...", "0x...", "0x..."],
    "proof": "merkle"
  }'
```

Cost scales linearly: `wallets.length * 6` credits. Reveals raw on-chain balances per check — only opt in if needed.

## When to use batch vs single

| Situation | Use |
|---|---|
| Single wallet | `insumer-trust` |
| 2+ wallets, same call | `insumer-trust-batch` |
| Different conditions per wallet | Loop over `insumer-attest` (custom conditions) |
| Same custom conditions for many wallets | Currently no batch endpoint — loop over `insumer-attest` |

## Code emission rules

1. **Read the API key from an env var.** Never inline.
2. **Verify each profile's signature independently.** The batch wrapper does not produce an aggregate signature; each entry in `data.trust[]` is independently signed.
3. **Backend only.** The API key is a backend credential.
4. **Don't cache the verdict.** Wallet state changes.
5. **Pre-validate wallet format client-side** before sending — invalid addresses in a batch can cause the whole call to fail validation.

## Helper script

`scripts/trust_batch.py` — Python helper. Reads `INSUMER_API_KEY` from env, accepts a wallet list via `--wallets-file` (one per line) or `--wallets w1,w2,w3`.

```bash
python scripts/trust_batch.py --wallets-file allowlist.txt
```

## Error handling

| Status | Cause | Fix |
|---|---|---|
| `400` | Missing `wallets` array, invalid wallet format, or exceeds per-call cap | Validate addresses, split into smaller batches |
| `401` | Missing/invalid API key | See `insumer-auth` |
| `402` | Out of credits | Top up via Path 4 in `insumer-auth` |
| `503` | Upstream blockchain data source unavailable | Retryable; no credits charged for failed batches |

## Related skills

| Skill | Purpose |
|---|---|
| `insumer-auth` | API key creation, top-up |
| `insumer-trust` | Single-wallet curated profile |
| `insumer-attest` | Custom condition (single call, up to 10 conditions) |
| `insumer-jwks-verify` | Offline ES256 verification — apply per profile entry |

## References

- [InsumerAPI OpenAPI spec](https://insumermodel.com/openapi.yaml)
- [Public JWKS](https://insumermodel.com/.well-known/jwks.json)
- [Developer docs — trust profile](https://insumermodel.com/developers/trust/)
