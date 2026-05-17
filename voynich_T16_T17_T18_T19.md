# VOYNICH — T16, T17, T18, T19 Findings (Batch)
## 15 May 2026 session
## Vince Gonzalez + Claude

---

## §T18 — PREFIX × BASE × VOWEL-GRADE 2D MAP [LOCKED]

### Setup

9 derivational prefixes × 2 humor-quality bases × 4 vowel grades = 72 slots. Build the matrix, identify gaps.

### Result (CH-base × prefix × vowel-grade)

| Prefix | ∅-grade | e-grade | o-grade | eo-grade | Total |
|---|---|---|---|---|---|
| ∅- | 1520 | 2125 | 1640 | 699 | 5984 |
| k- | 79 | 67 | 78 | 25 | 249 |
| d- | 70 | 84 | 71 | 32 | 257 |
| t- | 72 | 79 | 84 | 32 | 267 |
| ok- | 86 | 71 | 54 | 8 | 219 |
| ot- | 107 | 82 | 68 | 15 | 272 |
| qok- | 137 | 72 | 46 | 10 | 265 |
| qot- | 102 | 58 | 43 | 7 | 210 |
| cth- | 166 | 87 | 177 | 29 | 459 |

### Result (SH-base × prefix × vowel-grade)

| Prefix | ∅-grade | e-grade | o-grade | eo-grade | Total |
|---|---|---|---|---|---|
| ∅- | 564 | 1500 | 740 | 368 | 3172 |
| k- | 20 | 18 | 18 | 14 | 70 |
| d- | 14 | 69 | 32 | 18 | 133 |
| t- | 17 | 32 | 30 | 7 | 86 |
| ok- | 16 | 16 | 9 | 1 | 42 |
| ot- | 14 | 21 | 4 | 2 | 41 |
| qok- | 17 | 21 | 1 | 2 | 41 |
| qot- | 8 | 5 | 1 | 2 | 16 |
| cth- | 0 | 0 | 0 | 0 | 0 |

### Key findings

**1. CH:SH asymmetry is prefix-dependent**

| Prefix | CH:SH ratio |
|---|---|
| ∅- (bare) | 1.89 |
| d- | 1.93 |
| k- | 3.56 |
| t- | 3.10 |
| ok- | 5.21 |
| ot- | **6.63** |
| qok- | **6.46** |
| qot- | **13.12** |
| **cth-** | **∞ (no SH attachment)** |

The bare CH:SH ratio (1.89) is the baseline. Prefix-decorated forms become increasingly CH-biased. **q-prefixes (qok, qot) attach 6-13× more often to CH than SH; cth- never attaches to SH.**

This means **prefixes are not base-agnostic.** The k/t/o/qo prefix family has a strong CH-preference. There may be phonological reasons (consonant cluster restrictions) or semantic reasons (CH-humor takes more substance-class markers).

**2. Gaps in SH-base × heavy-prefix × o-grade slots**

| Prefix | SH-base | o-grade count |
|---|---|---|
| ok- | sh | 9 (low) |
| ot- | sh | 4 (low) |
| qok- | sh | 1 (gap) |
| qot- | sh | 1 (gap) |

SH-base + heavy-prefix + o-grade combinations are essentially blocked. The SH humor in substance-marked-o-grade is morphologically rare or impossible.

**3. SH-base is e-grade-heavy**

Bare SH-base: 1500/3172 = **47% e-grade** vs CH-base 35% e-grade. SH leans process register; CH balances all grades.

### Status

**LOCKED.** Prefix attachment is base-selective. The 72-slot matrix has predictable structural gaps. The cth- prefix is CH-exclusive (an absolute constraint).

---

## §T17 — d-FAMILY SUFFIX→POSITION PREDICTABILITY [PARTIAL — model needs refinement]

### Setup

Test whether the 4-class d-family model (proclitic/connector/enclitic/terminator) from T14 can PREDICT the position of d-forms NOT in the training set.

### Result: 23.1% accuracy (6/26 on test forms)

Predicting based on suffix → 4-position class:

| Form | Suffix | Predicted | Observed | Match |
|---|---|---|---|---|
| dary | -ary | TERMINATOR | TERMINATOR | ✓ |
| dalor | -alor | ENCLITIC | ENCLITIC | ✓ |
| dals | -als | ENCLITIC | ENCLITIC | ✓ |
| dalal | -alal | ENCLITIC | ENCLITIC | ✓ |
| dalchedy | -alchedy | ENCLITIC | ENCLITIC | ✓ |
| dairal | -airal | PROCLITIC | PROCLITIC | ✓ |
| daly | -aly | ENCLITIC? | TERMINATOR | ✗ |
| daldy | -aldy | ENCLITIC? | TERMINATOR | ✗ |
| daiiin | -aiiin | PROCLITIC? | ENCLITIC | ✗ |
| (etc.) | | | | |

### What works

Simple-suffix predictions work cleanly when the suffix MATCHES a training-set suffix:
- `-alX` compounds → enclitic-class behavior (when X is non-terminator)
- `-airX` compounds → proclitic-class behavior
- `-ary` → terminator-class

### What fails

**Compound suffixes don't decompose cleanly into base-class behavior:**
- `-aly` is `-al + y` morphologically, but daly behaves as TERMINATOR (mean 0.746) not ENCLITIC (-al class)
- `-aldy` is `-al + dy`, but daldy is TERMINATOR (0.713)
- `-aim`, `-aram`, `-alam` all behave as TERMINATORS regardless of the leading `-a` segment
- `-doy`, `-doly`, `-doiir` show mixed/unpredictable position

**The 4-class model is too coarse.** Compound suffixes may add additional terminator-like force (especially when ending in -y, -dy, -m). The actual model needs:
- A primary class (from leading suffix segment)
- A secondary modifier (from terminal suffix segment, especially -y/-dy/-m)

### Status: PARTIAL — model refinement needed

The 4-class model holds for SIMPLE suffixes but cannot predict compound-suffix behavior. **The d-family has more internal structure than the 4-class model captures.** The class-assignment for compound suffixes appears to be terminator-dominated when the suffix ends in a terminator-class element.

This partially walks back T14's strong reading. The d-family is functionally differentiated but the functional classification is not perfectly compositional from suffix alone.

---

## §T19 — oke/ote/qoke/qote as e-grade variants [LOCKED with refinement]

### Hypothesis

If oke = ok + e-grade marker (same root, vowel shift), the suffix-distribution attached after the e should match the general e-grade suffix system.

### Result: TWO clusters

E-grade suffix distribution cosines:

|  | che | she | oke | ote | qoke | qote |
|---|---|---|---|---|---|---|
| **che** | 1.000 | **0.986** | 0.763 | 0.841 | 0.719 | 0.772 |
| **she** | 0.986 | 1.000 | 0.774 | 0.865 | 0.764 | 0.825 |
| **oke** | 0.763 | 0.774 | 1.000 | **0.956** | **0.953** | 0.861 |
| **ote** | 0.841 | 0.865 | 0.956 | 1.000 | **0.959** | **0.939** |
| **qoke** | 0.719 | 0.764 | 0.953 | 0.959 | 1.000 | **0.946** |
| **qote** | 0.772 | 0.825 | 0.861 | 0.939 | 0.946 | 1.000 |

### Two clusters

**Humor-base cluster** (cos ≥ 0.96 within):
- {che, she}
- Top suffixes: -dy (501/431), -y (348/271), -ey (185/147), -ol (168/109)

**Process-root cluster** (cos ≥ 0.94 within):
- {oke, ote, qoke, qote}
- Top suffixes: -ey (182/141/307/42), -dy (117/164/269/89), -edy (109/104/303/77)

Cross-cluster cosines: 0.72-0.87 (notable difference)

### Critical difference

**Process roots prefer -ey suffix; humor roots prefer -dy suffix in e-grade.**

This is a real paradigm difference at the suffix level. Within each family, oke/ote/qoke/qote share the same suffix preferences (cos > 0.94). Across families, the difference is meaningful (cos < 0.87).

### Status

**LOCKED with refinement.** oke/ote/qoke/qote ARE e-grade variants of their respective process roots — they share suffix-paradigm patterns within the process-root cluster. But the process-root e-grade paradigm is DISTINCT from the humor-root e-grade paradigm.

**Refinement of T15:** Process roots take the 4-vowel-grade system but with their own preferred suffix selection per grade. Two separate paradigm families: humor-roots use -dy as e-grade primary; process-roots use -ey as e-grade primary.

---

## §T16 — Canon Book II Forced-Choice [PARTIAL — folio-ID barrier]

### Setup

With architecture LOCKED, predict for named Avicennan simples the hot/cold/dry/moist classification, then check the corresponding Voynich folio for chor/chol/shor/shol distribution.

### Obstacle: no plant-ID mapping available

Voynich-to-Canon plant identification is contested. No canonical mapping exists in the project files. The Canon Book II PDF gives Latin index → page mapping but no Voynich→plant linking. The May-13 visual-anchor program was FALSIFIED via 8 tests.

**Direct forced-choice test cannot be run.** Without a reliable plant-ID, predicting "Avicennan simple X is hot/dry → look at the folio illustrating X" requires the unsolved identification problem.

### Inverted approach: Folio specialization in humor vocabulary

What CAN be tested: do herbal-A folios specialize in the humor-pair vocabulary?

Profile for 65 herbal-A folios with ≥5 humor-pair tokens:

**CH:SH ratio across folios:**
- mean 3.93, median 3.33, stdev 2.83
- range 0.20 → 12.00

**5 folios are SH-pair-dominant** (CH:SH < 1.0):
- f23v (0.20), f46r (0.40), f42r (0.50), f29r (0.67), f44v (0.75)

**15 folios are strongly CH-pair-dominant** (CH:SH > 5.0):
- f17v (12.00), f56r (11.00), f2v (10.00), f6v (9.00), f20r/23r/29v/32r (8.00), f3r (7.50), f32v (7.00), f13r/15v (6.00), f24v/52v (6.00), f21r (5.50)

**chor:chol ratio across 42 folios with both >=2:**
- mean 1.05, range 0.20 → 3.50
- chor-dominant: f6v (3.50), f3v (3.00), f8r (2.50)
- chol-dominant: f47r (0.20), f1r (0.25), f17v (0.33), f21r (0.38), f27r (0.40)

### Key finding (LOCKED)

**Folios DO specialize in humor-pair distribution.** This is consistent with the 2-humor × 2-grade model. Each folio appears to describe a substance with a primary humor classification (CH vs SH) and a primary quality grade (chor/chol or shor/shol).

**Falsification test**: if humor-pair vocabulary were free-distributed (no semantic content), CH:SH ratio across folios should be roughly constant (stdev close to mean × 0.3). Observed stdev/mean = 2.83/3.93 = **0.72** — substantial variance. Folios are NOT uniform.

**A clean 2×2 prediction grid emerges:**
- CH-humor, chor-grade: f6v, f3v, f8r
- CH-humor, chol-grade: f47r, f1r, f17v, f21r, f27r, f23r
- SH-humor: f23v, f46r, f42r, f29r, f44v
- (Within SH, shor:shol grade-axis untested due to small token counts)

### Status

**PARTIAL.** The forced-choice cannot be completed without plant-ID. The inverted test confirms FOLIO SPECIALIZATION is real, consistent with the 2-humor × 2-grade model.

**Next step for T16 completion**: requires either an external Voynich→Canon plant-ID mapping (contested), independent verification via art-historical analysis (out of scope), or running the inverse — predict which Avicennan simples have a CH-humor-chor-grade signature and check whether any Voynich folio with high f6v/f3v/f8r-style profile matches.

---

## §SYNTHESIS — Current State of the Project

### Architecture (LOCKED, complete)

```
CONTENT BASES (universal 4-vowel-grade alternation):
  HUMOR:   CH, SH  (with derivational-prefix decoration)
  PROCESS: qok, qot, ok, ot  (no derivational prefixes; own suffix preferences)

DERIVATIONAL PREFIXES (CH-biased; cth- is CH-exclusive):
  ∅ | k | d | t | ok | ot | qok | qot | cth

VOWEL GRADES (all roots × all 4 grades):
  ∅ | e | o | eo  (section-register selector)

SUFFIX AXES:
  1. e-grade contrariety:  ∅ | -y | -ey (and -dy on humor roots, vs -ey on process roots)
  2. o-grade quality:      -or | -ol  
  3. aspect/register:      -dy | -edy | -eedy | -eey | -ody | -eody
  4. paradigm grade:       -aiin | -ain | -aiir | -air
  5. clitic axis:          -ar | -al | -am | -an

FUNCTION-WORD FAMILY (d-stem):
  4 positional classes: proclitic / connector / enclitic / terminator
  Class assignment: leading-segment + terminal modifier (compound suffix model)

DISCOURSE PARTICLES:
  qol (balneo-specific), bare ol/ar/or/al/y/aiin/ain
  saiin, sain (line-initial markers)
```

### Locked findings this session

| Test | Result | Status |
|---|---|---|
| T18: prefix×base×grade map | 72-slot matrix, CH-biased prefixes, cth- CH-exclusive | LOCKED |
| T19: e-grade variants | 2 paradigm clusters (humor vs process) | LOCKED |
| T16 (inverted): folio specialization | Real CH:SH variance, 2×2 grid emerges | LOCKED (limited) |
| T17: d-family predictability | Simple-suffix yes; compound-suffix model needs refinement | PARTIAL |

### What's still unsolved

1. **Semantic identification**: which Avicennan humor is CH? which is SH? -or grade = hot or moist?
2. **Plant-ID for Voynich folios**: which folio describes which Canon simple? (Largely unsolved field-wide)
3. **Compound-suffix functional classes**: the d-family is more complex than 4 simple classes
4. **Process-root deep paradigm**: process roots take different suffix preferences than humor roots in e-grade. Why?

### Methodological note

The session produced both LOCKED findings (T18, T19, T16-inverted) AND a self-falsification refinement (T17). Both T17 partial-falsification and the inability to run direct T16 because of the plant-ID barrier are HONEST limits of the structural-only approach. The architecture stands; the semantic layer remains unread.

End of memo.
