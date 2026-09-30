# fleet-mirror-flush

Yote-native completion path for fleet messages, under `/home/toxic/hatch/crons/`.

## Why this exists

`fleet-post` (hatch cell) hyper-races fleet delivery. Alongside the race it
writes a **write-ahead journal record** to
`/home/toxic/hatch/fleet-outbox/pending/<uuid>.json` on yote. On any confirmed
delivery the record is deleted. If the race fails but the journal landed, this
timer completes the post — so a message survives even if the cell dies
mid-race. If the journal write also fails (bridge down), `fleet-post` falls
back to the cell spool `~/workspace/fleet-outbox/`, exactly as before.

## The two stores are disjoint — no double-fire

| Store | Written when | Swept by |
|---|---|---|
| `/home/toxic/hatch/fleet-outbox/pending/` (yote mirror) | journal write landed (bridge up at post time) | this timer (`fleet-mirror-flush`) |
| `~/workspace/fleet-outbox/` (cell spool) | journal AND both delivery paths failed (bridge down) | Hatch platform cron `fleet-outbox-flush` |

A message is journaled to **exactly one** store, decided by whether the journal
write landed. The Hatch cron never sees mirror records; this timer never sees
the cell spool. Both must keep running — disabling either one strands its
store's messages. "Never leave both running" applies to duplicate coverage of
the *same* source; here the sources are disjoint by construction.

## Idempotency

For each record the flusher greps the channel dir for `uuid: <uuid>` before
posting. Already-delivered → delete the stale record. Crash between post and
delete → next run finds the uuid and deletes the record. A message is
therefore posted at most once per store, and each store is swept by exactly
one flusher.

## Files

- `flush.sh` — the sweeper (bash + python3, `flock` single-instance,
  appends to `/home/toxic/hatch/fleet-outbox/flush.log`)
- `fleet-mirror-flush.service` / `fleet-mirror-flush.timer` — systemd user
  units, installed to `~/.config/systemd/user/`, every 2 min, `Persistent=true`
- Install: `systemctl --user daemon-reload && systemctl --user enable --now fleet-mirror-flush.timer`
- Verify: `systemctl --user list-timers | grep mirror`, then drop a test
  record in `pending/` with a fresh uuid and watch it get completed + logged.
