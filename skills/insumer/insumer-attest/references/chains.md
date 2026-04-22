# Chain Coverage

InsumerAPI evaluates wallet conditions on **33 chains** total: 30 EVM, plus Solana, XRPL, and Bitcoin.

## EVM (30 chains)

Pass `chainId` as the canonical numeric ID. Merkle storage proofs (`proof: "merkle"`) are available on **27 of 30 EVM chains** — Ronin (2020), Moonriver (1285), and Viction (88) return `proof.available: false`.

Full supported set, from the canonical `ChainId` enum in <https://insumermodel.com/openapi.yaml>:

| Chain | chainId |
|---|---|
| Ethereum | 1 |
| OP Mainnet (Optimism) | 10 |
| BNB Smart Chain | 56 |
| Viction | 88 |
| Gnosis | 100 |
| Unichain | 130 |
| Polygon | 137 |
| Sonic | 146 |
| opBNB | 204 |
| zkSync Era | 324 |
| Scroll | 534352 |
| World Chain | 480 |
| Mantle | 5000 |
| Linea | 59144 |
| Blast | 81457 |
| Base | 8453 |
| Soneium | 1868 |
| Ronin | 2020 |
| Berachain | 80094 |
| Sei | 1329 |
| Moonbeam | 1284 |
| Moonriver | 1285 |
| ApeChain | 33139 |
| Celo | 42220 |
| Arbitrum One | 42161 |
| Avalanche C-Chain | 43114 |
| Ink | 57073 |
| Plume | 98866 |
| Chiliz | 88888 |
| Taiko | 167000 |

For the always-current canonical list, check the `ChainId` schema in <https://insumermodel.com/openapi.yaml>.

## Non-EVM (3 chains)

For these chains, use the dedicated wallet field (not `wallet`) and pass the chainId as a string:

| Chain | chainId | Wallet field | Native unit | Token type field | Merkle proof |
|---|---|---|---|---|---|
| Solana | `"solana"` | `solanaWallet` | SOL (9 decimals) | SPL token by mint address (`contractAddress`) | ✗ |
| XRPL | `"xrpl"` | `xrplWallet` | XRP (`contractAddress: "native"`) | Trust line tokens (`currency` field) | ✗ |
| Bitcoin | `"bitcoin"` | `bitcoinWallet` | BTC (`contractAddress: "native"`) | n/a | ✗ |

### XRPL specifics

- XRP balance: `contractAddress: "native"`
- Trust line tokens (RLUSD, USDC on XRPL): `contractAddress` is the issuer r-address, plus `currency` field (e.g. `"RLUSD"`, `"USDC"`, or any 3-char code)
- 3-char currency codes pass through as-is; longer names (e.g. `"RLUSD"`) are auto hex-encoded to the 40-char XRPL canonical format
- NFTokens use `taxon` field for issuer + taxon filtering

### Bitcoin specifics

- Only native BTC balance is supported (no Ordinals, no BRC-20)
- Address types accepted: P2PKH, P2SH, bech32 (P2WPKH/P2WSH), Taproot (P2TR)
- BTC balance threshold is in **BTC** (not satoshis) — the API handles satoshi conversion internally

### Solana specifics

- Native SOL balance: `contractAddress: "native"` (or omit; the API treats this as native by default for Solana)
- SPL token balance: `contractAddress` is the mint address (base58)
- USDC on Solana mint: `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`
- USDT on Solana mint: `Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB`

## Decimals

Always set `decimals` explicitly for stablecoin conditions to avoid silent failure (the API defaults to `18` when omitted):

| Token | Decimals |
|---|---|
| USDC (any chain) | 6 |
| USDT (any chain) | 6 |
| USDC.e | 6 |
| WETH | 18 |
| DAI | 18 |
| Most other ERC-20s | 18 |

For tokens you're not sure about, omit `decimals` only if you've confirmed the contract is 18-decimal — otherwise look it up.

## See also

- [InsumerAPI OpenAPI spec — `ChainId` enum](https://insumermodel.com/openapi.yaml)
- [Developer docs — verification](https://insumermodel.com/developers/verification/)
