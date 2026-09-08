# kimi-code-sovereign

Sovereign fork of [MoonshotAI/kimi-code](https://github.com/MoonshotAI/kimi-code) (MIT).
Tracks upstream `main`; carries a small set of token-frugality and privacy
patches for the toxicwind sovereign fleet (llama-swap :25100, 43-MCP
federation via mcpproxy :25109).

- **Upstream**: `https://github.com/MoonshotAI/kimi-code.git` (remote `upstream`)
- **Fork**: `https://github.com/toxicwind/kimi-code-sovereign` (remote `origin`)

All patches are marked inline with `SOVEREIGN PATCH` comments — grep for that
string to enumerate them.

---

## Patches

### 1. Thinking keep default → off

**File**: `packages/agent-core-v2/src/kosong/model/thinking.ts` (`resolveThinkingKeep`)

Upstream defaults the thinking-keep value to `'all'` when neither
`KIMI_MODEL_THINKING_KEEP` nor `[thinking] keep` is set — meaning every
request re-sends all prior turns' reasoning blocks. On long sessions this is
the single largest avoidable token cost. The fork flips the unset default to
keep-off (`undefined`): reasoning is not persisted across requests unless the
user opts in via env or config. The wire field stays `thinking.keep`; type and
schema compatibility are untouched, and the always-on clamp for
`always_thinking` models is unaffected (it lives in effort resolution, not
keep resolution).

Test updated: `packages/agent-core-v2/test/kosong/model/thinking.test.ts`
(default case now expects `undefined`).

### 2. `tool-select` experimental default → true

**File**: `packages/agent-core/src/flags/registry.ts` (`tool-select` entry)

Progressive tool disclosure keeps MCP tool schemas out of the immutable
top-level `tools[]`; the model loads them on demand via `select_tools`. With a
43-MCP federation, inlining every schema is pure token bloat on every request.
The fork flips `default: false` → `default: true`. Still gated by model
capability (only takes effect on models whose capability catalog declares
dynamically loaded tools) and overridable via
`KIMI_CODE_EXPERIMENTAL_TOOL_SELECT` / `[experimental] tool-select`.

Tests updated: `packages/agent-core/test/agent/tool-select.e2e.test.ts`
("flag off" helper now pins the flag off explicitly),
`packages/node-sdk/test/config.test.ts` (expected `defaultEnabled`/`enabled`).

### 3. Telemetry default → off (opt-in)

**Files**:

- `apps/kimi-code/src/cli/telemetry.ts` — CLI + `kimi web` bootstrap gates
- `apps/kimi-code/src/cli/v2/run-v2-print.ts` — v2 print-mode gate
- `packages/kap-server/src/services/telemetry.ts` — kap-server engine gate

Upstream treats telemetry as opt-out (`config.telemetry !== false` → enabled
when unset). The fork flips every config gate to `=== true`: telemetry is off
unless `telemetry = true` is explicitly set in `config.toml`.
`KIMI_DISABLE_TELEMETRY` still force-disables regardless. The telemetry code
path itself (client, sink, `noopTelemetryClient` seam) is fully intact — only
the default changed.

---

## Sync procedure

Upstream is pushed daily; patches are small and localized so conflicts stay
rare.

```bash
cd /home/toxic/projects/kimi-code-sovereign
git fetch upstream
git merge upstream/main
# resolve any conflicts at the SOVEREIGN PATCH anchors, then:
git push origin main
```

If upstream refactors one of the patch sites, re-apply the intent (default
flips only — never restructure upstream logic).

## Build

```bash
cd /home/toxic/projects/kimi-code-sovereign
pnpm install --frozen-lockfile

# JS bundle (npm-style dist/main.mjs):
pnpm --filter @moonshot-ai/kimi-code run build

# Native single-executable (SEA), drop-in replacement for ~/.kimi-code/bin/kimi:
pnpm -C apps/kimi-code run build:native:sea
node apps/kimi-code/scripts/native/smoke.mjs   # smoke-test the binary
```

Verify: `<binary> --version`. Do not replace `~/.kimi-code/bin/kimi` until the
sovereign binary has been smoke-tested.
