#!/usr/bin/env python3
"""unshare-root.py: Run commands in unshared user namespace as root."""
import os, sys, subprocess, ctypes

SYS_unshare = 272
CLONE_NEWUSER = 0x10000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNS = 0x00020000
CLONE_NEWNET = 0x40000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWUTS = 0x04000000

libc = ctypes.CDLL(None, use_errno=True)

def unshare_root():
    """Enter new user namespace with root mapping."""
    flags = CLONE_NEWUSER | CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWNET | CLONE_NEWIPC | CLONE_NEWUTS
    ret = libc.syscall(SYS_unshare, flags)
    if ret == -1:
        err = ctypes.get_errno()
        print(f"unshare failed: errno {err}", file=sys.stderr)
        return False
    # Map current user to root in new namespace
    uid = os.getuid()
    gid = os.getgid()
    with open("/proc/self/uid_map", "w") as f:
        f.write(f"0 {uid} 1\n")
    with open("/proc/self/setgroups", "w") as f:
        f.write("deny\n")
    with open("/proc/self/gid_map", "w") as f:
        f.write(f"0 {gid} 1\n")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: unshare-root.py <command> [args...]")
        sys.exit(1)
    if not unshare_root():
        sys.exit(1)
    os.execlp(sys.argv[1], *sys.argv[1:])

if __name__ == "__main__":
    main()
