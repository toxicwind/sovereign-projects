        # Sovereign Monorepo (toxicwind/sovereign-projects)

        > **The unified workspace layer for the Sovereign autonomous agent ecosystem.**

        The Sovereign monorepo houses the core execution engines, editors, tools, gateways, and desktop interface layers. It
 operates in tandem with the Sovereign control plane (`/home/toxic/sovereign`).

        ---

        ## 🏛️ Ecosystem Topology

        The stack is strictly decoupled into two operating layers:

        ```
        ┌─────────────────────────────────────────────────────────────────────────┐
        │                      Sovereign Control Plane (~/sovereign)              │
        │  - Supervisor (pitchfork)       - Port SSOT (config/ports.env)          │
        │  - Daemons & Orchestration      - Modular Profiles (profiles/toxic)     │
        └────────────────────────────────────┬────────────────────────────────────┘
                                             │ coordinates
        ┌────────────────────────────────────▼────────────────────────────────────┐
        │                  Sovereign Workspaces (~/projects/sovereign-projects)   │
        │                                                                         │
        │  [yote/]        Minimal embeddable agent runtime | :25102               │
        │  [openfang/]    C++ inference engine fork          │
        │  [tau/]         Canonical AI Agent Engine (1M+ context, coding CLI)       │
        │  [herd/]        Inference Router & Llama-Swap (:25100, AstMatrix V2)      │
        │  [mesh/]         MCP Tool Federation Gateway (:25127, 43 upstreams)        │
        │  [qed/]         Definitive AI-Native Code Editor (:25130, Zedra host)     │
        │  [shell/]        OS / Desktop Interface (Hyprland + QuickShell Wayland)    │
        │  [boundless/]   Autonomous Document Ingestion & Chunking Engine (:10200)  │
        └─────────────────────────────────────────────────────────────────────────┘
        ```

        ---

        ## 📦 Primary Workspaces

        | Workspace | Directory | Role & Technology | Key Endpoints / Ports |
        |---|---|---|---|
        | **Yote** | [`/yote`](./yote/README.md) | Minimal embeddable agent runtime | :25102 |
        | **OpenFang** | [`/openfang`](./openfang/README.md) | C++ inference engine fork | Integrated into Herd |
        | **Tau** | [`/tau`](./tau/README.md) | Canonical AI coding agent engine (TypeScript / Bun / Rust) | CLI: `tau`, Web:
 `:25192` |
        | **Herd** | [`/herd`](./herd/README.md) | Multi-model inference router & llama-swap fork | API: `:25100/v1`, UI:
 `:25100/ui/` |
        | **Mesh** | [`/mesh`](./mesh/README.md) | Sovereign MCP federation gateway (`mcpproxy-go`) | MCP: `:25127/mcp`, Hub:
 `:25115` |
        | **QED** | [`/qed`](./qed/README.md) | Definitive AI-native editor (our Zed fork) & Zedra host | Host: `:25130`, Collab
 |
        | **Shell** | [`/shell`](./shell/README.md) | Desktop environment (Hyprland + QuickShell) | Wayland / Hyprland |
        | **Boundless** | [`/boundless`](./boundless/README.md) | ADA/508-compliant document splitting substrate | Web UI:
 `:10200` |

        ---

        ## 🧩 Integrated Packages (`packages/`)

        - **`sovereign-skills`**: Reusable agent skill definitions and multi-strategy prompts.
        - **`sovereign-router`**: Abstract model discovery, dynamic routing, and MCP protocol mappings.
        - **`sovereign-scripts`**: Maintenance, audit, and benchmark automation scripts.
        - **`caddy-sovereign-auth`**: Unified reverse-proxy authentication middleware.
        - **`utils`**: High-performance logging (`packages/utils/logger.ts`), streams, and timing utilities.

        ---

        ## ⚡ Active Emergent Features

        - **Port SSOT Consistency**: All service ports are registered and verified against
 `/home/toxic/sovereign/config/ports.env` (`25xxx`).
        - **MCP Federation Across 43+ Upstreams**: Single unified MCP endpoint on `:25127/mcp` connects agents to GHAS, Qdrant,
 and developer tools.
        - **High-Frequency Health Probing**: Sub-second failfast liveness checks across daemons with circuit breakers.
        - **Dynamic `${ENV_VAR}` Interpolation**: First-class environment resolution across configurations.
        - **Hardware Optimization**: Throttled build profiles (`jobs = 12`, `codegen-units = 16`, `znver4`) tuned for the AMD
 Ryzen 7 8700F to eliminate interactive shell lag.

        ---

        ## 🚀 Quick Verification

        ```bash
        # Verify core services are responding
        curl -sf http://127.0.0.1:25100/v1/models >/dev/null && echo "✅ :25100 Herd (LLM)"
        curl -sf http://127.0.0.1:25102/health >/dev/null && echo "✅ :25102 Yote"
        curl -sf http://127.0.0.1:25127/health >/dev/null && echo "✅ :25127 Mesh (MCP)"

        # Check git status across workspace
        git status --short
        ```
        EOF

        echo "✅ Updated sovereign-projects/README.md with yote and openfang""

{ _ble_edit_exec_gexec__save_lastarg "$@"; } 4>&1 5>&2 &>/dev/null
