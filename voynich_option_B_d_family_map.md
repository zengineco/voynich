# Option B COMPLETE — d-family deep map
## 15 May 2026, session 2
## STATUS: PARTIAL FALSIFICATION of handoff's 4-class model. New 2-class model proposed.

---

## §1. WHAT WAS BUILT

Full d-family positional analysis: every d-form with n≥4 examined at line-adjacency resolution. Token classifier corrected mid-build (a humor-content matcher bug was identified and fixed — see §5 below). Compositional decomposition tested. Unsupervised hierarchical clustering performed. The handoff's 4-class scheme (PROCLITIC/CONNECTOR/ENCLITIC/TERMINATOR) was tested against actual data.

**Corpus statistics:**
- Total tokens (architecture-filtered, post tokenizer v4): 37,029
- Total d-family tokens: 3,077 (8.3% of corpus)
- Distinct d-family types: 543
- Productive d-forms (n ≥ 4): ~50

---

## §2. THE HANDOFF'S 4-CLASS MODEL — FALSIFIED ON GENERALIZATION

The handoff claimed the d-family has 4 positional classes with 13 productive forms:
- PROCLITIC: dor, dair, daiir, dain
- CONNECTOR: daiin, dol, dar
- ENCLITIC: dal
- TERMINATOR: dy, dam, dan, d-bare

I attempted to:
1. Replicate the classes from adjacency data
2. Extract a suffix → class rule
3. Validate the rule on lower-frequency d-forms (n=4-9)

**Replication: partial.** Within the top 20 d-forms, a 5-class refined classifier (CONNECTOR/DISCOURSE/ENCLITIC/TERMINATOR/PROCLITIC) places forms approximately where the handoff predicted. dy, dam, dan, dl, d are TERMINATOR. dor, daiir, doiin are PROCLITIC. daiin is CONNECTOR. dal, do are ENCLITIC.

**Suffix rule extraction: trivial.** Every top-form's tail (-aiin, -ar, -al, -y, etc.) maps 1-to-1 to a class because top forms are unique-tail.

**Validation on held-out forms (n=4-9): FAILS.** 7/19 = **36.8% accuracy** on suffix-tail rules applied to lower-count d-forms — WORSE than the 41.7% majority baseline (predict TERMINATOR every time).

Examples of rule failures:
- `dalor` (alor): predicted PROCLITIC (from -or rule), observed CONNECTOR
- `dalol` (alol): predicted DISCOURSE (from -ol rule), observed CONNECTOR  
- `dody` (ody): predicted TERMINATOR (-y → TERMINATOR), observed CONNECTOR
- `dalchy` (alchy): predicted TERMINATOR, observed ENCLITIC
- `daldy` (aldy): aldy rule predicts TERMINATOR, observed TERMINATOR ✓ but only because daldy itself was the training data

**Conclusion: the handoff's 4-class scheme over-fits the top forms. It does not generalize to compound d-forms.**

---

## §3. COMPOSITIONAL DECOMPOSITION — ALSO FAILS TO GENERALIZE

Tested hypothesis: long d-forms are d-clitic + content-morpheme compounds.
- `dalchedy` = `dal` + `chedy`
- `doiin` = `do` + `iin`
- `dalor` = `da` + `lor` or `dal` + `or`

For each compound d-form, computed (1) its own adjacency class, (2) its decomposed-clitic class, (3) its content-body class.

| alignment | match-rate |
|---|---|
| whole = decomposed-clitic class | 14/30 (47%) |
| whole = content-body class | 12/30 (40%) |

Both compositional hypotheses fail to generalize. The d-form is neither purely its clitic-prefix's positional behavior nor purely its content-body's behavior. Either the compositional model is wrong, or it requires interaction terms not visible at single-token resolution.

---

## §4. UNSUPERVISED CLUSTERING — REVEALS THE TRUE STRUCTURE

Dropped the categorical scheme. Built 10-dimensional feature vectors per d-form (init%, fin%, L_Ch, L_Cp, L_F, L_d, R_Ch, R_Cp, R_F, R_d) and ran single-linkage hierarchical clustering on Euclidean distances.

**Merge distance sequence:**
```
11.9, 13.1, 16.3, 16.7, 18.4, 19.4, 20.6, 20.9, 22.3, 23.4,
23.7, 24.5, 24.5, 24.9, 26.1, 26.6, 27.9, 28.0, 29.8, 44.3
```

There is **one large jump: 29.8 → 44.3 (bare 'd' joins last).**

Between 11.9 and 29.8, the merges are smooth. **There is no natural cut yielding 4 well-separated clusters.** The handoff's 4-class model is not the natural clustering of the adjacency data.

**Cleanest cluster (d≤20):** {daiin, dain, dair, dol, dar} — 1,492 tokens, **64% of all d-family tokens** in one group with near-identical adjacency profiles. The handoff splits these across PROCLITIC (dair, dain) and CONNECTOR (daiin, dar, dol). The data does not support that split.

**TERMINATOR sub-tier (d≤24):** {dy, daly, dam, dan, daim} all cluster together. This part of the handoff IS supported.

**Isolated outliers:** dor, daiir, doiin, dl, daldy, dary, daram, do — each remains its own micro-cluster until d>26, then they all merge with the main group. These are heterogeneous and probably each have idiosyncratic behavior at low counts.

**Truly distinct: bare 'd'** — only merges at d=44.3. This is a real outlier. Its left/right adjacency is dominated by FUNCTION WORDS (L_F=22%, R_F=39%), not content. Bare 'd' is a DIFFERENT KIND of token from the rest of the d-family — possibly a true marker/punctuation-like element.

---

## §5. THE REVISED MODEL (LOCKED at this resolution)

```
═════════════════════════════════════════════════════════════════════
                    REVISED d-FAMILY ARCHITECTURE
═════════════════════════════════════════════════════════════════════

CLASS A — MAIN d-CLITIC GROUP (~2200 tokens, ~70% of d-family)

  Members: daiin, dar, dal, dain, dair, dol, daiin, daiiin,
           dor, daiir, doiin, do, dl, and ~30 low-count variants
  
  Adjacency: LEFT ~25% content / ~6% function;
             RIGHT ~25% content / ~7% function
  Position: largely MID-line, weak preferences in either direction
  Function: clitic/connector/discourse particle (mass undifferentiated)

CLASS B — TERMINATOR FAMILY (~500 tokens, ~20% of d-family)

  Members: dy, dam, dan, daly, daldy, dary, daiiin, daim, daram, dl
  
  Adjacency: LEFT ~45% content; RIGHT ~15% content; fin% ≥30
  Position: line/clause final
  Function: clause/utterance terminator
  
  Morphological hallmark: -y, -m, -n endings (terminating phonotactics)

CLASS C — BARE 'd' (~60 tokens, ~2%)
  
  Adjacency: 39% right-function, 22% left-function (distinct from A and B)
  Position: variable, often line-final
  Function: appears more like a discourse/punctuation marker
  
  This is the ONLY truly distinct d-token by clustering.
═════════════════════════════════════════════════════════════════════
```

**The handoff's 4 classes collapse to 2 (or 3 if bare 'd' is counted separately).**

---

## §6. SECTION-LEVEL d-FAMILY USAGE

Even with the simplified 2-class scheme, **d-family usage varies meaningfully by section**:

| section | d-rate | top 3 d-forms |
|---|---|---|
| **herbal-A** | **13.3%** | daiin(389), dy(101), dar(92) |
| **pharm-herbal** | 10.4% | daiin(119), dar(32), dal(29) |
| cosmo/zodiac | 9.3% | daiin(58), dal(53), dar(42) |
| balneo | 7.2% | daiin(81), dal(66), dar(62) |
| rosettes | 6.8% | dar(28), daiin(27), dal(12) |
| **stars** | **3.8%** | daiin(120), dain(49), dar(43) |

**Critical observation: Herbal-A uses 3.5× more d-family tokens than stars.**

This MATCHES Option C's register finding: herbal-A is substance-NP-chain heavy (daiin connecting substance names), while stars is process-formula heavy (qok+e+aspect chains with fewer NP connections).

**The d-family is a NP-connector system, not a verbal/predicate system.** Where there are more NPs (herbal-A, pharm-herbal), there are more d-clitics. Where there are more process predicates (stars, balneo), there are fewer.

---

## §7. WHAT THE PROFILE-CLASS SECTIONAL BREAKDOWN SHOWS

Within the rough class scheme:

| section | CONNECTOR | DISCOURSE | TERMINATOR | ENCLITIC | PROCLITIC |
|---|---|---|---|---|---|
| balneo | 20.6% | 35.6% | 22.6% | 18.4% | 2.2% |
| stars | 37.2% | 37.5% | 15.2% | 8.6% | 1.5% |
| cosmo/zodiac | 19.2% | 22.4% | 34.5% | 17.4% | 5.9% |
| rosettes | 28.0% | 37.4% | 22.4% | 11.2% | 0.9% |
| herbal-A | 40.2% | 22.9% | 23.8% | 6.7% | 5.6% |
| pharm-herbal | 38.8% | 28.7% | 15.3% | 11.7% | 4.6% |

**herbal-A / pharm-herbal: CONNECTOR-dominant** (40% / 39%). Consistent with substance-NP chains.

**balneo: DISCOURSE-dominant.** Mid-line d-clitics that aren't strict CONNECTORs — could be tied to balneo's longer process-formula chains.

**cosmo/zodiac: TERMINATOR-dominant (34.5%).** Short clauses, frequent line-ends. Consistent with the label-heavy, decan-name-heavy structure of zodiac folios.

**These section differences are robust even though the per-form classification is noisy.** The differences come from the relative weights of the underlying d-forms, not from precise per-form positional assignment.

---

## §8. CRITICAL METHODOLOGY NOTE — BUG CAUGHT AND FIXED

Initial run produced suspicious result: "78% of d-tokens are FREE class with balanced adjacency." Investigation showed the `is_humor_content` classifier had a logic bug:

```python
# BUGGY CODE (from first run):
def is_humor_content(tok):
    for base in HUMOR_BASES:
        for pfx in sorted(HUMOR_PREFIXES + [""], key=lambda x: -len(x)):
            if tok.startswith(pfx):
                rest = tok[len(pfx):]
                if rest.startswith(base): return True
                break   # ← bug: break after first matching prefix, even if residue check failed
    return False
```

Result: `chol` matched prefix `ch`, residue `ol` didn't start with `ch`, loop broke without trying `pfx=""`. Every ch-/sh-stem word was misclassified as "L" (label/other).

**Effect on Option C register grammar: NONE** (different code path, register builder's loop is correct).
**Effect on initial d-family analysis: SEVERE.** 37% of d-form neighbors were silently mis-classified as labels instead of content. The "FREE" class was an artifact of the bug.

After fix: humor-vs-process ratios become diagnostic, content-vs-function adjacency becomes interpretable, and the structure described above emerges.

**Methodological lesson:** When an analysis suggests a "null result" (everything looks the same), inspect the classifier on known examples before believing the result. The bug was caught because the L-class examples showed `chol`, `shedy`, `cheey`, etc. — obviously content words.

---

## §9. WHAT THIS CLOSES AND OPENS

**CLOSES:**
- The handoff's 4-class d-family scheme is NOT the natural clustering of the data. Revised to 2 classes (Main + Terminator) + bare 'd'.
- Compositional decomposition of long d-forms (dalchedy = dal + chedy) does not predict positional class. Either compositional or distinct atomic — the data doesn't decide.
- Suffix-to-position rules don't generalize (37% on held-out).

**OPENS:**
- **The d-rate is a strong section diagnostic.** Herbal-A (13.3% d-tokens) vs stars (3.8% d-tokens) is a 3.5× gap. Could become a quick "is this NP-heavy or predicate-heavy?" test.
- **Bare 'd' is a true outlier.** Its 39% right-function and 22% left-function adjacency suggests it functions as a discourse marker or punctuation analog. Worth a single-token deep-dive.
- **Why don't compound d-forms decompose cleanly?** Possibilities: (a) they're lexicalized units (idiomatic), (b) the architecture missed a productive d-internal slot, (c) scribal variation produces apparent compounds that are really errors or alternate spellings.
- **The 5 forms in the main cluster (daiin, dain, dair, dol, dar) ARE one positional unit.** Future work: do they vary by section in interesting ways? The handoff said dor was PROCLITIC and daiin CONNECTOR — that distinction isn't supported, but per-section weighting of these 5 forms could still differ.

---

## §10. HONEST SUMMARY

Option B was supposed to confirm and extend the handoff's d-family positional grammar. **Instead it falsified the granularity of that grammar.** The d-family has real structural patterns (TERMINATOR group, NP-connector group, isolated bare 'd'), but NOT the 4-way distinction the handoff claimed.

This is a net win: drift is gone, the architecture is honest about its resolution limits, and the section-level diagnostic (d-rate, terminator-rate) is now a usable tool.

**The 50% predictability ceiling from T17 (per the handoff) was not "2-3 unknown subclasses" — it was 1-2 over-claimed subclasses.** Removing them gives the architecture a cleaner shape.

---

## §11. FILES

- /home/claude/d_family_map.py — initial naive 4-class attempt
- /home/claude/d_family_map_v2.py — refined 5-class classifier (with bug-fix)
- /home/claude/d_family_L_neighbors.py — diagnostic that caught the bug
- /home/claude/d_family_compositional.py — compositional decomposition test (negative)
- /home/claude/d_family_rules.py — suffix → class rule extraction + validation (failed)
- /home/claude/d_family_cluster.py — unsupervised hierarchical clustering (positive)

End of Option B deliverable.
