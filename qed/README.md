# QED

**QED** is the sovereign AI-native editor — a fork of [Zed](https://github.com/zed-industries/zed) maintained as `toxicwind/qed` (with `toxicwind/zedra` as the remote LSP host fork). It is the workspace IDE that consumes [Tau](/tau) agent tools and [Mesh](/mesh) MCP tools.

QED is **not** the control plane. The authoritative supervisor lives in `~/sovereign/`.

## Layout
```
qed/
├── editor/       # QED fork of Zed (GPUI, Rust)
└── zedra-host/   # Headless remote LSP host process; binds :25130
```

## Documentation Index
- [Monorepo Overview](/README.md)
