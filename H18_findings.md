# H18 — Classifier audit (bug sweep across session helpers)

## Result: All session classifiers PASS at 100% on known-truth test suite. Zero break-after-first-match antipatterns found. Zero cross-classifier overlap on real corpus. Session code is clean.

---

## Method

The Option B `is_humor_content` bug (break-after-first-prefix-match) silently misclassified ch-/sh-stem words as labels, producing a spurious "78% FREE class" result. H18 sweeps the session's classifier helpers for:

1. **Direct bug pattern match** (static scan: nested loop + break in classifier-style code)
2. **Test-suite correctness** (60-token suite with known-truth tags for each classifier dimension)
3. **Cross-classifier consistency** (any token matching multiple mutually-exclusive categories?)
4. **Corpus sweep** (apply each classifier to full ZL3b, inspect outputs for unexpected matches/misses)

---

## Finding 1 — Session classifiers all pass at 100%

Tested against a 60-token test suite covering humor content, [Cdy] ablaut, d-family, process roots, bare-suffix forms, gallows-prefixed forms, and edge cases (cth-, cph-, cfh-, lk-, eo-grade):

| Classifier | TP | FP | TN | FN | Accuracy |
|---|---|---|---|---|---|
| is_gallows_init | 8 | 0 | 52 | 0 | **100%** |
| is_chsh_init | 15 | 0 | 45 | 0 | **100%** |
| is_qok | 7 | 0 | 53 | 0 | **100%** |
| is_d_family | 11 | 0 | 49 | 0 | **100%** |
| is_short_function | 10 | 0 | 50 | 0 | **100%** |
| is_ot_ok | 7 | 0 | 53 | 0 | **100%** |

All six session classifiers are bug-free at the resolution our session tests them at.

---

## Finding 2 — No break-after-first-match antipattern in session code

Static scan of every `.py` in the session directory for nested-loop + break patterns:

| File | Site | Status |
|---|---|---|
| h17_part4.py:30 | `if n >= 20: break` (output cap, not classifier) | safe |
| h17_part4.py:42 | `if n >= 20: break` (output cap, not classifier) | safe |
| h18_audit.py:177 | deliberately-reproduced bug for testing | testing-only |

**No classifier in the session uses `break` at all.** Every session classifier is structured as a single `return` or a flat `or`-chain of `startswith()` calls. Architecturally immune to the Option B bug.

---

## Finding 3 — Zero cross-classifier overlap on real corpus

Cross-checked every token in ZL3b against the six classifiers. The `neighbor_category()` function applies them in priority order: d → d-family → ch/sh → qok/qot → ot/ok → gallows → function → short-other → content-other. If any token matched multiple categories simultaneously, ordering would matter and could introduce silent miscounts.

**Result: zero tokens in the entire corpus match more than one of {d, chsh, qok, otok, gallows, fn} simultaneously.** 

This is partially by design — the prefix structures are mutually exclusive: a token starting with `d` doesn't start with `ch`/`sh`/`q`/`o`/`k`/`t`; a token starting with `q` doesn't start with `o`/`t`/`ch`/`sh`; a token in the short-function set is single-token-matched (not prefix-matched). The architecture is clean enough that classification order does not affect any real token.

---

## Finding 4 — Canonical `is_humor_content_v3` defined (for future use)

Although the session never used the buggy is_humor_content (Option B's helper that wasn't ported into this session), I wrote a canonical version aligned with the LOCKED architecture and verified it. v3 passes 42/42 humor positives and 59/59 humor negatives on the test suite.

Definition:
```
humor_content(t) ⇔
  ∃ prefix ∈ {∅,k,d,t,ok,ot,qok,qot,cth} and base ∈ {ch,sh,cph,cfh}:
    t = prefix + base + grade + tail
    where grade ∈ {∅, e, o, eo, ee, a}
    and tail ∈ {or, ol, ordy, oldy, ory, oly, dy, y, ey, edy, eedy, eey, ody, eody}
  OR
    prefix = cth and tail ∈ {or, ol, ordy, oldy, edy, ey, eey, eedy, ody, y, dy}
```

When applied to full ZL3b: catches 250 unique types / 6,005 tokens (~16% of corpus). The LOCKED architecture is conservative — additional content prefixes (l-, op-, ckh-) and additional suffix axes (paradigm grade -aiin/-ain, clitic -ar/-al/-am) would expand coverage but those go beyond the strict humor-content classifier.

This `is_humor_content_v3` is now the canonical reference. If we ever need a humor-content classifier in future sessions, use this — not Option B's buggy original.

---

## Verdict

**Session code passes the audit cleanly.** No bugs, no antipattern instances, no cross-classifier conflicts. The H15/H16/H17 results are not contaminated by classifier errors.

The Option B bug was real but lived in a code path that was discarded that session. No future session needs to fear it as long as classifier helpers stay structured as flat `or`-chains of `startswith()` calls without nested-loop break.

**Lesson preserved (already in master prompt §22 LOCKED methodology note):** when an analysis produces a null/uniform result, audit the classifier on known-positive examples BEFORE believing the null. The h15_part4 diagnostic that caught the Option B bug remains the canonical pattern.
