# QED — Definitive AI-Native Code Editor & Remote Substrate

**Port**: `:25130` (Host & Collaboration)  
**Role**: The unified editor layer for the Sovereign autonomous agent ecosystem.

---

## 🏛️ Workspace Topology

QED unifies the desktop editor engine and the remote mobile/P2P substrate under a single cohesive workspace:

```
qed/
├── zed/     ← Definitive AI-native editor engine (our toxicwind/zed fork)
│               - 240+ Rust crates, GPUI accelerated rendering
│               - First-class NVIDIA NIM, Inkling, and MCP tool normalizers
│               - Port: :25130 (Livekit collaboration & server)
└── zedra/   ← Remote daemon & mobile client substrate (Zedra host)
                - P2P tunnel over QUIC/UDP (Iroh)
                - Mobile agent hooks, e2e encryption
                - Remote headless daemon
```

---

## 🚀 Quick Verification

```bash
# Verify Zed workspace builds
cargo check --manifest-path qed/zed/Cargo.toml --package zed

# Verify Zedra daemon builds
bun --cwd qed/zedra test
```
