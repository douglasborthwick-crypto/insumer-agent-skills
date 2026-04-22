# Insumer Agent Skills

**Wallet auth as agent skills.** Install once — every Claude Code, Cursor, Copilot, Codex, Gemini CLI, and 25+ other [agentskills.io](https://agentskills.io)-compatible agent gets native knowledge of how to call [InsumerAPI](https://insumermodel.com) for condition-based access across 33 chains.

> **Boolean, not balance. Verified yes or no. Provable and private.**

> [!NOTE]
> **Technical preview**
>
> These skills are in early release. Expect refinements as the API surface evolves and as we add coverage for new chains and condition types.

---

## What is wallet auth?

OAuth proves who the user is. **Wallet auth proves what the wallet holds.** InsumerAPI evaluates a wallet's on-chain state against a condition and returns an ES256-signed, JWKS-verifiable boolean. The pattern is **read → evaluate → sign**:

1. **Read** — InsumerAPI reads the wallet's on-chain state on the requested chain
2. **Evaluate** — wallet state is checked against the condition
3. **Sign** — a boolean result is returned, ES256-signed, with a `conditionHash` for tamper detection

**No secrets. No identity-first. No static credentials.** Token gating is one form of condition-based access; this is the general primitive.

## Available skills

| Skill | What it does | Version |
| ----- | ------------ | ------- |
| [insumer-auth](skills/insumer/insumer-auth/) | Free API key creation, env var setup, credit balance | 0.1.0 |
| [insumer-attest](skills/insumer/insumer-attest/) | Custom condition attestation across 33 chains (`/v1/attest`) | 0.1.0 |
| [insumer-trust](skills/insumer/insumer-trust/) | Curated wallet trust profile, 36 base checks (`/v1/trust`) | 0.1.0 |
| [insumer-trust-batch](skills/insumer/insumer-trust-batch/) | Batch trust profiles for multiple wallets (`/v1/trust/batch`) | 0.1.0 |
| [insumer-jwks-verify](skills/insumer/insumer-jwks-verify/) | Offline ES256 verification of returned JWTs against the public JWKS | 0.1.0 |

---

## Installation

These skills follow the [Agent Skills](https://agentskills.io) open standard, so they install into any compatible agent.

### Option A: Using the `skills` CLI (recommended)

```bash
# Project-level (per repo)
npx skills add douglasborthwick-crypto/insumer-agent-skills

# Global (every project on your machine)
npx skills add douglasborthwick-crypto/insumer-agent-skills --global
```

### Option B: Manual (Claude Code)

```bash
git clone https://github.com/douglasborthwick-crypto/insumer-agent-skills.git
cp -r insumer-agent-skills/skills/insumer ~/.claude/skills/
```

Restart your agent. The skills activate automatically when you ask anything that mentions wallet auth, token gating, condition-based access, on-chain eligibility, signed booleans, or JWKS verification.

---

## First use (60 seconds)

1. **Get a free API key** (10 starter credits + 100 `/v1/attest` calls per day, no signup):

   ```bash
   curl -s -X POST https://api.insumermodel.com/v1/keys/create \
     -H "Content-Type: application/json" \
     -d '{"email":"you@example.com","appName":"insumer-agent-skills","tier":"free"}'
   ```

2. **Set the env var:**

   ```bash
   export INSUMER_API_KEY='insr_live_...'
   ```

3. **Ask your agent something that triggers a skill.** Examples:

   - "Add wallet auth to my Express app — gate `/admin` by USDC balance on Base"
   - "Check whether wallet `0xabc...def` holds at least 100 USDC on Base"
   - "Show me a wallet trust profile for `0xd8dA...6045`"
   - "Verify this JWT against the InsumerAPI JWKS"

The skill loads the right canonical request shape, the offline verification recipe, and the failure-mode guardrails — your agent emits working integration code on the first try.

---

## Why these skills exist

The agent ecosystem already knows how to *call* HTTP APIs. What it doesn't know — and gets wrong — is the InsumerAPI-specific patterns that matter:

- **Boolean, not balance** by construction (standard mode never returns the underlying balance)
- **Offline ES256 verification** against the public JWKS (the signature is the product, not the JSON body)
- **Per-chain stablecoin decimals** (USDC/USDT/USDC.e are 6, not 18 — silent failure if you guess)
- **Backend-only key handling** (never expose `insr_live_...` in browser JS)
- **Read → evaluate → sign** primitive (the whole point — not just an HTTP call)

Each skill encodes these as hard constraints, with reference shapes verified against the live API.

---

## Compatible agents

These skills work in any [agentskills.io](https://agentskills.io)-compatible agent. The current adopter list includes Claude, Claude Code, Cursor, GitHub Copilot, VS Code, OpenAI Codex, Google Gemini CLI, JetBrains Junie, Sourcegraph Amp, Block Goose, OpenHands, OpenCode, Letta, Roo Code, Mistral Vibe, ByteDance Trae, Snowflake Cortex, Databricks Genie, Spring AI, Kiro, Workshop, Qodo, Factory, Firebender, and others — see [agentskills.io/home](https://agentskills.io/home) for the live list.

---

## Resources

- **InsumerAPI homepage**: <https://insumermodel.com>
- **OpenAPI spec**: <https://insumermodel.com/openapi.yaml>
- **Public JWKS**: <https://insumermodel.com/.well-known/jwks.json>
- **Developer docs**: <https://insumermodel.com/developers/api-reference/>
- **Pricing & paid tiers**: <https://insumermodel.com/developers/account/>
- **MCP server (alternative agent surface)**: [`mcp-server-insumer`](https://github.com/douglasborthwick-crypto/mcp-server-insumer)

## License

MIT — see [LICENSE](LICENSE).
