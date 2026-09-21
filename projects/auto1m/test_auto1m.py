#!/usr/bin/env python3
"""Proof test for auto1m: ~700k-token real-doc corpus (192 md files, far beyond
any single worker model's window), one cross-chunk question whose answer
requires facts from THREE different source files. Pass = all key phrases
present + every citation resolves to a real chunk."""

import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auto1m import answer_question, est_tokens

CORPUS_DIRS = [
    "/home/toxic/sovereign/docs",
    "/home/toxic/sovereign/projects/tau/docs",
    "/home/toxic/sovereign/projects/herd/docs",
]

QUERY = (
    "Answer all three, one line each: "
    "(1) What are yote's hardware specs — cores, RAM, GPU? "
    "(2) Which two endpoints does google-antigravity auto-failover across, and which is primary? "
    "(3) What is kimi-auto — is it an alias for K1.5? "
    "Cite every claim like [C0007]."
)

# key phrases per sub-question; all must appear (case-insensitive)
EXPECT = [
    ["16 cores", "62 GB", "RTX 3090"],                       # fleet-knowledgebase.md
    ["daily-cloudcode-pa.googleapis.com", "sandbox"],        # tau provider-quirks.md
    ["resolver-owned virtual model", "K1.5"],                # herd models.md
]


def build_corpus():
    parts, n = [], 0
    for d in CORPUS_DIRS:
        for root, _, files in os.walk(d):
            for fn in sorted(files):
                if fn.endswith(".md"):
                    p = os.path.join(root, fn)
                    parts.append(f"\n\n===== FILE: {p} =====\n" +
                                 open(p, encoding="utf-8", errors="replace").read())
                    n += 1
    return "".join(parts), n


def main():
    corpus, nfiles = build_corpus()
    toks = est_tokens(corpus)
    print(f"corpus: {nfiles} files, {len(corpus)} chars, ~{toks} est tokens")
    assert toks > 200_000, "corpus must exceed any single worker window"

    t0 = time.time()
    res = answer_question(QUERY, corpus, force_composite=True)
    dt = time.time() - t0

    print(f"lane: {res['lane']}")
    print(f"stats: {json.dumps(res['stats'])}")
    print(f"wall: {dt:.1f}s")
    print("---- ANSWER ----")
    print(res["answer"])
    print("----------------")

    ans = res["answer"].lower()
    failures = []
    for i, phrases in enumerate(EXPECT):
        missing = [p for p in phrases if p.lower() not in ans]
        if missing:
            failures.append(f"Q{i+1} missing: {missing}")
    # provenance: every [Cxxxx] citation must resolve to a real chunk
    cites = set(re.findall(r"\[C(\d{4})\]", res["answer"]))
    prov = res["provenance"] if isinstance(res["provenance"], dict) else {}
    bad = [c for c in cites if f"C{c}" not in prov]
    if bad:
        failures.append(f"dangling citations: {bad}")
    if not cites:
        failures.append("no citations in answer at all")

    print(f"citations: {sorted(cites)} -> "
          f"{[prov.get('C'+c, {}).get('source','?')[:60] for c in sorted(cites)]}")
    if failures:
        print("FAIL:")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    print("PASS: all three cross-chunk facts present, citations resolve.")
    json.dump({"query": QUERY, "answer": res["answer"], "lane": res["lane"],
               "stats": res["stats"], "expect": EXPECT},
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "test-evidence.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
