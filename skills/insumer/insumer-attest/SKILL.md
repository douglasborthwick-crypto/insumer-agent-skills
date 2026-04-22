---
name: insumer-attest
description: >
  Wallet auth via InsumerAPI — condition-based access with cryptographically
  verifiable, ES256-signed, JWKS-verifiable boolean responses across 33 chains.
  Use when the user needs a "verified yes or no" on whether a wallet satisfies
  an on-chain condition (token balance, NFT ownership, EAS attestation,
  Farcaster ID), wants to gate a feature by what a wallet holds, add token
  gating, or compose a wallet_state signal in a multi-issuer trust envelope.
  Read → evaluate → sign, in one call.
allowed-tools: Bash
metadata:
  version: "0.1.0"
  author: InsumerAPI
---

# InsumerAPI Wallet Condition Attestation

**Boolean, not balance.** A signed `true`/`false` answering "does this wallet satisfy this condition right now?" — never the underlying balance. The response is ES256-signed and verifiable offline against the public JWKS at `https://insumermodel.com/.well-known/jwks.json`. The signing key never leaves the issuer; anyone holding the JWKS can independently re-run the verification.

You send conditions in. You get cryptographically verifiable results out.

## The primitive

Wallet auth is the OAuth-equivalent for what a wallet holds. The pattern is **read → evaluate → sign**:

1. **Read** — InsumerAPI reads the wallet's on-chain state on the requested chain
2. **Evaluate** — wallet state is checked against the supplied condition
3. **Sign** — a boolean result is returned, ES256-signed, with a `conditionHash` for tamper detection and a block anchor for replay defense

**No secrets. No identity-first. No static credentials.** Token gating is one form of condition-based access; this is the general primitive.

## Capabilities

- Single-call attestation across 33 chains: 30 EVM, Solana, XRPL, Bitcoin
- Up to 10 conditions per request — overall `pass` is `true` only if every condition is `true`
- Four condition types: `token_balance`, `nft_ownership`, `eas_attestation`, `farcaster_id`
- ES256 signature on every response, with optional ES256 JWT (`format: "jwt"`) for standard JWT-library verification
- Optional EIP-1186 Merkle storage proofs (`proof: "merkle"`) on token_balance conditions for 27 EVM chains
- 30-minute attestation TTL (`expiresAt` in response)

## Setup

Get the API key from the `insumer-auth` skill, then:

```bash
export INSUMER_API_KEY='insr_live_...'
```

## Reference values (do not hallucinate)

- **API base**: `https://api.insumermodel.com`
- **JWKS URL**: `https://insumermodel.com/.well-known/jwks.json`
- **Signing algorithm**: ES256 (ECDSA P-256)
- **Primary kid**: `insumer-attest-v1`
- **Auth header**: `X-API-Key: insr_live_...`
- **Attestation TTL**: 30 minutes (`expiresAt` in response)
- **Signature format**: base64 P1363 (88 chars) on the `sig` field; ES256 JWT on the `jwt` field when `format: "jwt"` is requested

## Usage

### Example 1: ERC-20 balance threshold

User says: "Check if `0xd8dA...6045` holds at least 100 USDC on Base."

```bash
curl -X POST https://api.insumermodel.com/v1/attest \
  -H "X-API-Key: $INSUMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "conditions": [
      {
        "type": "token_balance",
        "contractAddress": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "chainId": 8453,
        "threshold": 100,
        "decimals": 6,
        "label": "USDC >= 100 on Base"
      }
    ]
  }'
```

Returns `{ "ok": true, "data": { "attestation": { "pass": true|false, ... }, "sig": "...", "kid": "insumer-attest-v1" }, "meta": { "creditsRemaining": ..., "creditsCharged": 1, ... } }`.

### Example 2: NFT ownership

```bash
curl -X POST https://api.insumermodel.com/v1/attest \
  -H "X-API-Key: $INSUMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "conditions": [
      {
        "type": "nft_ownership",
        "contractAddress": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
        "chainId": 1,
        "label": "Bored Ape holder"
      }
    ]
  }'
```

### Example 3: EAS attestation via compliance template

```bash
curl -X POST https://api.insumermodel.com/v1/attest \
  -H "X-API-Key: $INSUMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "conditions": [
      {
        "type": "eas_attestation",
        "template": "coinbase_verified_account",
        "label": "Coinbase KYC verified"
      }
    ]
  }'
```

Available templates: see `references/condition-shapes.md` or `GET https://api.insumermodel.com/v1/compliance/templates`.

### Example 4: JWT format for standard library verification

Add `"format": "jwt"` to the request body to receive an ES256 JWT in the response (no extra cost). Verify with `jose` (Node), `PyJWT` (Python), `go-jose` (Go), etc., pointed at the JWKS URL. See the `insumer-jwks-verify` skill for the canonical recipe.

### Example 5: Merkle storage proofs (advanced)

```bash
curl -X POST https://api.insumermodel.com/v1/attest \
  -H "X-API-Key: $INSUMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "proof": "merkle",
    "conditions": [
      {
        "type": "token_balance",
        "contractAddress": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "chainId": 8453,
        "threshold": 100,
        "decimals": 6,
        "label": "USDC >= 100 on Base"
      }
    ]
  }'
```

`proof: "merkle"` returns EIP-1186 storage proofs alongside the boolean and **costs 2 credits instead of 1**. **Note**: Merkle mode reveals the raw on-chain balance to the caller — standard mode does not. Only opt in if the consumer needs the raw balance.

### Example 6: XRPL trust line

```bash
curl -X POST https://api.insumermodel.com/v1/attest \
  -H "X-API-Key: $INSUMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "xrplWallet": "rN7n3473SaZBCG4dFL83w7p1W9cgPJqKro",
    "conditions": [
      {
        "type": "token_balance",
        "contractAddress": "rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De",
        "chainId": "xrpl",
        "currency": "RLUSD",
        "threshold": 50,
        "label": "RLUSD >= 50 on XRPL"
      }
    ]
  }'
```

XRPL conditions use `xrplWallet` instead of `wallet` and require a `currency` field. See `references/chains.md` for the full chain coverage table.

## Code emission rules

When emitting integration code that calls `/v1/attest`, the agent MUST:

1. **Read the API key from an env var.** Never inline `insr_live_...`.
2. **Verify the signature offline.** Pair this skill with `insumer-jwks-verify`. The signed boolean is the product — the JSON body alone is untrusted.
3. **Set `decimals` explicitly for stablecoins.** USDC, USDT, USDC.e are all `6` decimals on every chain. The API defaults to `18` when omitted — getting this wrong silently fails the threshold check.
4. **Call from a backend, not a browser.** The API key is a backend credential.
5. **Don't cache the verdict.** Cache the JWKS (the `jose` library's `createRemoteJWKSet` does this for you). Pass/fail expires in 30 minutes — wallet state changes.
6. **Don't request `proof: "merkle"` unless the caller needs the raw balance.** Standard mode is boolean-not-balance by construction; Merkle mode opts out of that privacy property.

## Helper script

`scripts/attest.py` — Python helper that wraps `POST /v1/attest`. Reads `INSUMER_API_KEY` from env, accepts a JSON conditions payload on stdin or via `--conditions-file`, prints the signed response.

```bash
echo '{"wallet":"0x...","conditions":[{"type":"token_balance",...}]}' | python scripts/attest.py
```

## Error handling

| Status | Cause | Fix |
|---|---|---|
| `400` | Missing/invalid wallet, conditions, or condition fields | Check request body against `references/condition-shapes.md` |
| `401` | Missing or invalid API key | See `insumer-auth` skill |
| `402` | Out of verification credits | Top up via `POST /v1/credits/buy` |
| `503` | Upstream blockchain data source unavailable | Retryable after a short delay; no credits charged |

## Related skills

| Skill | Purpose |
|---|---|
| `insumer-auth` | Get a free API key, configure env vars |
| `insumer-jwks-verify` | Offline ES256 verification of the response |
| `insumer-trust` | Curated multi-dimensional wallet profile (alternative to custom conditions) |

## References

- [chains.md](references/chains.md) — full 33-chain coverage table
- [condition-shapes.md](references/condition-shapes.md) — every supported condition type with full request shape
- [InsumerAPI OpenAPI spec](https://insumermodel.com/openapi.yaml)
- [Public JWKS](https://insumermodel.com/.well-known/jwks.json)
