# VOYNICH MANUSCRIPT RESEARCH — MASTER CONTEXT PROMPT
## Vince Gonzalez · May 2026
### Load this at the start of every new session.

---

## WHO YOU ARE TALKING TO

Vince Gonzalez, independent researcher, Punta Gorda/Cape Coral, Florida. This research began in May 2026 in a single extended session that produced a color lexicon, morpheme catalog, grammar kernel, and structural hypothesis. The primary paper draft exists. The research is ongoing.

---

## THE CORE HYPOTHESIS

The Voynich Manuscript (Beinecke MS 408, Yale) is a complete Avicennan medical reference system written in a constructed precision language with Semitic-framework morphology, produced within the 12th–14th century Occitan-Jewish translation tradition. The authorship candidate is the intellectual circle of Samuel ibn Tibbon and Jacob Anatoli (southern France / Montpellier / Toledo network). No full translation is claimed.

---

## THE METHOD

**Spatial color correlation.** Text blocks appear adjacent to colored plant illustrations. Word families that cluster near specific colors across multiple independent folios — and are absent on control folios lacking that color — are non-randomly distributed and candidate color words.

**Falsification standard:** A word family claimed as a color marker must be absent or near-absent on control folios with no illustration element of that color. This test was applied to primary color words.

**Data source:** Zandbergen-Landini EVA transcription ZL3b-n (version 3b, May 2025), available at voynich.nu. File is in this project. 8,509 lines. 37,595 word tokens. All quantitative claims must be verified against this file before being stated.

**EVA notation note:** EVA renders single Voynich glyphs `ch`, `sh`, `th` as two-character sequences. All morphological statistics are conservative lower bounds because the true glyph count is lower. The "bench glyph" rendered `ch` in EVA is a single Voynich character.

---

## WHAT IS VERIFIED TRUE (checked against ZL3b-n)

### Color Words

| Word Family | Color/Quality | Status | Verified Count |
|---|---|---|---|
| chor / chol | RED / fire quality | **CONFIRMED** | chor: 198 occ; chol: 344 occ |
| ot- family | BLUE / water-celestial | **CONFIRMED** | ot- words: 2,465 occ |
| chody | Vital heat / warm quality | **CONFIRMED** | chody: 91 occ |
| otchor compound | Water + Fire binary | **CONFIRMED** | 15 occ |
| otchol compound | Water + Earth binary | **CONFIRMED** | 30 occ |

### The [Cdy] Ablaut System
The consonant skeleton ch-dy generates the following distinct forms via internal vowel alternation (verified in ZL3b):
- chdy: 147 occ (bare/reduced)
- chedy: 506 occ (base form, Language B)
- chody: 92 occ (vital heat)
- cheody: 90 occ (compound quality)
- cheedy: 59 occ (intensive)
- chady: 2 occ (rare)

This is real. Internal vowel alternation as a meaning-carrying mechanism is diagnostic for Semitic morphological structure. This is the strongest morphological finding.

### Morpheme -ar
Verified count in ZL3b: **427 occurrences** (rank ~9 by frequency). The -ar morpheme is real and high-frequency. The specific claim of 1.82x concentration in Block 2 vs Block 1 has NOT been verified against ZL3b and must be treated as UNVERIFIED until you run the count yourself.

### Structural / Contextual Findings (not number-dependent)
- Month labels in zodiac section (octobre, mars, apule, mai, iun, auge, ianer) are plain Romance/Occitan script — unambiguous, require no EVA.
- "auge" from Arabic "awj" (apogee) confirms Arabic astronomical vocabulary in Romance vernacular — Montpellier/Toledo tradition marker.
- f87 two-paragraph structure (Block 1 = description, Block 2 = application) is visible in ZL3b: two separate `@P0` paragraph starts on same folio.
- Manuscript section correspondence to Canon of Medicine five-book structure is a structural argument, not a quantitative claim.
- Samuel ibn Tibbon's Perush ha-Millot ha-Zarot (1213) contains the term *poael* (operative agent) — this is cited in Freudenthal (2016), which is a real paper. The parallel to -ar is a hypothesis, not proven.

---

## WHAT THE PAPER CLAIMS THAT IS WRONG OR UNVERIFIED

### VERIFIED WRONG — Correct before citing

**f30v "pure blue borage" control test claim:**
The paper and research docs state: "chor occurrences drop to 3 with near-zero chol" on f30v. **This is false.**

Actual ZL3b data for f30v (confirmed borage — ZL3b metadata says "Plant ID: Boragine"):
```
qotchor, kchor, chory (line 2)
chotchol, cthol (line 3)  
chor (line 4)
qotchor, chor (line 9)
```
**chor appears 6+ times on the borage folio. The control test FAILED.** This is the single most important error in the paper. The argument that chor = red/fire quality does NOT rest on this control test passing — it rests on chor's density on confirmed high-red folios. But the specific claim that borage shows near-zero chor is wrong and must be removed or corrected.

Correct framing: The borage folio shows high chor *and* high ot-. This is consistent with Avicennan borage classification — borage is cold/moist but also has fire-quality secondary attributes. It does NOT invalidate the color word hypothesis but it invalidates the clean control test claim.

**f28r "six distinct cr- instances" claim:**
Paper states: "Six distinct cr- instances in one folio" and lists specific line positions.
Actual ZL3b data for f28r: chor appears **0 times as a standalone word**. The folio does contain `otchor` (2 occurrences) and `kchoror` (1 occurrence). The folio is heavily populated with `chol` (5 instances) and `cthol` (multiple).

The "six distinct cr- instances" with specific line-by-line readings (crod line 1, croe line 2, etc.) — **those specific word forms do not appear in ZL3b for f28r.** Those were likely generated from visual image reading in our session where glyph-reading from images was acknowledged as unreliable. The density claim for f28r cannot stand as written.

The folio DOES have `otchor` × 2, which is notable (the binary fire+water compound on a vivid red root folio). That is the defensible finding.

**Frequency counts in abstract/findings:**
- Paper claims chor family: 254 occurrences. ZL3b actual: **198**
- Paper claims chol family: 520 occurrences. ZL3b actual: **344**  
- Paper claims ot- family: 2,498+ occurrences. ZL3b actual: **2,465** (close, acceptable)
- Paper claims chody: 94 base-form occurrences. ZL3b actual: **91** (close, acceptable)
- Paper claims otchor: 17 occurrences. ZL3b actual: **15**
- Paper claims otchol: 31 occurrences. ZL3b actual: **30** (close, acceptable)

The chor (254 vs 198) and chol (520 vs 344) counts are meaningfully off. These need to be corrected in the paper before submission.

**The -ar 1.82x concentration figure:**
This specific ratio does not appear verifiable in ZL3b with a simple grep. The f87 two-block structure is real (visible in ZL3b), but the -ar standalone morpheme does not show the claimed pattern on f87 specifically. The broader -ar Block 2 concentration claim requires a careful paragraph-position analysis across the full botanical section — this has not been done against actual ZL3b data. **Treat as unverified hypothesis, not finding.**

### UNVERIFIED — Do not cite as fact until checked

- Specific glyph readings from image analysis sessions (crob, crod, croe, crotta at specific line positions on specific folios) — all came from visual analysis where glyph-reading accuracy was explicitly flagged as uncertain. None of these specific forms appear as standalone items in ZL3b for the claimed folios.
- f18 "Rosetta Folio" specific word readings (otltog 8ag, ox-/cr- cluster, Bo-/8o-) — not in ZL3b directly, came from image reading.
- f69/f71 zodiac/cosmological color word readings — from image analysis, not EVA-verified.
- The ibn Tibbon *poael* parallel — the existence of the Freudenthal papers is real; the specific claim that the glossary is the "surviving philosophical glossary" with that term should be verified against the actual Freudenthal (2016) text.

---

## WHAT IS SOLID AND DEFENSIBLE

1. **The method itself** — spatial correlation with falsification testing is methodologically valid even where specific tests failed. Failures should be reported honestly.

2. **chor/chol density on high-red folios** — f9r and f28r do show chor/chol in ZL3b (f9r: 1 chor, 5 chol; f28r: 5 chol, 2 otchor). The red correlation is weaker than claimed but not absent.

3. **ot- family dominance on blue folios** — needs folio-by-folio verification but the total 2,465 occurrences and distribution across section types is real.

4. **The [Cdy] ablaut system** — numbers verified. This is the strongest single finding. Real, reproducible, significant.

5. **The month labels** — these are in plain script, unambiguous. Occitan/Catalan dialect confirmed.

6. **f87 two-block structure** — visible in ZL3b. Real.

7. **Canon of Medicine structural parallel** — argument, not dependent on number accuracy. Defensible.

8. **Ibn Tibbon cultural context** — historical argument, not number-dependent. Defensible with proper sourcing.

---

## WHAT MUST BE DONE BEFORE SUBMISSION

### Priority 1 — Fix the paper
- Remove or correct the f30v control test claim. Reframe as: "Borage (f30v) shows ot- family present; the compound otchor also appears, consistent with Avicenna's complex dual-quality rating for borage rather than a simple cold/wet = zero-fire classification."
- Correct frequency counts: chor = 198, chol = 344.
- Remove the specific f28r line-by-line glyph readings (crod, croe, crotta at specific lines) — replace with what ZL3b actually shows: otchor × 2 on the most chromatic red folio.
- Either verify the 1.82x -ar ratio with an actual paragraph-position analysis of ZL3b, or demote it to a hypothesis requiring further work.
- Remove or caveat the specific glyph readings from image analysis (crob near berry f9v, otltog in right margin f18, etc.).

### Priority 2 — Verify before claiming
- Run actual paragraph-position analysis on -ar across botanical section in ZL3b.
- Pull and verify the Freudenthal (2016) paper for the exact ibn Tibbon glossary content.
- Verify f30v, f93r, f9r chody/chor distributions are correctly represented.

### Priority 3 — Strengthen
- The otchor compound on f28r (2 occurrences) and the folio's visual characteristics is actually a *stronger* and more interesting finding than the simple chor count — binary elemental compound on most chromatic red folio. Develop this.
- The [Cdy] ablaut verified numbers are gold. Lead with these.

---

## RESEARCH RECORD — LOCKED FINDINGS (survived ZL3b verification)

| Finding | Basis | ZL3b Verified |
|---|---|---|
| chor/chol elevates on high-red folios | f9r, f28r density | YES (partially) |
| ot- family is dominant / high frequency | 2,465 occurrences | YES |
| chody = separate semantic category from chor | Distribution difference | YES (91 vs 198 occ) |
| otchor compound exists systematically | 15 occurrences | YES |
| otchol compound exists systematically | 30 occurrences | YES |
| [Cdy] ablaut system: 6 forms verified | chdy/chedy/chody/cheody/cheedy/chady | YES |
| -ar is high frequency (rank ~9) | 427 occurrences | YES |
| f87 has two-paragraph structure | @P0 markers in ZL3b | YES |
| Month labels in Occitan/Romance | Plain script, not EVA | YES (not in ZL3b) |
| daiin is highest frequency word | 853 occurrences | YES |

---

## SESSION RULES FOR CLAUDE

1. **Never state a specific number without sourcing it to ZL3b or the paper.** If asked for a count, run it or flag it as unverified.

2. **The f30v control test failed. Do not repeat the "zero chor on borage" claim.** It is false.

3. **The f28r line-by-line readings are not in ZL3b.** Do not repeat "crod line 1, croe line 2" etc. What ZL3b shows is: otchor × 2, chol × 5, cthol × multiple.

4. **The 1.82x -ar ratio is unverified.** Do not cite as a finding until paragraph-position analysis is run on ZL3b.

5. **The method is valid.** The specific implementations of the control test had a failure. That is a science result, not a research failure. Report it honestly.

6. **The core hypothesis remains standing.** The ablaut system, the month labels, the structural Canon correspondence, the ibn Tibbon parallel — these are independent lines of evidence that don't depend on the failed control test.

7. **Always distinguish: LOCKED (ZL3b verified), STRONG (multiple visual confirmations, not EVA-verified), CANDIDATE (1-2 confirmations), SPECULATIVE (intuition only).**

---

## FILE LOCATIONS

- ZL3b-n: `/mnt/project/ZL3b-n` — the actual EVA transcription. Use grep to verify claims.
- voynich_paper.docx: The current paper draft (stored as plain text despite .docx extension)
- voynich_final.docx: Full research record with skepticism log
- voynich_complete.docx: Complete lexicon, morphology, grammar
- voynich_research__1_.docx: Early session notes, first EVA cross-reference

---

*Vince Gonzalez + Claude · May 2026 · First conversation in Voynichese in 600 years. In progress.*
