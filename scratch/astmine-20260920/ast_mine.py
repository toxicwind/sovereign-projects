#!/usr/bin/env python3
"""AST structural mining across nim-repos v2. Fixed patterns, stderr visible."""
import json, os, re, subprocess, sys

ROOT = "/home/toxic/sovereign/projects/nim-repos"
OUT = "/tmp/astmine"
os.makedirs(OUT, exist_ok=True)

def run_ast(pattern, extra=None):
    cmd = ["ast-grep", "--json", "--pattern", pattern] + (extra or [])
    cmd += ["--globs", "!**/node_modules/**", "--globs", "!**/.git/**",
            "--globs", "!**/dist/**", "--globs", "!**/build/**",
            "--globs", "!**/*.min.js", ROOT]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if p.returncode != 0 and not p.stdout.strip():
            print("ASTERR", pattern, p.stderr.strip()[:150], file=sys.stderr)
            return []
        return json.loads(p.stdout) if p.stdout.strip() else []
    except Exception as e:
        print("ERR", pattern, e, file=sys.stderr)
        return []

def run_rule(rule_yaml):
    rp = "/tmp/ast_rule.yaml"
    open(rp, "w").write(rule_yaml)
    cmd = ["ast-grep", "scan", "--rule", rp, "--json",
           "--globs", "!**/node_modules/**", "--globs", "!**/.git/**",
           "--globs", "!**/dist/**", ROOT]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if p.returncode != 0 and not p.stdout.strip():
            print("RULEERR", p.stderr.strip()[:200], file=sys.stderr)
            return []
        return json.loads(p.stdout) if p.stdout.strip() else []
    except Exception as e:
        print("ERR rule", e, file=sys.stderr)
        return []

def short(t, n=1200):
    t = (t or "").replace("\n", "\\n")
    return t[:n] + ("..." if len(t) > n else "")

def save(name, items):
    json.dump(items, open(os.path.join(OUT, name + ".json"), "w"), indent=1)
    print(name, len(items), flush=True)

def rel(f): return f[len(ROOT)+1:] if f.startswith(ROOT) else f

STATUS = re.compile(r"\b(404|410|402|429|403)\b")
NOTFOUND = re.compile(r"not found|Function", re.I)

# Q1: try/catch inspecting status / error bodies
hits = []
for pat in ["try { $$$A } catch ($E) { $$$B }", "try { $$$A } catch { $$$B }"]:
    for m in run_ast(pat):
        t = m.get("text", "")
        if STATUS.search(t) or NOTFOUND.search(t):
            hits.append({"file": rel(m["file"]), "text": short(t)})
save("catch_status", hits)

# Q2: NVCF-* header string literals (rule with regex on string fragments)
hits = []
rule = """id: nvcf-header
language: Tsx
rule:
  regex: 'NVCF-[A-Za-z-]+'
"""
for m in run_rule(rule):
    hits.append({"file": rel(m["file"]), "line": m["range"]["start"]["line"],
                 "text": short(m.get("text", ""), 300)})
save("nvcf_headers", hits)

# Q3: model map objects
hits = []
for m in run_ast("const $M = { $$$ }"):
    t = m.get("text", "")
    head = t[:100]
    if re.search(r"[Mm]odel|MODEL|router|Router|fallback|Fallback|provider|PROVIDER", head):
        ids = re.findall(r"['\"]([a-z0-9][a-z0-9_.-]*/[a-z0-9_./-]+)['\"]", t)
        if ids:
            hits.append({"file": rel(m["file"]), "head": short(head, 150),
                         "model_ids": sorted(set(ids))[:50], "n_ids": len(set(ids))})
save("model_maps", hits)

# Q4: switch on model/provider
hits = []
for m in run_ast("switch ($X) { $$$ }"):
    t = m.get("text", "")
    if re.search(r"model|Model|MODEL|provider|Provider", t[:300]):
        cases = re.findall(r"case\s+['\"]([^'\"]+)['\"]", t)
        hits.append({"file": rel(m["file"]), "cases": cases[:40], "text": short(t, 500)})
save("switch_routing", hits)

# Q5: client calls w/ full config — find calls then filter text for NIM host
hits = []
for pat in ["fetch($A, $B)", "axios($C)", "axios.post($U, $D, $C)", "axios.get($U, $C)",
            "$C.post($U, $D, $O)", "$C.get($U, $O)"]:
    for m in run_ast(pat):
        t = m.get("text", "")
        if "integrate.api.nvidia.com" in t:
            hdrs = re.findall(r"['\"]([A-Za-z][A-Za-z0-9-]*)['\"]\s*:", t)
            hdrs = [h for h in hdrs if len(h) > 2]
            hits.append({"file": rel(m["file"]), "headers": sorted(set(hdrs)),
                         "text": short(t, 1500)})
save("client_calls", hits)

# Q6: setTimeout retry/backoff
hits = []
for m in run_ast("setTimeout($$$)"):
    t = m.get("text", "")
    if re.search(r"retry|Retry|backoff|Backoff", t):
        hits.append({"file": rel(m["file"]), "text": short(t, 400)})
save("retry_backoff", hits)

# Q7: http client construction files (any file that mentions the host, in code)
hits = []
for m in run_ast("'integrate.api.nvidia.com'"):
    f = rel(m["file"])
    if f.endswith((".md", ".txt", ".rst")): continue
    hits.append({"file": f, "line": m["range"]["start"]["line"]})
byf = {}
for h in hits: byf[h["file"]] = byf.get(h["file"], 0) + 1
save("host_refs", [{"file": f, "n": n} for f, n in sorted(byf.items(), key=lambda x: -x[1])])

print("done", OUT, flush=True)
