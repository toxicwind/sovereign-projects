#!/usr/bin/env python3
"""deploy.py -- apply the openrouter pool-split deployment on yote.
Run from /home/toxic/sovereign. Small steps, verify after every write.
Idempotent-ish: re-running re-applies the patch only if not already applied.
"""
import ast
import subprocess
import sys
import time

TS = time.strftime("%Y%m%d-%H%M%S")
BACKUP = f".backup/openrouter-{TS}"
STAGING = ".staging"


def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    return r


def main():
    # 0. branch check
    br = sh("git", "branch", "--show-current").stdout.strip()
    print("branch:", br)

    # 1. backup
    sh("mkdir", "-p", BACKUP)
    for f in ("bin/herd-keypool.py", "config/keypools.yaml", "config/herd.yaml"):
        r = sh("cp", f, f"{BACKUP}/")
        assert r.returncode == 0, r.stderr
    print("backup ->", BACKUP)

    # 2. patch keypool (skip if already patched)
    src = open("bin/herd-keypool.py").read()
    if "free_only" not in src:
        r = sh("python3", f"{STAGING}/patch_keypool2.py", "bin/herd-keypool.py")
        print(r.stdout.strip(), r.stderr.strip())
        assert r.returncode == 0, "patch failed"
    else:
        print("keypool already patched, skipping")
    src = open("bin/herd-keypool.py").read()
    ast.parse(src)
    assert src.count("free_only") >= 15, "patch incomplete?"
    print("keypool patched+parses OK")

    # 3. install new keypools.yaml
    r = sh("cp", f"{STAGING}/keypools-test.yaml", "config/keypools.yaml")
    assert r.returncode == 0
    print("keypools.yaml installed")

    # 4. parse-check new config with the PATCHED parser
    sys.dont_write_bytecode = True
    import importlib.util
    spec = importlib.util.spec_from_file_location("kp", "bin/herd-keypool.py")
    kp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kp)
    doc = kp._parse_simple_yaml(open("config/keypools.yaml").read())
    pools = doc.get("pools", {})
    assert set(pools) == {"openrouter-free", "openrouter-paid", "gemini"}, set(pools)
    fe = pools["openrouter-free"]["keys"]
    assert isinstance(fe[0], dict) and fe[0].get("free_only") is True, fe
    assert "OPENROUTER_API_KEY_FREE" not in str(pools["openrouter-paid"]["keys"])
    print("config parses: pools", sorted(pools))

    # 5. repoint herd peers
    herd = open("config/herd.yaml").read()
    if "127.0.0.1:25109/openrouter-free" not in herd:
        r = sh("python3", "/tmp/patch_herd_peers.py")
        print(r.stdout.strip(), r.stderr.strip())
        assert r.returncode == 0, "herd repoint failed"
    else:
        print("herd peers already repointed, skipping")

    # 6. selftest on the LIVE file
    r = sh("python3", "bin/herd-keypool.py", "--selftest")
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    print("selftest:", " | ".join(tail))
    assert r.returncode == 0, "selftest failed"

    print("DEPLOY_OK", TS)


main()
