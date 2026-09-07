# Mesh — Sovereign MCP Federation Gateway (`mcpproxy-go` fork)

> **Priority 0 Infrastructure Service**: Federates 231+ tools across 43 MCP servers behind a unified endpoint.

Mesh provides the tool execution substrate for every agent runtime in the Sovereign ecosystem (Tau, QED, Yote, OpenFang). If Mesh is offline, agents boot into a zero-tool degraded state.

---

## 🏛️ Architecture & Ports Matrix

Mesh is structured into three coordinated layers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Agent Clients                                 │
│                   (Tau CLI, QED Editor, OpenFang)                       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               mcp-gateway (:25120) — Reverse Proxy Router               │
│  - tools/sovereign-router/sovereign-mcp-gateway/gateway.ts               │
│  - Circuit breaking, sticky sessions & request normalization            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ proxies to upstream
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              mcpproxy-go (:25127) — MCP Tool Federation Gateway         │
│  - mesh/gateway/mcpproxy binary                                         │
│  - Loads ~/.mcpproxy/mcp_config.json (43 active MCP upstreams)          │
│  - Exposes /mcp (JSON-RPC 2.0 transport) & /health                      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ connects to
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          43 MCP Server Upstreams                        │
│  GHAS (:25113), Qdrant (:25134), Filesystem, Python, Browser, etc.      │
└─────────────────────────────────────────────────────────────────────────┘
```

| Component | Port | Implementation | Role |
|---|---|---|---|
| **`mesh` (mcpproxy-go)** | `:25127` | Go binary (`mesh/gateway/mcpproxy`) | Primary tool federation gateway & JSON-RPC handler |
| **`mcp-gateway`** | `:25120` | Bun script (`gateway.ts`) | Aggregator, circuit-breaker & proxy router |
| **`mesh-hub`** | `:25115` | Bun script (`mesh-hub.ts`) | 20 GHAS-linked feature catalog & status endpoint |

---

## ⚙️ Configuration & Schema SSOT

The primary configuration resides at `/home/toxic/.mcpproxy/mcp_config.json`:

- **Schema Requirement**: `mcpServers` must be defined as an **array of objects** (`[ { "name": "...", "protocol": "..." } ]`), not a dictionary/map.
- **Upstreams**: Configured with 43 servers including GHAS, Qdrant, Docker isolated runtimes, and local tool providers.
- **Clients**:
  - `tau` (`~/.tau/agent/mcp.json`): points to `http://127.0.0.1:25127/mcp`.
  - `opencode` (`~/.config/opencode/opencode.json`): points to `http://127.0.0.1:25127/mcp`.

---

## 📡 Live Verification & Probing

```bash
# 1. Probe mcpproxy-go health (:25127)
curl -sf http://127.0.0.1:25127/health && echo "✅ :25127 mcpproxy-go HEALTHY"

# 2. Test JSON-RPC 2.0 initialize handshake
curl -s -X POST http://127.0.0.1:25127/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1.0"}}}'

# 3. Verify mesh-hub status (:25115)
curl -sf http://127.0.0.1:25115/health && echo "✅ :25115 mesh-hub HEALTHY"
```

---

## 🔧 Service Management

```bash
# Start/Restart via Pitchfork supervisor:
cd ~/sovereign
pitchfork restart mesh

# Direct binary execution (fallback):
nohup /home/toxic/projects/sovereign-projects/mesh/gateway/mcpproxy serve \
  --config=/home/toxic/.mcpproxy/mcp_config.json \
  --log-level=info \
  --listen=127.0.0.1:25127 > /tmp/mcpproxy-25127.log 2>&1 &
```
