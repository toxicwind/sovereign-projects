# Sovereign Monorepo (toxicwind/sovereign-projects)

The workspace layer for the Sovereign ecosystem. 

## Ecosystem Architecture
- **Control Plane (`~/sovereign/`):** Orchestrates daemons via `mise` and `pitchfork`.
- **Workspace Layer (`~/projects/sovereign-projects/`):** Implementation of core tools.

## Workspaces
- [Tau](/tau/README.md) - Agent engine (Canonical CLI).
- [Herd](/herd/README.md) - Inference router & AstMatrix V2.
- [Mesh](/mesh/README.md) - MCP tool federation gateway.
- [QED](/qed/README.md) - AI-native editor & Zedra host.
- [Shell](/shell/README.md) - OS/UI layer (Hyprland + QuickShell).

## Integrated Packages (`packages/`)
- **sovereign-skills**: Custom skill library for agents and multi-strategy workflows.
- **sovereign-router**: Model routing, discovery, and gateway abstractions.
- **sovereign-scripts**: Automation and maintenance scripts across the stack.
- **caddy-sovereign-auth**: Unified authentication middleware for web surfaces.
- **gayxxx-sovereign**: High-performance optimized media indexing component.
- **boundless**: EPUB/document parsing and reading substrate.
- **utils**: Common TypeScript logging (`packages/utils/logger.ts`) and telemetry.

## Active Emergent Features
- **Failfast & High-Frequency Health Probing**: Sub-second liveness probes with per-attempt timeouts.
- **Worker-Limit & Concurrency Handling**: Graceful backpressure control for agent swarms.
- **Multi-Strategy Inference**: Herd dynamic routing with AstMatrix V2 token-bucket rate limits and circuit breaker.
- **Subagent Mesh Routing**: Coordinated MCP tool federation across 43+ upstreams.
- **Dynamic `${ENV_VAR}` Interpolation**: First-class environment resolution across configurations.
## Development
- **Configuration:** Managed centrally via `~/sovereign/scripts/generate.ts`.
- **Dependencies:** Workspace managed via `tau/engine/package.json`.
- **Logging:** Use `packages/utils/logger.ts` (JSON format).

## Documentation
Each workspace contains its own `README.md`.
EOF
