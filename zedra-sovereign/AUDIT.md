# AUDIT.md — zedra (tanlethanh/zedra)

> Cloned 2026-07-20 to `/home/toxic/projects/zedra-tanlethanh` (depth-1).
> Verdict: **this is the "Zed agent on my phone" solution the user asked for.**
> It is a mobile GPUI app (Android + iOS) + a Linux/macOS/Windows **host daemon**
> that relays a full editor/terminal/git/AI surface over an e2e-encrypted iroh
> P2P tunnel. The host daemon builds on Linux.

## 1. What it is (verdict)

- **Mobile client**: `zedra` crate — GPUI app compiled to iOS/Android cdylib.
  Renders editor, terminal (alacritty VTE), file tree, git, AI panel.
- **Host daemon**: `zedra-host` crate — runs on the desktop, exposes FS / PTY /
  Git / LSP / **AI** over RPC. Pair with a QR code; phone connects P2P.
- **Why it fits "external Zed agent via phone"**: the phone is a *viewer + input*
  for a daemon running on this box. The daemon's `AiPrompt` RPC can be pointed at
  any CLI agent via `ZEDRA_CLAUDE_BIN` (default `claude`). To use our sovereign
  stack, set that env var to a wrapper that calls the local router at `:25104`.

## 2. Repo map (top-level crates)

| Crate | Role |
|-------|------|
| `zedra-rpc` | Protocol types, QR pairing codec. No deps on other zedra crates |
| `zedra-telemetry` | Typed Event enum + TelemetryBackend trait (pure) |
| `zedra-terminal` | Remote terminal view (alacritty VTE + GPUI). Standalone |
| `zedra-session` | Client session: iroh connection, RPC, auto-reconnect |
| `zedra` | Mobile editor app (iOS+Android cdylib) |
| `zedra-host` | Desktop daemon + CLI (the part we run on Linux) |

`vendor/zed` is a **git submodule** (branch `feat/gpui-mobile` of tanlethanh/zed) —
a patched Zed fork. Treat it as editable upstream, not untouchable.

## 3. Architecture / data flow

```
Mobile (zedra)  <== iroh QUIC/TLS1.3, NAT hole-punch/relay ==>  Desktop (zedra-host)
GPUI + Metal/wgpu                                          RPC Daemon + PTY/Git/FS/AI
```

- **Transport**: iroh (QUIC/TLS 1.3). ALPN `zedra/rpc/3`. Ed25519 keypair per
  device (`~/.config/zedra/identity.key`).
- **Pairing**: QR encodes `zedra://zedra<BASE32(postcard(ZedraPairingTicket))>`
  (endpoint id, relay URL, addrs, handshake key, session id).
- **Auth**: `Register` (HMAC-SHA256 of handshake_key) → `Connect` → `Challenge`
  → `AuthProve` (Ed25519 sig) → `SyncSession`. Session tokens for fast resume.
- **RPC surface** (`zedra-rpc/src/proto.rs`): Auth, Health, Session, Filesystem
  (`FsRead`/`FsWrite`/...), Terminal (`TermCreate`/`TermAttach` bidi), Git
  (`GitCommit`/...), **AI (`AiPrompt`)**, LSP, Events (server-stream `HostEvent`).
- **AI bridge** (`crates/zedra-host/src/rpc_daemon.rs:3720`): `AiPrompt` spawns
  `Command::new(ZEDRA_CLAUDE_BIN).args(["--print", prompt])` in the workdir.
  Output streamed back as `AiPromptResult{text,done}`. **This is the seam to
  redirect at our sovereign router.**

## 4. Security model

| Layer | Mechanism |
|-------|-----------|
| Transport | QUIC/TLS 1.3 (iroh, Ed25519) |
| Identity | Ed25519 keypair per device |
| Pairing | QR out-of-band key exchange + HMAC registration |
| Session | PKI challenge-response + session tokens |
| Relay | Forwards encrypted QUIC only (zero-trust) |

Note: `ZEDRA_CLAUDE_BIN` is resolved from env to avoid a malicious `claude` earlier
in `$PATH` — good supply-chain hygiene. Relay fallback only on Symmetric/CGNAT.

## 5. Build / run / setup (Linux host)

```bash
# deps
rustup target add aarch64-linux-android        # only if building the APK
git submodule update --init --recursive        # pulls vendor/zed (large)
cargo build -p zedra-host                      # host daemon (what we run)

# run (from a project dir)
cargo run -p zedra-host -- start --workdir ~/project --detach
cargo run -p zedra-host -- qr --workdir .      # print pairing QR
# phone: install Zedra from Google Play / AppStore, scan QR
```

Pre-commit (their CI parity): `cargo fmt && cargo check -p zedra-rpc -p zedra-session -p zedra-terminal -p zedra-host`.

## 6. Gotchas

- **Submodule is heavy** (`vendor/zed` = full Zed fork). `git submodule update`
  is mandatory or the build fails. Disk: this box hits ~95% full — free
  `target/` before building.
- **`AiPrompt` is Claude-shaped** (`--print`). To use our router, write a wrapper
  script that translates `--print <prompt>` → POST `:25104/v1/chat/completions`
  and prints the reply to stdout; export `ZEDRA_CLAUDE_BIN=/path/wrapper.sh`.
- **Android build needs NDK r25c+** and `cargo-ndk`; iOS needs Xcode 26 + CocoaPods.
  We only need the **host daemon** on Linux — skip mobile SDKs.
- **`SwitchSession` is reserved/dead** — handler returns unsupported. Active
  dispatch stays bound to the original session.
- **Black screen (Android)**: surface dims must be physical px; check
  `adb shell getprop ro.hardware.vulkan` (Vulkan 1.1+).

## 7. Why this answers the user's ask

User wanted "an extension with GHAS to see all 'zed agent' via my phone /
something external / simple." `zedra` is exactly that: a phone client for a Zed
agent running on this machine, e2e-encrypted, no cloud. The `AiPrompt` seam lets
us bind it to the sovereign router instead of Claude. Setup = build `zedra-host`
+ set `ZEDRA_CLAUDE_BIN` to our wrapper + scan QR from the app.

## 8. Alternatives considered (GHAS)

- `Virtual0ps/zedra`, `tieubao/zedra` — sibling forks of the same project
  (GPUI Android experiments). `tanlethanh/zedra` is the maintained upstream with
  the shipping app + host daemon. Use it.
