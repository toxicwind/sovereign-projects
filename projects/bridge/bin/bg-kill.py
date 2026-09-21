#!/usr/bin/env python3
"""bg-kill.py — SIGTERM a detached bridge-bg job's whole process group.

Usage: bg-kill.py <handle>

Reads the pid from /home/toxic/.cache/bridge-bg/<handle>/status.json,
verifies via /proc/<pid>/cmdline that it is still OUR bg-run.py for this
handle (never signal a reused pid), then SIGTERMs the process GROUP
(negative pid — the runner is setsid'd, so the group is just it and its
children). The runner's SIGTERM handler reaps the child tree and records
"killed"; the next bg-status query reaps anything else as "stale".

Fallback: if the runner itself is dead but state is still "running" and
status.json records the child pgid, the orphaned tree is signaled via
that pgid — killpg(pgid, 0) must succeed first, and a pgid whose whole
group died can never be recycled while a member lives, so a live pgid
here is still our tree.

Prints one JSON doc: {"handle", "signaled": pid} or
{"handle", "signaled_pg": pgid} or
{"handle", "state": "not-running"/"bad-handle", ...}.

Canonical source: projects/bridge/bin/bg-kill.py in
toxicwind/sovereign-projects (bridge-max, 2026-09-20).
"""
import json
import os
import re
import signal
import sys

BASE = "/home/toxic/.cache/bridge-bg"
HANDLE_RX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _pid_is_ours(pid, handle):
    try:
        with open("/proc/%d/cmdline" % pid, "rb") as f:
            cl = f.read().decode("utf-8", "replace").replace("\x00", " ")
        return "bg-run.py" in cl and handle in cl
    except Exception:
        return False


def main():
    if len(sys.argv) != 2 or not HANDLE_RX.match(sys.argv[1]):
        print(json.dumps({"handle": sys.argv[1] if len(sys.argv) > 1 else None,
                          "state": "bad-handle"}))
        return 2
    handle = sys.argv[1]
    st_path = os.path.join(BASE, handle, "status.json")
    try:
        with open(st_path) as f:
            st = json.load(f)
    except Exception as e:
        print(json.dumps({"handle": handle, "state": "unknown",
                          "error": "no status.json: %s" % e}))
        return 0
    pid = st.get("pid")
    if st.get("state") != "running" or not isinstance(pid, int) \
            or not _pid_is_ours(pid, handle):
        # Runner gone. Fall back to the recorded child process group: a
        # crashed runner can leave its tree alive with state "running".
        # A pgid is only recycled after its whole group dies, and then
        # killpg(pgid, 0) raises ProcessLookupError — so a pgid that
        # answers the existence probe is still our orphaned tree.
        pgid = st.get("pgid")
        if st.get("state") == "running" and isinstance(pgid, int) \
                and pgid > 0:
            try:
                os.killpg(pgid, 0)
            except ProcessLookupError:
                pass  # group gone; status query will reap as stale
            except (PermissionError, OSError) as e:
                print(json.dumps({"handle": handle, "state": "error",
                                  "error": "pgid %d not signalable: %s: %s"
                                  % (pgid, type(e).__name__, e)}))
                return 0
            else:
                try:
                    os.killpg(pgid, signal.SIGTERM)
                except (ProcessLookupError, PermissionError, OSError) as e:
                    print(json.dumps({"handle": handle, "state": "error",
                                      "error": "%s: %s"
                                      % (type(e).__name__, e)}))
                    return 0
                print(json.dumps({"handle": handle, "signaled_pg": pgid,
                                  "note": "runner dead; SIGTERM sent to "
                                          "orphaned process group %d" % pgid}))
                return 0
        print(json.dumps({"handle": handle, "state": "not-running",
                          "note": "no live runner for this handle"}))
        return 0
    try:
        os.killpg(pid, signal.SIGTERM)
    except Exception as e:
        print(json.dumps({"handle": handle, "state": "error",
                          "error": "%s: %s" % (type(e).__name__, e)}))
        return 0
    print(json.dumps({"handle": handle, "signaled": pid,
                      "note": "SIGTERM sent to process group %d" % pid}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
