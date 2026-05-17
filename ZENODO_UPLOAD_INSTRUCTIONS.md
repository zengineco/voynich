# Zenodo upload checklist — Voynich preprint v1.0

**Stage:** DRAFT — do not upload until Epistemend synthesis pass and your final read are complete.

---

## What gets uploaded

Two files, attached to a single Zenodo deposit:

1. **`voynich_preprint_v1.0_DRAFT.docx`**
   - Rename to `voynich_preprint_v1.0.docx` after final revisions.
   - Optionally also upload a PDF export. Zenodo recommends PDF for primary deposits; .docx is fine as an additional format for editability.

2. **`voynich_preprint_v1.0_supplementary.zip`**
   - Contains: tokenizer_v4.py, five analysis scripts, folio_section_assignments.csv, README.md.
   - Does **not** contain the ZL3b-n corpus file itself — that's third-party data hosted at voynich.nu. The README directs users to fetch it.

`SUPERSEDED.md` is for the local project — it does **not** get uploaded to Zenodo.

---

## Zenodo deposit metadata

Fill these into the Zenodo upload form exactly as written.

### Title

> Productive Paradigms in the Voynich Manuscript: A Distributional Analysis of ZL3b-n

### Upload type

`Publication` → `Preprint`

### Authors

| Field | Value |
|---|---|
| Family name | Gonzalez |
| Given name | Vincent |
| Affiliation | Independent researcher |
| ORCID | (insert your ORCID iD after registration — see below) |

**ORCID note:** If you haven't registered an ORCID iD yet, do so at https://orcid.org before this upload. Free, takes about three minutes. The iD will be permanently associated with this and all future deposits. The Modulign-academic skill flags ORCID as pending — this is the moment to resolve it.

### Description (abstract field)

Paste this in the abstract field:

> This preprint reports a distributional analysis of the Voynich Manuscript (Beinecke MS 408) using the Zandbergen–Landini EVA transcription (ZL3b-n, version 3b, May 2025). The analysis identifies a productive morphological system organised around three components: prefix-classes, fused vowel-grade-and-suffix templates of the type known in Semitic linguistics as binyanim, and consonantal root skeletons. Under this grammar 76.1 per cent of running tokens decompose into prefix-and-stem-and-template; the remaining residue is dominated by hapax compounds whose internal structure is consistent with the grammar but whose specific elements are not in the present inventory.
>
> The strongest single observation is a productive vowel-grade contrariety in which o-grade and e-grade forms of the same skeleton polarise across a substance-or-process register axis at 52 of 53 measurable minimal pairs (98.1 per cent, p ≈ 1.2 × 10⁻¹⁴). The second strongest is a corpus-wide coupling between vowel grade and suffix template (χ² = 106.1 on 25 degrees of freedom for the ch-d root alone, p ≈ 1.4 × 10⁻¹¹), which is the diagnostic morphological signature of binyan-style inflection.
>
> Three previously uncatalogued productive paradigms are reported: cth- in the herbal-A section (four forms, top section-specificity 33.6); lk- in the stars section (five forms, top section-specificity 16.2); and cheo-/sheo- in the pharmacological section (twelve forms). Comparison against Book II of the Canon of Medicine is included as comparative-typology context; no claim of textual derivation, authorship, or dating is made. The purpose of this preprint is to establish priority on the distributional observations and to make the underlying tokeniser and analysis scripts available for replication.

### Keywords

```
Voynich Manuscript
Beinecke MS 408
computational palaeography
distributional morphology
corpus linguistics
EVA transcription
templatic morphology
Semitic morphology
binyan
medieval encyclopedic texts
```

### Additional notes / methods

```
Analysis was performed on the Zandbergen–Landini EVA transcription (ZL3b-n, version 3b of 13 May 2025), available at voynich.nu. The corpus file is not redistributed in this deposit; the supplementary materials direct readers to fetch it from voynich.nu. All numerical claims in the preprint are reproducible from the supplied tokenizer (tokenizer_v4.py) and analysis scripts. Tokenisation, statistical analysis, paradigm enumeration, and manuscript drafting were performed with computational assistance from Claude (Anthropic); all methodological decisions, hypothesis formation, falsification design, statistical-test pre-registration, and final interpretation are the responsibility of the author.
```

### Access rights

`Open Access`

### Licence

`Creative Commons Attribution 4.0 International (CC BY 4.0)`

This is the standard preprint licence — anyone can read, share, and build on the work, with attribution. Compatible with future journal submission (almost all journals accept CC BY preprints).

### Related identifiers

After upload, you can edit the deposit to add a relation:

| Relation | Identifier |
|---|---|
| `Is supplemented by` (if you upload supplementary separately) | (DOI of supplementary zip) |
| `Cites` | `https://www.voynich.nu` (the ZL transcription source) |

### Communities

If a Zenodo community exists for "computational linguistics" or "manuscript studies", consider adding the deposit to it. Optional; affects discoverability only.

### Version

`1.0`

If you later revise, upload as a new version (Zenodo supports this via the "New version" button on the deposit page). The DOI updates with each version; the concept DOI (pointing to the all-versions record) stays stable for citations.

---

## Pre-upload checklist

Before clicking publish:

- [ ] ORCID iD registered and entered in author field
- [ ] Epistemend synthesis pass complete; revisions incorporated
- [ ] All numerical claims in the preprint match the script outputs (re-run `headline_tests.py` once more after any text revision)
- [ ] Author name spelled correctly (Vincent Gonzalez vs Vince — choose one and stay consistent)
- [ ] Affiliation written as you want it permanently displayed
- [ ] Abstract within Zenodo's character limits (no limit in practice, but readable in one screen is better)
- [ ] Licence selection confirmed (CC BY 4.0 recommended)
- [ ] DRAFT label removed from the filename and the document title
- [ ] PDF export validated (open the PDF, confirm tables and headings render correctly)
- [ ] Supplementary zip contents validated (unzip locally, run one script, confirm output)

After clicking publish, the DOI is permanent. Zenodo does not allow deletion; only new versions.

---

## After upload

Within 24 hours of upload:

1. Add the resulting DOI to the project's local `SUPERSEDED.md` file (replace the bracketed placeholder).
2. Update modulign.org (or wherever your scholarship-first site lists publications) with the new DOI.
3. If posting publicly anywhere (X, Bluesky, Reddit r/voynich, academic Twitter), keep the announcement neutral: "Preprint posted to Zenodo, [DOI link]." Let the paper speak for itself. No marketing copy.
4. Consider whether to mirror on PhilPapers, SSRN, or arXiv. ArXiv requires an endorser for first-time submissions; not trivial. PhilPapers is friendlier and indexes preprints in the relevant categories. Optional.

---

*V. Gonzalez · May 2026*
