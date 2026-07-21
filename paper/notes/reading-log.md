# Reading Log — CTI NER Survey

Loop state: which corpus papers have been read and annotated into `bibliography.md`.
Status: `READ` (bibliography entry complete), `PARTIAL` (skimmed, entry stubbed), `UNREAD`.

| # | arXiv ID | Short name | Status | Iteration | Survey sections fed |
|---|----------|------------|--------|-----------|---------------------|
| 1 | 2311.08526 | GLiNER original | READ | 1 | Methods (zero-shot), Background |
| 2 | 2404.07765 | AnnoCTR | READ | 1 | Datasets, Schemas, TTP mapping |
| 3 | 2507.13870 | Label unification | READ | 1 | Schemas, Open problems |
| 4 | 2510.26499 | CyberNER harmonized STIX | READ | 1 | Schemas, Datasets, Background |
| 5 | 2006.15509 | BOND distant supervision | READ | 2 | Methods (weak supervision) |
| 6 | 2311.08010 | Uncertainty-aware teacher | READ | 2 | Methods (weak supervision) |
| 7 | 2408.05149 | AttackER | READ | 2 | Datasets |
| 8 | 2406.07599 | CTIBench | READ | 5 | Evaluation |
| 9 | 2503.23175 | LLMs unreliable for CTI | READ | 5 | Methods (LLM), Open problems |
| 10 | 2507.16852 | SynthCTI | READ | 2 | Methods (augmentation) |
| 11 | 2507.18546 | GLiNER2 schema-driven | READ | 3 | Methods (zero-shot) |
| 12 | 2605.10108 | GLiNER-Relex joint NER+RE | READ | disc-2 | Methods (zero-shot), KG section anchor |
| 13 | 2605.07982 | GLiGuard | READ | 3 | Methods (zero-shot) |
| 14 | 2605.09973 | GLiNER2 PII | READ | 3 | Methods (zero-shot, adjacent domain) |
| 15 | 2502.10825 | MITRE ATT&CK applications survey | READ | 6 | TTP mapping, Background |
| 16 | 2512.19414 | TTPrompt | READ | 6 | TTP mapping, Methods (LLM) |
| 17 | 2601.14556 | MITRE hierarchical classification | READ | 6 | TTP mapping |
| 18 | 2604.02377 | What adversaries are doing (systematic review) | READ | 6 | TTP mapping, Background |
| 19 | 2604.07470 | Beyond single reports | READ | 6 | TTP mapping, Open problems |
| 20 | 2505.09261 | Evolvable memory ATT&CK | READ | 6 | TTP mapping |
| 21 | 2511.01144 | AthenaBench | READ | 5 | Evaluation |
| 22 | 2507.16576 | STIX entity+relationship extraction | READ | 5 | Methods (LLM, data-centric), Beyond NER |
| 23 | 2507.06252 | Adversarial attacks on CTI NER | READ | 7 | Open problems |
| 24 | 2602.17458 | CTI Echo Chamber | READ | 7 | Datasets, Open problems |
| 25 | 2602.00513 | Minerva RLVR CTI LLM | READ | 5 | Methods (LLM), SOTA |
| 26 | 2602.18487 | Million-Label GLiNER bi-encoder | READ | 3 | Methods (zero-shot), SOTA |
| 27 | eswa-2026 (no arXiv) | LETNER label-efficient CTI NER | READ | disc-1 | Methods (zero-shot, weak sup.), Evaluation, Open problems |
| 28 | 2606.01208 | Schema-agnostic CTI KG ontology discovery | READ | 7 | KG section (SOTA) |
| 29 | 2605.16714 | GRID security-text KG construction | READ | 7 | KG section (SOTA) |
| 30 | 2411.08359 | MultiKG multi-source technique KG | READ | 7 | KG section |
| 31 | 2410.21060 | CTINexus LLM CTI KG construction | READ | 7 | KG section |
| 32 | 2407.02528 | Actionable CTI with KGs and LLMs | READ | 7 | KG section |
| 33 | 2405.04753 | AttacKG+ LLM attack KG | READ | 7 | KG section |
| 34 | 2212.10388 | ThreatKG automated OSCTI KG | READ | 7 | KG section (pre-LLM contrast) |
| 35 | 2208.01693 | Cybersecurity entity extraction | READ | 7 | Methods (supervised), Datasets |
| 36 | 2204.04769 | KG-in-cybersecurity review | READ | 7 | KG section (positioning), Related surveys |
| 37 | 2111.07093 | AttacKG technique KG construction | READ | 7 | KG section (pre-LLM contrast) |

| 38 | 2103.03530 | CTI taxonomies/standards/ontologies evaluation | READ | 4 | Taxonomies 2.3 (anchor) |
| 39 | 2512.00857 | Hesperus threat-actor naming taxonomies | READ | 4 | Taxonomies 2.3, Schemas 3 (thesis) |
| 40 | 2509.00081 | Transparent CTI LLMs + domain ontologies | READ | 4 | Taxonomies 2.3 (SOTA) |
| 41 | 2605.31199 | MAECO-Lite malware analysis ontology | READ | 4 | Taxonomies 2.3 (SOTA) |
| 42 | none (Sensors DOI 10.3390/s25247627) | Hard/Easy sample discrimination cybersecurity NER | READ | 9 | Methods (data-centric curriculum) — real paper fetched from MDPI 2026-07-18 (no arXiv preprint exists; the ID previously assigned, 2512.20737, is an unrelated numerical-analysis paper) |
| 43 | 2601.17898 | Assessment of generative NER (output-format effects) | READ | 9 | Methods (LLM generative extraction) — real paper fetched + read 2026-07-18 |
| 44 | 2509.12098 | Hope benchmark contextual entity ambiguity | READ | 9 | Open problems — real paper fetched + read 2026-07-18; note in bibliography: minor pilot study (n=119 tokens, single annotator), cite as directional only |
| 45 | 2404.19192 | BOND-MoE mixture-of-experts NER | READ | 9 | Methods (BOND lineage, ensemble denoising) — real paper fetched + read 2026-07-18 |
| 46 | none (Symmetry DOI 10.3390/sym17050783) | SSNER segment-level CTI NER (SecureBERT_SME) | READ | 9 | Methods (semantic enhancement) — real paper fetched from MDPI 2026-07-18 (no arXiv preprint exists; the ID previously assigned, "2525.05xxx", was never valid) |
| 47 | none (PLOS ONE DOI 10.1371/journal.pone.0315479) | BOND-derived self-training denoising, CVE Vendor/Product | READ | 9 | Methods (weak sup., BOND lineage) — real paper fetched from PLOS ONE 2026-07-18 (no arXiv preprint exists) |
| 48 | 2504.00676 | GLiNER-BioMed biomedical domain variant | READ | 9 | Methods (zero-shot, domain adaptation, bi-encoder) — real ID found via arXiv search 2026-07-18 (the ID previously assigned, "2609.xxxxx", was never valid), fetched + read |

Note: all 7 rows above were fabricated-then-corrected in iteration 8 (2026-07-18, see paper/ISA.md Changelog) and are now genuinely READ as of iteration 9 (2026-07-18, same day, following principal's "fetch those from arxiv" request) — each PDF was fetched from a verified real source (arXiv, MDPI, or PLOS ONE directly), docling-converted, and read in full before the bibliography entries were rewritten a second time.

Note: rows for 2512.19414 (already read iteration 6, see row 16 "TTPrompt") and 2602.18487 (already read iteration 3, see row 26 "Million-Label GLiNER bi-encoder") were duplicated by mistake during iteration 8 and have been removed from this log; the duplicate bibliography entries (which also contained fabricated detail not matching the real, correctly-sourced entries) were deleted 2026-07-18. See bibliography.md and ISA.md Changelog for the full correction record.

## Next iteration plan

Iteration 2 — weak-supervision + datasets batch: BOND (5), Uncertainty-aware teacher (6), AttackER (7), SynthCTI (10).
Iteration 3 — GLiNER family completion: GLiNER2 (11), GLiNER-Relex (12), GLiGuard (13), GLiNER2-PII (14), Million-Label (26).
Iteration 4 — taxonomy/ontology batch (principal-prioritized): 38, 39, 40, 41 — draft full section 2.3.
Iteration 5 — LLM + benchmarks: LLMs-unreliable (9), CTIBench (8), AthenaBench (21), Minerva (25), STIX-extraction (22).
Iteration 6 — ATT&CK/TTP cluster: 15, 16, 17, 18, 19, 20.
Iteration 7 — open-problems batch: adversarial attacks (23), echo chamber (24); gap-driven arXiv searches (ISC-38: source datasets, SecureBERT, recency sweep).
Iteration 8 — KG construction batch A: AttacKG (37), ThreatKG (34), CTINexus (31), AttacKG+ (33) — paradigm contrast pre-LLM vs LLM.
Iteration 9 — KG construction batch B: MultiKG (30), Actionable-CTI (32), Schema-agnostic (28), GRID (29); position against KG review (36); entity-extraction paper (35).
Iteration 10+ — prose deepening, consistency pass, citation audit (ISC-5, 33, 35, 36); discovery sweeps for newly-read anchors (ISC-37).

Each iteration: also run forward-citation sweep for that batch's papers (Semantic Scholar) and reconcile any accepted additions here — see notes/discovery-log.md.

## Notes

- Corpus papers are docling conversions; formulas appear as `<!-- formula-not-decoded -->`. Verify against PDF if a key passage is garbled.
- Check `ls data/papers/*.md` each iteration for newly added papers and reconcile this table (ISC-5).
