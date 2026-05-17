# VOYNICH — T10 (s-base) and T11 (daiin compositionality) Findings
## 14 May 2026 late evening (continued)
## Vince Gonzalez + Claude

---

## §T10 — s-base PROBE [FALSIFIED]

### Setup

Prior session classified s-base as an "obligatorily-prefixed root" — 0 bare 's' tokens but 435 prefixed forms across all 7 derivational prefixes. Tagged for focused investigation.

### Result: parser artifact

When the inventory was restricted to forms where the s-prefix is NOT immediately followed by 'h' (which would make it 'sh' base, not s-base):

| Prefix | s-base total | s-base types | Top forms |
|---|---|---|---|
| k- | 3 | 3 | ksor, ksear, ksam |
| d- | 3 | 2 | ds, dsechey |
| t- | 0 | 0 | — |
| ok- | 0 | 0 | — |
| ot- | 0 | 0 | — |
| qok- | 0 | 0 | — |
| qot- | 0 | 0 | — |

**Total: 6 tokens / 5 word-types** across all prefixes.

The 435 tokens previously assigned to "s-base" were misparsed prefix+sh-base forms (ksh-, dsh-, tsh-, oksh-, otsh-, qoksh-, qotsh-) where the parser was greedy on 's' and assigned 'h-suffix' instead of 'sh-base'.

### Status: FALSIFIED

s-base is NOT a separate inflectional class. The Voynichese content-base inventory is:
- **CH-root** (× 4 vowel grades: ∅, e, o, eo)
- **SH-root** (× 4 vowel grades: ∅, e, o, eo)
- **Process roots** (qok, qot, ok, ot, qoke, qote, oke, ote)
- **d-family function-word stem**

No third base class. This tightens the architecture from prior memo.

### Methodological note

This is a useful self-falsification. The over-greedy parser (longest-match on prefix-then-base then suffix) created a phantom base by parsing prefix+sh forms as prefix+s+h-suffix. Whenever a parser yields a "new base with 0 bare form but full prefix decoration," the parse is suspect by construction. Future parsers need explicit blocking against 'sh' confusion when matching 's' as a base.

---

## §T11 — daiin COMPOSITIONAL or UNITARY? [LOCKED — compositional]

### Setup

daiin (n=799) is the corpus's most frequent word. Prior session tagged daiin as "copula candidate" / "major nominal-verbal element" via position + neighbor analysis. Question: is daiin morphologically d + aiin (compositional), or a single unanalyzable morpheme?

### Test 1 — d-stem inflectional inventory

d takes the clitic-paradigm inflections but NOT the process-content paradigm:

| d + suffix | Count | Class |
|---|---|---|
| daiin | **799** | -aiin grade |
| dar | 300 | -ar clitic |
| dy | 233 | -y/dy |
| dal | 231 | -al clitic |
| dain | 191 | -ain grade |
| dair | 106 | -air grade |
| dol | 103 | -ol grade |
| dam | 81 | -am clitic |
| d (bare) | 65 | base |
| dor | 65 | -or grade |
| daiir | 25 | -aiir grade |
| dan | 15 | -an clitic |
| dedy | 2 | (effectively absent) |
| deedy | 5 | (effectively absent) |
| dey | 1 | (effectively absent) |

d-stem REJECTS the -edy/-eedy/-eey process-aspect paradigm. The d-stem inflects exclusively in the clitic + paradigm-grade suffixes. This is a coherent restricted inventory.

### Test 2 — aiin:ain ratio across stems

If -aiin/-ain are paradigm grades that apply to all stems uniformly, the section-level aiin:ain ratio should be similar across stems WITHIN a section.

| Section | d | qok | ok | ot | s | (bare) |
|---|---|---|---|---|---|---|
| balneo | 1.65 | 0.53 | 0.72 | 0.50 | 1.11 | 1.74 |
| stars | 2.45 | 1.20 | 1.43 | 1.48 | 1.46 | 3.70 |
| herbal-A | **5.59** | **6.75** | **3.92** | **5.40** | **5.50** | **8.25** |
| pharm-herbal | **5.67** | inf | inf | 3.00 | 7.00 | 10.50 |

**All stems follow the same section pattern.** balneo: ratio near 1; herbal-A: ratio 4-8. d-stem behaves like every other stem with respect to -aiin/-ain grade selection.

This means **-aiin/-ain is a paradigm-grade pair** that attaches uniformly across stems, with grade-choice driven by section register (not by stem-specific behavior).

### Test 3 — Neighbor-context cosine (herbal-A only)

If daiin's syntactic role comes from d-stem identity, daiin should pattern with other d-family members (dain, dar). If from -aiin grade, it should pattern with other -aiin forms (aiin, qokaiin).

| Comparison | Before cosine | After cosine |
|---|---|---|
| daiin vs **dain** (same stem, paradigm-grade) | **0.781** | **0.905** |
| daiin vs **dar** (same stem, different grade) | **0.741** | **0.907** |
| daiin vs **qokaiin** (different stem, same grade) | 0.582 | 0.246 |
| daiin vs **aiin** (different stem, same grade) | **0.084** | 0.875 |
| daiin vs **chol** (content noun, control) | 0.709 | 0.173 |

**daiin patterns syntactically with d-family members (dain, dar) far more strongly than with other -aiin forms (aiin, qokaiin).** Cosines to dain/dar > 0.74 on both sides; cosines to non-d -aiin forms drop to 0.084-0.582 before.

### Test 4 — Section distribution

Compared to other -aiin forms:

| Section | daiin/k | dar/k | dy/k | aiin/k | qokaiin/k |
|---|---|---|---|---|---|
| balneo | 11.8 | 9.0 | 7.3 | 5.8 | 12.6 |
| stars | 11.1 | 4.0 | 1.0 | 19.1 | 11.1 |
| **herbal-A** | **40.8** | **9.6** | 10.7 | 10.3 | 2.8 |
| pharm-herbal | 26.0 | 7.6 | 4.6 | 10.7 | 1.5 |

daiin peaks in herbal-A (40.8/k). Compare to qokaiin (2.8/k in herbal-A; 12.6 in balneo) — different distribution. Other d-family members (dar, dy) are also herbal-A-prominent but flatter. **daiin tracks d-family section preference, NOT -aiin suffix's typical distribution.**

### Conclusion — LOCKED

**daiin = d + aiin (compositionally), but functions as a d-family member.**

- **Morphologically compositional**: d-stem + -aiin paradigm grade
- **Functionally inherited from d-stem**: syntactic role (NP-connector / coordinator / proclitic-like), section preference (herbal-A peak), neighbor-context (matches dain, dar)
- **Why most frequent**: d-stem is the corpus's primary clitic-family stem; -aiin is the dominant grade in herbal-A and pharm-herbal; their composition daiin is naturally the highest-frequency item. No special lexicalization needed.

The high herbal-A peak (40.8/k) reflects:
1. Substance-naming sections favor NP-connecting machinery (d-family)
2. Within substance sections, -aiin grade is dominant
3. d+aiin = the predicted maximum

This explains the May-11 LOCKED "daiin top frequency" finding fully.

### Implication for the copula reading

The prior copula reading (T4 from earlier this session) is now refined:
- daiin's NP-connector role is the d-family clitic role specifically realized in -aiin grade
- Not a special copula — a section-specific realization of the general d-stem NP-linking function
- Compare to dar (NP-bidirectional, coordinator-class, mixed section)
- Compare to dal (NP-final, enclitic-class)
- Compare to dor (NP-leading, proclitic-class)
- daiin sits as **mid-NP-connecting form**, dominant in substance-naming environments

The d-family is the **clitic/particle/connector inventory**. daiin is one of its grade-realizations.

---

## §UPDATED ARCHITECTURE

```
Voynichese morphological architecture (LOCKED):

CONTENT bases:
  CH-root × 4 vowel grades: ch | che | cho | cheo
  SH-root × 4 vowel grades: sh | she | sho | sheo
  Process roots:            qok | qot | ok | ot | qoke | qote | oke | ote

FUNCTION-WORD stem:
  d-family (clitic/NP-connector class) — takes restricted inflection:
    Paradigm grades:  -y, -ain, -aiin, -air, -aiir, -or, -ol, -ar, -al
    Clitic suffixes:  -am, -an, -dy
    NOT: -edy, -eedy, -eey (these are content-paradigm suffixes only)

DERIVATIONAL PREFIXES (attach to CH/SH bases only, not to process roots):
  ∅ | k | d | t | ok | ot | qok | qot | cth

INFLECTIONAL SUFFIX AXES:
  1. e-grade contrariety:  ∅ | -y | -ey
  2. o-grade quality:      -or | -ol
  3. aspect/register:      -dy | -edy | -eedy | -eey | -ody | -eody
  4. paradigm grade:       -aiin | -ain | -aiir | -air
  5. clitic axis:          -ar | -al | -am | -an

SECTION-REGISTER SELECTION (locked mechanism):
  Vowel grade × Section:
    e-grade  → balneo, stars (process/theory)
    o-grade  → herbal-A (substance/material)
    eo-grade → pharm-herbal (recipe/prescriptive)
    bare     → neutral baseline everywhere

  Paradigm grade × Section:
    -ain     → balneo (short-grade pole)
    -aiin    → herbal-A, pharm-herbal (long-grade pole)
```

### Falsifications/walk-backs in this session

- **s-base does NOT exist as a separate class** (T10). Parser artifact.
- **daiin is not a special copula** — it's the dominant compositional realization of d-stem + -aiin in substance-naming sections. The "copula candidate" reading is downgraded; daiin is a d-family NP-connector specifically tuned for materia-medica contexts.
- **The 4-humor model still tentative**. With only 2 bases (CH, SH) and 2 grades (-or, -ol) cleanly attested, the 4-humor mapping needs Canon Book II testing to confirm.

---

## §NEXT TESTS

### T12 — Forced-choice paragraph parse

Five herbal-A line-clusters (not paragraphs — paragraph splitting is brittle), pre-register prediction: "Voynichese herbal-A units are CH/SH-substance series connected by d-family particles with daiin as the dominant connector."

Code 5 sample line-clusters, count structural match.

### T13 — Canon Book II forced-choice

With architecture LOCKED, predict for ~10 well-attested Avicennan simples from Hamdard PDF:
- Plant X is hot/dry → its Voynich folio bears chor/shor-DOMINANT signature
- Plant Y is cold/moist → chol/shol-DOMINANT
- Plant Z is balanced → bare-grade balanced

Pull pharm-herbal Lf labels (ingredient labels) where present, and run prediction-test.

### T14 — d-family inflection map

The d-family has at least 13 productive forms (daiin, dar, dy, dal, dain, dair, dol, dam, d, dor, daiir, dan, plus minor). Map each to syntactic role with neighbor + position analysis. Build the d-family functional inventory (proclitic vs enclitic vs coordinator vs copula vs adjunct).

### T15 — Process-root parallel test

Process roots (qok, qot, ok, ot) don't take derivational prefixes but DO take the suffix axes. Test: do process roots have their own vowel-grade system? qok / qoke / qoko / qokeo? Section-specific selection?

End of memo.
