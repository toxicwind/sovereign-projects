# Herd

Sovereign **inference router** for the whole stack. Upstream: `mostlygeek/llama-swap`. Fork: `toxicwind/llama-swap` → `toxicwind/herd`.

Exposes a single OpenAI-compatible endpoint that every agent runtime (tau, openfang, yote) talks to:

- `http://127.0.0.1:25100/v1` — chat / completions / embeddings (OpenAI schema)
- `http://127.0.0.1:25100/ui/` — built-in chat playground

Behind that one port sit three C++ inference engine forks; herd picks and loads the right one per model.

## Where it fits

Herd is a workspace inside the [Sovereign Monorepo](/README.md). It is **not** the control plane — that lives in `~/sovereign/` (supervisor, ports SSOT, launcher).

## Layout
```
herd/
├── tools/llama-swap/            # llama-swap fork (Go router + UI)
├── engines/                     # C++ inference engine forks (beellama.cpp, llama-cpp-turboquant)
└── package.json                 # sync:ssot scripts
```

## Active Emergent Features
- **AstMatrix V2**: Autonomous token bucket rate limiting and circuit breaking (5-strike failfast, 30s backoff cooldown).
- **Bench-Orchestrator**: Automated multi-strategy latency and throughput benchmarking engine (`cmd/bench-orchestrator`).
- **SSE Normalization & Stream Multiplexing**: Canonical `chat.completion.chunk` formatting for agent clients (Zed, Tau, OpenFang).
- **High-Frequency Health Probes**: Sub-second health polling and zero-downtime model hot-swapping.

## Documentation Index
- [Model SSOT](/herd/tools/llama-swap/config.yaml)
- [Monorepo Overview](/README.md)
