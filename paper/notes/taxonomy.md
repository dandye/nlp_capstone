# Method Taxonomy & Open Problems — working notes

Working analytical scaffold for the survey's Methods and Open Problems sections.
Status: v1 after iteration 1 (4/21 papers). Expect restructuring as evidence accumulates.

## Method taxonomy (organizing axis: supervision source × matching mechanism)

```
NER for InfoSec/CTI
├── 1. Rule/dictionary-based
│   ├── Regex for structured IOCs (CVE IDs, hashes, IPs, T-codes)     [CyberNER §II; this repo's annotate_iocs]
│   └── Gazetteers / KB lookup (MITRE ATT&CK entity lists)            [Hanks 2022, Alam 2022 via CyberNER; mitre_lookup.py]
├── 2. Feature-engineered statistical (historical)
│   └── HMM/SVM → CRF as sequence-labeling standard                   [CyberNER §II]
├── 3. Neural sequence labeling (supervised, fixed schema)
│   ├── BiLSTM-CRF (+char features, domain embeddings)                [CyberNER §II; label-unification's testbed]
│   └── Transformer fine-tuning; domain-pretrained encoders
│       (SecureBERT, CySecBERT, DarkBERT) + CRF heads                 [CyberNER §II]
├── 4. Weak/distant supervision                                        [BOND, uncertainty-aware teacher — UNREAD]
│   └── (this repo's ensemble pipeline = distant supervision variant:
│        dict∩NER agreement as silver labels for fine-tuning)
├── 5. Zero/few-shot span matching (open-type, schema-free)
│   ├── GLiNER: BiLM span-type matching in latent space               [2311.08526]
│   └── GLiNER2 / Relex / domain variants                              [UNREAD cluster]
├── 6. LLM-based extraction (generative)
│   ├── Prompted (ChatGPT-style; InstructUIE, UniNER, GoLLIE lineage) [via GLiNER §1]
│   └── CTI-specific prompting (TTPrompt)                              [UNREAD]
│       └── reliability concerns                                       [2503.23175 — UNREAD]
└── 7. Data-centric methods (orthogonal axis — operate on the corpus, not the model)
    ├── Schema harmonization (STIX-anchored mapping)                   [2510.26499]
    ├── Label unification (coarse; largely negative result)            [2507.13870]
    ├── Synthetic augmentation                                          [SynthCTI — UNREAD]
    └── Description-based augmentation (ATT&CK concept text)           [AnnoCTR few-shot finding]
```

**Taxonomy design note (hard-to-vary check):** families 1–6 are distinguished by *where supervision comes from* (rules, features+labels, large labeled corpora, noisy/derived labels, type descriptions, instruction-following) and *how types bind to text* (pattern match, tag transition, token classification, span-type similarity, generation). Family 7 is deliberately orthogonal — data-centric methods compose with any model family. Chronology is incidental; several families coexist in production systems (cf. this repo's 3-layer pipeline = families 1 + 5 ensembled into 4).

## Adjacent task: TTP/ATT&CK mapping (not span NER, but the survey must position it)

- AnnoCTR shows technique *mentions* can be implicit → entity linking beats sequence tagging (micro-F1 ~65 vs NER-style approaches).
- Document-level (rcATT) vs sentence-level (TRAM) vs span-level (AnnoCTR) granularity progression.
- UNREAD cluster (2502.10825, 2512.19414, 2601.14556, 2604.02377, 2604.07470, 2505.09261) will fill this section.

## The annotation-scarcity thesis (candidate central synthesis — euphoric surprise target)

Working claim: **label fragmentation, distant supervision, schema harmonization, synthetic augmentation, and zero-shot NER are all responses to the same root condition: expert CTI annotation is too expensive to produce at scale, so the field keeps inventing ways to avoid needing it.**

Evidence so far:
- AnnoCTR Table 1: nearly every corpus is small (39–1490 docs) AND unlicensed — scarcity is legal as well as economic.
- Label unification fails (Schmidt) because each tiny dataset encodes its annotator's local definitions — fragmentation is a *symptom* of scarcity (no dataset is big enough to become the standard).
- CyberNER's harmonization is a scarcity workaround: manufacture scale by merging.
- GLiNER's zero-shot framing eliminates the labeled-data requirement entirely — types-as-natural-language is annotation avoidance by architecture.
- CONFIRMED iteration 2: BOND/CENSOR derive labels from KBs; SynthCTI manufactures labeled text with LLMs; LETNER architects for minimal labels.
- CONFIRMED iteration 5 (supervision from structure): Minerva — canonical identifiers built for interoperability double as free verifiable rewards; RLVR substitutes existing taxonomy structure for unaffordable annotation. Second route alongside distant supervision.
- CONFIRMED iteration 4 (instance level): Hesperus — vendors cannot converge on actor names because agreement requires sharing private telemetry; fragmentation is a market equilibrium, not carelessness. Same economics keep corpora small/unlicensed.

If this holds across the remaining 17 papers, it becomes the survey's organizing argument in §Introduction and §Open Problems.

## Open problems ledger (candidates; each needs ≥1 paper as evidence — ISC-31)

1. **Schema fragmentation / no standard label set** — Schmidt et al. (failure data), CyberNER (partial fix, lossy via exclusion mapping).
2. **Licensing of corpora** — AnnoCTR Table 1: most datasets legally unusable; blocks replication and commercial application.
3. **Annotation-definition drift between corpora** — 'sample', 'backdoor', 'Dridex' assigned contradictory types across datasets (Schmidt §4).
4. **LLM reliability for CTI extraction** — CONFIRMED: precision 0.76 on real-size reports (vs 0.83-0.89 on sentences), inconsistency across identical prompts, miscalibration both directions (2503.23175). Mitigations exist: task decomposition + fine-tuning (AZERG), RLVR (Minerva), ontology constraints (OntoLogX). No benchmark measures consistency/calibration — sub-problem.
5. **Concept drift / temporal validity** — CONFIRMED for benchmarks AND extraction: evolvable memory (2505.09261) is the extraction-side answer to ATT&CK versioning drift; also adds standard-faithfulness axis (datasets drift from the standard; fitting them propagates inconsistency). Benchmarks: static corpora rot + contaminate; AthenaBench's live-source regeneration (NVD API, ATT&CK STIX, publication windows) is the current fix (2511.01144). Extraction-model drift still pending evolvable-memory paper.
6. **Cross-report aggregation** — CONFIRMED: +26% F1 from aggregating campaign reports, saturation 5-15 reports, but ceilings stay 54.9-78.6 F1; 33.3% of errors confuse same-tactic similar techniques; best method misses 23% of mitigation controls (2604.07470). Dense CISA/MITRE reports contribute most — direct input for principal's corpus source selection.
7. **Implicit mention problem** — techniques described periphrastically ("send phishing e-mails with malicious attachments" → T1566.001); tagging fails, linking partially works (AnnoCTR).
8. **Multi-label entity assignment** — real CTI entities hold multiple functional roles simultaneously; single-label span formulations (incl. LETNER, by its own admission) cannot express this (LETNER §conclusion).
9. **Annotation-budget optimization as a first-class question** — LETNER's PoDR framework is the only corpus paper treating "how much annotation is worth buying" formally; no benchmark evaluates label efficiency (LETNER).
10. **Adversarial robustness of CTI extraction** — placeholder pending 2507.06252.
11. **No CTI-specific relation extraction benchmark** — GLiNER-Relex evaluates on general-domain RE only; its FewRel weakness (100 fine-grained types) warns that ATT&CK-scale CTI relation vocabularies are untested (2605.10108).
12. **Synthetic span-annotated CTI text unattempted** — constraint-driven generation produces winning span detectors in PII (GLiNER2-PII); the STIX-inventory CTI analogue is an open research direction (and a concrete plan candidate for the principal's corpus).
13. **Actor-name normalization unsolved** — 3,287 names, 17 taxonomies, erroneous mappings; entity linking is the mitigation path (Hesperus 2512.00857).
14. **Extraction targets are ontologically confused** — MAEC/STIX conflate endurants and events with measurable reasoning costs (MAECO-Lite 2605.31199); harmonizing onto STIX inherits this.
15. **KG ontology fragmentation** — hypothesis: CTI KG systems each define their own ontology, recapitulating the NER schema problem (§3) one level up; 2026 schema-agnostic/ontology-discovery work (2606.01208) suggests the field noticed. Verify in iterations 7–8.

## Dataset comparison table (skeleton — ISC-28; grows as dataset papers are read)

| Corpus | Size | Entity types | Source texts | License | Notes |
|--------|------|--------------|--------------|---------|-------|
| CyNER | 107k tok / 7.6k ents | 5 | 60 TI reports | open (per CyberNER use) | coarse |
| DNRTI | 176k tok / 36.9k ents | 12–13 | TI reports, gov, GitHub | check | BIO |
| APTNER | 260k tok / 39.7k ents | 21–23 | network-security vendor reports | check | BIOES; fine-grained (MD5, VULID) |
| AttackER | 67–79k tok / 31.1k ents | 18–20 | attack-attribution reports/blogs | check | long spans; STIX-informed (verify in 2408.05149) |
| AnnoCTR | 400 docs (120 cyber-annotated), 12,179 sent | GNE + CyNE + TACTIC/TECHNIQUE | 5 CTI vendor blogs, donated | **CC-BY-SA 4.0** | explicit/implicit; ATT&CK + Wikipedia links |
| CyberNER (harmonized) | 610k tok / 103k ent tokens | 21 (STIX 2.1) | union of first four | public | 16.93% annotation density |
| MalwareTextDB, CTI-Reports, rcATT, CyEnts, CySecED, CASIE, TRAM | — | various | — | mostly none | from AnnoCTR Table 1; cite as landscape |

(Token/entity counts differ slightly between Schmidt Table and CyberNER Table I for AttackER — reconcile when reading 2408.05149.)
