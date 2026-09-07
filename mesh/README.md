# Mesh — Sovereign MCP Federation Gateway (mcpproxy-go fork)

> **SSOT: `.omp` == `.tau` == our renamed monorepo.** `mesh/` lives under `~/projects/sovereign-projects/`. The `omp` binary/symlink is a leftover install artifact; the real CLI is `tau` or `opencode` (`/home/toxic/.local/bin/tau`).

**Priority 0.** If mesh is dead, everything boots in failed-tool state. Fix mesh first; everything else follows.

## Live state (verified 2026-09-07)

- Config (`~/.config/opencode/opencode.json`): `mesh` points to `http://127.0.0.1:25120/mcp` (was 25127 — wrong port, caused generic "Unable to connect" miss).
- Running: `mesh-hub.ts` (bun, PID 4091904) on `0.0.0.0:25115`; mesh gateway on `0.0.0.0:25120`.
- Health: `curl -i http://127.0.0.1:25120/mcp -H "Accept: application/json, text/event-stream"` returns `502 Bad Gateway` (`"no healthy upstream"`) — server is live, upstream unhealthy. Not connection refused.
- `ss -lntp`: 25108, 25112, 25113, 25115 (mesh-hub), 25117 (hindsight), 25118 (next-server), 25120 (mesh gateway/proxy), 25121, 25130, 25134 (qdrant), 25199 (valkey), 25143.

## Fix applied

```json
"mesh": { "type": "remote", "url": "http://127.0.0.1:25120/mcp", "enabled": true }
```

Remote = needs the `Accept` header or 406s (bug in 18.0.11, fixed 18.1.12). The server responds correctly when the header is present.

## What mesh is

Mesh is the sovereign MCP tool federation gateway (`mcpproxy-go` fork / `mesh-hub.ts`). It federates 231+ tools across 18 MCP servers behind a single HTTP endpoint (`:25120/mcp`). Every agent runtime — Tau (`.tau` / `.omp`), QED, Yote, OpenFang — talks to mesh over that endpoint.

Mesh is **not** the stack control plane. The control plane is `~/sovereign/` (mesh-front services on 25101, 25103, 25106, etc.). Mesh is a service consumed by every workspace in the Sovereign Monorepo.

## Quick commands

```bash
# Verify mesh connects (not refused)
curl -i -s --max-time 3 http://127.0.0.1:25120/mcp -H "Accept: application/json, text/event-stream"
# Expected: 502 "no healthy upstream" (live) — NOT empty/timeout.

# Check running mesh
ss -lntp | grep 251
ps auxf | grep mesh

# Check config
cat ~/.config/opencode/opencode.json | grep -A4 '"mesh"'

# Restart tau/opencode (not `omp`)
pkill -f tau || true
tau
```

## Harness links

- Real bin: `/home/toxic/.local/bin/tau` (symlink `omp` is leftover).
- Config: `/home/toxic/.tau/` (`.omp` → `.tau`, `.pi` → `.tau`).
- Mesh source: `~/projects/sovereign-projects/mesh/` (this repo), `mesh-hub.ts`, `mesh-front.ts`.
- MCPP proxy config: `/home/toxic/.mcpproxy/mcp_config.json` (43 upstreams via `pitchfork start mcpproxy`).
