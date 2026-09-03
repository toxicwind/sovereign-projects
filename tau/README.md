# tau

The sovereign **agent runner**: a CLI + TUI + extension host that drives the
sovereign AI stack. Forked from `can1357/oh-my-pi`, repointed at the Sovereign
fleet (Herd for inference, Nexus for tools), and bundled with the Soverign-Stack
control plane contract.

Version: **18.0.8** (from `engine/packages/coding-agent/package.json`).
Runtime: Bun `>=1.3.14`.

## What this is

`tau` is **not** a coding IDE, kernel, or control plane. It is the runtime
that lets an LLM act on your repo: it reads files, runs shell, edits code,
manages sessions, and federates tools/inference through the Sovereign stack.

Per-turn contract:

- **1M-token context** per session.
- **11-tool advisor suite** wired into every run (read, bash, edit, write, …).
- **MCP federation** through `mesh` (Nexus) on `:25127` — every approved tool
  in the mesh is a candidate tool.
- **Inference** through `herd` (llama-swap) on `:25100` — model registry,
  routing, and quotas.
- **Omnifoo MCP** for omnibar/files/desktop-notify glue.

## Active Emergent Features
- **High-Frequency Liveness Probes & Failfast**: Sub-second health polling and strict per-attempt deadlines.
- **Worker-Limit Handling**: Backpressure-aware subagent concurrency control (up to 32 concurrent workers).
- **Multi-Strategy Inference**: Dynamic failover across Herd local models, NVIDIA NIM, and OpenRouter endpoints.
- **Subagent Mesh Routing**: Autonomous cross-agent delegation through Mesh MCP gateway on `:25127`.
- **Dynamic `${ENV_VAR}` Interpolation**: First-class runtime variable expansion across agent settings and launch configs.

The agent logic lives in `engine/packages/coding-agent`; the TUI is in
`engine/packages/tui`; the model registry and providers live in
`engine/packages/ai` (pi-catalog with `registry/*.ts` provider definitions).

## Where it fits

`tau` is one workspace inside the **`sovereign-projects`** monorepo
(`github.com/toxicwind/sovereign-projects`). Sibling workspaces include
`herd`, `mesh`, `qed`, `sovereign`, and others. Each workspace owns one
service or client; tau owns the agent runtime.

The authoritative **control plane** lives in `~/sovereign/`
(`toxicwind/sovereign`). It is generated from `~/sovereign/config/ports.env`
and `~/sovereign/src/services/*` via `bun run scripts/generate.ts`. tau
**consumes** the SSOT defined there — it does not own ports, models, or
service registrations.

Launchers in this monorepo (`pi`, `omp`, `tau`) all resolve to the same dev
wrapper that execs `engine/packages/coding-agent/src/cli.ts`.

## Layout

The repo is split into three subtrees:

- **`engine/`** — the actual product code. A Bun workspaces monorepo with
  packages:
  - `ai` — model catalog and provider registry (herd-backed).
  - `coding-agent` — the CLI/TUI agent loop, session state, tool dispatch.
    Entry: `src/cli.ts` (exports the `omp` bin).
  - `tui` — terminal UI, omnibar, theme/i18n (`src/i18n/`).
  - `collab-web` — collaborative web UI + tool-view bundle.
  - `browser-relay` — local browser automation relay (extension + worker).
  - `wire` — worker/daemon IPC protocols (blob-broker, LSP-mux, daemon-broker).
  - `utils` — shared pi-utils: CLI runner, dirs, worker-host, postmortem.
  - `agent` — agent core types and runtime helpers.
  - `stats` — telemetry / session stats.
  - `omptype` — public type surface for extensions.
  - `types` — shared type packages.
  - `native` — native binaries (Bun `--compile` targets).
  - `typescript-edit-benchmark` — edit/codemod benchmark harness.
  - Plus `kimi/`-specific vendors under `engine/vendor/` (submodules):
    `oh-my-pi`, `pi-upstream`, `pi-subagents`, `kimi-code-sovereign`,
    `modelbeats`, `tinker-cookbook`. Init with
    `git submodule update --init --recursive`.

- **`extensions/`** — the `omp-extensions` monorepo: external OMP plugins
  (e.g. `omp-kafka`, `omp-edit-committer`). See `extensions/README.md`.

- **`kimi/`** — `kimi-code-sovereign` fork integration surface.

## Run it

From this directory (`tau/`):

```sh
bun install              # once, at monorepo root
bun run dev              # execs engine/packages/coding-agent/src/cli.ts
```

Global launchers on PATH:

- `tau` — workspace launcher
- `omp` — canonical alias for `tau` (matches the upstream bin name)
- `pi` — legacy alias (preserved for muscle memory)

- **bin/tau** — a local symlink for first-class dev convenience in this 
  environment. It links to the canonical `~/.local/bin/tau` for quick access.

All three preserve the caller's `$PWD` — they do not `cd` you into the
monorepo. If you launch from `/tmp`, tau stays in `/tmp` (unless `--cwd` is
passed).

The CLI self-checks Bun and exits cleanly if the runtime is too old:

```
error: Bun runtime must be >= 1.3.14 (found v<Bun.version>). Please upgrade: bun upgrade
```

## Extensions

`extensions/` is a separate workspace for OMP plugins. tau loads them as
sidecar capabilities (tools, slash commands, MCP bridges). See
[`extensions/README.md`](./extensions/README.md) for the plugin manifest
contract and authoring guide.

## MCP / Herd wiring

tau does not hardcode endpoints. The MCP and inference URLs live in the
**agent settings** under `provider_urls`:

- `provider_urls.herd` → `http://127.0.0.1:25100` (llama-swap / herd)
- `provider_urls.mesh` → `http://127.0.0.1:25127` (Nexus / mcpproxy)

Other providers (Cloudflare AI Gateway, NVIDIA NIM, OpenRouter, …) are
configured in `engine/packages/ai/src/registry/` as `ProviderDefinition`
entries with `prepareRequest` hooks for model-id transforms. The registry is
hot-reloadable; no CLI restart is needed to pick up a new model.

Omnifoo MCP is wired the same way — declare it in `provider_urls` and tau
will discover its tools through the mesh federation layer.

## Status

- **Version:** 18.0.8 (from `engine/packages/coding-agent/package.json`).
- **Runtime:** Bun `>=1.3.14`.
- **Context window:** 1M tokens per session.
- **Tool surface:** 11-tool advisor suite, expandable via mesh MCP federation.
- **Launcher invariants:** preserves caller's `$PWD`; redirects `/tmp` and
  `/var/tmp` to `$HOME` only when no explicit `--cwd` is passed.
- **Upstream:** forked from `can1357/oh-my-pi`; tracked upstream as
  `badlogic/pi-mono`.

## Where to look next

- `engine/packages/coding-agent/src/cli.ts` — CLI entry, command registration.
- `engine/packages/ai/src/registry/` — provider/model registry.
- `engine/packages/tui/src/i18n/` — i18n runtime (pilot: en + no).
- `engine/AGENTS.md` — toolchain and vendor submodule layout.
- `extensions/README.md` — plugin authoring.