# JWKS Format & Verification Reference

## JWKS document shape

`GET https://insumermodel.com/.well-known/jwks.json` returns a standard [RFC 7517](https://datatracker.ietf.org/doc/html/rfc7517) JWKS document:

```json
{
  "keys": [
    {
      "kty": "EC",
      "crv": "P-256",
      "x": "<base64url x coordinate>",
      "y": "<base64url y coordinate>",
      "use": "sig",
      "alg": "ES256",
      "kid": "insumer-attest-v1"
    }
  ]
}
```

| Field | Value | Meaning |
|---|---|---|
| `kty` | `"EC"` | Elliptic-curve key |
| `crv` | `"P-256"` | NIST P-256 curve (secp256r1) |
| `x`, `y` | base64url | Public key coordinates |
| `use` | `"sig"` | For signature verification |
| `alg` | `"ES256"` | ECDSA with SHA-256 |
| `kid` | `"insumer-attest-v1"` | Current key identifier |

The endpoint is cached for 24 hours at the edge (`Cache-Control: public, max-age=86400`) and never requires authentication.

## What's signed

For `/v1/attest`:
- The `data.attestation` object — including `pass`, `results`, `conditionHash`, `blockNumber`, `blockTimestamp`, `wallet`, `expiresAt`

For `/v1/trust` and `/v1/trust/batch`:
- The `data.trust` object (or each entry in `data.trust[]` for batch) — including `id`, `wallet`, `dimensions`, `conditionSetVersion`, `expiresAt`

## JWT claim mapping

When `format: "jwt"` is requested, the response includes a `data.jwt` field with these claims:

| Claim | Source | Meaning |
|---|---|---|
| `iss` | `https://api.insumermodel.com` | Issuer |
| `sub` | wallet address | Subject |
| `jti` | unique attestation ID | JWT ID — useful for replay defense |
| `iat` | unix timestamp | Issued at |
| `exp` | iat + 30 min | Expiration |
| `pass` | boolean | Overall verification result |
| `results` | array | Per-condition booleans (attest only) |
| `dimensions` | object | Per-dimension results (trust only) |
| `conditionHash` | array of hex strings | SHA-256 of each condition's canonical evaluatedCondition. Top-level JWT payload aggregates one entry per condition (1-element array for single-condition requests). The per-result `conditionHash` inside `results[].conditionHash` is a single string. |
| `blockNumber` | hex string | Block number on EVM, slot on Solana, ledgerIndex on XRPL |
| `blockTimestamp` | ISO 8601 | Block timestamp |

## conditionHash recomputation

The `conditionHash` is `sha256(canonical_json(evaluatedCondition))` with sorted keys, prefixed with `0x`. Verifiers can independently recompute it from `data.attestation.evaluatedCondition` to confirm exactly what condition logic was evaluated:

```python
import json
import hashlib

def recompute_condition_hash(evaluated_condition: dict) -> str:
    canonical = json.dumps(
        evaluated_condition,
        separators=(",", ":"),  # no whitespace
        sort_keys=True,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return "0x" + digest
```

This is belt-and-suspenders — the JWT signature already covers `conditionHash` — but it lets a downstream service confirm the exact predicate, not just that *some* result was signed.

## Key rotation

Key rotation is signaled via the `kid` field in signed responses. When a new key is rolled in:

1. JWKS endpoint returns **both** the old and new keys for the rotation window
2. New responses are signed with the new `kid`
3. Old `kid` continues to verify historical attestations until the rotation window closes
4. After the window, old `kid` is removed from JWKS — historical attestations beyond the 30-min TTL are no longer verifiable (which is correct: they've expired)

Verifiers should:
- Always look up the public key by `kid` (don't hardcode)
- Use `createRemoteJWKSet` (jose) or `PyJWKClient` (PyJWT) for automatic refresh
- Never cache the public key directly — cache the JWKS document and let the library handle key lookup

## Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| `unknown kid` after rotation | Stale JWKS cache | Force refresh; if persistent, kid was retired |
| `JWT signature invalid` | Payload tampered or wrong key | Reject; do not retry with different keys |
| `JWT expired` (`exp` in past) | Beyond 30-min TTL | Re-request a fresh attestation |
| `JWT issuer mismatch` | Response not from InsumerAPI | Reject |
| `algorithm not allowed` | Verifier didn't pin ES256 | Always pass `algorithms: ['ES256']` |

## Library-specific gotchas

### `jose` (Node)
- `createRemoteJWKSet` caches with `cooldownDuration` and `cacheMaxAge` — defaults are sane, don't override unless you know why
- Always pass `algorithms: ['ES256']` to `jwtVerify` — never accept `none` or default

### `PyJWT` (Python)
- Requires `pip install 'pyjwt[crypto]'` (the `cryptography` extra) for ES256 support
- `PyJWKClient.get_signing_key_from_jwt()` handles kid lookup automatically
- Pass `algorithms=["ES256"]` and `issuer="https://api.insumermodel.com"` to `jwt.decode()`

### `go-jose` (Go)
- Use `jose.ParseSigned` then verify against the JWKS keys
- Pin `Algorithm: jose.ES256`

## See also

- [SKILL.md](../SKILL.md) — usage examples and code emission rules
- [JWT spec (RFC 7519)](https://datatracker.ietf.org/doc/html/rfc7519)
- [JWS spec (RFC 7515)](https://datatracker.ietf.org/doc/html/rfc7515)
- [JWK spec (RFC 7517)](https://datatracker.ietf.org/doc/html/rfc7517)
- [`insumer-verify` on npm](https://www.npmjs.com/package/insumer-verify)
