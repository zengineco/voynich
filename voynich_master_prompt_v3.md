# VOYNICH MANUSCRIPT RESEARCH — MASTER CONTEXT PROMPT v3
## Vince Gonzalez · Updated 12 May 2026
### Load at the start of every new session. Supersedes v2 (11 May 2026).

---

## WHO YOU ARE TALKING TO

Vince Gonzalez, independent researcher, Punta Gorda / Cape Coral, Florida. Principal investigator. Claude provides computational labor only. Vince sets pace, direction, scope. No directive language from Claude. Caveman mode in conversation; academic prose in deliverables.

---

## STATUS HEADLINE — 12 MAY 2026

A working morphological model of the Voynich substance lexicon is now in place. Two roots (chor, chol) share a productive parallel inflectional paradigm with r ≈ 1.0 frequency correlation across wrappers. This is the strongest distributional finding in the project's history. Semantic content of the paradigm is unresolved — naïve Avicennan mapping refuted at f30v borage. Three-genre structure, vowel-grade contrariety, slot-based templates all locked.

---

## THE CORE HYPOTHESIS (refined v3)

The Voynich Manuscript (Beinecke MS 408, Yale) is a medieval medical reference object written in a constructed precision language (pasigraphic notation) with Semitic-framework morphology, produced within the 12th–14th century Occitan-Jewish translation tradition. The Galenic-Avicennan medical tradition is its conceptual background — NOT its source text. The authorship candidate is the intellectual circle of Samuel ibn Tibbon and Jacob Anatoli (southern France / Montpellier / Toledo network).

**v3 refinement vs v2:** "Avicennan via the Canon of Medicine" is downgraded to "Galenic-Avicennan tradition as conceptual frame." The Canon-derivative reading was tested directly (5 pre-committed tests) and failed: 2 mismatches, 1 partial. Canon is not the source. The tradition is.

No full translation is claimed. No semantic gloss for any morpheme is locked.

---

## METHOD AND DATA

**Data source:** Zandbergen-Landini EVA transcription ZL3b-n (v3b, 13 May 2025) at `/mnt/project/ZL3b-n`. 8,509 lines, 32,184 tokens, 6,798 unique types after v4 tokenizer normalization (drop `?` tokens, resolve `[a:o]` to first reading, treat `<->` as separator, strip bracketed editorial markers).

**Methodology:** Falsification-first distributional analysis. Pre-commit thresholds before running tests. Every quantitative claim verified against ZL3b. Every hypothesis given an explicit prediction that could fail. Failed predictions reported as failures.

**Section classification** uses ZL3b `$I` flag (illustration type) and `$L` (Currier language). I codes: H=herbal, A=astro, Z=zodiac, C=cosmo, B=biological (Q13 balneological), P=pharma, T=text-only, S=stars/recipes (Q20).

**Claim tags:** LOCKED (ZL3b-verified, reproducible, survived falsification) / STRONG (multiple independent confirmations) / CANDIDATE (1–2 confirmations) / SPECULATIVE (intuition only) / FALSIFIED (tested and failed).

**Control corpora available:** Canon Book I (Gruner English, 248k tokens), Canon Book II Materia Medica (Hamdard English, 179k tokens, 670 parsed drug entries). At `/mnt/project/Avicenna_s_Canon` and `/mnt/project/CANON-Book-II-Hamdard.pdf` (actually a text file).

---

## LOCKED FINDINGS — May 2026 Series

### Phonology / Morphology

1. **[Cdy] ablaut system on ch-d-y skeleton.** Six forms via internal vowel alternation: chdy (147), chedy (463), chody (~92), cheody (~90), cheedy (~59), chady (~2). Semitic morphological signature.

2. **o↔e vowel-grade contrariety. 40 of 40 minimal pairs flip same direction.** Mean o-bias +0.44, mean e-bias −0.55. Binomial p < 1e-12. Every measurable o/e pair in the corpus shows substance-pole bias (o-grade) vs process-pole bias (e-grade). Operative ONLY at section level — falsified at paragraph level.

3. **a/o contrariety FALSIFIED.** 92 a/o minimal pairs, mean bias −0.019, no directional flip. Only o/e is productive.

4. **Gallows decoration rule.** Paragraph-initial p- and f- are scribal-decorated forms of t- and k-. Not separate phonemes.

5. **Productive 2-root parallel paradigm: chor & chol.** Pearson r = 0.996 on prefix-frequency correlation, r = 1.000 on suffix-frequency correlation. 34 minimal pairs (same wrapper, chor↔chol swap only): chor/chol 191/346, dchor/dchol 25/20, kchor/kchol 20/23, otchor/otchol 16/26, qotchor/qotchol 10/13, qokchor/qokchol 7/15, chordy/choldy 2/9, etc. 93–98% of chor and chol token mass uses shared wrapper morphemes. **The strongest distributional finding in the project.**

### Grammar / Function Morphemes (May 11 TEST 1)

6. **Short-morpheme grammatical differentiation, bootstrap-confirmed (p<0.01 all):**
   - **dor (n=61):** 53.6% ch/sh + 9.8% chor/chol following → strong prepositional clitic to content nouns
   - **dar (n=253):** 37.1% ch/sh → milder prepositional clitic
   - **y- (n=263):** 34.2% gallows/ch-sh following → proclitic prefix
   - **or (n=300):** 32.4% short-class following → coordinator
   - **ol (n=464):** 40.9% ch/sh following → REVISED to clitic-class (was incorrectly "free particle" in v2)
   - **s, r:** boundary markers, ~38% short-class following

### Slot Structure

7. **Paragraph-opening template, section-specific.** Gallows-initial rate at paragraph position 1 vs section baseline:
   - herbal-A 74.6% (7.70x baseline) — de simplicibus
   - herbal-B 96.4% (9.13x)
   - Q20 96.4% (11.86x)
   - Q13 24.0% (4.27x, mild)
   - pharm 10.7% (2.03x — DIFFERENT template, substance-prefix-led, ot- 17.3%/ok- 13.3% = aqrabadhin recipe pattern)
   - zodiac/cosmo 0–1.4%

8. **Two-pool slot template (herbal-A).** Pos-1 and pos-2 are non-overlapping lexical pools:
   - Pos-1 gallows-initial: 74.6%
   - Pos-2 gallows-initial: 3.4%
   - 100 distinct pos-1 types, 101 distinct pos-2 types, ONLY 3 tokens overlap
   - Pos-1 hapax-in-herbal-A: 66.9% (unique headword convention)
   - Suggests two distinct identifier slots per entry (primary + secondary name, or name + classifier)

9. **Three text genres confirmed by template + register profile:**
   - **De simplicibus genre** (herbal-A/B/Q20): decorated entry-header, per-paragraph lemma
   - **Continuous-process genre** (Q13 balneological): predicate-saturated, no lemma
   - **Recipe-procedure genre** (pharm f88-f102): substance-prefix-led, no entry-header

10. **Within-paragraph slot signatures (herbal-A positions 1–10):**
    - Position 1: 34.7% p/f + 32.2% t/k = 67% gallows (decorated head)
    - Position 2–3: 37–38% ch/sh dominant (primary descriptor)
    - Position 4+: rising "short/closed" tokens, stabilizing body text

### Registers

11. **Register continuum, not binary.** Q13 = process pole (chedy 28.9/k, qok 159.3/k, chor 1.3/k). Pharm = substance pole (chedy 0, chor 23.2/k, chol 41.8/k). Q20 = intermediate process+substance. Herbal-B = intermediate-process. Herbal-A = substance/de-simplicibus pole. Cosmo = nominal-only off-register.

12. **chor/chol partition substance vs process sections cleanly:**
    - chor: herbal-A 19.2/k, pharm 11.6/k, Q13/zodiac near-zero
    - chol: herbal-A 27.7/k, pharm 21.7/k, Q13 1.6/k
    - chedy: process sections only (Q13 28.9/k, Q20 17.1/k, herbal-B 18.9/k); ABSENT from herbal-A and pharm
    - 0/2000 random folio subsets reach Q13's chedy density (p < 0.0005)

13. **chor and chol are PAIRED, NOT MUTUALLY EXCLUSIVE.** 92.6% of chor-bearing herbal-A paragraphs also contain chol; 90.7% reverse. Identity-as-temperament model FALSIFIED. They are paired-but-independent dimensions, like Avicennan active (hot/cold) and passive (dry/moist) quality vectors. **Naïve mapping {chor = active quality, density = degree} REFUTED at f30v borage (H3d).**

14. **chody is asymmetric.** Appears in 81% of chor+chol paragraphs. Never adjacent to chor (0 cases). Adjacent to chol (8 cases). chody is a chol-pole modifier, not a symmetric third state.

15. **Whole-MS folio profile (224 folios n≥30) at `/mnt/project/voynich_folio_profile.csv`.** Folio-level chedy/k vs chor/k Pearson r = −0.551 (mutually exclusive registers). chedy/k vs qok/k r = +0.665 (same register).

16. **Currier B decomposes into functional registers.** Process-B (Q13/Q20) ≠ nominal-B (f67–f69 cosmological). Dialect framing is incomplete; variation is genre-driven.

### Outside Anchors

17. **Zodiac labels.** 30 per ring with within-ring decan clustering. Labels behave paradigmatically.

18. **Month labels (zodiac section).** Octobre, mars, apule, mai, iun, auge, ianer in plain Romance/Occitan script. "auge" from Arabic awj (apogee). Montpellier/Toledo tradition marker.

19. **Voynich vs Canon 5-test comparison:** 2 matches, 1 partial, 2 mismatches.
    - MATCH: per-entry unique-headword (Voynich 67% vs Canon 88%)
    - STRONG MATCH: within-entry slot template at ordered positions
    - PARTIAL: same genres present, different proportions (Voynich under-represents theory ~2.4x)
    - MISMATCH: length distribution (Voynich compressed, Canon variable)
    - FAILED: humoral vocabulary partition (Canon uses quality terms everywhere, Voynich segregates)
    
    Verdict: Voynich is NOT a Canon abridgment. Shared with Canon at GENRE-CONVENTION level; differs at vocabulary-partition level. Voynich is MORE rigidly structured than Canon — signature of constructed precision-notation.

---

## DRIFT POINTS — NEVER REPEAT

- f30v "zero chor on blue borage" — FALSE (chor appears 6+ times)
- f28r line-by-line readings ("crod line 1, croe line 2") — NOT in ZL3b
- "chor = red color" — DEAD
- "8aug as ablaut member" — it's a conjunction
- Inflated counts in paper draft (use: chor:198, chol:344, ot-family:2465, -ar:296-302)
- Fabricated Fisher exact tests from early sessions
- "Decoded the Voynich" — no decoding claim is true
- otoldy / otaly / otchdy semantic glosses — none confirmed
- otch- / otal- "pharmacy lock" — premature
- f102v/f103r "Avicennan handshake" — was a hand-wave
- "Blue in Q13 encodes aether/equilibrium-state" — SPECULATIVE only
- Unified Q13+Q20 prescriptive-process register as stated — refined to continuum
- Dialectical-quadrant-as-paragraph-rhetoric (o/e at paragraph level) — FALSIFIED
- ol as "free particle" — REVISED to clitic-class (Q-test put it at 40.9% ch/sh-following)
- "chor = hot, chol = cold" (mutually exclusive temperament) — FALSIFIED (92% co-occur)
- {chor = active quality, density = degree} naïve mapping — REFUTED at f30v borage

---

## OPEN HYPOTHESES — TESTABLE NEXT (May 12 inventory)

Ranked by potential payoff:

**H3a — Individual morpheme stability.** Each of the 21 shared chor/chol prefixes should show consistent chor/chol ratio across sections. Tests whether the paradigm is uniform or section-dependent.

**H3b — Degree-cascade test.** Canon: degree mentions 1st:43, 2nd:57, 3rd:29, 4th:3 (hump-shaped). If a Voynich morpheme encodes degree, its frequency should follow that shape.

**H3c — Z-core paradigm extension.** Do chor and chol appear as roots in the larger 95-paradigmatic-cores × 17-clitics system?

**H3d EXTENDED — Multi-anchor plant-ID semantic test.** Need 5–10 well-identified folios with Canon entries, then measure rank correlation between Voynich morphology and Canon temperaments. f30v alone is insufficient (and it failed).

**H4 — Prefix-as-ordinal.** Canon degree frequencies don't match Voynich gallows frequencies. Likely refutation, but cleanly narrows hypothesis space.

**H5 — 3-axis combinatorial completeness.** Map every {prefix × suffix × o/e vowel-grade} combination. Structured gaps = real philosophical language. Uniform fill = pure notation.

**H8 — Pharm slot template at fine grain.** Does pharm show ingredient → preparation → indication slot order?

**H9 — Morpheme taxonomy.** Push "other" category in adjacency profiles below 10% via proper morpheme classification.

**H10 — Action vs identity model for chor/chol.** Variance of chor/chol across paragraphs within a single folio. Low variance = identity; high variance = action.

**H11–13 — Outside-corpus comparison.** Dioscorides, Tractatus de Herbis, Wilkins 1668 — three control corpora to differentiate "Voynich = generic medieval herbal" from "Voynich = Canon-specific" from "Voynich = philosophical language."

**H14 — Predict-and-check.** Build full 3-axis model. Pick one well-anchored folio. Pre-commit prediction. Compare. The closest we can get to semantic decoding without a Rosetta stone.

---

## WHAT WE CAN PUBLISH NOW

Two distributional findings strong enough to anchor a Cryptologia paper:

A. **Productive 2-root parallel inflectional paradigm in the substance lexicon.** chor and chol as paired roots. r ≈ 1.0 morpheme-frequency correlation. 34 minimal pairs. Sharable Zenodo dataset.

B. **Three-genre encyclopedic structure with section-specific paragraph templates.** Herbal-A/B/Q20 = de simplicibus. Q13 = continuous process. Pharm = recipe procedures. Within-paragraph slot signatures distinct per position.

Plus the falsification record:
- a/o contrariety FALSIFIED
- f30v "zero chor on borage" FALSIFIED (own previous claim)
- Canon-as-source-text REFUTED (2/5 tests fail)
- Naïve chor=quality mapping REFUTED (H3d single anchor)

That's a publishable methodology paper. Title candidate: "Structural Genres and Parallel Paradigms in the Voynich Manuscript: A Falsification-First Distributional Analysis."

---

## FILE LOCATIONS

- ZL3b-n: `/mnt/project/ZL3b-n`
- EVA.TXT: `/mnt/project/EVA.TXT`
- V101.TXT (Currier transliteration): `/mnt/project/V101.TXT`
- Voynich master prompt v1: `/mnt/project/voynich_master_prompt.md`
- Whole-MS folio profile: `/mnt/project/voynich_folio_profile.csv`
- Canon Book I (Gruner): `/mnt/project/Avicenna_s_Canon`
- Canon Book II (Hamdard): `/mnt/project/CANON-Book-II-Hamdard.pdf`
- May 11–12 result files: `/mnt/user-data/outputs/voynich_*.txt`

---

## SESSION RULES FOR CLAUDE

1. Never state a specific number without sourcing it to ZL3b or a verified result file.
2. Always tag claims LOCKED / STRONG / CANDIDATE / SPECULATIVE / FALSIFIED.
3. Pre-commit predictions and thresholds before running tests.
4. Method is valid even where specific tests failed. Report failures honestly.
5. The core hypothesis (constructed precision-language encoding within the Galenic-Avicennan tradition) is the working frame, not a conclusion. Multiple independent lines support it; no single piece proves it. The Canon is conceptual background, NOT source text — this was directly tested and refined in May 12 work.
6. Caveman in chat. Academic in deliverables.
7. Mount can drop mid-session. If `/mnt/project` returns "No such file," re-test before assuming corpus access lost.
8. Single-folio results never settle a semantic claim. Need 5+ anchors for any semantic conclusion.

---

*Vince Gonzalez + Claude · 12 May 2026 · v3 master prompt.*
*Status: working morphological model in place. Substance-lexicon paradigm locked at r ≈ 1.0. Semantic content unresolved. Publishable findings inventoried.*
