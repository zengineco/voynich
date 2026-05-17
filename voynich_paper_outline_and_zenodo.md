# VOYNICH PAPER — OUTLINE AND ZENODO STRATEGY
## Vince Gonzalez · 11 May 2026

---

## PAPER OUTLINE — "Structural Genres in the Voynich Manuscript: Three Encyclopedic Text Types Identified by Distributional Morphology"

**Working title alternative:** "The Voynich Manuscript as a Three-Genre Avicennan Reference Compendium: Evidence from Paragraph-Opening Templates and Vowel-Grade Contrariety"

### Target venue
Cryptologia (primary) — accepts methodological work without semantic-decoding claims. Secondary: Journal of the Royal Asiatic Society (for the Avicennan / ibn Tibbon historical framing). Tertiary: PalaeoBiblos or Digital Philology for the computational-philology angle.

### Abstract (target 250 words)
State what is shown distributionally without claiming a translation. Three genres identified by independent statistical signatures. Productive Semitic-style morphology (vowel-grade contrariety, prepositional clitics). Section-specific scribal entry-header convention. No semantic decoding claimed.

### Section structure

**1. Introduction (1500 words)**
- The state of Voynich research as of 2026: failed cipher attacks, failed natural-language candidates, accumulating evidence for non-random internal structure.
- The constructed-precision-language hypothesis: not new, but underdetermined. What would distinguish a constructed precision-language from natural language or random output?
- This paper's contribution: distributional evidence for three distinct text genres within MS 408, each with its own scribal and grammatical signature. No translation; instead, the genre and grammatical-class structure that any future decoding effort must respect.

**2. Data and Method (1200 words)**
- ZL3b-n transcription (Zandbergen-Landini 2025). 32,184 tokens, 6,798 types after v4 tokenizer normalization.
- Section assignment via ZL3b illustration flags. Five primary sections: herbal-A (1215 lines), herbal-B (338), Q13 biological (860), Q20 stars (1164), pharm (242), plus cosmo, zodiac, other.
- Falsification-first methodology. Every claim has explicit prediction; failed predictions reported.

**3. Vowel-Grade Contrariety: o↔e (1800 words)**
- The [Cdy] ablaut system: ch-d-y skeleton generates six forms by internal vowel alternation.
- Productive o↔e rule across 9 minimal pairs, mean o-bias +0.44, e-bias −0.55. All 9 flip same direction.
- o-grade leans substance-register vocabulary; e-grade leans process-register vocabulary.
- Falsification: a↔o tested as parallel rule. FAILED — 92 pairs, mean bias −0.019, no directional flip.
- Falsification: o↔e operates at paragraph level (dialectical-rhetoric reading). FAILED — Q13 paragraphs run 60-100:1 favoring e-grade; the rule partitions vocabulary at section level, not within paragraph.
- Conclusion: One operative vowel-grade contrariety, partitioning a substance-pole vocabulary from a process-pole vocabulary. Internal-vowel-alternation morphology is diagnostic Semitic morphological pattern (cf. Arabic ablaut, Hebrew binyanim).

**4. The Three-Genre Structure (2500 words)**
- *Paragraph-opening template analysis.* Gallows-initial rate at paragraph position 1 vs section baseline:
  - Herbal-A: 74.6% vs 9.7% baseline (7.70x ratio)
  - Herbal-B: 96.4% vs 10.6% baseline (9.13x ratio)
  - Q20: 96.4% vs 8.1% baseline (11.86x ratio)
  - Q13: 24.0% vs 5.6% baseline (4.27x ratio)
  - Pharm: 10.7% vs 5.3% baseline (2.03x ratio)
  - Zodiac/cosmo: 0–1.4%, below baseline
- *Register profile comparison* (chedy/k, qok-/k, chor/k, suffix-edy %).
- *Three genres:*
  - Genre I — *de simplicibus* (herbal-A, herbal-B, Q20). Per-entry decorated lemma head, substance-rich morphology. Single-entity entries.
  - Genre II — continuous-process (Q13 balneological). Predicate-saturated, low decoration, no per-paragraph lemma. Galenic humoral-process prose.
  - Genre III — recipe-procedure (pharmacy f88–f102). Flat headings, substance-rich, low predicate. Aqrabadhin tradition.
- *Continuum reading.* The genres are poles on a process/substance continuum. Q20 and herbal-B sit at intermediate positions.
- *Whole-MS folio profile* (224 folios, n≥30) confirms registers cluster by section. Folio-level chedy/k vs chor/k Pearson r = −0.551 (mutually exclusive). chedy/k vs qok/k r = +0.665 (co-occurring).

**5. Grammatical Differentiation of Short Morphemes (1800 words)**
- Adjacency profiling of dar, dor, ar, or, ol, y-, s, r.
- dor (n=61): 37.7% ch/sh + 9.8% chor/chol following → prepositional clitic to content nouns.
- dar (n=253): 24.5% ch/sh following → milder prepositional clitic.
- y- (n=263): 22% gallows + 22% ch/sh following → proclitic prefix; same morpheme as word-initial y- in ydain/ychor.
- or (n=300): 30% short/closed following → coordinator.
- ol (n=464): even distribution → free particle.
- s, r: ~38% short following → phrase-boundary markers.
- Implication: The Voynich short-morpheme inventory is grammatically differentiated. dar/dor look Semitic-clitic; or coordinates; y- prefixes content stems; ol is free; s/r mark boundaries. This is the morphological signature of a designed precision-notation, not a cipher artifact.

**6. Historical Framing (1500 words)**
- Manuscript dated 1404–1438 (carbon dating, vellum). The constructed-precision-language convention fits the 12th–14th century scholastic and translation environment of Languedoc/Provence/Toledo.
- The Ibn Tibbon family and Jacob Anatoli translated Avicenna into Hebrew (Nathan ha-Me'ati, 1279). They were bilingual Hebrew/Arabic scholars producing Latin and Romance commentary.
- Romance/Arabic month labels (octobre, mars, auge) point to Occitan or Catalan vernacular. "auge" from Arabic *awj* (apogee).
- Three-genre structure parallels Avicenna's Canon: Book II (*al-Adwiyya al-Mufrada*, simple drugs) = de simplicibus = herbal-A/B/Q20. Book I (humoral theory) = continuous-process = Q13. Book V (*Aqrabadhin*, compound recipes) = recipe-procedure = pharm.
- This is structural homology, not proof of source. No semantic gloss is claimed.

**7. Falsification Record (800 words)**
- a/o contrariety FAILED.
- o/e at paragraph level FAILED.
- Unified Q13+Q20 register FAILED-as-stated, refined.
- f30v borage zero-chor control FAILED (publish the failure).
- The discipline of reporting failures distinguishes this work from earlier Voynich-decoding claims.

**8. What Remains Open (700 words)**
- No semantic gloss locked.
- dor/dar functional distinction not yet pinned.
- y- function (article/topic/negation) not discriminated.
- f57v matrix as decoder key untested.
- Authorship not proven, only environment-localized.

**9. Conclusion (400 words)**
Three distributional findings stand: vowel-grade contrariety, three-genre structure, grammatical differentiation of short morphemes. They form an internally consistent picture of a designed precision-notation encoding medical reference material in the Avicennan tradition. The work does not decode the manuscript; it bounds what any successful decoding must explain.

### Appendices
- A: Tokenizer specification (v4)
- B: Section assignment by ZL3b flag
- C: Full table of o/e minimal pairs with counts
- D: Full table of a/o pair counts (negative result)
- E: Adjacency profile tables (all candidates)
- F: Paragraph-opening template counts per folio
- G: Whole-MS folio register profile (CSV summary)

### Target length
~12,000 words main text + appendices. Submission-ready after one more revision pass and one external read.

### Pre-submission requirements
- Verify Freudenthal (2016) citation for ibn Tibbon *poael* parallel.
- Run paragraph-position analysis on -ar across botanical section to either lock or demote the 1.82x ratio.
- One external linguist read for the Semitic-morphology framing (the strongest claim that needs cross-checking).
- One external Voynich-community read for prior-art conflicts.

---

## ZENODO DOI STRATEGY

Zenodo grants each upload a permanent DOI, supports versioning, and ORCID linkage. Files small enough fit one record; large or thematically separate items get their own DOI so they can be cited independently.

### Recommended DOI-worthy artifacts

**1. Master dataset: ZL3b-derived folio-level register profile.**
- File: `voynich_folio_profile.csv` (224 folios, register metrics).
- Description: "Folio-level distributional profile of the Voynich Manuscript, derived from Zandbergen-Landini transcription ZL3b-n. Includes chedy/k, qok-/k, chor/k, suffix-rate, paragraph-opening template rate, and register classification for 224 folios with n≥30 tokens."
- This is the single most-reusable data artifact in the project. Citeable by anyone testing register hypotheses against ZL3b.

**2. Methodology preprint: the paper itself (after submission).**
- Standard practice: Zenodo preprint deposit alongside journal submission. Establishes priority and date.

**3. Code/tokenizer: v4 tokenizer specification + analysis scripts.**
- Files: `tokenize.py`, `test_setup.py`, `run_tests.py` (or cleaned versions).
- Description: "Voynich v4 tokenizer and distributional analysis scripts for ZL3b-n. Reproduces all quantitative claims in Gonzalez (2026)."
- A working tokenizer is reusable infrastructure. Citeable.

**4. The three-genre dataset (if separable from #1).**
- Paragraph-opening template counts per section, with section-baseline word-initial gallows rates.
- This is the headline empirical claim. Worth its own data citation.

**5. The o/e contrariety pair dataset.**
- All 9 locked o/e pairs with full counts. All 92 a/o pair counts (negative result).
- Includes both the positive and the falsified result. The negative result is independently citeable.

**6. The adjacency profile dataset.**
- Following/preceding token-class counts for dar, dor, ar, or, ol, y-, s, r.
- Reusable for anyone profiling Voynich short morphemes.

**7. (LATER) The whole-MS distributional atlas.**
- Once finalized: a polished Zenodo deposit combining all of #1, #4, #5, #6 plus per-folio CSVs and replication notes. This becomes the "Voynich Distributional Atlas, ZL3b basis, 2026" — a community resource.

### What NOT to Zenodo

- The v1 paper draft with the f30v error. Keep private until corrected.
- The early speculative session logs. Not reproducible work product.
- Anything still tagged SPECULATIVE in the master prompt.

### Recommended DOI sequencing

**Phase 1 (immediate, before journal submission):**
- DOI #1: folio register profile dataset (citeable foundation for the paper)
- DOI #2: tokenizer + analysis code (reproducibility infrastructure)

**Phase 2 (with journal submission):**
- DOI #3: paper preprint (priority + open access)

**Phase 3 (after acceptance):**
- DOI #4: consolidated distributional atlas (community resource)

### ORCID linkage
Register ORCID before first Zenodo upload. Vince's name on every DOI links the corpus together as a research program rather than disconnected uploads. Independent-researcher credibility anchor.

### Versioning
Zenodo supports versioned DOIs: each revision gets its own DOI, and a "concept DOI" points to the latest. Use versioning aggressively — the folio profile in particular will be revised as more sections are profiled in detail.

---

*Vince Gonzalez + Claude · 11 May 2026.*
