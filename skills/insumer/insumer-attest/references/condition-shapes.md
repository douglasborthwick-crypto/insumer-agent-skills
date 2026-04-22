# Condition Shapes

Every condition object passed in `/v1/attest` (`conditions[]` array, 1–10 items) follows one of four shapes determined by the `type` field.

## 1. `token_balance`

Threshold check on a fungible token balance.

```json
{
  "type": "token_balance",
  "contractAddress": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  "chainId": 8453,
  "threshold": 100,
  "decimals": 6,
  "label": "USDC >= 100 on Base"
}
```

| Field | Required | Notes |
|---|---|---|
| `contractAddress` | yes (EVM/Solana/XRPL) | Token contract. For XRPL: `"native"` for XRP, or the issuer r-address for trust lines. For Bitcoin: must be `"native"`. |
| `chainId` | yes | Numeric for EVM, `"solana"`/`"xrpl"`/`"bitcoin"` for non-EVM |
| `threshold` | yes | Minimum balance in **human units**. Must be `> 0` when `proof: "merkle"` (use `0.000001` for prove-any-balance). |
| `decimals` | recommended | **Always set explicitly for stablecoins** (USDC/USDT/USDC.e are `6`). API defaults to `18` if omitted. Auto-detected for EVM ERC-20s when reliable. |
| `currency` | XRPL only | Trust line currency code (e.g. `"RLUSD"`, `"USDC"`) |
| `label` | recommended | Human-readable label (max 100 chars) |

Operator: `gte` (>=).

## 2. `nft_ownership`

Check whether the wallet owns at least one NFT in a collection.

```json
{
  "type": "nft_ownership",
  "contractAddress": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
  "chainId": 1,
  "label": "Bored Ape holder"
}
```

| Field | Required | Notes |
|---|---|---|
| `contractAddress` | yes | NFT contract address (ERC-721 or ERC-1155 on EVM, NFToken issuer on XRPL) |
| `chainId` | yes | |
| `taxon` | XRPL only | Filter by issuer + taxon (optional, NFToken filtering on XRPL) |
| `label` | recommended | |

Operator: `gt` (> 0).

## 3. `eas_attestation`

Verify the wallet has a valid EAS (Ethereum Attestation Service) attestation.

### Via compliance template (preferred)

```json
{
  "type": "eas_attestation",
  "template": "coinbase_verified_account",
  "label": "Coinbase KYC verified"
}
```

Available templates (current list — fetch live from `GET https://api.insumermodel.com/v1/compliance/templates`):

| Template | Provider | Chain |
|---|---|---|
| `coinbase_verified_account` | Coinbase | Base (8453) |
| `coinbase_verified_country` | Coinbase | Base (8453) |
| `coinbase_one` | Coinbase | Base (8453) |
| `gitcoin_passport_score` | Gitcoin | Optimism (10) |
| `gitcoin_passport_active` | Gitcoin | Optimism (10) |

### Via raw schema ID (advanced)

```json
{
  "type": "eas_attestation",
  "schemaId": "0xf8b05c79f090979bf4a80270aba232dff11a10d9ca55c4f88de95317970f0de9",
  "attester": "0x357458739F90461b99789350868CD7CF330Dd7EE",
  "indexer": "0x2c7eE1E5f416dfF40054c27A62f7B357C4E8619C",
  "chainId": 8453,
  "label": "Coinbase Verified Account"
}
```

| Field | Required | Notes |
|---|---|---|
| `template` | one-of | Compliance template name |
| `schemaId` | one-of | Raw EAS schema ID (with `attester`, `indexer`, `chainId`) |
| `attester` | with schemaId | Trusted attester address |
| `indexer` | with schemaId | EAS indexer contract address |
| `chainId` | with schemaId | |

Operator: `valid`.

## 4. `farcaster_id`

Check whether the wallet has a registered Farcaster ID.

```json
{
  "type": "farcaster_id",
  "label": "Has Farcaster account"
}
```

Operator: `registered`.

## Composing multiple conditions

Up to 10 conditions per request. Overall `pass` is `true` only if **every** condition passes. Each individual condition's result is also returned in `data.attestation.results[]`.

```json
{
  "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
  "conditions": [
    {
      "type": "token_balance",
      "contractAddress": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      "chainId": 8453,
      "threshold": 100,
      "decimals": 6,
      "label": "USDC >= 100 on Base"
    },
    {
      "type": "eas_attestation",
      "template": "coinbase_verified_account",
      "label": "Coinbase KYC"
    }
  ]
}
```

This evaluates to `pass: true` only if the wallet holds 100+ USDC on Base AND has a Coinbase-verified attestation.

## Cross-chain wallets in one call

Pass multiple wallet fields to verify across ecosystems:

```json
{
  "wallet": "0xabc...",
  "solanaWallet": "5xY...",
  "xrplWallet": "rN7n...",
  "bitcoinWallet": "bc1q...",
  "conditions": [
    { "type": "token_balance", "chainId": 1, "contractAddress": "0x...", "threshold": ... },
    { "type": "token_balance", "chainId": "solana", "contractAddress": "EPjF...", "threshold": ... },
    { "type": "token_balance", "chainId": "xrpl", "contractAddress": "rMxC...", "currency": "RLUSD", "threshold": ... },
    { "type": "token_balance", "chainId": "bitcoin", "contractAddress": "native", "threshold": 0.01 }
  ]
}
```

The API routes each condition to the matching wallet field by `chainId`.
