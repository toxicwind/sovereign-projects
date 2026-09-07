# Herd — Sovereign Multi-Engine Inference Router

Herd is our production inference router for the entire Sovereign stack. Forked from `mostlygeek/llama-swap`, it has evolved with AstMatrix, multi-engine GPU orchestration, and sovereign-native routing.

Exposes a single OpenAI-compatible endpoint that every agent runtime (Tau, OpenCode, OpenFang, Yote, CodeShift) talks to:

- `http://127.0.0.1:25100/v1/chat/completions` — OpenAI-compatible chat completions
- `http://127.0.0.1:25100/v1/models` — Active model list
- `http://127.0.0.1:25100/health` — Sub-second health polling and readiness probe
- `http://127.0.0.1:25100/ui/` — Built-in chat playground
- `http://127.0.0.1:25100/metrics` — Runtime telemetry and routing counters

---

## Architecture

A high-performance Go router on `:25100` orchestrating 3 C++ inference engine forks on an NVIDIA GeForce RTX 3090 (24GB VRAM):

```
                       ┌──────────────────────────────┐
                       │        Agent Runtimes         │
                       │ (Tau, OpenCode, CodeShift)    │
                       └──────────────┬───────────────┘
                                      │ :25100 (OpenAI API)
                       ┌──────────────▼───────────────┐
                       │             Herd             │
                       │  Go Router + AstMatrix Core  │
                       └──────────────┬───────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
┌───────────▼───────────┐ ┌───────────▼───────────┐ ┌───────────▼───────────┐
│     beellama.cpp      │ │  llama-cpp-turboquant │ │       ik_llama.cpp    │
│  CUDA 86 / znver4     │ │  Fast quantized       │ │  Experimental         │
│  Flash attention,     │ │  inference, low VRAM  │ │  kernels & custom     │
│  AVX-512 optimization │ │  footprint            │ │  quantization         │
└───────────────────────┘ └───────────────────────┘ └───────────────────────┘
```

Herd dynamically handles process management, context eviction, model loading, and engine invocation behind a unified endpoint.

---

## AstMatrix Production Routing & Resilience

AstMatrix is Herd's first-class routing and reliability subsystem (`llama-swap/internal/astmatrix/`, 2000+ lines of Go):

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
**Source**: `~/projects/sovereign-projects/llama-swap/internal/astmatrix/`.

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
│   ├── engines/                     # C++ inference engine forks (beellama.cpp, llama-cpp-turboquant, ik_llama.cpp)
│   ├── internal/config/             # Historical config parser references
│   └── README.md                    # Authoritative Herd architecture document
└── llama-swap/                      # Build-ready Go router source + AstMatrix core
    ├── internal/astmatrix/          # Circuit breaker, rate limiting, and dispatch engines
    ├── internal/server/             # HTTP handlers, SSE streamer, proxy pipeline
    ├── internal/router/             # Model lifecycle manager and engine supervisor
    ├── internal/config/             # Full YAML configuration parser and validator
    └── Makefile                     # Build targets
```

---

## Operations & Configuration

- **Configuration SSOT**: `~/sovereign/config/herd.yaml` (852 lines).
- **Service Launcher**: `~/sovereign/stack/services/herd.sh`.
- **System Binary**: `~/projects/llama-swap/llama-swap` (symlinked directly to `~/projects/sovereign-projects/llama-swap/llama-swap`).
- **Health Check**:
  ```bash
  curl -s http://127.0.0.1:25100/health
  curl -s http://127.0.0.1:25100/v1/models | jq .
  ```
