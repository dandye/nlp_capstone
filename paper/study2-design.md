# Study 2 — Redeeming Silver: Document-Local Structured Supervision and Hybrid Deterministic–Neural CTI NER

Status: DESIGN (2026-07-26). Nothing in this document has been run except the
feasibility censuses marked **[measured]**, which were computed from the actual
repos on the date above.

## 0. One-sentence thesis

Study 1 did not refute silver labels — it refuted silver whose
document-membership claim was *guessed* (a global dictionary). Study 2
characterizes the **free-supervision frontier** for CTI NER: which entity
classes can be bought without paid annotation — by a deterministic tier for
closed-grammar labels, by *authored-provenance* silver (each report's own
STIX bundle projected onto its own text), and by class-conditional transfer
from external human-labeled corpora — which classes cannot, and what each
one costs relative to LLM gold. Judged, as always, only against frozen
human-curated gold. (Deliberately a frontier characterization, not a SOTA
claim: 16 eval docs power per-class signs and CIs, not leaderboard deltas.)

## 1. Lessons from Study 1 (each one is load-bearing below)

- **L1 — Circularity is fatal.** Eval against gold that shares training-label
  blind spots reported 0.74 F1 for a model that scored 0.35 against honest
  gold. Eval gold is never regenerated, never trained on.
- **L2 — Global dictionaries fabricate document membership.** 50.2% of
  silver-flagged "false positives" were real entities; seven semantic classes
  had recall exactly 0.00 because absent-from-dictionary ⇒ labeled O
  (false-O teaches recall suppression).
- **L3 — Closed-grammar classes are nearly free.** Even dictionary-silver
  models hit 0.81–1.00 on attack technique id / TLP / CVE / file hash against
  honest gold. Model capacity spent there is wasted.
- **L4 — Architecture comparisons require identical training data.** The
  GLiNER "zero-shot retention" hypothesis was a training-data confound.
- **L5 — Seed variance is ~2 points** (RoBERTa-large 0.630 vs 0.648, identical
  recipe). Headline comparisons need ≥3 seeds.
- **L6 — Audit labels before training on them** (the blind-audit finding is
  what caught L2). Silver gets scored against gold *before* any GPU hour.

Survey-side lessons (paper/survey.md): cross-corpus transfer collapses
(off-diagonal span-F1 0.01–0.31; training on a 4-corpus union *hurt* APTNER by
−0.11) — so external corpora enter class-conditionally via explicit label
mapping, never as naive union. "STIX-derived supervision for span-annotated
CTI" sits on the survey's open-problems ledger as unattempted.

## 2. The framing: a 2×2 the sequel completes

|  | Closed-grammar labels | Open (semantic) labels |
|---|---|---|
| **Guessed provenance** (global dictionary) | Study 1: worked anyway (L3) | Study 1: catastrophic (L2) |
| **Authored provenance** (validator grammar / doc-local artifact) | **Tier D:** deterministic extractors | **Tier N + doc-local silver:** this study's core question |

Study 1 lived entirely in the top row. Study 2 fills the bottom row and stops
paying the neural tax on the left column.

## 3. Label partition (all 16 labels)

**Tier D — deterministic (8 labels, 46% of eval spans / 42% of train spans [measured]):**
file hash, ip address, email address, cve identifier, cwe identifier,
attack technique id, tlp classification, yara rule name.
Each already has a format grammar in `ner/span_validators.py` (incl. defanged
IP/email forms); Tier D is those grammars promoted from *validation gate* to
*extractor*, plus the existing text_normalize protections (split-hash rejoin).
These labels are **removed from every neural label space** in Study 2.

**Tier N — neural (8 labels, 54% / 58% of spans):**
affected software product, attack technique name, file name, file path,
hacking tool, malware family, tactic, threat actor group.

**Free extension (optional, enabled by the partition):** the STIX bundles
contain 209 domain-name, 168 url, and 265 mutex indicators [measured] that the
current 16-label space cannot express. Adding `domain name` / `url` / `mutex`
as Tier-D labels costs a regex each and zero retraining — evidence for the
partition's practical value, reported as a secondary observation.

**Composition rule:** Tier D runs first and is authoritative for its labels.
Character-overlap conflicts between tiers resolve D-over-N (D precision is the
measured justification; if Phase-1 shows D precision <0.9 on any label, that
label's precedence is revisited). Spans merge into one prediction set scored by
the unchanged `ner.evaluate.Scorer`.

## 4. Supervision sources

### 4.1 Document-local STIX silver (the new idea)

CISA publishes a STIX 2.1 bundle *for the same advisory* the model reads. The
bundle's author read the same report — document membership is authored, not
guessed, which is precisely the atom global dictionaries fabricate (L2).

**[measured] scrape_cisa inventory:** 52 advisories with STIX bundles (of
2,825 in the DB; 50 bundles on disk in `data/stix/`, and of the 52 paired
slugs: 40 in gold train + 9 in gold eval + 3 in no gold set yet — the
52/50/49 counts below are these, not discrepancies). Object census across all 50 on-disk bundles: 2,127
indicator, 757 attack-pattern, 556 relationship, 180 malware, 176
malware-analysis, 70 file, 39 location, 32 vulnerability, 17 threat-actor,
15 identity, **0 tool**. Indicator patterns: ipv4 473, file-hash 304, mutex
265, domain 209, url 168, email 119. ATT&CK ids and CVEs appear only as free
text in `name` fields (`Execution - Command and Scripting Interpreter
[T1059]`), so extraction regexes are required even from the "structured" side.

**STIX object → label mapping:**

| STIX source | → label | Tier | Notes |
|---|---|---|---|
| malware.name (+aliases), is_family | malware family | N | 180 objects |
| threat-actor.name (+aliases) | threat actor group | N | 17 objects — sparse |
| attack-pattern.name text part | attack technique name | N | strip trailing `[Txxxx]` |
| attack-pattern.name `[Txxxx]` | attack technique id | D | cross-check only; Tier D owns it |
| vulnerability.name | cve identifier | D | cross-check only |
| file.name / file.hashes | file name / file hash | N / D | 70 objects |
| indicator patterns (ip, email, hash) | Tier-D labels | D | cross-check only |
| indicator patterns (domain/url/mutex) | new Tier-D labels | D | optional extension |
| malware-analysis, identity, location, report | — excluded | — | AV-scan results / no matching label |

**Generation procedure** (`ner/stix_silver.py`, new): parse bundle → typed
surface strings (incl. alias lists) → **verbatim projection** onto that slug's
`{base}.clean.md` using the existing fused-token span matcher
(`annotation_text.find_token_span`) → `span_validators` gate for structured
types → per-slug `{slug}.json` in gold schema `{text, label}` +
`{slug}.dropped.json` for non-verbatim/failed-gate proposals (mirrors
`llm_gold`'s discipline; Study-1 invariants 1–2 hold unchanged).

**Known structural holes (this is a feature of the design, not a surprise):**
STIX cannot supervise *affected software product*, *hacking tool* (0 tool
objects), or *tactic*. Silver coverage is per-class, and RQ3 is built around
that asymmetry rather than pretending it away.

### 4.2 External human-labeled corpora (the "other studies' labels")

| Corpus | Labels | Size | Provenance | License | Use here |
|---|---|---|---|---|---|
| AnnoCTR | GROUP, MALWARE, TOOL, TACTIC, TECHNIQUE, + general NEs | 120 expert-annotated reports, 12.2k sentences | single expert | **CC-BY-SA 4.0 — the only cleanly licensed one** | primary augmentation source |
| CyberNER (2025) | 21 STIX types (harmonized union of CyNER+DNRTI+APTNER+AttackER) | 610k tokens | remapped human labels | inherits unclear upstream licenses | secondary; convenient pre-harmonized bridge |
| CyNER | malware, indicator, system, organization, vulnerability | 107k tokens | human (BRAT) | unclear | via CyberNER |
| APTNER | 21 fine-grained (MAL, APT, TOOL, OS, FILE, …) | 260k tokens | human | unclear (paywalled paper) | via CyberNER |
| DNRTI | 13 | 176k tokens | human | unclear | via CyberNER |
| AttackER | 18 STIX-derived, long spans | 2.6k sentences | human+semi-auto | zenodo release | long-span convention breaks comparability — excluded from span training, noted in paper |
| MalwareTextDB | token+relation, MAEC | 39 APT reports | human, κ=0.36 | unclear; local copy at data/evals/ | out-of-domain eval only (RQ-X stretch) |

**Mapping into Tier-N labels** (Phase-1 deliverable `ner/corpus_map.py`; ✓ =
direct, ~ = partial/risky, ✗ = unavailable):
malware family ✓ (MALWARE/MAL), threat actor group ✓ (GROUP/APT),
hacking tool ✓ (TOOL), tactic ✓ (AnnoCTR TACTIC),
attack technique name ✓ (AnnoCTR TECHNIQUE),
affected software product ~ (CyNER *system* / APTNER *OS* — definitional
mismatch documented in survey: same token gold-typed differently across
corpora), file name ~ (APTNER FILE), file path ✗.
Unmappable external labels are dropped, never coerced. Every mapping decision
is recorded in the released mapping table (the survey's harmonization-loss
lesson, made auditable).

### 4.3 LLM gold (paid reference arm)

Study-1 machinery (`ner.llm_gold`, Sonnet) unchanged. Its role in Study 2 is
the *cost ceiling*: the thing silver is trying to approximate. Per-doc cost and
time recorded from the actual API logs for the cost frontier (RQ4).

## 5. Research questions

### RQ1 — Does the hybrid partition beat monolithic 16-label NER?

*Lesson: L3.* **H1:** Tier D matches/beats the best neural model on the 8
closed-grammar labels at zero training cost. **H1′ (rival):** context
sensitivity (hash-vs-filename, defanged forms) favors learned models.
**H2:** removing Tier-D labels from the neural space improves semantic-8 F1 at
fixed data/compute (capacity + label-confusion reallocation).
**Design:** (a) Tier D standalone vs SecureBERT-16's per-label scores on RX
labels; (b) SecureBERT-8 vs SecureBERT-16 on semantic labels — identical docs,
windows, hyperparameters, 3 seeds (L5); (c) composed hybrid vs monolithic on
the full-16 view. **Falsified if** regex ≤ neural on RX labels or 8-label ≤
16-label on semantic F1. Either outcome is publishable; H2's effect size is the
novel number (CyNER merged at inference; nobody reports the *training-time
label-space partition* effect).

### RQ2 — Is authored-provenance silver better than guessed-provenance silver, and how close is it to gold?

*Lessons: L1, L2, L6.* **H1:** on identical docs, STIX-silver-trained ≥
dictionary-silver-trained on covered semantic classes, by a large margin.
**H2:** STIX-silver reaches ≥80% of LLM-gold-trained F1 on covered classes.
**Design:** four arms on the *same* docs (STIX∩train = 40 docs [measured]):
(i) doc-local STIX silver, (ii) Study-1 global-dictionary silver regenerated on
those docs, (iii) **placebo: deranged-bundle silver** — a fixed derangement of the 40
bundles, so each doc is labeled by exactly one *other* advisory's bundle
(never its own, never a pool — a pooled placebo would collapse into arm (ii)),
isolating doc-locality itself as the active ingredient (if (i) ≈ (iii), STIX
is just a cleaner dictionary and the provenance thesis is dead), (iv) LLM gold restricted
to the same 40 docs (subset restriction kills the data-quantity confound — L4
discipline applied to supervision comparisons). All scored on the untouched
human-curated gold. **Falsification thresholds are variance-anchored:** a
claimed Δ must exceed the document-level bootstrap CI plus the measured 5-seed
spread — no a-priori magic numbers. **Gate:** the Phase-0 audit (below) must
show silver precision ≥0.80 on covered classes or the provenance argument dies
before training does.

### RQ3 — Which classes can structured artifacts supervise, and can mapped external corpora fill the rest?

*Lessons: L2 (false-O), survey transfer-collapse.* **H1 (predictive form):** for classes with substantial bundle coverage
(malware: 180 objects, attack-pattern: 757), silver-trained recall lands
within the RQ2 variance band of gold-trained recall; for zero-coverage classes
(tool: 0 objects, products: no field), recall stays at the untrained baseline
— the object-count → recall relation is the testable claim, not the
zero-object observation itself. **H2:** class-conditional augmentation from
AnnoCTR/CyberNER lifts exactly the classes it maps to. **H2′ (rival):**
transfer collapse makes even class-conditional augmentation net-negative on
CISA-domain eval. **Design:** class-conditional training with per-class loss
masking — classes a doc's supervision doesn't cover are *masked, not taught as
O*. GLiNER's label-conditioned architecture supports heterogeneous per-doc
label coverage natively, which makes it the natural RQ3 vehicle (an
architectural rationale, unlike Study 1's confounded one — L4); for
softmax token classifiers, each arm's label space = its supervision's covered
classes (eval label space from checkpoint, Study-1 invariant 3). Augment one
class-slice at a time; report per-class deltas with bootstrap CIs over
documents (eval n per class is small: threat actor 49, malware family 46
spans [measured]) — sign and CI, never bare micro-F1.

### RQ4 — What does the annotation-cost frontier look like?

*Lesson: the memory-note discipline (cost next to F1, always).* **H1:**
free supervision (D + silver + external) reaches ≥90% of full-LLM-gold
hybrid F1 at ≈0% *marginal* annotation cost (marginal to this project:
external corpora embed sunk expert-annotation cost paid by others — the paper
says so explicitly, since the contribution *is* a cost frontier). **H2 (rival):** gold's advantage
concentrates precisely in silver-blind classes, flattening the frontier early.
**Design (axis resolved to what 40 paired docs can support):** the free stack
(Tier D + STIX silver + external corpora) is a *fixed comparator*; the swept
axis is **dollars of LLM gold** — 0, 10, 20, 40, 66 gold docs (cost from the
actual llm_gold API logs) — asking "how many gold dollars does the free stack
equal?" plus the silver-pretrain→gold-finetune schedule (BOND-style) at each
point. Y: strict micro-F1 (both views); every point reports time/doc, tokens,
and cost alongside F1. A doc-count scaling *curve* for silver itself is out of
reach at 52 bundles; **scoped extension probe (Phase 1, go/no-go):** parse the
"Indicators of Compromise" tables/sections present in `body_text` of the 2,825
bundle-less advisories — the same doc-local idea with 50× the n, targeting
exactly the classes STIX covers well. One day of effort to measure yield on 20
sampled advisories decides whether a true scaling curve enters scope.

### RQ-X (stretch, only if Phases 0–3 leave budget) — Does hybrid+silver training generalize out-of-domain better than gold-only?

Score the RQ2/RQ3 fleet on mapped AnnoCTR test and local MalwareTextDB.
Survey's transfer numbers predict collapse; measuring it honestly for the
hybrid is a contribution either way.

## 6. Phase 0 — go/no-go pilot (no GPU, ~1 day)

Project every STIX bundle onto its own clean.md (the `stix_silver` generator)
and score the projection *as if it were predictions* against curated gold on
the 9 STIX∩eval docs [measured: aa23-158a, aa23-284a, aa23-352a, aa25-022a,
aa25-050a, aa25-141b, ar23-187a, ar23-230a, ar25-261a], using
`ner.evaluate.Scorer`. Also record: alias-match rate (verbatim gate drop rate),
per-class span recall vs gold, per-class precision.

**One-shot rule (leak prevention):** the STIX→label mapping (§4.1) is frozen
*before* this audit runs; the gate is evaluated once against the pre-registered
thresholds below, and **no mapping revisions are permitted after seeing
eval-doc results** — otherwise the mapping is fit to the eval set and RQ2's
provenance claim is contaminated. Mapping debugging happens exclusively on
STIX∩train projections (spot-checked by hand), which touch no eval gold.

**Gate:** covered-class precision ≥0.80 AND recall ≥0.50 → proceed to full
RQ2/RQ3. Precision <0.60 → kill the doc-local arm; the study degrades
gracefully to RQ1 + RQ3(external-only) + RQ4, all still publishable.

## 7. Experiment matrix (headline runs; 3 seeds each where marked)

| Arm | Train supervision | Docs | Label space | Architecture(s) |
|---|---|---|---|---|
| A0 | none (Tier D only) | — | 8 RX | regex |
| A1* | LLM gold (Study-1 baseline, rerun in 8-label space) | 66 | 8 SEM | SecureBERT, GLiNER |
| A2* | LLM gold, 16-label (existing Study-1 checkpoints) | 66 | 16 | SecureBERT (published 0.712), GLiNER (0.560) |
| B1* | STIX silver | 40 | covered SEM | SecureBERT, GLiNER |
| B2* | dictionary silver (regenerated, same docs) | 40 | covered SEM | SecureBERT |
| B3* | LLM gold restricted | 40 | covered SEM | SecureBERT |
| B4* | placebo: deranged-bundle silver (fixed derangement) | 40 | covered SEM | SecureBERT |
| C1 | STIX silver + AnnoCTR class-conditional | 40+120 | 8 SEM | GLiNER |
| C2 | C1 + CyberNER slices | + | 8 SEM | GLiNER |
| D1 | silver-pretrain → gold-finetune | 40→66 | 8 SEM | SecureBERT |
| F | frontier LLM reference (Study-1 result stands) | — | 16 | Gemini 0.795 |

(*) = **5-seed** arms (3 is too few to defend a variance estimate; seeds are
the cheapest insurance in the matrix). Compute: existing Colab notebooks; each
arm logs wall-clock, tokens, and cost per the standing reporting rule.
**Checkpoint rule (leak prevention):** model selection uses a dev slice carved
from *training* docs (or fixed epoch count, pre-registered per arm) — never
the 16 eval docs.

## 8. Evaluation protocol

- Eval gold: Study-1 human-curated 16 docs — frozen. Val for tuning; test
  scored once per arm (multiple-comparison hygiene; headline comparisons
  pre-registered in this doc).
- Metrics: strict + relaxed span P/R/F1 (`ner.evaluate`), reported on **two
  views**: full-16 (comparability with Study 1) and semantic-8 (so Tier D
  can't inflate the neural story). Per-class tables with bootstrap CIs over
  documents.
- **One pre-registered headline metric per RQ** (strict×relaxed × two views =
  4 slices per config; with 16 docs some slice will always look significant):
  RQ1 → strict semantic-8 micro-F1 (H2) and strict full-16 (hybrid vs Study 1);
  RQ2 → strict micro-F1 on covered classes; RQ3 → per-class strict recall
  delta; RQ4 → strict full-16 per dollar. Everything else is labeled
  exploratory in the paper.
- **Stratified eval (designed contrast):** report paired (n=9) vs unpaired
  (n=7) eval docs separately — bundle-shipping advisories are plausibly
  IOC-denser and series-skewed, and the unpaired stratum answers "does
  doc-local silver training transfer to documents *without* bundles?"
  The n=7 stratum supports directional observation only, and the paper says so.
- Provenance statement in the paper: training labels machine-derived (STIX /
  external / LLM); eval labels human-curated (Study-1 curation pass); no new
  human annotation performed or required.

## 9. Module plan

| Module | Status | Role |
|---|---|---|
| `ner/stix_silver.py` | new | bundle → gold-schema silver + dropped log |
| `ner/regex_tier.py` | new | span_validators grammars as extractors; CLI: text in → spans out |
| `ner/corpus_map.py` | new | external corpus → Tier-N label mapping + JSONL emit |
| `ner/span_validators.py` | reuse | grammars (both as gate and as Tier D) |
| `ner/annotation_text.py` | reuse | find_token_span verbatim projection |
| `ner/gold_to_training.py` | reuse | unchanged (schema shared by design) |
| `ner/evaluate.py` | reuse | Scorer, both views |
| `ner/finetune_roberta.py`, `finetune_gliner.py` | minor edits | label-space parameterization already exists via checkpoint config |
| `ner/llm_gold.py` | reuse | reference arm only |

Slug join to scrape_cisa: `advisories.stix_path` column (STIX filenames are
title-encoded; the DB column is the reliable map).

## 10. Threats to validity

1. **Small per-class eval n** (threat actor 49, malware family 46 spans) →
   bootstrap CIs, relaxed-F1 secondary, claims stated as sign+CI. Classes
   under ~20 eval spans (cwe 5, cve 18, yara 19 — all Tier D) are pre-declared
   **descriptive-only**: no per-class claims made on them.
1b. **Grammar provenance:** the span_validators grammars predate this study
   (built during Study-1 gold generation, exercised against Study-1 data) and
   are **frozen as-is for Tier D** — any grammar change during Study 2 would
   constitute fitting the deterministic tier to the eval set.
2. **STIX skew:** 52 bundles lean recent/#StopRansomware; silver arms
   inherit that topical bias vs the 66-doc gold set → report per-era splits.
3. **Alias/surface mismatch:** STIX `SILENT CHOLLIMA` vs prose "Andariel";
   verbatim gate drops these (correctly — L2's opposite failure would be
   forcing them in). Drop rate is measured and reported; alias lists narrow it.
4. **License contamination:** APTNER/DNRTI licenses unclear; CyberNER is a
   derivative of them. AnnoCTR (CC-BY-SA) is the only arm whose redistribution
   is clean — released artifacts include only AnnoCTR-derived and self-produced
   data; other corpora are used-not-redistributed with the caveat stated.
5. **Transfer collapse** (survey): augmentation may hurt — that is RQ3's H2′,
   an outcome, not a threat to the design.
6. **Seed variance ~2 points** (L5): 3 seeds on starred arms; deltas smaller
   than seed spread are reported as null.
7. **Eval reuse across many arms:** pre-registered comparisons (this doc),
   val/test discipline, test touched once per arm.
8. **Circularity re-entry via cross-checks:** STIX-derived Tier-D cross-checks
   never modify eval gold — Tier D is evaluated against gold, not merged into it.

## 11. Phases & timeline

| Phase | Work | Depends on | Est. |
|---|---|---|---|
| 0 | stix_silver generator + audit census + go/no-go | — | ~1 day |
| 1 | regex_tier + Tier-D standalone eval (RQ1a); corpus_map + license check | 0 | ~1 wk |
| 2 | Training matrix A/B arms (RQ1b, RQ2) on Colab | 1 | ~1–2 wk |
| 3 | C/D arms (RQ3, RQ4 frontier) | 2 | ~1–2 wk |
| 4 | Analysis, CIs, paper | 3 | ~1 wk |

## 12. Out of scope

Relation extraction / KG construction, actor-name normalization, event
extraction, synthetic text generation (noted as the survey's other open gap;
stretch only), new human annotation campaigns, non-CISA scraping, UNK-cluster
label discovery (Study-1 machinery remains available but is not a Study-2
deliverable).

## 13. Novelty positioning (for the related-work section)

- **Bridges et al. 2013**: structured-DB distant supervision, but on NVD
  descriptions — text that restates the DB fields. Ours: long prose reports
  where the bundle is a lossy, *authored* summary — the hard direction.
- **CyNER 2022**: regex+model *inference-time merge*. Ours: *training-time
  label-space partition*, with the capacity-reallocation effect quantified
  (RQ1-H2 — no prior measurement found in the 41-paper survey).
- **CyberNER 2025**: harmonizes corpora onto STIX as a *taxonomy*. Ours uses
  each document's own STIX *instance data* as supervision — per-doc, not
  per-schema.
- **Minerva 2026** ("standards double as free supervision" via RLVR): same
  thesis, different mechanism — we instantiate it for span supervision.
- Survey open-problems ledger: STIX-derived span supervision for CTI listed as
  unattempted (paper/survey.md §9 / paper/notes/taxonomy.md open-problems
  entries); annotation-budget optimization nearly untreated — one formal
  treatment (LETNER) in 41 surveyed papers (RQ4 addresses both).

## 14. What each outcome means

| Result | Interpretation |
|---|---|
| Phase-0 gate fails on precision | Authored provenance ≠ verbatim presence; paper pivots to RQ1+RQ3+RQ4 (still complete) |
| RQ1-H2 positive | Label-space partition is a free lunch; recommend as default CTI NER practice |
| RQ2: silver ≈ gold on covered classes | Gold budget should be spent *only* on silver-blind classes — changes the economics of CTI NER |
| RQ2: silver ≈ placebo | Doc-locality is inert; STIX is merely a cleaner dictionary — provenance thesis refuted, publish as negative result |
| RQ3: augmentation hurts even class-conditionally | Strongest yet evidence for the survey's fragmentation thesis, now under clean controls |
| RQ4 frontier flat after silver | "Free supervision suffices" headline with measured dollars |

Negative results in any cell are pre-committed for publication — the field's
failure mode (per the survey) is reporting only wins.

## Appendix A — Measured gold label census (2026-07-26)

| Label | Tier | eval (16 docs) | train (66 docs) |
|---|---|---|---|
| attack technique id | D | 217 | 1015 |
| file hash | D | 191 | 775 |
| ip address | D | 124 | 465 |
| email address | D | 61 | 168 |
| tlp classification | D | 20 | 71 |
| yara rule name | D | 19 | 85 |
| cve identifier | D | 18 | 195 |
| cwe identifier | D | 5 | 73 |
| file name | N | 148 | 796 |
| attack technique name | N | 136 | 664 |
| hacking tool | N | 131 | 753 |
| file path | N | 106 | 407 |
| tactic | N | 77 | 380 |
| affected software product | N | 77 | 538 |
| threat actor group | N | 49 | 126 |
| malware family | N | 46 | 190 |
| **Total** | | **1,425** (46% D) | **6,701** (42% D) |
