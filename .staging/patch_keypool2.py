#!/usr/bin/env python3
"""patch_keypool2.py -- add free_only model-aware key eligibility to herd-keypool.py.

Written against the LIVE 709-line herd-keypool.py (2026-09-20, real schema:
Pool.__init__ takes cfg with upstream/health-mapping/fail_status/cooldowns,
pick(self) takes no model arg, keys loop assumes plain string names).

Usage: patch_keypool2.py <target-file>
Surgical exact-match edits (each asserts exactly one match):
  1. KeyState gains free_only slot + ctor arg (default False).
  2. Pool.__init__ keys loop accepts {name:, free_only:} dict entries.
  3. Module helpers _is_free_model + _extract_model.
  4. _eligible(now, model_id) + pick(model_id=None) gate free_only keys;
     recovery sweep applies the same gate.
  5. _proxy extracts model from JSON body, passes to pick().
  6. /status exposes free_only (names only, no values).
  7. pick() audit records the model for forensics.
  8. selftest gains cases 6-8 (free_only selection/exclusion, dict config).
"""
import sys
from pathlib import Path

path = Path(sys.argv[1])
src = path.read_text()
n = 0


def rep(old, new):
    global n, src
    assert src.count(old) == 1, f"match count {src.count(old)} for: {old[:70]!r}"
    src = src.replace(old, new)
    n += 1


# 1. KeyState slot + ctor
rep('''    __slots__ = ("name", "value", "fp", "state", "latency_ms",
                 "last_error", "down_until", "last_probe_ok")

    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.fp = fingerprint(value)''',
    '''    __slots__ = ("name", "value", "fp", "state", "latency_ms",
                 "last_error", "down_until", "last_probe_ok", "free_only")

    def __init__(self, name, value, free_only=False):
        self.name = name
        self.value = value
        self.free_only = bool(free_only)
        self.fp = fingerprint(value)''')

# 2. keys loop accepts dict entries
rep('''        self.keys = []
        for kname in cfg.get("keys") or []:
            val = secrets.get(kname)
            if val:
                self.keys.append(KeyState(kname, val))
            else:
                log(f"pool {name}: key {kname} not in secrets — skipped (names only)")''',
    '''        self.keys = []
        for kspec in cfg.get("keys") or []:
            # entry: plain name, or {name: ..., free_only: true}.
            # A free_only key may serve ONLY free-model requests.
            if isinstance(kspec, dict):
                kname, free_only = kspec.get("name"), bool(kspec.get("free_only"))
            else:
                kname, free_only = kspec, False
            val = secrets.get(kname) if isinstance(kname, str) else None
            if val:
                self.keys.append(KeyState(kname, val, free_only))
            else:
                log(f"pool {name}: key {kname} not in secrets — skipped (names only)")''')

# 3. module helpers (after fingerprint)
rep('''def fingerprint(value):
    """Non-reversible label for a key value. Safe to show in /status."""
    return hashlib.sha256(value.encode()).hexdigest()[:12]''',
    '''def fingerprint(value):
    """Non-reversible label for a key value. Safe to show in /status."""
    return hashlib.sha256(value.encode()).hexdigest()[:12]


def _is_free_model(model_id):
    """True only for OpenRouter free-model IDs. This gates a free-ONLY key
    (what the key may serve), never what any key must serve."""
    return bool(model_id) and (
        model_id == "openrouter/free" or model_id.endswith(":free"))


def _extract_model(raw):
    """Best-effort model ID from a proxied JSON body. None when absent."""
    try:
        if raw:
            doc = json.loads(raw)
            m = doc.get("model") if isinstance(doc, dict) else None
            if isinstance(m, str) and m:
                return m
    except Exception:
        pass
    return None''')

# 4a. _eligible gates free_only
rep('''    def _eligible(self, now):
        """Keys usable right now (not in cooldown)."""
        out = []
        for ks in self.keys:
            if ks.state == "down" and now < ks.down_until:
                continue
            out.append(ks)
        return out''',
    '''    def _eligible(self, now, model_id=None):
        """Keys usable right now (not in cooldown). A free_only key is
        eligible only for free-model requests -- never for paid traffic."""
        out = []
        for ks in self.keys:
            if ks.state == "down" and now < ks.down_until:
                continue
            if ks.free_only and not _is_free_model(model_id):
                continue
            out.append(ks)
        return out''')

# 4b. pick takes model_id
rep('''    def pick(self):
        """First-valid-wins. Returns a KeyState or None (all down)."""
        now = time.time()
        cands = self._order(self._eligible(now))''',
    '''    def pick(self, model_id=None):
        """First-valid-wins. Returns a KeyState or None (all down).
        model_id gates free_only keys: they serve only free models."""
        now = time.time()
        cands = self._order(self._eligible(now, model_id))''')

# 4c. recovery sweep applies the same gate
rep('''        for ks in self._order(self.keys):
            if ks.state == "down" and time.time() < ks.down_until:
                continue
            if self._probe_and_update(ks):''',
    '''        for ks in self._order(self.keys):
            if ks.state == "down" and time.time() < ks.down_until:
                continue
            if ks.free_only and not _is_free_model(model_id):
                continue
            if self._probe_and_update(ks):''')

# 5. _proxy extracts model, passes to pick
rep('''        raw = _read_body(self)

        tried = []
        while True:
            ks = pool.pick()''',
    '''        raw = _read_body(self)
        model_id = _extract_model(raw)

        tried = []
        while True:
            ks = pool.pick(model_id)''')

# 6. /status exposes free_only
rep('''                    keys.append({
                        "name": ks.name,
                        "fingerprint": ks.fp,''',
    '''                    keys.append({
                        "name": ks.name,
                        "free_only": ks.free_only,
                        "fingerprint": ks.fp,''')

# 7. pick() audit records the model (both select sites)
old_sel = '''                if self._probe_and_update(ks):
                    self._audit("select", ks, {"latency_ms": ks.latency_ms})
                    return ks'''
assert src.count(old_sel) == 1
src = src.replace(old_sel, '''                if self._probe_and_update(ks):
                    self._audit("select", ks, {"latency_ms": ks.latency_ms,
                                              "model": model_id})
                    return ks''')
n += 1
old_sel2 = '''            self._audit("select", ks, {"latency_ms": ks.latency_ms})
            return ks'''
assert src.count(old_sel2) == 1
src = src.replace(old_sel2, '''            self._audit("select", ks, {"latency_ms": ks.latency_ms,
                                              "model": model_id})
            return ks''')
n += 1

# 8. selftest: free_only cases (append before srv.shutdown())
rep('''    srv.shutdown()
    print("keypool selftest: " + ("ALL PASS" if not fails else f"{fails} FAILURES"))''',
    '''    # case 6: free_only key IS selected for a :free model
    pool = mkpool([("FREENAME", "KF"), ("PAIDNAME", "KP")],
                  {"FREENAME": (True, 5.0, 200), "PAIDNAME": (True, 6.0, 200)})
    pool.keys[0].free_only = True
    got = pool.pick("x/y:free")
    if got is None or got.name != "FREENAME":
        print(f"FAIL case6: free model -> {got and got.name}"); fails += 1

    # case 7: free_only key is NEVER selected for a paid model;
    # only-free_only pool + paid model -> None (no silent fallback)
    got = pool.pick("x/y")
    if got is None or got.name != "PAIDNAME":
        print(f"FAIL case7a: paid model -> {got and got.name}"); fails += 1
    pool2 = mkpool([("FREENAME", "KF")], {"FREENAME": (True, 5.0, 200)})
    pool2.keys[0].free_only = True
    got = pool2.pick("x/y")
    if got is not None:
        print(f"FAIL case7b: paid model on free-only pool -> {got.name}"); fails += 1
    got = pool2.pick("openrouter/free")
    if got is None or got.name != "FREENAME":
        print(f"FAIL case7c: openrouter/free -> {got and got.name}"); fails += 1

    # case 8: dict key entries via real Pool.__init__ + _is_free_model/_extract_model
    cfg = {"upstream": f"http://127.0.0.1:{port}",
           "health": {"method": "GET", "path": "/auth", "ok": [200]},
           "keys": [{"name": "D1", "free_only": True}, "D2"]}
    pool3 = Pool("cfgtest", cfg, {"D1": "VD1", "D2": "VD2"})
    if len(pool3.keys) != 2 or not pool3.keys[0].free_only or pool3.keys[1].free_only:
        print("FAIL case8a: dict key entries"); fails += 1
    if not (_is_free_model("a/b:free") and _is_free_model("openrouter/free")
            and not _is_free_model("a/b") and not _is_free_model(None)
            and not _is_free_model("")):
        print("FAIL case8b: _is_free_model"); fails += 1
    if _extract_model(b'{"model":"a/b:free"}') != "a/b:free" or \\
       _extract_model(b"") is not None or _extract_model(b"not json") is not None:
        print("FAIL case8c: _extract_model"); fails += 1
    # legacy pick() with no args still works
    got = pool.pick()
    if got is None:
        print("FAIL case8d: legacy pick()"); fails += 1

    srv.shutdown()
    print("keypool selftest: " + ("ALL PASS" if not fails else f"{fails} FAILURES"))''')

path.write_text(src)
print(f"patched {path} ({n} edits)")
