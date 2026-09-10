# Mesh — Sovereign Mesh Inference Router

Mesh is the mesh inference router for the Sovereign stack. It provides a secondary inference endpoint for agents that need fast, lightweight model access.

## Endpoints

- `http://127.0.0.1:25120/v1/chat/completions` — OpenAI-compatible chat completions
- `http://127.0.0.1:25120/v1/models` — Active model list
- `http://127.0.0.1:25120/health` — Health check

---

## Config

- `mesh/config.yml` — Mesh-specific agent configuration
- Port: `25120` (not `25127`)
- Default model: `openrouter/inclusionai/ling-3.0-flash-fin:free:high`

---

## Status

| Component | State | Notes |
|---|---|---|
| Router (`:25120`) | ⚠ needs attention | Port fixed from 25127 to 25120 |
| Upstream | 502 | Upstream unhealthy, not refused |

---

## Related

- `herd/` — Primary inference router (port 25100)
- `.tau/config.yml` — Tau agent configuration (nvidia models)
- `~/sovereign/config/` — Sovereign stack configuration
