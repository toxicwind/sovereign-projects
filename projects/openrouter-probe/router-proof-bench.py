#!/usr/bin/env python3
"""Head-to-head router proof benchmark (2026-09-21).

Contender A (intelligent): sovereign-router v3.2 :25104, model "sovereign/free"
Contender B (dumb direct): herd llama-swap :25100, model "openrouter-free/cohere/north-mini-code:free"

30 trials x 3 prompt types per contender, strictly sequential (no parallelism).
429s and errors are DATA: recorded, never retried.

Trial types:
  EXACT   - "Output exactly: BENCH-<token>. No other text." -> exact match
  QUALITY - recursion prompt -> fixed judge (openrouter-free/nex-agi/nex-n2.5-pro:free) scores 0-10
  CODE    - fib(n) prompt -> 1 if "def fib" in body else 0
Empty/whitespace-only body = failure for ALL types (substance guard).
max_tokens=512 on every request (reasoning models need headroom).
Timeout 120s per request.
"""
import json
import random
import re
import time
import urllib.request
import urllib.error
from collections import Counter

HERD = "http://127.0.0.1:25100"
SOV = "http://127.0.0.1:25104"
OUTDIR = "/home/toxic/sovereign/projects/openrouter-probe"
OUT = OUTDIR + "/router-proof-20260921.json"
LOG = OUTDIR + "/router-proof-20260921.log"

TRIALS = 30
REQ_TIMEOUT = 120
MAX_TOKENS = 512

CONTENDERS = [
    ("A_intelligent", SOV, "sovereign/free"),
    ("B_dumb_direct", HERD, "openrouter-free/cohere/north-mini-code:free"),
]
JUDGE_BASE, JUDGE_MODEL = HERD, "openrouter-free/nex-agi/nex-n2.5-pro:free"

QUALITY_PROMPT = ("Explain recursion in exactly three sentences for a smart 12-year-old, "
                  "with one concrete real-world example.")
CODE_PROMPT = "Write a Python function fib(n) returning the nth Fibonacci number. Code only."
JUDGE_PROMPT_TMPL = (
    "Score 0-10: exactly-three-sentences (0-3), correctness (0-3), "
    "concrete example (0-2), age-fit (0-2). Reply with just the number.\n\n"
    "ANSWER TO SCORE:\n{answer}"
)


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def chat(base, model, prompt, timeout=REQ_TIMEOUT):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
    }).encode()
    req = urllib.request.Request(
        base + "/v1/chat/completions", data=body,
        headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        dt = (time.monotonic() - t0) * 1000.0
        d = json.loads(raw)
        if d.get("error"):
            err = d["error"]
            return {"ok": False, "latency_ms": round(dt, 1),
                    "error": f"api_error: {str(err.get('message', err))[:200]}"}
        ch = (d.get("choices") or [{}])[0]
        content = ((ch.get("message") or {}).get("content")) or ""
        return {"ok": True, "content": content, "serving_model": d.get("model"),
                "latency_ms": round(dt, 1)}
    except urllib.error.HTTPError as e:
        dt = (time.monotonic() - t0) * 1000.0
        try:
            detail = e.read().decode(errors="replace")[:300]
        except Exception:
            detail = ""
        return {"ok": False, "latency_ms": round(dt, 1),
                "error": f"http_{e.code}: {detail}"}
    except Exception as e:
        dt = (time.monotonic() - t0) * 1000.0
        return {"ok": False, "latency_ms": round(dt, 1),
                "error": f"{type(e).__name__}: {str(e)[:200]}"}


def parse_judge_number(text):
    m = re.search(r"\d+(?:\.\d+)?", text or "")
    if not m:
        return None
    try:
        v = float(m.group(0))
    except ValueError:
        return None
    return max(0.0, min(10.0, v))


def run_trial(contender_name, base, model, trial_idx, token):
    rec = {"contender": contender_name, "trial": trial_idx,
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    # ---- type 1: EXACT ----
    prompt = f"Output exactly: {token}. No other text."
    r = chat(base, model, prompt)
    e = {"type": "EXACT", "latency_ms": r["latency_ms"],
         "serving_model": r.get("serving_model"), "error": r.get("error")}
    body = (r.get("content") or "")
    if not r["ok"] or not body.strip():
        e.update(success=False, score=0.0,
                 note="empty" if r["ok"] else "transport_error")
    else:
        exact = body.strip() == token
        e.update(success=exact, score=1.0 if exact else 0.0)
    rec["exact"] = e

    # ---- type 2: QUALITY (judged) ----
    r = chat(base, model, QUALITY_PROMPT)
    q = {"type": "QUALITY", "latency_ms": r["latency_ms"],
         "serving_model": r.get("serving_model"), "error": r.get("error")}
    body = (r.get("content") or "")
    if not r["ok"] or not body.strip():
        q.update(success=False, score=None, judge_score=None,
                 note="empty" if r["ok"] else "transport_error")
    else:
        jr = chat(JUDGE_BASE, JUDGE_MODEL,
                  JUDGE_PROMPT_TMPL.format(answer=body[:4000]))
        q["judge_latency_ms"] = jr["latency_ms"]
        q["judge_model"] = jr.get("serving_model")
        if not jr["ok"]:
            q.update(success=False, score=None, judge_score=None,
                     judge_error=jr.get("error"))
        else:
            js = parse_judge_number(jr.get("content") or "")
            if js is None:
                q.update(success=False, score=None, judge_score=None,
                         judge_error="unparseable_judge_output",
                         judge_raw=(jr.get("content") or "")[:120])
            else:
                q.update(success=js >= 6.0, score=js, judge_score=js)
    rec["quality"] = q

    # ---- type 3: CODE ----
    r = chat(base, model, CODE_PROMPT)
    c = {"type": "CODE", "latency_ms": r["latency_ms"],
         "serving_model": r.get("serving_model"), "error": r.get("error")}
    body = (r.get("content") or "")
    if not r["ok"] or not body.strip():
        c.update(success=False, score=0.0,
                 note="empty" if r["ok"] else "transport_error")
    else:
        has = "def fib" in body
        c.update(success=has, score=1.0 if has else 0.0)
    rec["code"] = c
    return rec


def percentile(xs, p):
    if not xs:
        return None
    s = sorted(xs)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return round(s[f] + (s[c] - s[f]) * (k - f), 1)


def summarize(records):
    out = {}
    for cname, _, _ in CONTENDERS:
        recs = [r for r in records if r["contender"] == cname]
        per = {}
        for tkey in ("exact", "quality", "code"):
            ts = [r[tkey] for r in recs]
            n = len(ts)
            ok_transport = sum(1 for t in ts if not t.get("error"))
            succ = sum(1 for t in ts if t.get("success"))
            scores = [t["score"] for t in ts if t.get("score") is not None]
            lats = [t["latency_ms"] for t in ts if t.get("latency_ms") is not None]
            wins = Counter(t.get("serving_model") or "unknown"
                           for t in ts if t.get("success"))
            per[tkey] = {
                "n": n,
                "transport_ok_rate": round(ok_transport / n, 4) if n else None,
                "success_rate": round(succ / n, 4) if n else None,
                "mean_score": round(sum(scores) / len(scores), 3) if scores else None,
                "scored_n": len(scores),
                "p50_latency_ms": percentile(lats, 50),
                "p95_latency_ms": percentile(lats, 95),
                "models_serving_wins": dict(wins),
                "errors": Counter(t["error"].split(":")[0]
                                  for t in ts if t.get("error")),
            }
            per[tkey]["errors"] = dict(per[tkey]["errors"])
        out[cname] = per
    return out


def main():
    random.seed(20260921)
    tokens = [f"BENCH-{''.join(random.choices('ABCDEFGHJKMNPQRSTUVWXYZ23456789', k=6))}"
              for _ in range(TRIALS)]
    records = []
    started = time.strftime("%Y-%m-%dT%H:%M:%S")
    log(f"START trials={TRIALS} contenders={[c[0] for c in CONTENDERS]}")
    done = 0
    total = TRIALS * 3 * len(CONTENDERS)
    for cname, base, model in CONTENDERS:
        for i in range(TRIALS):
            rec = run_trial(cname, base, model, i, tokens[i])
            records.append(rec)
            done += 3
            with open(OUT, "w") as f:
                json.dump({"started": started, "tokens": tokens,
                           "summary": summarize(records),
                           "records": records}, f, indent=1)
            e, q, c = rec["exact"], rec["quality"], rec["code"]
            log(f"[{done}/{total}] {cname} t{i}: "
                f"EXACT ok={e['success']} {e['latency_ms']}ms {e.get('serving_model','?')} | "
                f"QUAL ok={q['success']} score={q.get('score')} {q['latency_ms']}ms | "
                f"CODE ok={c['success']} {c['latency_ms']}ms")
        log(f"CONTENDER DONE: {cname}")
    summary = summarize(records)
    with open(OUT, "w") as f:
        json.dump({"started": started,
                   "finished": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "tokens": tokens, "summary": summary,
                   "records": records}, f, indent=1)
    log("FINISHED all contenders")
    log("SUMMARY: " + json.dumps(summary))


if __name__ == "__main__":
    main()
