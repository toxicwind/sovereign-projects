#!/usr/bin/env python3
"""auto1m — virtual 1M-context composite route (prototype).

No single model here has a 1M-token window, so this route *composes* one:
oversized inputs are chunked, mapped in parallel across the model fleet via
the sovereign router, and tree-reduced to a single answer with provenance.
When the prompt fits a native 1M model, it routes direct (no map-reduce tax).

Design lineage (repos cloned + read on yote, code-verified):
- thunlp/LLMxMapReduce V1 Generator.py: sentence-aware chunking with
  token-budget accounting (window - prompt - max_tokens), mr_map fan-out,
  mr_collapse tree-collapse loop, mr_reduce with "Information of Chunk N"
  provenance labels.
- THUNLP-MT/ExtAgents pipeline.py: iterative map with info scoring,
  score-sorted selection, exponential candidate counts, early exit.

Hot-path doctrine: race parallel map calls, fail fast per call (120s ceiling,
errors recorded never retried), most query-relevant chunks dispatch first so
partial failure still yields the key facts.
"""

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

ROUTER = "http://127.0.0.1:25104"
MAP_MODEL = "sovereign/free"               # fleet route: router picks, fails over
DIRECT_MODEL = "deepseek/deepseek-v4-pro-0813"  # native ~1M via API (1.6T MoE: never local)
CHUNK_TOKENS = 4000                        # safe for free-tier / local workers
CHUNK_OVERLAP_TOKENS = 200
MAP_WORKERS = 8
CALL_TIMEOUT = 120
DIRECT_BUDGET = 800_000                    # est tokens under which direct lane is tried
REDUCE_BUDGET = 5000                       # est tokens the final reduce may consume
SCORE_BATCH = 12

MAP_PROMPT = (
    "You extract facts. Question: {query}\n"
    "From the text chunk below, copy out ONLY facts that help answer the question.\n"
    "Rules: one fact per line; start each line with [{cid}]; keep each fact short.\n"
    "If nothing in this chunk helps answer, reply with exactly: NO RELEVANT INFO\n"
    "Chunk:\n{chunk}"
)
SCORE_PROMPT = (
    "Question: {query}\n"
    "Rate how relevant each extracted fact is to answering the question, 0-10 "
    "(0 = useless, 10 = directly answers part of it).\n"
    "Reply with one line per fact, format: <number> <score> and nothing else.\n"
    "Facts:\n{facts}"
)
COLLAPSE_PROMPT = (
    "Combine these extracted facts into a short deduplicated bullet list.\n"
    "Keep every [Cxxxx] tag attached to its fact. Drop exact duplicates.\n"
    "Question context: {query}\nFacts:\n{facts}"
)
FINAL_PROMPT = (
    "Answer the question using ONLY the facts below. "
    "Every claim in your answer must cite its chunk like [C0007]. "
    "If the facts do not contain the answer, say what is missing.\n"
    "Question: {query}\nFacts:\n{facts}"
)


def est_tokens(s):
    return len(s) // 4 + 1


def chat(model, messages, max_tokens=512, timeout=CALL_TIMEOUT):
    t = time.time()
    r = requests.post(
        f"{ROUTER}/v1/chat/completions",
        json={"model": model, "messages": messages, "max_tokens": max_tokens},
        timeout=timeout,
    )
    r.raise_for_status()
    d = r.json()
    return d["choices"][0]["message"]["content"].strip(), round(time.time() - t, 1)


def split_sentences(text):
    parts = re.split(r"([.!?;\n。！？；])", text)
    sents, buf = [], ""
    for i in range(0, len(parts) - 1, 2):
        s = (parts[i] + parts[i + 1]).strip()
        if s:
            if len(s) > 2000:  # pathological long line: hard split
                sents.extend(s[j:j + 2000] for j in range(0, len(s), 2000))
            else:
                sents.append(s)
    if len(parts) % 2 == 1 and parts[-1].strip():
        sents.append(parts[-1].strip())
    return [s for s in sents if s]


def chunk_text(text, source, chunk_tokens=CHUNK_TOKENS,
               overlap_tokens=CHUNK_OVERLAP_TOKENS, start_id=0):
    """Sentence-aware chunks with token budget + overlap. Returns chunk dicts."""
    sents = split_sentences(text)
    chunks, cur, cur_tok, cid = [], [], 0, start_id
    offset = 0
    for s in sents:
        st = est_tokens(s)
        if cur and cur_tok + st > chunk_tokens:
            body = " ".join(cur)
            chunks.append({"id": f"C{cid:04d}", "source": source,
                           "start": offset, "end": offset + len(body),
                           "text": body})
            cid += 1
            offset += len(body) + 1
            # overlap: carry trailing sentences worth ~overlap_tokens
            ov, ov_tok = [], 0
            for ps in reversed(cur):
                pt = est_tokens(ps)
                if ov_tok + pt > overlap_tokens:
                    break
                ov.insert(0, ps)
                ov_tok += pt
            cur, cur_tok = ov, ov_tok
        cur.append(s)
        cur_tok += st
    if cur:
        body = " ".join(cur)
        chunks.append({"id": f"C{cid:04d}", "source": source,
                       "start": offset, "end": offset + len(body), "text": body})
    return chunks


def query_terms(query):
    return [w.lower() for w in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-./]{2,}", query)]


def rank_chunks(chunks, query):
    """Query-aware ordering: keyword-overlap score, most relevant maps first."""
    terms = query_terms(query)
    scored = []
    for c in chunks:
        low = c["text"].lower()
        score = sum(low.count(t) for t in terms)
        scored.append((score, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored]


def map_extract(chunk, query):
    prompt = MAP_PROMPT.format(query=query, cid=chunk["id"], chunk=chunk["text"])
    try:
        out, dt = chat(MAP_MODEL, [{"role": "user", "content": prompt}],
                       max_tokens=512)
    except Exception as e:
        return {"chunk": chunk, "ok": False, "error": f"{type(e).__name__}: {e}"}
    if "NO RELEVANT INFO" in out.upper():
        return {"chunk": chunk, "ok": True, "empty": True, "secs": dt}
    facts = [l.strip() for l in out.splitlines()
             if l.strip() and not l.strip().upper().startswith("NO RELEVANT")]
    return {"chunk": chunk, "ok": True, "facts": facts, "secs": dt}


def score_facts(facts, query):
    """Batched LLM relevance scoring (ExtAgents-style). Falls back to keyword order."""
    if not facts:
        return []
    terms = query_terms(query)
    scored = []
    for i in range(0, len(facts), SCORE_BATCH):
        batch = facts[i:i + SCORE_BATCH]
        listed = "\n".join(f"{n + 1}. {f}" for n, f in enumerate(batch))
        try:
            out, _ = chat(MAP_MODEL, [{"role": "user",
                                       "content": SCORE_PROMPT.format(query=query, facts=listed)}],
                           max_tokens=256)
            for line in out.splitlines():
                m = re.match(r"\s*(\d+)\s+(\d+)", line)
                if m:
                    n, s = int(m.group(1)) - 1, int(m.group(2))
                    if 0 <= n < len(batch):
                        scored.append((min(max(s, 0), 10), batch[n]))
            got = {f for _, f in scored[-len(batch):]}
            for f in batch:  # unscored -> keyword fallback
                if f not in got:
                    low = f.lower()
                    scored.append((sum(low.count(t) for t in terms), f))
        except Exception:
            for f in batch:
                low = f.lower()
                scored.append((sum(low.count(t) for t in terms), f))
    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored]


def collapse_once(facts, query):
    """One tree-collapse level: group facts into budget-fitting batches, collapse in parallel."""
    batches, cur, cur_tok = [], [], 0
    for f in facts:
        ft = est_tokens(f)
        if cur and cur_tok + ft > REDUCE_BUDGET:
            batches.append(cur)
            cur, cur_tok = [], 0
        cur.append(f)
        cur_tok += ft
    if cur:
        batches.append(cur)
    if len(batches) <= 1:
        return facts

    def _collapse(batch):
        try:
            out, _ = chat(MAP_MODEL, [{"role": "user", "content": COLLAPSE_PROMPT.format(
                query=query, facts="\n".join(batch))}], max_tokens=1024)
            return [l.strip() for l in out.splitlines()
                    if l.strip() and re.search(r"\[C\d+\]", l)]
        except Exception as e:
            return batch  # fail-open: keep uncollapsed rather than lose facts

    out = []
    with ThreadPoolExecutor(max_workers=MAP_WORKERS) as ex:
        futs = [ex.submit(_collapse, b) for b in batches]
        for f in futs:
            out.extend(f.result())
    return out


def tree_reduce(facts, query, max_levels=6):
    level = 0
    while est_tokens("\n".join(facts)) > REDUCE_BUDGET and level < max_levels:
        facts = collapse_once(facts, query)
        level += 1
    return facts


def answer_question(query, corpus_text, force_composite=False):
    """Main entry. Returns dict(answer, provenance, stats, lane)."""
    t0 = time.time()
    total = est_tokens(corpus_text) + est_tokens(query)

    # Direct lane: prompt fits a native 1M model -> one call, no map-reduce tax.
    if not force_composite and total <= DIRECT_BUDGET:
        try:
            out, dt = chat(DIRECT_MODEL,
                           [{"role": "user",
                             "content": f"Answer the question using the corpus below. "
                                        f"Cite sources.\nQuestion: {query}\nCorpus:\n{corpus_text}"}],
                           max_tokens=2048, timeout=600)
            return {"answer": out, "lane": f"direct:{DIRECT_MODEL}",
                    "provenance": [{"chunk": "FULL", "source": "direct-pass"}],
                    "stats": {"secs": round(time.time() - t0, 1),
                              "est_tokens": total, "chunks": 1}}
        except Exception as e:
            sys.stderr.write(f"direct lane failed ({e}); falling back to composite\n")

    # Composite lane
    chunks = chunk_text(corpus_text, source="corpus")
    ordered = rank_chunks(chunks, query)
    stats = {"est_tokens": total, "chunks": len(chunks)}

    t_map = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=MAP_WORKERS) as ex:
        futs = {ex.submit(map_extract, c, query): c for c in ordered}
        for fut in as_completed(futs):
            results.append(fut.result())
    stats["map_secs"] = round(time.time() - t_map, 1)

    ok = [r for r in results if r.get("ok") and not r.get("empty")]
    failed = [r for r in results if not r.get("ok")]
    empty = [r for r in results if r.get("ok") and r.get("empty")]
    stats.update({"mapped_ok": len(ok), "mapped_empty": len(empty),
                  "mapped_failed": len(failed)})
    if failed:
        sys.stderr.write(f"map failures: {len(failed)} e.g. {failed[0].get('error')}\n")
    facts = [f for r in ok for f in r.get("facts", [])]
    if not facts:
        return {"answer": "NO RELEVANT INFO in corpus.", "lane": "composite",
                "provenance": [], "stats": stats}

    t_red = time.time()
    facts = score_facts(facts, query)
    stats["facts_scored"] = len(facts)
    facts = tree_reduce(facts, query)
    stats["facts_after_collapse"] = len(facts)
    final, _ = chat(MAP_MODEL, [{"role": "user", "content": FINAL_PROMPT.format(
        query=query, facts="\n".join(facts))}], max_tokens=1024)
    stats["reduce_secs"] = round(time.time() - t_red, 1)

    prov = {}
    for r in ok:
        c = r["chunk"]
        prov[c["id"]] = {"source": c["source"], "start": c["start"], "end": c["end"]}
    stats["secs"] = round(time.time() - t0, 1)
    return {"answer": final, "lane": "composite:chunk-map-tree-reduce",
            "provenance": prov, "stats": stats}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="auto1m virtual 1M-context route")
    ap.add_argument("--query", required=True)
    ap.add_argument("--corpus", required=True, help="text file (or dir of .md files)")
    ap.add_argument("--force-composite", action="store_true")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    import os
    if os.path.isdir(a.corpus):
        parts = []
        for root, _, files in os.walk(a.corpus):
            for fn in sorted(files):
                if fn.endswith(".md"):
                    p = os.path.join(root, fn)
                    parts.append(f"\n\n===== FILE: {p} =====\n" +
                                 open(p, encoding="utf-8", errors="replace").read())
        corpus = "".join(parts)
    else:
        corpus = open(a.corpus, encoding="utf-8", errors="replace").read()

    res = answer_question(a.query, corpus, force_composite=a.force_composite)
    report = {"query": a.query, "answer": res["answer"], "lane": res["lane"],
              "stats": res["stats"],
              "provenance": res["provenance"] if isinstance(res["provenance"], dict)
              else res["provenance"]}
    text = json.dumps(report, indent=2)
    if a.out:
        open(a.out, "w").write(text)
        print(f"wrote {a.out}")
    print(text[:6000])
