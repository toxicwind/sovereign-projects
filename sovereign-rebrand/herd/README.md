# Herd

> Orchestrate fleets of LLM inference engines. Zero downtime, zero friction.

[![CI](https://github.com/toxicwind/herd/actions/workflows/ci.yml/badge.svg)](https://github.com/toxicwind/herd/actions)
[![Lint](https://github.com/toxicwind/herd/actions/workflows/lint.yml/badge.svg)](https://github.com/toxicwind/herd/actions)
[![Test](https://github.com/toxicwind/herd/actions/workflows/test.yml/badge.svg)](https://github.com/toxicwind/herd/actions)
[![Security](https://github.com/toxicwind/herd/actions/workflows/security.yml/badge.svg)](https://github.com/toxicwind/herd/actions)
[![License: SOL](https://img.shields.io/badge/License-SOL%20v1.0-blue.svg)](./LICENSE)
[![Upstream Sync](https://github.com/toxicwind/herd/actions/workflows/upstream-sync.yml/badge.svg)](https://github.com/toxicwind/herd/actions)

## Why Herd?

A swap is one action. A herd is orchestration.

We started with the same foundation — hot-swapping LLM models — and made it scale. Where the original handled one model at a time, Herd manages entire fleets. Where it dropped connections, Herd keeps them alive with SSE. Where it lacked visibility, Herd provides health dashboards and rate limiting.

## What Makes Herd Scale

| Feature | Original | Herd |
|---------|----------|------|
| Model switching | Single swap | **Fleet orchestration** |
| Connections | Drop on swap | **SSE keep-alive** |
| Monitoring | None | **Health UI + API** |
| Rate limiting | None | **AstMatrix engine** |
| Backends | llama.cpp | **llama.cpp + vLLM + SGLang + Ollama** |

## Architecture

```mermaid
graph LR
    A[Client] --> B[Herd Router]
    B --> C{Route}
    C -->|Small| D[llama.cpp 7B]
    C -->|Medium| E[vLLM 13B]
    C -->|Large| F[SGLang 70B]
    C -->|Fallback| G[Ollama CPU]
    D --> H[Response]
    E --> H
    F --> H
    G --> H
```

## Quick Start

```bash
git clone https://github.com/toxicwind/herd.git
cd herd
go build -v -ldflags="-s -w" -o herd ./cmd
./herd --config config.yaml
```

## Lineage

Herd is a sovereign evolution of the inference gateway space. We maintain sync capability with the original [mostlygeek/llama-swap](https://github.com/mostlygeek/llama-swap) project — our common ancestor.

- **Daily automated sync** via GitHub Actions
- **29 commits ahead** with routing enhancements
- **All upstream contributions** preserved and attributed
- **Upstream code** remains under its original MIT license
- **Herd enhancements** are licensed under SOL v1.0

## License

Sovereign Open License (SOL) v1.0 — see [LICENSE](./LICENSE)

## Stars

If Herd saves you from model management hell, please ⭐ star it. Orchestrate, don't swap.
