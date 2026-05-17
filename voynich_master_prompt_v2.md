# VOYNICH MANUSCRIPT RESEARCH — MASTER CONTEXT PROMPT v2
## Vince Gonzalez · Updated 11 May 2026
### Load this at the start of every new session. Supersedes voynich_master_prompt.md (May 2026 v1).

---

## WHO YOU ARE TALKING TO

Vince Gonzalez, independent researcher, Punta Gorda / Cape Coral, Florida. Principal investigator. Claude provides computational labor only. Vince sets pace, direction, scope. No directive language from Claude.

---

## THE CORE HYPOTHESIS (unchanged since v1)

The Voynich Manuscript (Beinecke MS 408, Yale) is a complete medieval medical reference system written in a constructed precision language with Semitic-framework morphology, produced within the 12th–14th century Occitan-Jewish translation tradition. The authorship candidate is the intellectual circle of Samuel ibn Tibbon and Jacob Anatoli (southern France / Montpellier / Toledo network). The structural reference frame is Avicennan Galenic medicine via the Canon of Medicine.

No full translation is claimed. No semantic gloss for any morpheme is locked. All findings are behavioral / distributional classifications.

---

## METHOD AND DATA

**Data source:** Zandbergen-Landini EVA transcription ZL3b-n (v3b, 13 May 2025) at `/mnt/project/ZL3b-n`. 8,509 lines, 32,184 tokens, 6,798 unique types after v4 tokenizer filtering (drop `?` tokens, resolve `[a:o]` to first reading, treat `<->` as separator).

**Methodology:** Falsification-first distributional analysis. Every quantitative claim verified against ZL3b before stated. Every hypothesis given an explicit prediction that could fail. Failed predictions reported as failures.

**Section classification** uses ZL3b `$I` flag (illustration type) and `$L` (Currier language). I codes: H=herbal, A=astro, Z=zodiac, C=cosmo, B=biological (Q13 balneological), P=pharma, T=text-only, S=stars/recipes (Q20).

**Claim tagging:** LOCKED (ZL3b-verified, reproducible) / STRONG (multiple independent confirmations) / CANDIDATE (1–2 confirmations) / SPECULATIVE (intuition only) / FALSIFIED (tested and failed).

---

## LOCKED FINDINGS (ZL3b-verified, reproducible)

### Morphology

1. **[Cdy] ablaut system on ch-d-y skeleton.** Six distinct forms via internal vowel alternation: chdy (147), chedy (463), chody (~92), cheody (~90), cheedy (~59), chady (~2). Internal vowel alternation as meaning-carrying mechanism is diagnostic Semitic morphological signature.

2. **Productive o↔e vowel-grade contrariety.** 9/9 minimal pairs flip same direction. o-grade leans substance register, e-grade leans process register. Mean o-bias +0.44, mean e-bias −0.55. Pairs: qokeody/qokeedy, shody/shedy, chody/chedy, chodaiin/chedaiin, sheody/sheedy, cheody/cheedy, oteody/oteedy, choky/cheky, cheos/chees.

3. **a/o contrariety FALSIFIED.** 92 a/o minimal pairs, mean a-bias −0.019, no directional flip. The o↔e rule is the only operative vowel-grade contrariety.

4. **Gallows decoration rule.** Paragraph-initial p- and f- are scribal-decorated forms of t- and k-. NOT separate phonemes. This is now known to be one piece of a wider entry-header convention (see finding 7).

5. **Color/quality word frequencies** (corrected from v1 paper draft):
   - chor: 198 occ. chol: 344 occ. chor-family-total ≈459.
   - ot- family: 2,465 occ.
   - chody: 91 occ.
   - otchor: 15 occ. otchol: 30 occ.
   - -ar morpheme: 296–302 occ depending on tokenizer. Rank ~9.
   - daiin highest-frequency word: 670–721 occ depending on tokenizer.

### Grammar and Adjacency

6. **Short-morpheme grammatical differentiation** (May 11 TEST 1, 32k-token corpus):
   - **dor (n=61):** 37.7% ch/sh + 9.8% chor/chol following → STRONG prepositional clitic to content nouns.
   - **dar (n=253):** 24.5% ch/sh following → milder prepositional clitic.
   - **y- (n=263 as free token):** 22% gallows + 22% ch/sh following → STRONG proclitic prefix. Same morpheme that surfaces word-initial as ydain/ychor/ytain.
   - **or (n=300):** 30% short/closed following → coordinator signature.
   - **ol (n=464):** even distribution → true free particle.
   - **s, r:** 35–38% short-class following → boundary markers / phrase terminators.
   - Conclusion: short morphemes are NOT a single class. dar/dor look Semitic-clitic; or coordinates; y- prefixes; ol is free; s/r mark boundaries.

### Section Structure and Registers

7. **Paragraph-opening template (May 11 TEST 3, full corpus).** Gallows-initial rate at paragraph position 1 vs section baseline word-initial gallows rate:

   | Section   | #paras | para-open gallows | baseline | ratio |
   |-----------|--------|-------------------|----------|-------|
   | herbal-A  | 118    | 74.6%             | 9.7%     | 7.70x |
   | herbal-B  | 28     | 96.4%             | 10.6%    | 9.13x |
   | Q20       | 28     | 96.4%             | 8.1%     | 11.86x|
   | Q13       | 96     | 24.0%             | 5.6%     | 4.27x |
   | pharm     | 150    | 10.7%             | 5.3%     | 2.03x |
   | zodiac    | 22     | 0.0%              | 3.9%     | 0.00x |
   | cosmo     | 71     | 1.4%              | 5.6%     | 0.25x |

   The decorated entry-header convention is section-specific. Herbal-A/B/Q20 use it heavily. Pharm does NOT use it. Q13 uses it weakly. This is a real scribal-tradition signature distinguishing genre types.

8. **Three encyclopedic-text genres confirmed** by template + register profile:
   - **De simplicibus genre** (herbal-A/B, Q20): decorated entry-header, per-paragraph lemma structure. Single-substance entries.
   - **Continuous-process genre** (Q13 balneological): low decoration, predicate-saturated, no per-paragraph lemma. Galenic humoral-process prose.
   - **Recipe-procedure genre** (pharmacy f88-f102): flat headings, substance-rich, low predicate. Aqrabadhin tradition (Canon Book V) of compound recipes.

9. **Register continuum, not binary** (May 11 TEST 4 refinement). "Process register" lies on a continuum:
   - Q13 = process pole (chedy 28.9/k, qok 159.3/k, chor 1.3/k)
   - Herbal-B = intermediate process (chedy 18.9/k, -dy 26.8%)
   - Q20 = intermediate process+substance (chedy 17.1/k, ot- 72.6/k)
   - Pharm = substance pole (chedy 0, chor 23.2/k, chol 41.8/k)
   - Herbal-A = substance/de-simplicibus pole (chedy 0.0, chor 46.1/k, chol 54.9/k)
   - Cosmo = nominal-only, off-register (chedy 0, qok 6.3/k)

10. **Whole-MS folio profile** (224 folios n≥30) at `/mnt/project/voynich_folio_profile.csv`. Q13 balneo 20/20 process-register; Q20 stars 19/23; herbal-A 17/110; pharm-herbal 1/32; cosmo/zodiac 1/26. Folio-level chedy/k vs chor/k Pearson r = −0.551 (mutually exclusive registers). chedy/k vs qok/k r = +0.665 (same register). Process vs substance is real corpus-wide split.

11. **f67-f69 cosmological control test passed.** Cosmological folios show suffix ~0%, chedy ~0, qok sparse, nominal-prefix 25-40%. Falsifies the null hypothesis that process register is corpus-wide; it is section-specific.

12. **Currier A/B decomposes into functional registers, not just dialects.** Currier B has at least two sub-registers (process-B = Q13/Q20; nominal-B = f67-f69 cosmo). Currier-Bennett dialect framing is incomplete; the variation is at least partly genre-driven.

13. **Zodiac labels.** 30 labels per zodiac ring with within-ring decan clustering. Distinct from continuous-text grammar. Labels behave as paradigmatic.

14. **Month labels (zodiac section).** Octobre, mars, apule, mai, iun, auge, ianer in plain Romance/Occitan script. "auge" from Arabic awj (apogee). Confirms Arabic astronomical vocabulary in Romance vernacular — Montpellier/Toledo tradition marker.

15. **f87 two-paragraph structure.** Block 1 (description) + Block 2 (application) visible in ZL3b as two `@P0` paragraph starts. Real.

---

## DRIFT POINTS — NEVER REPEAT

- f30v "zero chor on blue borage" — FALSE. chor appears 6+ times on borage folio (control test FAILED).
- f28r line-by-line readings ("crod line 1, croe line 2") — NOT in ZL3b. Were generated from unreliable image reading.
- "chor = red color" — DEAD. chor is a quality marker, not a color name.
- "8aug as ablaut member" — it's a conjunction.
- Inflated counts in paper draft: chor:254, chol:520, -ar:1.82x ratio. CORRECT: chor:198, chol:344, -ar ratio unverified.
- Fabricated Fisher exact test in early sessions — never re-cite.
- "Decoded the Voynich" — no decoding claim is true. No semantic gloss is locked.
- otoldy / otaly / otchdy semantic glosses — none confirmed.
- otch-/otal- "pharmacy lock" — premature; pharm is its own genre but no morpheme is glossed.
- f102v/f103r "Avicennan handshake" — was a hand-wave, not a finding.
- "Blue in Q13 encodes aether/equilibrium-state" — SPECULATIVE only.
- Unified Q13+Q20 prescriptive-process register as stated — refined; they are related but not identical (continuum).
- Dialectical-quadrant-as-paragraph-rhetoric (o/e contrariety at paragraph level) — FALSIFIED.

---

## OPEN HYPOTHESES (CANDIDATE — testable next session)

1. **dor vs dar functional distinction.** Both are clitics; dor connects to content nouns more tightly. Hypothesis: dor = with/from substance (instrumental/ablative); dar = more general adposition. Test: profile dor vs dar by which specific stem-classes follow, controlling for section.

2. **y- as definite article / topic marker / negation.** Strong proclitic, but function not yet discriminated. Test: minimal-pair contexts where same stem appears with and without y-, examine surrounding clause structure.

3. **Q20 as a second de-simplicibus genre.** Decorated paragraph headers at 96.4%. Hypothesis: Q20 paragraphs are per-star entries with the same lemma-template as herbal-A/B but applied to celestial bodies, not plants.

4. **Pharm as Canon Book V aqrabadhin.** Recipe genre confirmed structurally. Hypothesis: pharm paragraphs encode compound-medicine recipes. Test: paragraph-internal positional template (do pharm paragraphs show recipe-procedure slot order: ingredients → preparation → indication?).

5. **f57v 4×16 symbol matrix as decoder key.** Untested. Speculative. Position 8 varies p↔f (gallows), position 15 varies l/c. If those are parameter slots of a transformation table, this could be the constructed-language design specification.

6. **Ibn Tibbon poael / -ar parallel.** Mentioned in Freudenthal (2016). Real paper, claim not verified against actual text. Pull Freudenthal source and check before citing.

---

## FILE LOCATIONS

- ZL3b-n: `/mnt/project/ZL3b-n`
- EVA.TXT (parallel transcription): `/mnt/project/EVA.TXT`
- V101.TXT (Currier transliteration): `/mnt/project/V101.TXT`
- Voynich master prompt v1: `/mnt/project/voynich_master_prompt.md`
- Whole-MS folio profile: `/mnt/project/voynich_folio_profile.csv`
- May 11 followup results: `/mnt/project/voynich_may11_followup_results.txt`
- Paper draft (errors uncorrected): `/mnt/project/voynich_paper.docx`
- Avicenna Canon (English): `/mnt/project/Avicenna_s_Canon` and `/mnt/project/CANON-Book-II-Hamdard.pdf`

---

## SESSION RULES FOR CLAUDE

1. Never state a specific number without sourcing it to ZL3b or a named verification file. If asked for a count, run it or flag it unverified.
2. Always tag claims LOCKED / STRONG / CANDIDATE / SPECULATIVE / FALSIFIED.
3. Method is valid even where specific tests failed. Report failures honestly as science results.
4. The core hypothesis (Occitan-Jewish constructed precision-language encoding of Avicennan medical material) is the working frame, not a conclusion. Independent lines of evidence support it; no single piece proves it.
5. Caveman mode in conversation. Academic prose in deliverables.
6. Mount can drop mid-session. If `/mnt/project` returns "No such file," re-test before assuming corpus access lost; recover via project_knowledge_search if necessary.

---

*Vince Gonzalez + Claude · 11 May 2026 · v2 master prompt.*
