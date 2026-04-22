---
name: insumer-jwks-verify
description: >
  Offline ES256 verification of InsumerAPI signed responses against the public
  JWKS. Use when the user receives a signed attestation from /v1/attest,
  /v1/trust, or /v1/trust/batch and needs to verify the signature without
  trusting the JSON body. Covers both the JWT path (jose / PyJWT / go-jose) and
  the raw sig path (ES256 over the canonical attestation/trust object).
allowed-tools: Bash
metadata:
  version: "0.1.0"
  author: InsumerAPI
---

# InsumerAPI Offline JWKS Verification

The signed boolean is the product. The JSON body alone is untrusted — anyone can fabricate a JSON response. **Verify the signature, every time.**

InsumerAPI signs every `/v1/attest`, `/v1/trust`, and `/v1/trust/batch` response with ES256 (ECDSA P-256). The public key is published as a standard JWKS at `https://insumermodel.com/.well-known/jwks.json`. The signing key never leaves the issuer; anyone holding the JWKS can independently re-run the verification — no callback to InsumerAPI required.

## Reference values (do not hallucinate)

- **JWKS URL**: `https://insumermodel.com/.well-known/jwks.json`
- **Algorithm**: ES256 (ECDSA P-256)
- **Primary kid**: `insumer-attest-v1`
- **JWT issuer claim** (when `format: "jwt"` is requested): `https://api.insumermodel.com`
- **Raw signature format**: base64 P1363 (88 chars) on the `sig` field

## Two verification paths

InsumerAPI returns **two** verifiable forms in every signed response:

1. **`sig` field** — base64 P1363 ES256 signature over the canonical (sorted-key JSON) of `data.attestation` / `data.trust`. Verify with any ES256 library + the JWKS public key.
2. **`jwt` field** *(only when `"format": "jwt"` is in the request body)* — standard ES256 JWT with the same payload as standard JWT claims. Verify with any standard JWT library pointed at the JWKS URL.

The `jwt` path is easier when the consumer is already using a JWT library; the `sig` path is more compact and avoids JWT envelope overhead. Both produce the same security guarantees.

## Recipe 1: JWT verification (Node.js, `jose`)

Add `"format": "jwt"` to the `/v1/attest` or `/v1/trust` request body, then:

```javascript
import { createRemoteJWKSet, jwtVerify } from 'jose';

const JWKS = createRemoteJWKSet(
  new URL('https://insumermodel.com/.well-known/jwks.json')
);

async function verifyAttestation(jwtString) {
  const { payload } = await jwtVerify(jwtString, JWKS, {
    issuer: 'https://api.insumermodel.com',
    algorithms: ['ES256'],
  });
  // payload.pass is the verified boolean
  // payload.conditionHash, payload.blockNumber, payload.blockTimestamp
  // are also verified as part of the signed JWT
  return payload;
}
```

`createRemoteJWKSet` caches the JWKS automatically with sane defaults. Don't fetch the JWKS yourself on every call.

## Recipe 2: JWT verification (Python, `PyJWT` + `cryptography`)

```python
import jwt
from jwt.jwks_client import PyJWKClient

jwks_client = PyJWKClient("https://insumermodel.com/.well-known/jwks.json")

def verify_attestation(jwt_string: str) -> dict:
    signing_key = jwks_client.get_signing_key_from_jwt(jwt_string)
    payload = jwt.decode(
        jwt_string,
        signing_key.key,
        algorithms=["ES256"],
        issuer="https://api.insumermodel.com",
    )
    # payload["pass"] is the verified boolean
    return payload
```

## Recipe 3: Raw `sig` verification (Node.js)

When the response was returned without `format: "jwt"`:

```javascript
import { importJWK, compactVerify, calculateJwkThumbprint } from 'jose';

async function verifyRawSig(response) {
  // 1. Fetch the JWKS once and cache it
  const jwksRes = await fetch('https://insumermodel.com/.well-known/jwks.json');
  const { keys } = await jwksRes.json();
  const jwk = keys.find(k => k.kid === response.kid);
  if (!jwk) throw new Error(`unknown kid ${response.kid}`);
  const publicKey = await importJWK(jwk, 'ES256');

  // 2. Recompute canonical payload bytes (sorted-key JSON of attestation/trust)
  const canonical = JSON.stringify(response.attestation, Object.keys(response.attestation).sort());

  // 3. Verify the base64 P1363 signature
  // (use insumer-verify npm package for the canonical signing scheme)
  // ...
}
```

For raw sig verification, the official package is **`insumer-verify`** on npm:

```bash
npm install insumer-verify
```

```javascript
import { verifyAttestation } from 'insumer-verify';

const ok = await verifyAttestation(response);
// ok === true if signature valid, throws if invalid or kid unknown
```

## Recipe 4: Conditional verification + tamper detection

Beyond signature verification, you can independently re-derive the `conditionHash` to confirm the condition wasn't tampered with:

```javascript
import { keccak256 } from 'viem';

function recomputeConditionHash(evaluatedCondition) {
  const canonical = JSON.stringify(
    evaluatedCondition,
    Object.keys(evaluatedCondition).sort()
  );
  return '0x' + keccak256(new TextEncoder().encode(canonical));
}

// After signature verification, re-derive and compare
const recomputed = recomputeConditionHash(payload.evaluatedCondition);
if (recomputed !== payload.conditionHash) {
  throw new Error('conditionHash mismatch — payload may have been tampered with');
}
```

This is belt-and-suspenders — the signature already covers `conditionHash` — but it lets a verifier confirm the *exact condition logic* that was evaluated, not just that the result was signed.

## Code emission rules

1. **Cache the JWKS, not the verdict.** Libraries like `jose`'s `createRemoteJWKSet` and `PyJWT`'s `PyJWKClient` cache automatically with TTL. Do not cache `pass` — wallet state changes and the attestation has a 30-minute `expiresAt`.
2. **Pin the algorithm.** Always pass `algorithms: ['ES256']` — never accept any algorithm. This blocks "alg confusion" attacks.
3. **Pin the issuer.** Always pass `issuer: 'https://api.insumermodel.com'` for JWT verification.
4. **Verify in the trust boundary.** Verify on the server that's making the access decision — never verify in the browser and trust the result. (Browsers can verify; they just can't be the trust boundary.)
5. **Fail closed.** If verification throws, deny access. Never default to "allow" on verification failure.

## Helper script

`scripts/verify.py` — Python helper that takes a JWT or raw response on stdin and verifies it against the public JWKS. Prints `OK` + payload, or `INVALID` + reason.

```bash
echo '{"jwt":"eyJhbG...","kid":"insumer-attest-v1"}' | python scripts/verify.py
```

## Error handling

| Symptom | Cause | Fix |
|---|---|---|
| "unknown kid" | Response signed with a key not in current JWKS | Refresh JWKS cache; if persistent, the key may be rotated — check JWKS URL directly |
| "JWT signature invalid" | Payload tampered, or wrong public key | Confirm `kid` matches a JWKS entry, confirm algorithm pinned to ES256 |
| "JWT issuer mismatch" | Issuer claim doesn't match `https://api.insumermodel.com` | Confirm response actually came from InsumerAPI |
| "JWT expired" | Beyond 30-min TTL | Re-request a fresh attestation; do not extend TTL |
| "conditionHash mismatch" | Condition object was modified after signing | Untrusted payload — reject |

## Related skills

| Skill | Purpose |
|---|---|
| `insumer-auth` | Get a key (verifying responses doesn't need a key, but signing them does) |
| `insumer-attest` | Produces signed responses to verify |
| `insumer-trust` | Produces signed responses to verify |
| `insumer-trust-batch` | Verify each profile entry independently |

## References

- [jwks-format.md](references/jwks-format.md) — full JWKS document shape, key rotation policy, JWT claim list
- [`insumer-verify` on npm](https://www.npmjs.com/package/insumer-verify) — canonical raw-sig verification package
- [Public JWKS](https://insumermodel.com/.well-known/jwks.json) — fetch the live key set
- [JWT spec (RFC 7519)](https://datatracker.ietf.org/doc/html/rfc7519)
- [JWS spec (RFC 7515)](https://datatracker.ietf.org/doc/html/rfc7515)
