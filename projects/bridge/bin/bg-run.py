#!/usr/bin/env python3
"""bg-run.py — detached background command runner (bridge-max).

Launched fully detached from the bridge exec lane, e.g.:
    setsid nohup python3 bg-run.py <handle> <cmdb64> [workdir] [timeout_s] \
        >launcher.log 2>&1 < /dev/null &

State dir: /home/toxic/.cache/bridge-bg/<handle>/
    cmd.txt      the decoded command
    status.json  {"state": "running"|"done"|"killed"|"timeout",
                  "pid", "pgid", "started", "finished"?, "code"?,
                  "signal"?, "cmd"}
    stdout.log / stderr.log   captured output (unbounded via files, not memory)

The launcher is expected to run with cwd set to the state dir so `&` binds
only to this process (see AGENTS.md: daemon-start `&` scoping). This script
does NOT daemonize itself — detachment is the launcher's job via setsid.
The command runs in its own process group (start_new_session) so timeout /
signal kills reap the whole tree, not just the direct child.

Status writes are atomic (write tmp + os.replace) so readers never see
a torn file. SIGTERM/SIGINT mark the job "killed" instead of leaving a
stale "running". Poll-free: readers just `cat status.json`.
"""

import base64
import json
import os
import re
import signal
import subprocess
import sys
import time

BASE = "/home/toxic/.cache/bridge-bg"
HANDLE_RX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

_proc = None       # the running child Popen, for the signal handler
_term_signum = 0   # set when SIGTERM/SIGINT arrives


def _wjson(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def _on_term(signum, frame):
    """SIGTERM/SIGINT: kill the whole child process group, then let the
    main flow fall through to the finally block which records "killed"."""
    global _term_signum
    _term_signum = signum
    try:
        if _proc is not None:
            os.killpg(os.getpgid(_proc.pid), signal.SIGTERM)
    except Exception:
        pass
    # Do NOT exit here: the main flow's finally records the killed state
    # after reaping. Raise so a blocking wait() wakes up promptly.
    raise SystemExit(128 + signum)


def _kill_tree(proc, escalate_s=5):
    """SIGTERM the child process group, escalate to SIGKILL after escalate_s.

    Event-driven: Popen.wait(timeout) reaps via waitpid — no sleep loops.
    (A dead-but-unreaped child keeps its pgid alive for killpg(pgid, 0),
    so polling the pgid alone would spin the full escalation window.)
    """
    try:
        pgid = os.getpgid(proc.pid)
    except (ProcessLookupError, PermissionError, OSError):
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        return
    try:
        proc.wait(timeout=escalate_s)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(pgid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass


def main():
    global _proc
    if len(sys.argv) < 3 or len(sys.argv) > 5:
        print("usage: bg-run.py <handle> <cmdb64> [workdir] [timeout_s]",
              file=sys.stderr)
        return 2
    handle, cmdb64 = sys.argv[1], sys.argv[2]
    workdir = sys.argv[3] if len(sys.argv) > 3 else "/home/toxic"
    try:
        timeout = float(sys.argv[4]) if len(sys.argv) > 4 else 0
    except ValueError:
        print("bad timeout_s", file=sys.stderr)
        return 2
    if not HANDLE_RX.match(handle):
        print("bad handle", file=sys.stderr)
        return 2
    if not os.path.isdir(workdir):
        print("bad workdir: %r" % workdir, file=sys.stderr)
        return 2
    d = os.path.join(BASE, handle)
    os.makedirs(d, exist_ok=True)
    try:
        cmd = base64.b64decode(cmdb64.encode()).decode("utf-8", "replace")
    except Exception as e:
        print("bad cmdb64: %s" % e, file=sys.stderr)
        return 2
    if not cmd.strip():
        print("empty command", file=sys.stderr)
        return 2
    with open(os.path.join(d, "cmd.txt"), "w") as f:
        f.write(cmd)

    st_path = os.path.join(d, "status.json")
    started = time.time()
    signal.signal(signal.SIGTERM, _on_term)
    signal.signal(signal.SIGINT, _on_term)

    state, code, extra = "done", 1, {}
    pgid = None
    try:
        with open(os.path.join(d, "stdout.log"), "wb") as out, \
             open(os.path.join(d, "stderr.log"), "wb") as err:
            _proc = subprocess.Popen(
                cmd, shell=True, cwd=workdir,
                stdout=out, stderr=err,
                start_new_session=True,  # own process group: killpg reaps all
            )
            try:
                pgid = os.getpgid(_proc.pid)
            except (ProcessLookupError, PermissionError, OSError):
                pgid = None
            _wjson(st_path, {"state": "running", "pid": _proc.pid,
                             "pgid": pgid, "started": started,
                             "cmd": cmd[:500], "workdir": workdir,
                             "timeout_s": timeout or None})
            try:
                code = _proc.wait(timeout=timeout if timeout > 0 else None)
            except subprocess.TimeoutExpired:
                _kill_tree(_proc)
                _proc.wait()
                state, code = "timeout", -1
                extra = {"timeout_s": timeout}
    except SystemExit as e:
        # from _on_term: child group already SIGTERMed; reap (event-driven),
        # escalate if it ignores the signal, and record "killed".
        try:
            if _proc is not None:
                pgid = os.getpgid(_proc.pid)
                _proc.wait(timeout=5)
            else:
                pgid = None
        except subprocess.TimeoutExpired:
            if _proc is not None:
                _kill_tree(_proc, escalate_s=2)
            try:
                _proc.wait()
            except Exception:
                pass
        except Exception:
            pass
        state, code = "killed", 128 + (_term_signum or 15)
        extra = {"signal": _term_signum or 15}
        # fall through to finally which writes the status
    except Exception as e:
        try:
            with open(os.path.join(d, "stderr.log"), "ab") as err:
                err.write(("bg-run failed: %s: %s\n"
                           % (type(e).__name__, e)).encode())
        except OSError:
            pass
    finally:
        _wjson(st_path, {"state": state,
                         "pid": _proc.pid if _proc else None,
                         "pgid": pgid,
                         "started": started, "finished": time.time(),
                         "code": code, "cmd": cmd[:500],
                         "workdir": workdir, **extra})
    return 0


if __name__ == "__main__":
    sys.exit(main())
