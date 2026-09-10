# Herd — Sovereign Multi-Engine Inference Router

Herd is our production inference router for the entire Sovereign stack. Forked from `mostlygeek/llama-swap`, it has evolved with AstMatrix, multi-engine GPU orchestration, and sovereign-native routing.

Exposes a single OpenAI-compatible endpoint that every agent runtime (Tau, OpenCode, OpenFang, Yote, CodeShift) talks to:

- `http://127.0.0.1:25100/v1/chat/completions` — OpenAI-compatible chat completions
- `http://127.0.0.1:25100/v1/models` — Active model list
- `http://127.0.0.1:25100/health` — Sub-second health polling and readiness probe
- `http://127.0.0.1:25100/ui/` — Built-in chat playground
- `http://127.0.0.1:25100/metrics` — Runtime telemetry and routing counters

---

## Current Status

| Component | State | Notes |
|---|---|---|
| Router (`:25100`) | ⚠ needs restart | llama-swap was killed, queue cleared |
| beellama.cpp engine | ✗ binary missing | `${BEELLAMA_BIN}` not on disk |
| llama-cpp-turboquant | ✗ binary missing | `${TURBO_BIN}` not on disk |
| ik_llama.cpp | ✗ binary missing | `${IK_BIN}` not on disk |
| Models (83 listed) | All unloaded | No VRAM allocated until engines fixed |
| Model files | 22/23 present | `Qwen2.5-1.5D-Draft-Q8_0.gguf` missing |

### Fork Summary

| Fork | Binary | Models Served | Flags |
|---|---|---|---|
| **beellama.cpp** (CUDA 86) | `${BEELLAMA_BIN}` | EXAONE 1.2B, Qwen 3.5/3.6 Flash, Gemma 12B/21B, MN Grand 23B, Qwen 28B | `--kv-unified --no-host --cache-ram 0` |
| **llama-cpp-turboquant** | `${TURBO_BIN}` | *(none assigned)* | `--no-warmup` |
| **ik_llama.cpp** | `${IK_BIN}` | heretic-27B Q5 variants | `--fit --fit-margin 512 --no-warmup --defrag-thold 0.1` |

### Config SSOT
- `~/sovereign/config/herd.yaml` (852 lines)
- Routing via AstMatrix: circuit breaker, token bucket, dispatch strategies
- Priority schedule in `routing.scheduler.fifo.priority`

Herd dynamically handles process management, context eviction, model loading, and engine invocation behind a unified endpoint.

---

## AstMatrix Production Routing & Resilience

AstMatrix is Herd's first-class routing and reliability subsystem (`herd/internal/config/`, Go config parser with matrix DSL):

- **Circuit Breaker**: 5-strike failfast threshold with automatic 30s half-open backoff cooldown. Flapping or crashing backends are isolated before degrading client agents.
- **Token Bucket Rate Limiting**: Per-provider rate limiting with exponential backoff on HTTP 429 status codes.
- **Dispatch Strategies**:
  - `ast_race`: Parallel speculative dispatch across candidate models/engines; first valid token stream wins.
  - `elo_weighted`: Performance/ELO-weighted probabilistic selection across models of matching capability.
  - `sticky`: Session affinity preserving KV-cache state for multi-turn conversations.
  - `round_robin` & `least_conn`: Classical load-balancing primitives.
- **Request Coalescing**: De-duplicates concurrent identical prompt prefixes to maximize throughput and minimize redundant VRAM evaluation.
- **SSE Stream Normalization**: Guarantees compliant `chat.completion.chunk` event streams for strict consumers (Zed, Tau, OpenFang).

**Configuration**: Configured via the `astMatrix:` block in `~/sovereign/config/herd.yaml`.
**Source**: `herd/internal/config/` — Go config parser, matrix DSL, model config, merge logic.

---

## Model Priority Schedule

Herd routes inference requests based on model scheduler priorities defined in `~/sovereign/config/herd.yaml`:

| Priority | Model Identifier | Engine / Role |
|:---|:---|:---|
| **35** | `beellama/exaone-4-0-1-2b-iq4xs` | Fast worker / tiny inference (highest priority) |
| **34** | `exaone-3.5-2.4b-instruct` | Sub-agent lightweight reasoning |
| **31** | `exaone-2b-family` | Low-latency parallel worker |
| **30** | `mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m` | Primary general-purpose agent driver |
| **24** | `gemma-4-12b-unified` | High-accuracy structured analysis & synthesis |
| **16** | `beellama/qwen-flash-64k` | Long-context document & code ingestion |

---

## Repository Layout

```
sovereign-projects/
├── herd/
│   ├── internal/config/         # Go config parser, matrix DSL, model config, merge logic
│   └── README.md                # Authoritative Herd architecture document
├── mesh/                        # Mesh inference router config
│   └── config.yml               # Mesh-specific agent configuration
├── .tau/                        # Tau agent runtime
│   ├── config.yml               # Tau agent configuration (nvidia models)
│   ├── models.yml               # Available model list
│   └── blackboard/              # Collaboration boards (hubs, signals, manifests)
├── packages/                    # Sovereign packages (router, scripts, skills, auth)
└── tau/vendors/                 # Vendor submodules (kimi-code, Relay-AI, etc.)
```

---

## Operations & Configuration

- **Configuration SSOT**: `~/sovereign/config/herd.yaml` (852 lines).
- **Service Launcher**: `~/sovereign/stack/services/herd.sh`.
- **Health Check**:
  ```bash
  curl -s http://127.0.0.1:25100/health
  curl -s http://127.0.0.1:25100/v1/models | jq .
  ```
