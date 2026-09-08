# OpenFang — Sovereign C++ Inference Engine Fork

**OpenFang** is a C++ inference engine fork maintained as part of the Sovereign Herd architecture.

- **Engine**: `beellama.cpp` / `llama-cpp-turboquant` forks
- **Port**: Integrated into Herd (`:25100`) 
- **AstMatrix**: Circuit breaker, token bucket rate limiting, 5-strike failfast
- **Purpose**: High-performance inference for the Sovereign router

## Architecture

OpenFang operates as one of three inference engine forks behind Herd:

```
┌─────────────────────────────────────────────┐
│            Herd (:25100)                     │
│  Go Router + AstMatrix Core                 │
│  └─ beellama.cpp        │  Fast quantized   │
│  ├─ llama-cpp-turboquant │ Low VRAM fallback │
│  └─ ik_llama.cpp      │ Experimental      │
└─────────────────────────────────────────────┘
```

## Configuration

Configured via `~/sovereign/config/herd.yaml` ASTMatrix block with priority assignments. See the [Herd README](https://github.com/toxicwind/llama-swap) for the full model priority schedule.

## Status

OpenFang is a core engine component of the Herd inference router, actively maintained as part of the Sovereign production stack.

*Added as part of sovereign/tau/herd consolidation.*
