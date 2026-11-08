# Annotated Bibliography — CTI NER Survey

Entry template: **Summary** (what/why) · **Method** (how) · **Findings** (key results, numbers) · **Relevance** (which survey sections; connections to other papers) · **Artifacts** (GitHub/HuggingFace/data releases, license, or "none found" — principal reproduces prior art; this field gates baseline candidacy).

---

## 2311.08526 — GLiNER: Generalist Model for NER using Bidirectional Transformer
Zaratiana, Tomeh, Holat, Charnois (LIPN/CNRS). NAACL 2024.

**Summary.** Compact open-type NER model: instead of generating entities autoregressively (LLM prompting), treats NER as matching natural-language entity-type embeddings against span embeddings in a shared latent space, using a small bidirectional encoder (BERT/DeBERTa).

**Method.** Input = `[ENT] type1 [ENT] type2 … [SEP] text`. BiLM encodes types and text jointly; a 2-layer FFN refines entity-type embeddings; span representations (max span length K=12, keeping linear complexity) are matched to type embeddings via sigmoid dot-product, trained with binary cross-entropy on Pile-NER (44,889 passages, 240k spans, 13k distinct entity types, ChatGPT-annotated). Greedy span decoding, flat or nested, O(n log n).

**Findings.** Zero-shot on 7 OOD NER benchmarks: GLiNER-L (0.3B) averages 60.9 F1, beating ChatGPT (47.5), UniNER-7B (53.7), UniNER-13B (55.6), and GoLLIE (58.0) with orders of magnitude fewer parameters. GLiNER-M (90M) ≈ UniNER-13B. Beats ChatGPT in 8/10 unseen languages.

**Relevance.** Methods §zero-shot — the architecture that makes schema-free CTI NER practical on commodity hardware; the base model fine-tuned by this repo's pipeline (`gliner_medium-v2.1`). Key trade-off vs LLMs: parallel span scoring vs sequential generation; types expressed in natural language → custom CTI labels without retraining. Sets up GLiNER2 (2507.18546), GLiGuard (2605.07982), GLiNER-Relex (2605.10108).

**Artifacts.** Available: github.com/urchade/GLiNER (Apache-2.0, actively maintained, pip-installable); models on HF (urchade/gliner_*); training data: HF Universal-NER/Pile-NER-type. **Prime baseline candidate — already in use in this repo's pipeline.**

---

## 2404.07765 — AnnoCTR: A Dataset for Detecting and Linking Entities, Tactics, and Techniques in Cyber Threat Reports
Lange, Müller, et al. (Bosch CAI, MPI, Uni Augsburg). LREC-COLING 2024.

**Summary.** CC-BY-SA-licensed corpus of 400 commercial cyber threat reports (Intel471, Lab52, Proofpoint, QuoIntelligence, ZScaler; 2013–2022), 120 expert-annotated with cybersecurity NEs, MITRE ATT&CK tactics/techniques (explicit AND implicit mentions), temporal expressions, and entity links to Wikipedia/ATT&CK. First clearly-licensed, document-level, fine-grained ATT&CK-linked corpus.

**Method.** Schema: general NEs (ORG, LOC, SECTOR, TIMEX, CodeSnippet) + cyber NEs (GROUP, MALWARE, TOOL, CONCEPT, TACTIC, TECHNIQUE) with explicit/implicit distinction for tactics/techniques. INCEpTION annotation tool; single domain expert. Baselines: transformer sequence taggers for NER; entity disambiguation models (BLINK/GENRE-style) for technique linking; few-shot experiments augmenting training with ATT&CK concept descriptions.

**Findings.** NER macro-F1 up to ~70% (general entities); technique identification micro-F1 ~65% via entity-linking formulation. ATT&CK concept descriptions are effective augmentation in few-shot. Survey of prior corpora (Table 1): nearly all (MalwareTextDB, CTI-Reports, rcATT, CyEnts, CySecED, CASIE) have no/unclear license — licensing is a structural problem for the field.

**Relevance.** Datasets § (anchor entry + its Table 1 seeds the comparison table, ISC-28); Schemas § (explicit/implicit mention distinction shows entity-vs-concept boundary); TTP mapping § (linking formulation outperforming tagging for techniques). Licensing finding feeds Open Problems.

**Artifacts.** Available: github.com/boschresearch/anno-ctr-lrec-coling-2024 (dataset, CC-BY-SA 4.0 — one of the only legally reusable CTI corpora; directly relevant to principal's corpus-building as both data source and annotation-schema template). Related: TRAM (github.com/center-for-threat-informed-defense/tram, Apache-2.0).

---

## 2507.13870 — Label Unification for Cross-Dataset Generalization in Cybersecurity NER
Jałocha, Schmidt (Johan Hausted), Michelseen (ITU Copenhagen). 2025.

**Summary.** Empirical study of what happens when you merge cybersecurity NER datasets by collapsing labels to a coarse shared set: it mostly fails, and the failure modes are diagnostic of the field's annotation inconsistency.

**Method.** Four datasets (APTNER 260k tokens/21 types; CYNER 107k/5; DNRTI 175k/13; AttackER 79k/18) unified to 4 coarse CyNER labels (Organization, System, Vulnerability, Malware); pairwise 4×4 cross-dataset evaluation with BiLSTM; alternatives: multi-head model (per-dataset output heads, shared embeddings/LSTM) and LST-NER graph-based transfer on BERT.

**Findings.** Cross-dataset span-F1 collapses: off-diagonal 0.01–0.31 vs in-dataset 0.23–0.41. Training on all four unified datasets *hurts* APTNER (-0.11) and CYNER (-0.02) vs single-dataset training — unification noise dominates data-size benefit. Error taxonomy: token-definition discrepancies ('sample'→Malware in DNRTI, O in APTNER; 'backdoor', 'Dridex' Malware vs System), label-definition discrepancies (threat actor→Organization mapping causes false negatives), annotation-span discrepancies (AttackER favors long spans). Multi-head with shared embeddings beats unified training on 2/4 datasets while preserving original label sets. JS-divergence of word/POS distributions correlates with cross-dataset performance (Pearson ≈ -0.74).

**Relevance.** Schemas § centerpiece — the negative result motivating principled harmonization (CyberNER cites and builds on this). Open Problems § (annotation inconsistency as a first-class failure mode). Direct contrast pair with 2510.26499: ad-hoc coarse unification fails where ontology-driven mapping succeeds.

**Artifacts.** Available: github.com/PLtier/NLP-Cyber-NER (unification code + experiment setup; license unverified). Useful less as a baseline than as a reusable cross-dataset evaluation harness for the principal's corpus.

---

## 2510.26499 — CyberNER: A Harmonized STIX Corpus for Cybersecurity NER
Ech-Chammakhy, Motii, Rabii, Azrara, Chbili (UM6P / Deloitte). 2025.

**Summary.** Harmonizes the same four datasets (CyNER, DNRTI, APTNER, AttackER) onto STIX 2.1 as target taxonomy: 50+ disparate source tags → 21 coherent entity types, ~610k tokens, 23,477 sentences, public corpus + benchmark.

**Method.** Five mapping strategies: consolidation (APT/HackOrg/THREAT_ACTOR → Threat-Actor), differentiation (Malware vs Tool vs Software), SCO mapping (IP → IPv4-Addr; FILE/MD5/SHA2 → File), ambiguity resolution by STIX definitions + manual review, exclusion (rare/unclear tags → O). BIOES→BIO normalization, rule-based cleaning, CoNLL-like release format.

**Findings.** Models trained on harmonized corpus gain ~30% relative F1 over naive concatenation of the same data. Related-work synthesis: field progression rules/gazetteers → CRF → BiLSTM-CRF → transformer+CRF, with domain-pretrained encoders (SecureBERT, CySecBERT, DarkBERT). Explicitly frames Jałocha et al. as demonstrating that simplistic merging fails; positions ontology-driven harmonization as the fix.

**Relevance.** Schemas § resolution arm of the fragmentation story; Datasets § (the corpus itself + Table I source stats). STIX 2.1 anchoring connects to this repo's pipeline (STIX-derived annotation) and to practitioner interoperability. Background § inherits its method-era progression. Open question it leaves: harmonization is still lossy (exclusion strategy discards source semantics) — feeds Open Problems.

**Artifacts.** Available: github.com/yasirech-chammakhy/CyberNER (corpus + harmonization code + benchmarking; URL reconstructed — docling split it across lines; verify on first clone). The harmonized corpus is a direct comparison target for the principal's corpus; the mapping rules are reusable for CISA-data harmonization.

---

## eswa-2026 (S0957417426013837) — LETNER: Label-EfficienT Named Entity Recognition for Cyber Threat Intelligence
Wang, Zhang, Bashar, Chandramohan, Nayak (QUT + Oracle Labs). Expert Systems With Applications, 2026. **Not on arXiv — provided by principal; cite by DOI.**

**Summary.** Label-efficient span-based NER for CTI: targets multi-token, sparsely distributed, fine-grained entity patterns under low annotation budgets. Pairs a model contribution with a decision-making contribution — a cost-aware evaluation framework for choosing annotation budgets.

**Method.** Metric learning over span/label embeddings (GLiNER lineage) with two modifications: a Span-CNN-Gate module learning dynamic intra-span representations (explicit critique: GLiNER builds span embeddings by boundary concatenation/mean pooling, failing to model internal token interactions — critical for long, noisy CTI entities like "remote code execution"), and orthogonal regularisation aligning entity-span relations in a shared metric space for similarity-based inference. Cost framework: annotation cost C(m)=am+b vs logarithmic performance P(m); Point of Diminishing Returns found by maximum performance-to-cost gain ratio.

**Findings.** On a complex CTI dataset with 22 fine-grained entity classes (APTNER), significantly outperforms baselines using only 10% of annotated data; ablations confirm Span-CNN-Gate and orthogonality constraint both contribute. Limitations acknowledged: cross-dataset generalisation untested at scale; no multi-label assignment (CTI entities can hold multiple functional roles).

**Relevance.** Methods §5.5 — first corpus paper *extending* the span-matching family specifically for CTI (intra-span modeling as the CTI-specific gap). Open Problems — multi-label entity assignment is a new ledger candidate. Evaluation — the PoDR cost framework is a novel evaluation axis no benchmark paper covers. Strongest direct evidence yet for the annotation-scarcity thesis: the entire paper is architected around minimizing labeled-data demand.

**Artifacts.** None found — extracted text links only baselines (flair, multitask-cyberthreat-detection) and base models (deberta-v3-small, all-MiniLM). No LETNER release; QUT + Oracle Labs. **Reproduction would require reimplementation from the paper's equations** — flag this if LETNER is shortlisted as a baseline; the Span-CNN-Gate + orthogonal regularisation are specified but unreleased.

---

## 2605.10108 — GLiNER-Relex: A Unified Framework for Joint Named Entity Recognition and Relation Extraction
Stepanov, Lukashov, Shtopko (Knowledgator), Kalyanarangan (IDfy). 2026.

**Summary.** Extends GLiNER from span-only NER to joint NER + relation extraction in a single forward pass: one shared encoder represents text, entity-type labels, and relation-type labels together, enabling zero-shot extraction of arbitrary entity AND relation types named at inference time. Explicitly positioned as KG-construction infrastructure (triples out, one call).

**Method.** Input = `[ENT] types… [REL] types… [SEP] text` over DeBERTa-v3; standard GLiNER span scoring for entities; entity-pair construction (all-pairs in released checkpoint, or adjacency-guided pruning with six interchangeable decoders: dot-product, bilinear, MLP, attention, GCN, GAT); relation scoring module inspired by KG-embedding approaches; multi-task loss (entity + adjacency + relation). 2048-word context limit, truncation beyond.

**Findings.** Zero-shot micro-F1 across four RE benchmarks, end-to-end setting: best on DocRED (31.3 vs GPT-5-mini 18.6, GLiNER2 11.7) and CrossRE (18.1), near-parity on CoNLL04 (40.4 vs GPT-5-mini 42.4), weaker on FewRel's 100 fine-grained Wikidata relations (12.5). DocRED result notable: document-level, multi-sentence relational reasoning from a compact encoder. GLiREL (gold entities) included only as a relation-classification ceiling.

**Relevance.** The bridge paper between this survey's NER core and the KG-construction scope: it makes the NER→RE→triples path zero-shot end-to-end within the same model family the CTI community is already adopting. Methods §5.5 extension + anchor of the new KG section. Caveats for CTI: benchmarks are general-domain (no CTI RE benchmark exists — Open Problems candidate); FewRel weakness suggests fine-grained CTI relation vocabularies (ATT&CK-style) may be hard. Cites GLiDRE for document-level and GLiREL as the pipeline alternative.

**Artifacts.** Available: Released "as an open-source Python package with a simple inference API" via the GLiNER ecosystem (github.com/urchade/GLiNER); Knowledgator checkpoints on HuggingFace — exact model ID not in extracted text, verify at hf.co/knowledgator. **Prime baseline candidate for the relation-extraction leg of the principal's corpus work.**

---

## A Cybersecurity NER Method Based on Hard and Easy Labeled Training Data Discrimination
Ye, Wu, Zhang, Ge (Harbin Institute of Technology / Nanyang Technological University). December 2025, *Sensors* 25(24):7627 (DOI 10.3390/s25247627). **READ 2026-07-18 — corrects a prior fabricated version of this entry (invented discriminator architecture, wrong F1 deltas, wrongly assumed proprietary corpus, and a fake arXiv ID 2512.20737 that actually points to an unrelated numerical-analysis paper). No arXiv preprint exists; fetched from MDPI directly. See paper/ISA.md Changelog.**

**Summary.** Cybersecurity NER on CyNER (Alam et al. — the same public MITRE ATT&CK-derived corpus already known via this bibliography's CTIBench entry), testing whether the *hard/easy composition* of a fixed-size training set matters independently of its size. Not weak/distant supervision — CyNER is human-annotated; this paper is about training-set curriculum, not label source.

**Method.** Two-stage difficulty discrimination: (1) a rule-based, model-agnostic sentence-difficulty score summing three interpretable metrics (entity length beyond single tokens, lexical rarity relative to a corpus-derived threshold, entity-type diversity within the sentence) against a data-driven threshold; (2) a DL-based discriminator (an ensemble of the compared backbones) that promotes a provisionally-easy entity to "hard" if ≥2 models misclassify it. Sentences containing ≥1 hard entity join the hard set; the two sets overlap (41.8% of tokens fall in both). Five hard:easy ratios tested (all-easy, all-hard, 1:2, 1:1, 2:1) at constant total entity count, on three lightweight backbones (BERT-base-uncased, ALBERT-base-v2, MobileBERT — Table 2's stated set; Section 4's discussion instead references "MiniLM" in one place, an inconsistency in the paper itself worth flagging rather than silently resolving). WordNet-based augmentation targets the corpus's severely sparse Vulnerability class (48 test instances vs. 1490 for the most common type).

**Findings.** 1:1 hard:easy consistently wins on F1/recall across all three backbones and 5 seeds (95% CI widths generally <0.06) — confirms the one claim available before reading. All-easy training inflates precision but hurts recall/F1: models undertrained on complex spans. Base full-dataset performance: BERT-base F1 0.66, MobileBERT 0.62, ALBERT 0.55 (Table 3) — ALBERT is weakest on the full set but the Discussion claims it "achieved the strongest overall performance," a tension between sections that a closer read of the ratio-experiment figures (not fully captured in this pass) would need to resolve. Augmentation is necessary specifically for sparse types: large models capture rare entities without it, small models don't.

**Relevance.** Methods §5.7 (data-centric) — training-set *composition* as a lever independent of both architecture and label source, complementary to this bibliography's other data-centric entries (SynthCTI manufactures text; this paper reweights existing text). Directly actionable for this repo's own `create_training_data.py`, which already implements a related idea (dict-only spans forced as hard negatives) — this paper's rule-based difficulty score is a more principled way to decide *which* weak-labeled chunks deserve oversampling than the current ad hoc dict∩NER-agreement split. Caveat: results are on human-annotated CyNER, not weak/distant labels, so the transferability of "1:1 hard:easy" to a noisy-label setting like this repo's is a hypothesis, not something this paper tested.

**Artifacts.** None found — no repo/code link in the paper.

---

## 2601.17898 — Assessment of Generative Named Entity Recognition in the Era of Large Language Models
Zhan, Wang, Huang (Shenzhen University). January 2026. **READ 2026-07-18 — corrects a prior fabricated version of this entry (wrong authors/institution/findings; see paper/ISA.md Changelog).**

**Summary.** Systematic evaluation of open-source LLMs (LLaMA, Qwen, Granite, Gemma families) on generative NER — output-as-text rather than token classification — across flat (CoNLL2003, OntoNotes5.0) and nested (ACE2005, GENIA) benchmarks. Central question: does output *format* determine whether generative NER is competitive with encoder taggers.

**Method.** Five output formats compared: Inline Bracketed, Inline XML, and three JSON variants (category-grouped, occurrence-indexed, character-offset). Parameter-efficient fine-tuning of 8 open LLMs; error taxonomy (8 types) via case study against BERT-MRC; a held-out general-capability check (DROP and others) before/after NER instruction tuning.

**Findings.** Output format is decisive: Inline Bracketed/XML average 91.9/82.9 F1 (flat/nested) vs. offset-based JSON's **53.9/34.5** — asking a generative model to emit precise character offsets collapses performance, while natural-language-shaped inline tagging does not. With the best format, LLaMA3.1-8B (93.85 F1) beats every pretrained baseline on CoNLL2003; Gemma2-9B beats BERT-MRC on ACE2005. LLMs still lag specialized models in the low-resource biomedical domain (GENIA, -4.02 F1 vs. best baseline) — general capability doesn't transfer to domains starved of training signal. NER instruction-tuning does not degrade general capability, and improves span-extraction-adjacent tasks (DROP, +25.5 to +45.3 F1).

**Relevance.** Directly explains a finding already documented in this repo's own pipeline: `scraper/frontier_llm_utils.py`'s critical-invariants note that Gemini's *returned* character offsets are wrong ~93% of the time, so extraction falls back to text search. This paper shows that's not an implementation quirk of one model — offset-based extraction is *structurally* the worst format for generative NER, independent of model or domain (53.9 vs 91.9 F1, the largest gap in the paper). Methods §5.6 (LLM-based generative extraction) — direct, quantified evidence for prompt/output-format as a first-class variable, not a footnote; strengthens RQ4-style fine-tuned-vs-LLM framing in the capstone with a mechanism, not just an outcome. The GENIA low-resource-domain gap is a data point for CTI (also low-resource) on why zero-shot LLM extraction underperforms fine-tuned encoders there.

**Artifacts.** Available: github.com/szutera/LLMs4NER (code + data, per paper).

---

## 2404.19192 — BOND-MoE: Mix of Experts Language Model for Named Entity Recognition
Chen (UIUC), Li (UIUC), Song (Columbia), Guo (UCSD). April 2024. **READ 2026-07-18 — corrects a prior fabricated version of this entry (invented specifics not grounded in any source); confirmed real via arXiv abstract page before reading. Short paper (2pp, IEEE workshop format).**

**Summary.** Extends BOND (2006.15509) with a Mixture-of-Experts layer: instead of one BERT fine-tuned on distant labels, K experts are trained on disjoint document subsets (hard-EM assignment) plus a fairness constraint preventing all documents collapsing onto one expert, then the ensemble self-trains on pseudo-labels as in BOND's second stage.

**Method.** Document-level (not token-level) expert assignment — a whole document goes to the expert with highest average posterior across its tokens, avoiding split-entity incoherence. Fair assignment via Sinkhorn matrix scaling (marginal constraints on both document-exposure and expert-utility axes) to stop degenerate single-expert collapse. Evaluated on 5 general-domain DS-NER benchmarks (CoNLL03, Twitter, OntoNotes5.0, WebPage, Wikigold) against BiLSTM-CRF, AutoNER, LRNT, ConNet, and BOND itself.

**Findings.** Mixed, not a clean win: BOND-MoE beats BOND on CoNLL03 (79.31 vs 77.12), WebPage (64.11 vs 63.69), and Wikigold (56.59 vs 55.76), but is marginally *worse* on Twitter (47.76 vs 48.07) and OntoNotes (71.00 vs 71.09). Ablation (Table II) shows self-training contributes the largest single gain of the three components (MoE, fair-assignment, self-training); dropping fair-assignment hurts more than dropping MoE alone, i.e. the assignment mechanism carries more of BOND-MoE's benefit than the expert-ensembling idea by itself.

**Relevance.** Methods §5.4 — another node in the BOND lineage (BOND → SCDL → ATSEN → CENSOR → BOND-MoE), pursuing noise-reduction via ensembling experts on document subsets rather than CENSOR's uncertainty-calibration route. Directly relevant to this repo's own BOND replication (`external/bond/`): where this paper ensembles multiple experts over subsets of the *same* weak-labeled corpus, our replication instead compares different *architectures* (RoBERTa-base/large, SecureBERT) trained on the *full* corpus each — a complementary axis of the same "how do you get more signal out of noisy distant labels" question, worth a sentence connecting the two in the survey's weak-supervision discussion. Caveat: general-domain only, no CTI application attempted, and the win margin (≤1.6% F1 on the paper's own framing) is thin enough that BOND-MoE should be described as a mixed/marginal result, not a clear improvement.

**Artifacts.** None found — no repo link in the paper.

---

## Prior biomedical NER papers (distant supervision, cited in principal's message)

Two entries referenced as biomedical distant-supervision NER:
- **"Named Entity Recognition for Cancer Immunology Research Using Distant Supervision"** (Trieu et al., BioNLP 2022) — **RESOLVED 2026-07-22 (Sweep 6): retrieved and fully annotated below** (`acl-2022.bionlp-1.17`). Note the framing correction: the paper does *not* build on or extend BOND — it cites Liang et al. 2020 once, in Related Work, as adjacent prior art. It is a UniProtKB-dictionary distant-supervision method in its own right, not a BOND adaptation.
- **"Knowledge-Driven Drug-Use Named Entity Recognition with Distant Supervision"** (NSF grant cited; no arXiv/DOI provided) — still deferred pending a URL.

---

## 2006.15509 — BOND: BERT-Assisted Open-Domain NER with Distant Supervision
Liang, Yu, Jiang, Er, Wang, Zhao, Zhang (Georgia Tech). KDD 2020.

**Summary.** Canonical distant-supervision NER framework: generate labels by matching text against knowledge bases (Wikidata + gazetteers), then train through the noise. Establishes the two failure modes all DS-NER work fights — incomplete annotation (KB coverage gaps → false O labels) and noisy annotation (ambiguous matches, e.g. 'Liverpool' city vs club).

**Method.** Two stages: (1) fine-tune RoBERTa on distant labels with aggressive early stopping (regularization against overfitting label noise); (2) drop distant labels entirely — teacher-student self-training on pseudo soft-labels, confidence-based sample selection, teacher updated from early-stopped student each iteration. Distant labeling: POS + rules to find candidates, SPARQL against Wikidata for types, multi-source gazetteers.

**Findings.** KB-matching alone is weak in open domain (CoNLL03 F1 59.6, Tweets 35.8 — vs 70+ in biomedical where gazetteers are clean). BOND beats prior DS-NER methods on all 5 benchmarks. Early stopping is the load-bearing trick in stage 1.

**Relevance.** Methods §5.4 foundation — the framework CTI distant supervision builds on. Direct architectural ancestor of this repo's pipeline: STIX-bundle/MITRE matching is exactly BOND-style distant labeling with cleaner (domain) gazetteers; the biomedical-vs-open-domain quality table predicts CTI gazetteer matching sits in the favorable regime. Lineage: BOND → SCDL → ATSEN → CENSOR (2311.08010).

**Artifacts.** Available: github.com/cliang1453/BOND (code + the distantly-labeled datasets). Baseline candidate for the distant-supervision leg of the principal's corpus experiments.

---

## 2311.08010 — Uncertainty-Aware Teacher Learning + Student-Student Collaborative Learning (CENSOR)
Si, Hu, Zhao, Zeng, An, Cai, Chang (PKU + Tencent). Findings of ACL 2024.

**Summary.** Latest refinement of the BOND lineage. Core critique: teacher networks are poorly calibrated, so confidence-thresholded pseudo-label selection (BOND, SCDL, ATSEN) admits high-confidence *wrong* labels and propagates errors.

**Method.** Two teacher-student pairs. (1) Uncertainty-aware selection: K stochastic forward passes (dropout) per token; prediction variance = uncertainty; keep pseudo-labels that are high-confidence AND low-uncertainty. (2) Student-student collaboration: each student transfers its small-loss (likely-clean) pseudo-labels to the other student, so mislabeled samples can be *corrected* rather than merely masked. EMA teacher updates.

**Findings.** Average +1.87 F1 over SOTA DS-NER across CoNLL03/OntoNotes5.0/Webpage/Wikigold/Twitter. The calibration critique is empirically grounded — confidence alone is an unreliable correctness signal.

**Relevance.** Methods §5.4 — the current SOTA shape of DS-NER denoising. Directly applicable critique for this repo's pipeline: ensemble agreement (dict ∩ NER) is also a confidence-style heuristic; uncertainty estimation over GLiNER outputs is an unexplored upgrade path worth naming in the survey's case study. Open Problems: calibration of extraction models is unmeasured in CTI.

**Artifacts.** Available: github.com/PKUnlp-icler/CENSOR.

---

## 2408.05149 — AttackER: Enhancing Cyber-Attack Attribution with an NER Dataset
Deka, Rajapaksha, Rani, Almutairi, Karafili (Southampton). 2024.

**Summary.** First NER dataset purpose-built for cyber-attack *attribution*: 18 entity types derived from STIX 2.1 (14 objects kept, Tool and Identity split into general/attack and general/victim subclasses, plus non-STIX IMPACT and ATTACK_MOTIVATION from an attribution ontology). 2,640 sentences, 7,026 entities from 217 expert reports (Mandiant, Malwarebytes, MITRE, Securelist, TrendMicro).

**Method.** Manual then semi-automatic annotation. Distinguishing design choice: annotations deliberately span phrases and whole sentences (COURSE_OF_ACTION, MALWARE_ANALYSIS, IMPACT) to capture attribution context — not just noun-phrase entities. Baselines: spaCy, HF transformer taggers, and instruction-fine-tuned LLMs (GPT-3.5, Llama-2, Mistral-7B); fine-tuned LLMs perform best.

**Findings.** Fine-tuned LLMs outperform encoder taggers on these long, context-heavy entity types — the inverse of the usual encoder-wins pattern, plausibly because sentence-length spans suit generative extraction. Positions itself against DNRTI/APTNER/CyNER as attribution-focused rather than IOC-focused.

**Relevance.** Datasets § (comparison table row — resolves the 67k/79k token discrepancy question and explains Jałocha et al.'s long-span anomaly: AttackER's spans are long *by design*). Schemas § — second STIX-anchored schema after CyberNER, but with attribution extensions: evidence STIX alone doesn't cover analyst needs. TTP/attribution framing feeds §6.

**Artifacts.** Available: dataset zenodo.org/records/10276922; models + data huggingface.co/Cyber-ThreaD. License: check Zenodo record (CC-BY expected, verify before corpus reuse).

---
## 2507.16852 — SynthCTI: LLM-Driven Synthetic CTI Generation to Enhance MITRE Technique Mapping
Ruiz-Ródenas, Pujante Sáez, García-Algora, Rodríguez Béjar, Blasco, Hernández-Ramos (U. Murcia + UPM). 2025.

**Summary.** Data augmentation for ATT&CK technique mapping (sentence-to-technique classification, not span NER): generate synthetic CTI sentences for underrepresented techniques with semantically guided LLM prompts. Attacks the class-imbalance half of the annotation-scarcity problem (CTI-to-MITRE and TRAM both have long-tail technique distributions).

**Method.** Per technique class: embed sentences (all-MiniLM-L6-v2), cluster with HDBSCAN, extract per-cluster features — few-shot exemplars, LDA topics, KeyBERT keyphrases, WordNet synonym expansions, tone (Flesch/Gunning-Fog buckets), text-type stats — and compose structured prompts for Gemma-3 4B to generate class-faithful synthetic sentences. Augmented data fine-tunes ALBERT/DistilBERT/BERT/SecureBERT.

**Findings.** Consistent macro-F1 gains: ALBERT 0.35 to 0.52 (+48.6% relative); SecureBERT 0.4412 to 0.6558. Headline: small augmented models beat larger unaugmented ones — augmentation buys more than architecture at this data scale.

**Relevance.** Methods §5.7 (data-centric) — the synthetic arm of the annotation-scarcity response, complementing harmonization (manufacture scale from existing labels) and distant supervision (derive labels from KBs): SynthCTI manufactures the labeled text itself. TTP mapping §6 (its target task). Caveat for the survey: gains are on classification, not span NER; synthetic span-annotated text is harder and remains open.

**Artifacts.** Partial: paper links a dessertlab GitHub org (URL truncated in extraction — likely the CTI-to-MITRE dataset source); no clearly named SynthCTI release found in extracted text. Verify before baseline shortlisting; pipeline is reimplementable from components (HDBSCAN + KeyBERT + LDA + Gemma).

---

## 2507.18546 — GLiNER2: An Efficient Multi-Task Information Extraction System with Schema-Driven Interface
Zaratiana, Pasternak, Boyd, Hurn-Maloney, Lewis (Fastino AI). 2025.

**Summary.** Unifies NER, text classification, and hierarchical structured extraction in one 205M encoder with a declarative schema interface — the GLiNER family's answer to its own fragmentation (GLiREL, GLiClass, domain variants each required separate models). Context window grows 512 to 2048 tokens; label *descriptions* supported alongside label names; multiple tasks compose into a single forward pass.

**Method.** Schema serialized into the input sequence (task prompt + separator + text); same span-type matching core as GLiNER. Trained on 254k examples: 136k real documents (news, Wikipedia, legal, PubMed, arXiv) GPT-4o-annotated, plus 119k GPT-4o synthetic examples targeting business/personal formats.

**Findings.** Zero-shot CrossNER 0.590 avg vs GPT-4o 0.599 (dedicated GLiNER-M still leads at 0.615 — multi-task generality costs a few NER points). Best open-source zero-shot classification average (0.72). CPU latency constant in label count (DeBERTa-style per-label inference is 6.8x slower at 20 labels).

**Relevance.** Methods 5.5 — the schema-driven turn: extraction tasks defined as data, not architecture. For CTI: label descriptions allow encoding ATT&CK technique *definitions*, not just names — directly relevant to the implicit-mention problem (AnnoCTR found description augmentation effective; GLiNER2 makes descriptions first-class inputs). Hierarchical schemas suit STIX object structures.

**Artifacts.** Available: github.com/fastino-ai/GLiNER2 (Apache 2.0, pip install gliner2), pre-trained weights on HuggingFace. Baseline candidate.

---

## SSNER — Threat Intelligence Named Entity Recognition Based on Segment-Level Information Extraction and Similar Semantic Space Construction
Chen, Deng, Zhang, Zheng, Jiang (China West Normal University). May 2025, *Symmetry* 17(5):783 (DOI 10.3390/sym17050783). **READ 2026-07-18 — corrects a prior fabricated version of this entry (invented method detail and a self-evidently invalid arXiv ID "2525.05xxx" — arXiv has no year 2525). No arXiv preprint exists; fetched from MDPI directly. See paper/ISA.md Changelog.**

**Summary.** Targets two specific, well-diagnosed traditional-NER failure modes in CTI text: (1) sequence taggers lose multi-token entities because standard masking treats tokens independently, and (2) a single semantic representation can't disambiguate polysemous entities (the same word meaning different things in different CTI contexts). Retrains **SecureBERT** — the same domain-pretrained backbone this repo's own capstone is independently fine-tuning — as the base encoder.

**Method.** Two components stacked on SecureBERT: **SME** (Segment Masking Enhancement) modifies BERT's MLM mask mechanism to mask *contiguous random-length segments* rather than independent tokens during a threat-intel-corpus retraining pass, teaching the model to represent multi-token spans coherently (yielding "SecureBERT_SME"). **SCE** (Semantic Collaborative Embedding) filters a candidate set of semantically similar words per entity mention and fuses them via self-attention into a compound representation, intended to separate senses of the same polysemous string. Evaluated on two established public CTI NER benchmarks: DNRTI and Bridges et al. — both already in this survey's dataset comparisons.

**Findings.** DNRTI: SSNER F1 86.12%, beats the next-best baseline NER4CTI (85.34%, +0.78%) and plain BERT+BiLSTM+CRF (82.04%) substantially; the paper's own BERT-only and SecureBERT_SME-only ablation rows (78.92%, 81.22%) show most of the gain needs both components together. Bridges et al.: SSNER F1 96.02%, beating the prior best FIEBD (94.56%, +1.46% — this is the one number the original one-line description got right) and DKNER (93.92%). Ablation (Table 9): removing SME costs -2.88% F1 (DNRTI) / -3.40% (Bridges); removing SCE costs -1.60% / -2.90% — both components matter, SME slightly more. Per-entity results correlate with multi-token share: DNRTI's "Way" (70% multi-token) and "Features" (72% multi-token) hit F1 0.95/0.97, among the model's best categories — direct evidence the SME mechanism is doing what it claims.

**Relevance.** Methods §5.3/5.4 (supervised sequence labeling / semantic enhancement) — a concrete, ablated demonstration that domain-pretrained-backbone-plus-architectural-modification beats plain fine-tuning on two real CTI benchmarks, with SecureBERT specifically as the base. Directly actionable for this repo's own SecureBERT fine-tuning run (`external/bond/`, in progress as of this correction): SSNER's SecureBERT_SME-only ablation rows (81.22% DNRTI, 93.32% Bridges, before the SCE polysemy module) are a useful sanity-check ceiling for what a modified SecureBERT can reach on CTI NER, and the paper's own plain-SecureBERT-finetuning baseline (not separately broken out from BERT-finetuning in the table) suggests domain pretraining alone gives a smaller boost than the segment-masking retraining does. The multi-token/boundary problem SME targets is a real, cited gap this repo's own weak-supervision pipeline hasn't specifically addressed (spans are matched longest-first but not trained toward boundary coherence).

**Artifacts.** None found — no repo/code link in the paper.

---

## Improved Self-Training-Based Distant Label Denoising Method for Cybersecurity Entity Extractions
Zhang, Wang, Li, Hao, He, Lan, Yang, Ye. December 2024, *PLOS ONE* (DOI 10.1371/journal.pone.0315479). **READ 2026-07-18 — corrects a prior fabricated version of this entry (the general shape happened to be roughly right, but specific mechanism/numbers were invented, not sourced); no arXiv preprint exists, fetched from PLOS ONE directly. See paper/ISA.md Changelog.**

**Summary.** Distant supervision + self-training denoising for cybersecurity NER, scoped narrowly to two entity types — Vendor and Product — extracted from CVE vulnerability descriptions. Same problem family as BOND (2006.15509): noisy weak labels, denoise via self-training.

**Method.** Distant labeling via RMP: Reverse Maximum Matching against two hand-built cybersecurity dictionaries, constrained by POS tags (compared against plain forward matching, FMM, as an ablation). Denoising via IST (Improved Self-Training): select high-confidence text first, train an initial model on it, then a teacher-student loop with *weight update constraints* (not just confidence thresholding) explores labels for the low-confidence remainder. Evaluated against 5 backbones (BiLSTM-CRF, LSTM-CNN, BiLSTM-CNN-CRF, RoBERTa, RoBERTa-wwm-RDCNN-CRF) under distant-only vs. full-supervision ceilings.

**Findings.** Dataset: 934 CVE descriptions from NIST NVD, 747/187 train/test sequences, Vendor/Product only (764/2630 and 185/655 entities respectively) — a much narrower scope than a general CTI entity schema. IST improves F1 over raw distant labels by +3.5% (Vendor) and +3.35% (Product) averaged across the 5 backbones; largest single gains BiLSTM-CRF +4.35% (Vendor), BiLSTM-CNN-CRF +3.95% (Product). RoBERTa-wwm-RDCNN-CRF is the strongest backbone throughout and lands closest to the full-supervision ceiling after IST (88.72/85.09 F1 vendor/product vs. 94.45/90.80 full-supervision ceiling) — pretrained transformer backbones generalize better under self-training than the LSTM/CNN family, consistent with BOND's own original finding.

**Relevance.** Methods §5.4 — a real, CTI-scoped instantiation of BOND-style denoising, though scoped to only 2 entity types (not the 16-label schema this repo or most CTI NER work targets) and reliant on hand-built dictionaries rather than STIX/MITRE structured sources. Directly comparable to this repo's own BOND replication (`external/bond/`): both apply BOND-family self-training to CTI-adjacent weak labels; this paper's RoBERTa-family backbone winning is an independent data point supporting what this repo's own capstone experiments (RoBERTa vs. GLiNER architecture comparison) are separately finding. The paper's self-acknowledged limitation — narrow lexicon coverage limits label-type coverage — is exactly the scalability question a STIX/MITRE-anchored dictionary (as used in this repo) is designed to answer at greater scope.

**Artifacts.** None found — no code/data repository link in the paper; PMC/PLOS ONE page is open access for the paper itself, not for any released implementation.

---

## 2504.00676 — GLiNER-BioMed: A Suite of Efficient Models for Open Biomedical Named Entity Recognition
Yazdani, Stepanov, Teodoro (U. Geneva / Knowledgator). 2025; *Bioinformatics* 42(6), 2026. **READ 2026-07-18 — corrects a prior fabricated version of this entry (self-evidently invalid arXiv ID "2609.xxxxx" and invented numbers; real ID found via arXiv search, verified against the Bioinformatics publication page before reading; see paper/ISA.md Changelog.**

**Summary.** Domain-adapts the GLiNER family (both uni-encoder and the bi-encoder variant already in this bibliography, 2602.18487) to biomedicine via a synthetic-data pipeline: distill a large biomedical LLM's annotation behavior into a smaller model, generate high-coverage synthetic biomedical NER data, pre-train GLiNER on that, then fine-tune on curated general-domain + biomedical data.

**Method.** Two architectures (uni-encoder: joint text+label attention, O((|labels|+|text|)²); bi-encoder: separate text/label encoders, label embeddings cacheable, O(|text|²) online cost — the same complexity argument as the Million-Label bi-encoder paper), each at small/base/large scale. Evaluated zero-shot and few-shot on 8 human-annotated biomedical benchmarks (TAC, CADEC, N2C2 2018, BC5CDR, BioRED, CHIA, Biomed NER, NCBI Disease — 10,918 passages, 85,959 mentions, 58 entity types) against GLiNER baselines, NuNER-Zero, and generative LLM baselines (OpenBioLLM, Qwen3, UniNER-7B, PP-UIE). Statistical testing throughout: Wilcoxon signed-rank on per-passage F1, not just point estimates.

**Findings.** GLiNER-BioMed-large: 59.77% zero-shot micro-F1, +5.96 points over the next-best baseline GLiNER-v2.5-large (p<0.001); beats UniNER-7B (the strongest generative baseline) by 11.22 points despite far fewer parameters. GLiNER-BioMed-small matches GLiNER-v2.5-large's performance at 1/7th the parameters (p>0.05, no significant difference). The bi-encoder's advantage is scale-dependent, not uniform: it beats the uni-encoder at small (+4.40 F1) and base (+3.94 F1) scales but *loses* to it at large scale (-4.87 F1) — the paper's own hypothesis is that doubled encoder capacity helps capacity-starved small models but stops mattering once the uni-encoder has enough capacity on its own.

**Relevance.** Methods §5.5/5.7 — direct evidence for exactly the recipe this repo's own pipeline uses (fine-tune GLiNER on domain-specific weak/synthetic labels), replicated with more statistical rigor (Wilcoxon tests, 8 benchmarks) in an adjacent low-resource specialist domain. The synthetic-data-generation-then-fine-tune approach is a concrete alternative worth comparing against this repo's dictionary/MITRE-ensemble weak supervision — GLiNER-BioMed manufactures its training text, ours derives labels from real CISA text. The bi-encoder scale-dependent result is a caution for any future CTI bi-encoder work (2602.18487's throughput gains may not come with the same F1 story at every scale). Cross-reference: this is the second paper in the corpus (after 2602.18487) independently validating the uni/bi-encoder split as a live research direction, not a one-off.

**Artifacts.** Available: github.com/ds4dh/GLiNER-biomed (code, data, and training pipelines, per paper's own claim).

---

## 2605.07982 — GLiGuard: Schema-Conditioned Classification for LLM Safeguard
Zaratiana, Newhauser, Hurn-Maloney, Lewis (Fastino Labs). 2026.

**Summary.** GLiNER2's schema-conditioned encoder adapted to LLM content moderation: prompt/response safety, refusal detection, 14 harm categories, and 11 jailbreak strategies evaluated in one non-autoregressive forward pass from a 0.3B model.

**Method.** Task definitions, label names, and label descriptions serialized into the input with task/label delimiter tokens; hard decision rules compose the final verdict (detected refusal overrides response safety; detected jailbreak strategy overrides prompt safety).

**Findings.** Within 1.7 F1 of the strongest 7B-27B decoder-based guard on prompt safety across nine benchmarks while 23-90x smaller; up to 16x throughput and 17x lower latency.

**Relevance.** Methods 5.5 — evidence of the schema-conditioned encoder paradigm's reach beyond extraction into multi-aspect classification; the architectural argument (classification reformulated as generation wastes billions of parameters) parallels the survey's GLiNER-vs-LLM-extraction framing. Security-adjacent (jailbreak taxonomy) but not CTI extraction — cite for family completeness, not as a CTI method.

**Artifacts.** Available: github.com/fastino-ai/GLiGuard (code + models).

---

## 2605.09973 — GLiNER2-PII: A Multilingual Model for PII Extraction
Zaratiana, Lewis, Hurn-Maloney (Fastino Labs). 2026.

**Summary.** GLiNER2 fine-tuned for 42 fine-grained PII types (7 semantic groups, nested/overlapping spans), trained *entirely* on synthetic data: 4,910 multilingual examples from a constraint-driven generation pipeline (Pioneer Agent framework).

**Method.** Constraint-driven synthesis: programmatic constraints from the label inventory (entity-type counts, exclusions, at-least-one rules) plus diversity constraints inferred from the task description (document type, locale, register) sampled per example and fed to a frontier LLM at temperature 0.01, producing span-annotated text across 7 languages and formats (chat logs, KYC forms, invoices, credential files).

**Findings.** Highest span-level exact-match F1 on the SPY benchmark (0.471 avg), beating OpenAI Privacy Filter and three GLiNER-based detectors; recall 0.68-0.72 (the metric that matters for redaction). Purely synthetic training transferred to naturally occurring text.

**Relevance.** Methods 5.7 — the load-bearing evidence that synthetic *span-annotated* training data is feasible: directly revises this survey's earlier caveat that span-level synthesis "remains open." The constraint-driven recipe is domain-transferable in principle — CTI's analogue would be generating annotated threat-report text from a STIX-derived label inventory; nobody has done it (Open Problems candidate, and a concrete research direction for the principal's corpus). Adjacent domain (PII not CTI), so cite as transfer evidence, not CTI SOTA.

**Artifacts.** Available: model hf.co/fastino/gliner2-privacy-filter-PII-multi; code via github.com/fastino-ai/GLiNER2. Synthesis framework (Pioneer Agent, 2604.09791) is separate — check its release if replicating the data pipeline.

---

## 2602.18487 — The Million-Label NER: Breaking Scale Barriers with GLiNER Bi-Encoder
Stepanov, Shtopko, Vodianytskyi, Lukashov (Knowledgator). 2026.

**Summary.** Decouples GLiNER's joint encoding into a dedicated label encoder and context encoder. Label embeddings are computed once, cached in a vector store, and reused — removing the context-window bottleneck on label count and making inference complexity independent of whether the schema has 10 or 10,000 entity types.

**Method.** Two independent transformers (heterogeneous backbones allowed — fast text encoder + semantically rich sentence-transformer label encoder); optional cross-attention fusion layer to recover cross-modal interaction; label retrieval as nearest-neighbor search. GLiNKER: a DAG-based entity-linking framework over the bi-encoder (mention extraction, candidate generation from KBs like Wikidata, disambiguation).

**Findings.** SOTA zero-shot 61.5% micro-F1 on CrossNER; 2-3x faster than uni-encoder GLiNER at dozens of labels, up to 130x throughput at 1024 labels.

**Relevance.** Methods 5.5 — resolves the exact bottleneck CTI label inventories hit: ATT&CK has ~600 technique/sub-technique labels, MITRE's entity lists run to thousands of names, and joint encoding caps practical schemas far below that. Also reframes this repo's Layer-2 MITRE gazetteer lookup as a candidate bi-encoder retrieval problem (semantic matching instead of string matching). GLiNKER's KB-linking pipeline is the architectural bridge to the survey's KG section.

**Artifacts.** Available: Knowledgator releases via github.com/urchade/GLiNER ecosystem + hf.co/knowledgator; GLiNKER framework named in paper — verify exact repo URL on first use.

---

## 2103.03530 — Cyber Threat Intelligence Model: An Evaluation of Taxonomies, Sharing Standards, and Ontologies within CTI
Mavroeidis, Bromander (U. Oslo / mnemonic). EISIC 2017, updated v5 2023.

**Summary.** The canonical evaluation of the CTI knowledge-representation landscape. Builds a CTI model around the 5W1H of threats (who/what/why/where/when/how, plus courses of action and technical indicators) and scores existing taxonomies, sharing standards, and ontologies for conceptual coverage and expressivity.

**Method.** Two evaluation models (CTI model + detail/abstraction layers); systematic coverage scoring of the standards inventory (STIX, MAEC, and the taxonomy/ontology efforts of the era: UCO, daedafusion cyber-ontology, security-metrics ontologies, CASE).

**Findings.** Damning and durable: little focus on comprehensive CTI ontology design; existing efforts "not thoroughly designed, non-interoperable, ambiguous, and lacking proper semantics and axioms for reasoning." Specific barriers: concept ambiguity blocking integration, prose-over-vocabulary undermining queryability, missing inter-concept relationships, minimal semantic axioms for consistency checking.

**Relevance.** Section 2.3 anchor — establishes both the standards inventory and the verdict that the survey's later sections confirm empirically: CyberNER/Schmidt show the *label-schema* consequences, Hesperus shows the *naming* consequences, and the KG section's ontology fragmentation is the same disease. The 2017-to-2023 persistence of these findings is itself evidence (the field has known and not fixed it).

**Artifacts.** Survey paper, no code of its own; it catalogs ontology repos: github.com/Ebiquity/Unified-Cybersecurity-Ontology, github.com/casework/case, github.com/daedafusion/cyber-ontology.

---

## 2512.00857 — Hesperus is Phosphorus: Mapping Threat Actor Naming Taxonomies at Scale
Roa, Suarez-Roman, Tapiador (UC3M). 2025.

**Summary.** Large-scale empirical study of threat-actor naming inconsistency across CTI vendors: the same group is APT29 here, Cozy Bear there, Midnight Blizzard elsewhere. Introduces HiP, a methodology for normalizing, integrating, and clustering TA names referring to the same entity.

**Method.** Graph analysis over 15 sources: 13,371 CTI reports, 17 vendor taxonomies, 3,287 TA names, 8 inter-vendor mappings. Name-graph clustering plus error analysis of existing mappings.

**Findings.** Aliases concentrate on a small subset of TAs; proliferation grows over time. Mapping errors and methodological pitfalls inflate clusters: temporary activity-cluster names, shared tooling/infrastructure, overlapping operations. Root cause of the standardization failure: agreeing that X equals Y requires sharing the private telemetry that justifies the attribution — naming fragmentation is structurally entangled with the economics of proprietary CTI.

**Relevance.** Section 2.3/3 — the fragmentation thesis at the *instance* level: vendors fragment on names for the same reason datasets fragment on labels (each shop's local view, no incentive or mechanism to converge). For NER this is concrete: ACTOR entity normalization across sources is unsolved, and any cross-vendor corpus (including the principal's) inherits it. Also directly relevant to entity *linking* (GLiNKER-style) as the mitigation path.

**Artifacts.** Available: github.com/0xjet/hip (HiP methodology + data). Reference resources it builds on: MISP galaxy clusters, mitre-attack/attack-stix-data.

---

## 2509.00081 — Enabling Transparent CTI Combining Large Language Models and Domain Ontologies
Cotti, Rula, Bianchini, Cerutti (U. Brescia / Cardiff / Southampton). XAI-KRKG @ ECAI 2025.

**Summary.** OntoLogX: ontology-constrained LLM extraction from security logs. A domain ontology plus SHACL shape constraints guide and *validate* LLM output structure, producing an ontology-enriched knowledge graph from honeypot-style log data.

**Method.** Prompt-driven LLM extraction where the ontology defines the output structure and SHACL validation enforces semantic validity over the resulting graph; extracted intelligence lands in a graph database for semantic querying.

**Findings.** Higher extraction accuracy than prompt-only baselines (evaluation on public log datasets); the explicit trade-off is quality over speed. Transparency argument: extraction logic is inspectable and modifiable through prompts plus formal constraints rather than opaque fine-tuning.

**Relevance.** Section 2.3 SOTA — the integration pattern where ontologies stop being passive type systems and become active output constraints on LLM extraction. Bridges three survey threads: taxonomies (2.3), LLM extraction reliability (5.6 — constraints as a mitigation for the unreliability findings), and KG construction (7 — validation at ingestion). Log-CTI rather than report-CTI, so cite as paradigm, not direct comparison.

**Artifacts.** None found in extracted text — no repo link. Flag: reimplementation would need their ontology definition; check the ECAI workshop page or contact authors before shortlisting.

---

## 2605.31199 — MAECO-Lite: Modular Ontology for Dynamic Malware Analysis
Adams, Svec, Kluka, Ploszek, Onoja, Balogh, Homola (Comenius U. / Slovak TU). 2026.

**Summary.** Foundational ontological analysis of MAEC and STIX through the lens of UFO (Unified Foundational Ontology), finding that both standards conflate enduring artifacts (a malware sample) with runtime events (what it did when executed) — then proposes a lightweight modular replacement ontology for dynamic malware analysis.

**Method.** UFO-based analysis of MAEC constructs and referenced STIX cyber-observables; MAECO-Lite design: modules for samples, processes, actions, system artifacts, and ATT&CK techniques, with a strict endurant/event separation. Evaluated via description-logic concept-learning performance.

**Findings.** The ontological mismatches in MAEC/STIX measurably hurt machine reasoning; the simplified, foundationally-grounded ontology significantly improves concept-learning performance. Practical demonstration that standards' representational sloppiness has computational costs, not just philosophical ones.

**Relevance.** Section 2.3 SOTA — the formal-ontology critique of the very standards (STIX, MAEC) the extraction field treats as ground truth: the type systems NER targets are themselves ontologically confused. Sharpens the survey's schema argument: harmonizing onto STIX (CyberNER) inherits STIX's conflations. Adjacent domain (dynamic analysis, not report text) — cite for the critique, not as an extraction method.

**Artifacts.** None found in extracted text — no repo link for the ontology itself. Check publisher supplementary material if needed.

---

## 2503.23175 — Large Language Models are Unreliable for Cyber Threat Intelligence
Mezzi, Massacci, Tuma (VU Amsterdam / TU Eindhoven). ARES 2025.

**Summary.** The reality check for LLM-based CTI extraction: prior high-precision claims were measured on sentences (18-54 words) and paragraphs (~106 words); on real reports (350 MITRE APT reports, average 3,009 words) performance degrades substantially, and the models are additionally inconsistent and miscalibrated.

**Method.** Five-step evaluation pipeline measuring three axes prior work ignored: effectiveness on full-length reports (zero-shot, few-shot, fine-tuned), consistency under repeated identical prompts, and confidence calibration. Ground truth: Di Tizio et al.'s STIX-structured corpus of 350 APT reports (pre-2020, so in-distribution for the models). OpenAI, Google, Mistral models.

**Findings.** Precision drops to ~0.76 on real reports (vs 0.83-0.89 claimed on sentence-level inputs); few-shot and fine-tuning only partially help. Same prompt twice can extract different CVEs — fatal for patch-management automation. Models are over/underconfident, so confidence thresholds cannot rescue the pipeline. Diagnosed cause: real reports mention related-but-irrelevant entities (other APTs, other campaigns' vectors) that models cannot contextually exclude.

**Relevance.** Methods 5.6 centerpiece — the empirical case against naive LLM extraction, and the direct counterpoint to encoder-family economics (5.5). Connects to CENSOR's calibration critique (5.4): the same failure mode at a different scale. Document-length degradation echoes GLiNER-Relex's DocRED finding inversely. Open Problems: confidence calibration in CTI extraction is unmeasured and load-bearing.

**Artifacts.** None found — no code release in extracted text. Evaluation dataset is third-party (Di Tizio et al., open access).

---

## 2406.07599 — CTIBench: A Benchmark for Evaluating LLMs in Cyber Threat Intelligence
Alam, Nguyen, Bhusal, Rastogi (RIT). NeurIPS 2024 D&B.

**Summary.** First benchmark suite for LLM capability in CTI beyond memorization: knowledge (CTI-MCQ, 2,500 questions from MITRE/CWE/standards sources), root-cause mapping (CTI-RCM: CVE description to CWE, 1,000 instances), severity prediction (CTI-VSP: CVSS v3 vector from description, 1,000), technique extraction (CTI-ATE: text to ATT&CK technique IDs, 60 malware instances incl. post-cutoff 2024 ones), and threat-actor attribution (CTI-TAA: 50 de-identified vendor reports, alias-aware manual verification).

**Method.** GPT-4o-generated questions from authoritative sources with manual validation; NVD-sourced CVE tasks; attribution with actor names masked.

**Findings.** Evaluates five SOTA LLMs; establishes the task taxonomy (memorization / understanding / problem-solving / reasoning) the successor benchmarks inherit.

**Relevance.** Evaluation section 8 anchor — defines what "evaluating CTI capability" means beyond span-F1. CTI-ATE is the benchmark face of section 6's TTP-mapping task. Heavily cited hub in our discovery sweeps (its citation trail produced 5 corpus papers).

**Artifacts.** Available: github.com/xashru/cti-bench (code + datasets).

---

## 2511.01144 — AthenaBench: A Dynamic Benchmark for Evaluating LLMs in CTI
Alam, Bhusal (RIT), Ahmad, Worth (Athena Security), Rastogi. 2025.

**Summary.** CTIBench's successor attacking benchmark staleness: tasks are dynamically regenerated from live sources (NVD API v2.0, MITRE ATT&CK STIX data, recent APT reports) instead of fixed corpora, with deduplication/contamination controls, a new Risk Mitigation Strategies task, refined metrics, and a unified aggregate score.

**Method.** Six tasks (knowledge test, root-cause mapping, severity prediction, technique extraction, attribution, risk mitigation); two-stage validation (dual-model disagreement flagging then human review); configurable publication windows (e.g., RCM from 2025 CVEs only — post-cutoff by construction).

**Findings.** Twelve LLMs including GPT-5 and Gemini-2.5 Pro: proprietary models lead but remain subpar on reasoning-intensive tasks (attribution, mitigation); open-source models trail badly everywhere. Structured prediction (VSP) is the easy case.

**Relevance.** Evaluation section 8 — the dynamic-construction answer to temporal drift (open problem 5 in our ledger gets its evidence here: static benchmarks rot, and the fix is live-source regeneration). The reasoning-gap finding tempers the LLM-extraction enthusiasm of 5.6 from the benchmark side, complementing the unreliability paper's degradation findings.

**Artifacts.** Available: github.com/Athena-Software-Group/athenabench (code + benchmark data).

---

## 2602.00513 — Minerva: Reinforcement Learning with Verifiable Rewards for CTI LLMs
Alam (RIT), Piplai (UTEP), Cardei (FAU), Rastogi, Worth. 2026.

**Summary.** The constructive answer to LLM unreliability: many CTI outputs are *deterministically verifiable* (canonical ATT&CK IDs, CWE labels, CVSS vectors, structured schemas), which makes CTI an ideal domain for reinforcement learning with verifiable rewards — no learned reward model, no human preference labels.

**Method.** Minerva-CTI: 16 training tasks in three families (vulnerability-centric CVE-to-CWE/CVSS/ATT&CK; detection-centric Sigma/Sentinel/Splunk rules-to-ATT&CK; procedure-oriented behavior-to-technique/tactic/mitigation/actor), each with a deterministic verifier. MinervaRL: GRPO-based RLVR plus hardness-gated answer-conditioned rationale generation — when no rollout verifies, temporarily reveal the gold label to elicit a rationale, filter for correctness, distill back onto the answer-free prompt (deployed model never sees label hints).

**Findings.** Averaged over four open-weight backbones and 12 CTI benchmarks: +15.8 points over base models, +4.3 over plain GRPO; beats SFT, rejection fine-tuning, and off-policy RLVR baselines.

**Relevance.** Methods 5.6 — the 2026 SOTA shape of LLM-based CTI: the field's standards infrastructure (the taxonomies of 2.3) becomes the supervision mechanism. Elegant thesis tie-in: canonical identifiers, created for interoperability, turn out to be free verifiable rewards — annotation scarcity partially bypassed by exploiting structure that already exists. Sparse-reward insight (long-tail identifiers) parallels SynthCTI's class-imbalance motivation.

**Artifacts.** Partial: paper references HuggingFace collection (URL truncated in extraction) and uses public data sources (attack-stix-data, Sigma, elastic/detection-rules, Azure-Sentinel). Verify model/code release at the RIT group's pages before baseline shortlisting.

---

## 2507.16576 — From Text to Actionable Intelligence: Automating STIX Entity and Relationship Extraction
Lekssays, Sencar (QCRI/HBKU), Yu (MBZUAI). 2025.

**Summary.** AZERG: task-specific fine-tuned LLMs producing STIX-compatible structured output from threat reports — the automation of exactly the manual analyst step (text to STIX) that motivates this survey's practitioner framing.

**Method.** Four-subtask decomposition: entity detection (T1), entity type identification (T2), related-pair detection (T3), relationship type identification (T4); task-specific fine-tuning (LLaMA-Factory/vLLM stack). New STIX-aligned dataset: 141 full threat reports, 4,011 entities, 2,075 relationships.

**Findings.** F1 84.43 (T1), 88.49 (T2), 95.47 (T3), 84.60 (T4) in real-world scenarios; 2-25% over open/closed LLMs and prior SOTA. Notable against 2503.23175: full-report extraction *can* work when models are task-decomposed and fine-tuned rather than prompted monolithically.

**Relevance.** Methods 5.6 + KG section 7 bridge — relationship extraction lands this in the construction path (its output is STIX objects + relationships = graph triples). Its dataset is also a Datasets section entry (one of few relationship-annotated CTI corpora). The decomposition finding partially rebuts the unreliability paper: the failure mode is monolithic prompting, not LLMs per se.

**Artifacts.** Partial: HuggingFace collection link truncated in extraction; fine-tuning stack is open (LLaMA-Factory, vLLM). Dataset release status needs verification — if public, it is directly valuable for the principal's corpus (relationship annotations are scarce).

---

## 2502.10825 — MITRE ATT&CK Applications in Cybersecurity and The Way Forward
Jiang, Meng, Shang, Oo, Minh, Lim, Sikdar (NUS + NCS). 2025.

**Summary.** Systematization of 417 peer-reviewed papers applying ATT&CK across threat intelligence, incident response, attack modeling, and vulnerability prioritization; covers NLP/ML integration, framework integrations (Kill Chain, NIST, STRIDE, CIS), and sector studies (ICS, healthcare).

**Method.** Systematic review: IEEE Xplore + Scopus + ACM, 1,168 deduplicated papers screened to 417; multi-phase relevance screening.

**Findings.** ATT&CK is the connective tissue of applied threat-informed defense; NLP/ML-ATT&CK integration is a major growth area; validation practices vary widely; ICS/healthcare adaptations strain the Enterprise-centric design.

**Relevance.** Background 2.3 (ATT&CK structure and reach: 4 components, 3 domains) and section 6 framing — establishes why text-to-ATT&CK mapping is the highest-volume adjacent task. Related-surveys positioning: it surveys ATT&CK *applications* broadly where we survey extraction specifically.

**Artifacts.** Available: github.com/LeThiHongMinh/MITRE-review-papers (review corpus).

---

## 2512.19414 — From Retrieval to Reasoning: TTPrompt — CTI NER with Explicit and Adaptive Instructions
Peng, Sun, Tian, Huang, Li, Yan (Sichuan U. / Renmin U. / Wuhan U.). 2025.

**Summary.** Two contributions: (1) an empirical teardown of retrieval-based in-context learning for CTI NER showing its success depends on *incidental entity-type overlap* in retrieved examples, not semantic similarity — implicit induction from examples is unreliable; (2) TTPrompt, a hierarchical explicit-instruction framework whose levels deliberately mirror CTI's own TTP abstraction (task definition as Tactic, guiding strategy as Technique, annotation guidelines as Procedure), plus FIR (feedback-driven instruction refinement) — instruction backpropagation that refines the guideline text from errors on ~1% of training data.

**Method.** Decomposition experiments splitting Semantic-kNN results by whether retrieved examples share entity types with the query; TTPrompt + FIR evaluated on five CTI NER benchmarks (incl. LADDER, CTINexus).

**Findings.** Type-overlap subset vastly outperforms no-overlap — the retrieval paradigm's "learning" is mostly type leakage. TTPrompt+FIR with 1% data approaches full-dataset fine-tunes (LADDER micro-F1 71.96) and beats fine-tuned ACLM by 10.91 macro-F1 on CTINexus.

**Relevance.** Methods 5.6 — the prompted-NER analogue of CENSOR's calibration critique: both expose an unreliable implicit signal (confidence; semantic retrieval) and replace it with an explicit mechanism. FIR is annotation-scarcity evidence (1% supervision). The TTP-shaped instruction hierarchy is a neat structural echo of section 6's subject matter.

**Artifacts.** None found in extracted text beyond component models — no TTPrompt repo link. Flag for verification.

---

## 2601.14556 — Constructing Multi-Label Hierarchical Classification Models for MITRE ATT&CK Text Tagging
Kumar, Crossman, Dodd, Plummer, Sekharudu, Warrier, Mohammed, Yekrangian (JPMorganChase). 2026.

**Summary.** A stratified "task space" formulation of ATT&CK text tagging (8 task types from multiclass tactic classification through text-to-text), then a deliberately classical construction: TF-IDF + multi-label hierarchical models (tactic level, then tactic-conditioned technique models).

**Method.** Bottom-up stage-wise model building following CISA's ATT&CK-mapping best practices; evaluation on general cyber-intelligence text plus a JPMC-internal financial threat-scenario corpus; GPT-4o comparison.

**Findings.** ~94% tactic accuracy, ~82% technique accuracy (multiclass-cast), meeting or beating SOTA with no LLMs, RAG, or agents — while GPT-4o manages ~60% at tactic level. The task-space table (Table 1) is the cleanest existing organization of the tagging literature (TRAM = multi-label technique; rcATT = mixed multi-label; TTPDrill = multiclass hierarchical).

**Relevance.** Section 6 — both the organizing task-space framework and the strongest "classical ML still wins" data point in the corpus; pairs with the GLiGuard/GLiNER efficiency argument against LLM-by-default. Industry provenance (JPMC) strengthens the practitioner thread.

**Artifacts.** Available: github.com/jpmorganchase/MITRE_models (public model release). Strong baseline candidate — reproducible and cheap.

---

## 2604.02377 — What Are Adversaries Doing? Automating TTP Extraction: A Systematic Review
Tamanna, Mitra, Erfan, Ryan, Mittal, Williams, Rahman (NCSU + U. Alabama). 2026.

**Summary.** Systematic review of 80 peer-reviewed TTP-extraction studies across seven dimensions: extraction purpose, data sources, dataset construction/annotation, modeling approach, evaluation, and reproducibility.

**Method.** Keyword search + open-coding qualitative categorization.

**Findings.** Technique-level classification dominates; tactic classification and technique *search* are underexplored. Method evolution: rules to traditional ML to transformers (BERT/SecureBERT/RoBERTa) with LLM approaches emergent. Critical limitations: single-label simplifications, narrow datasets, and a reproducibility crisis — proprietary datasets, unreleased code, inaccessible corpora block independent validation.

**Relevance.** Section 6 + related-surveys positioning (the TTP-specific review our survey cites rather than duplicates; our scope is wider — NER + KG — and method-deeper on the GLiNER/zero-shot side they barely touch). Its reproducibility findings independently corroborate our Artifacts-field discipline and the licensing open problem. Repeatedly cites Büchel et al. (SoK, watch list) as the unified-comparison baseline — raising that paper's priority.

**Artifacts.** Review paper; no artifact of its own found in extracted text.

---

## 2604.07470 — Beyond Single Reports: Evaluating Automated ATT&CK Technique Extraction in Multi-Report Campaign Settings
Haque, Hamer, Wroblewski, Rahman, Williams (NCSU + U. Alabama). 2026.

**Summary.** The campaign-level reality check: real attacks are documented across many reports from different vendors, but all extraction methods are evaluated on single reports. Replicates Büchel et al.'s 29-method comparison (NER, encoder-classification, decoder-LLM) in a multi-report setting: 90 reports across SolarWinds, XZ Utils, Log4j (CTIfecta test set; AnnoCTR for training).

**Method.** Conceptual replication + extension: aggregate predictions across reports per campaign; error analysis by technique semantic similarity; downstream control-coverage impact; saturation analysis; report-characteristic regression.

**Findings.** Aggregation improves F1 ~26% over single-report analysis; saturation at 5-15 reports. Ceilings remain low (best: 78.6 F1 SolarWinds, 54.9 XZ Utils). 33.3% of misclassifications are between semantically similar techniques (79.2% of those share a tactic). Best method covers only 77.1% of ground-truth mitigation controls. Technically dense, low-readability reports (MITRE, CISA) contribute most.

**Relevance.** Section 6 + Open Problems — cross-report aggregation gets its evidence (ledger item 6 confirmed): single-report evaluation systematically understates achievable coverage AND overstates per-report sufficiency. The control-coverage metric reframes extraction error in operational terms. CISA-report finding is directly relevant to the principal's CISA-based corpus: dense advisories are the highest-value extraction substrate.

**Artifacts.** Datasets are public (CTIfecta, AnnoCTR); replication code release not confirmed in extracted text — check Büchel et al.'s artifacts, which this replicates.

---

## 2505.09261 — Instantiating Standards: Standard-Driven Text TTP Extraction with Evolvable Memory
Meng, Jiang, Wang, Li, Ma, Dong, Ren, Liu (CAS IIE). 2025.

**Summary.** Attacks a failure mode the metrics-driven literature ignores: systems fit inconsistent labeled datasets rather than the ATT&CK standard itself, producing intelligence silos and contradictory assessments. Proposes converting official definitions into actionable dual-layer "situational knowledge" managed by an LLM-driven evolvable memory.

**Method.** SKR: layer 1 = shared situational context for groups of related techniques (retrieval index); layer 2 = contrastive distinguishing features between similar techniques (e.g., T1132 Data Encoding vs T1071 Application Layer Protocol). Memory lifecycle (generate from definitions + labeled examples, update, forget); two-step extraction (retrieve-classify, then verify); the verification step can re-standardize *other* systems' outputs.

**Findings.** Qwen2.5-32B + framework beats GPT-4o by 18% Technique F1; qualitative gains in consistency, transparency, explainability. Also documents ATT&CK's machine-unfriendliness: scale, no explicit contrastive relations, verbose definitions.

**Relevance.** Section 6 — standard-faithfulness as a distinct evaluation axis (datasets disagree with the standard; fitting them propagates the disagreement); the contrastive layer-2 directly targets the semantic-confusion error class 2604.07470 quantifies. Temporal-drift ledger: evolvable memory is the extraction-side answer to framework evolution. Echoes TTPrompt: both convert the standard into explicit machine-usable instructions.

**Artifacts.** None found in extracted text — no repo link. Flag for verification.

---

## 2507.06252 — False Alarms, Real Damage: Adversarial Attacks Using LLM-Based Models on Text-Based CTI Systems
Shafee, Bessani, Ferreira (LASIGE, U. Lisbon). 2025.

**Summary.** Threat-models the CTI *pipeline itself*: ingestion from open sources admits adversarial text. Studies evasion, flooding, and poisoning attacks, with evasion (fake cybersecurity-like text that classifiers accept) as the enabler of the other two.

**Method.** Adversarial text generation against CTI relevance classifiers; evaluation of specialized ML classifiers and ChatGPT-4o as filters.

**Findings.** False positive rate 97% for the specialized classifier and 75% for GPT-4o on adversarial samples — both filters are nearly transparent to generated fake intelligence. Conclusion: CTI pipelines need a verification component at ingestion.

**Relevance.** Open Problems 9 — adversarial robustness of extraction pipelines, previously absent from our ledger. Connects to the echo-chamber finding (vendor concentration amplifies poisoning impact) and to KG validation (section 7) as a structural mitigation point.

**Artifacts.** None found in extracted text.

---

## 2602.17458 — The CTI Echo Chamber: Fragmentation, Overlap, and Vendor Specificity in Twenty Years of Cyber Threat Reporting
Suarez-Roman, Marchiori, Conti, Tapiador (UC3M + U. Padova). 2026.

**Summary.** Large-scale meta-analysis of the CTI reporting ecosystem: LLM pipeline structures 16,096 open-source reports spanning two decades, extracting actors, motivations, victims, vendors, IoCs, TTPs.

**Method.** High-precision LLM ingestion/structuring pipeline; longitudinal density and specialization analysis; vendor marginal-coverage analysis.

**Findings.** The ecosystem is siloed: vendors show strong geographic and sectoral reporting biases; inter-vendor intelligence overlap is typically low; a few core providers give broad coverage and additional sources yield diminishing returns. Prior structured corpora lack attribution/victimology (6M STIX objects are mostly bare indicators).

**Relevance.** Datasets 4 and Open Problems — source-selection evidence for corpus builders: diversity must be *chosen* deliberately because vendor coverage barely overlaps (directly applicable to the principal's seek-more-variety plan, and same-team companion to Hesperus). Also evidence that the raw substrate of every CTI corpus carries structural vendor bias.

**Artifacts.** Structured dataset of 16,096 reports — release status not confirmed in extracted text; check (same UC3M group as HiP, which released).

---

## 2111.07093 — AttacKG: Constructing Technique Knowledge Graphs from CTI Reports
Li, Zeng, Chen, Liang (Zhejiang U. / NUS / Northwestern). ESORICS 2022.

**Summary.** The pre-LLM reference system for attack-KG construction: NER-pipeline extraction of attack behavior graphs from reports, then technique identification by alignment with template graphs built from ATT&CK procedure examples; cross-report aggregation into technique knowledge graphs.

**Method.** Entity/dependency extraction pipeline + graph alignment against technique templates; evaluated on 1,515 real reports (28,262 technique instances, 8,393 unique IoCs) and 16 manually labeled reports.

**Findings.** F1 0.887 (entities), 0.896 (dependencies), 0.789 (techniques) — beating Extractor and TTPDrill. Motivating insight: isolated IoCs are evadable; technique-level behavioral intelligence is durable.

**Relevance.** Section 7 pre-LLM paradigm pole; the template-alignment idea is the rule/dictionary family (5.1) operating at graph level. Baseline in nearly every later KG paper.

**Artifacts.** Available: github.com/li-zhenyuan/Knowledge-enhanced-Attack-Graph (verify URL on use — referenced widely as released).

---

## 2212.10388 — ThreatKG: AI-Powered System for Automated OSCTI Gathering and Management
Gao (VT), Liu, Choi, Ma, Yang, Song (Berkeley). ACM LAMPS 2024.

**Summary.** End-to-end OSCTI *system* (not just extractor): multi-source report collection, AI-based entity/relation extraction, KG construction, and continuous updating as new intelligence arrives; modular and extensible by design.

**Method.** Specialized extraction models per knowledge type; pipeline architecture with pluggable components.

**Findings.** Practical effectiveness in large-scale gathering/management; the system framing (collection-to-maintenance lifecycle) rather than one-shot extraction.

**Relevance.** Section 7 — the operational systems pole: KG construction as ongoing infrastructure with maintenance burden, not a one-time extraction. Pre-LLM contrast for CTINexus (same group's successor).

**Artifacts.** None confirmed in extracted text; check the VT/Berkeley group pages.

---

## 2410.21060 — CTINexus: Automatic CTI Knowledge Graph Construction Using LLMs
Cheng, Bajaber, Tsegai (VT), Song (Berkeley), Gao (VT). EuroS&P 2025.

**Summary.** The data-efficient LLM successor to ThreatKG: optimized in-context learning replaces both fixed-rule parsing and fine-tuning, adapting to new ontologies with minimal annotated examples.

**Method.** Three stages: automatic prompt construction with optimal demonstration retrieval; hierarchical entity alignment (canonicalization + dedup); long-distance relation prediction to complete missing links. Evaluated on 150 reports from 10 platforms.

**Findings.** Significantly outperforms prior methods on CSKG accuracy and completeness without parameter tuning.

**Relevance.** Section 7 LLM-paradigm pole. Its alignment stage is where actor-name normalization (Hesperus, 2.3) operationally lands. Also a CTI NER benchmark source (TTPrompt evaluates on a CTINexus dataset).

**Artifacts.** Available: github.com/peng-gao-lab/CTINexus (public release).

---

## 2405.04753 — AttacKG+: Boosting Attack Knowledge Graph Construction with LLMs
Zhang, Du, Ma, Wang, Xie, Yang, Lu, Chang (NUDT / USTC / NUS). 2024.

**Summary.** Fully automatic LLM rebuild of AttacKG: four prompted modules (rewriter, parser, identifier, summarizer) and an upgraded schema representing an attack as a temporally unfolding event — each step carrying a behavior graph, MITRE TTP labels, and a natural-language state summary.

**Method.** Instruction prompting + in-context learning per module; no fine-tuning.

**Findings.** Faithful extraction under the richer schema; temporal/state layers serve threat-event analysis needs the flat-graph predecessors could not express.

**Relevance.** Section 7 — the paradigm contrast made concrete: same task and lineage as AttacKG, rules-to-LLM swap plus schema enrichment. Schema upgrade evidences ontology fragmentation (every system redefines its own).

**Artifacts.** "Code and datasets released upon acceptance" — not confirmed; flag.

---

## 2411.08359 — MultiKG: Multi-Source Threat Intelligence Aggregation for Attack-Technique KGs
Wang, Zhu, Xiong, Chen (Zhejiang U. / ZJUT / Northwestern). 2024.

**Summary.** Extends KG sources beyond report text: aggregates CTI reports, dynamic audit logs, and static code analysis into one fine-grained technique KG, using LLMs to analyze, construct, and merge per-source graphs.

**Method.** Per-source automated graph construction, then cross-source merging; evaluated on 1,015 techniques and 9,006 technique-intelligence items.

**Findings.** Accurate per-source extraction and effective aggregation; case studies show fine-grained graphs benefit detection tasks.

**Relevance.** Section 7 — answers text-only incompleteness (reports are coarse-grained); the multi-source merge parallels cross-report aggregation (section 6) one level up. Out-of-scope boundary case: log/code analysis is beyond report text, cited for the aggregation architecture.

**Artifacts.** None confirmed in extracted text.

---

## 2407.02528 — Actionable Cyber Threat Intelligence Using Knowledge Graphs and LLMs
Fieblinger (Mittweida), Alam, Rastogi (RIT). ICMLA 2024.

**Summary.** Practical study of open-source LLMs (Llama-2 series, Mistral 7B, Zephyr) for triple extraction from CTI text and downstream KG construction with link prediction.

**Method.** Compares prompt engineering, the guidance framework (constrained decoding), and fine-tuning.

**Findings.** Guidance and fine-tuning beat prompting; small-scale extraction works, but scaling LLM-built KGs and link prediction remain open challenges.

**Relevance.** Section 7 — the honest mid-point: open-model triple extraction is feasible; industrial-scale graph completion is not solved. Constrained decoding echoes OntoLogX's ontology-constraint pattern (2.3).

**Artifacts.** None confirmed in extracted text; RIT group page worth checking.

---

## 2606.01208 — Schema-Agnostic KG Construction via Hybrid Ontology Discovery for CTI (ANCHOR)
Kim, Kim, Kang, Kim, Lee (Korean gov agencies + Korea U.). 2026.

**Summary.** 2026 SOTA on the schema problem at KG level: existing pipelines are schema-specific (rebuilt per ontology), prompt-based schema inclusion does not scale to large ontologies (UCO), and enterprise LLM APIs conflict with sensitive incident data. ANCHOR bridges LLMs and formal ontologies via hybrid ontology discovery — a search-and-navigate mechanism dynamically exploring large schemas — plus SHACL validation enforcing compliant type assignments.

**Method.** Dynamic ontology exploration + constraint validation; evaluated across UCO, STIX, and MALOnt schemas; local-LLM vs enterprise-LLM comparison.

**Findings.** Beats baselines on ontology typing and schema compliance; local LLM nearly matches enterprise APIs — privacy-preserving CTI KG construction is viable.

**Relevance.** Section 7 capstone — confirms the KG-ontology-fragmentation hypothesis AND supplies the resolution direction (schema-agnosticism + validation). Completes the OntoLogX/SHACL thread; multi-ontology evaluation directly evidences that no single CTI ontology won.

**Artifacts.** None confirmed in extracted text; flag.

---

## 2605.16714 — GRID: Graph Representation of Intelligence Data for Security-Text KG Construction
Huang, Liu (ASU), Shao, Ma, Zhang, Chen, Ye, Xiao. 2026.

**Summary.** Trains small (4B) security-domain KG extractors by manufacturing supervision: unsupervised article-graph alignment from CTI articles (graph extraction + KG-conditioned text revision), then a scripted task bank (multi-select questions + regex triple targets) giving cheap, stable rewards instead of LLM-judge scoring.

**Method.** Two Qwen3-4B extractors (task-bank reward; end-to-end LLM-judge reward); unified benchmark of 249 CTI articles across five sources (GRID, CASIE, CTINexus, MalKG, SecureNLP).

**Findings.** Task-bank model + ontology-guided pipeline: 84.62 source-averaged precision, 64.91 recall, 68.53 avg F1 — best recall and near-top F1 at a fraction of the model size.

**Relevance.** Section 7 SOTA — three survey threads converge: verifiable-reward training (Minerva, 5.6), synthetic supervision manufacture (5.7), and small-model economics (5.5). KGs framed as agent memory points at consumption (out of scope) but construction method is squarely in.

**Artifacts.** Preprint under review; release not confirmed in extracted text; flag.

---

## 2204.04769 — A Review of Knowledge Graph Application Scenarios in Cyber Security
Liu, Wang, Ding, Liang, Yu, Zhou (NUDT + LMU). 2022.

**Summary.** The standing review of cybersecurity KGs: concepts, schema, construction approaches, plus a 9-category/18-subcategory classification of application scenarios, with curated datasets and open-source library collections.

**Findings/positioning.** Pre-LLM snapshot (2022): construction coverage centers on BiLSTM/BERT-era extraction; the entire 2024-2026 LLM construction wave (CTINexus, AttacKG+, ANCHOR, GRID) postdates it, as does the ontology-discovery turn.

**Relevance.** Section 7 positioning anchor (ISC-46): we cover the text-to-KG construction path with the LLM wave and NER method depth; it covers application scenarios broadly. Complementary, minimally overlapping.

**Artifacts.** Review; its curated dataset/library collection is itself a useful artifact index.

---

## 2208.01693 — Recognizing and Extracting Cybersecurity Entities from Text
Hanks, Maiden, Ranade, Finin, Joshi (UMBC). ICML workshop 2022.

**Summary.** Early practical corpus + pipeline paper: initial open CTI corpus from diverse sources, spaCy-based cybersecurity entity models, self-learning exploration, and Wikidata entity linking. This is the "CyEnts/Hanks 2022" line cited by AnnoCTR's corpus survey.

**Findings.** Demonstrates the accessible-tooling path (spaCy) and flags the dataset-scarcity problem that later corpora address.

**Relevance.** Datasets 4 (landscape row) and Methods 5.3 (practical supervised lineage); the Wikidata-linking thread anticipates entity normalization (2.3, 7).

**Artifacts.** Corpus described as community-accessible; URL not in extracted text — check UMBC ebiquity pages.

---



## Sweep 6 arrivals (2026-07-22) — reference backfill

The entries below backfill papers the survey already cites or the discovery
ledger already held; grounded in the docling-converted source text, numbers
spot-checked against source. Not new scope acceptances (the 25-cap governs
scope, not citation backfill).

---

## 2204.02685 — SecureBERT: A Domain-Specific Language Model for Cybersecurity
Ehsan Aghaei, Xi Niu, Waseem Shadid (UNC Charlotte), Ehab Al-Shaer (Carnegie Mellon). arXiv 2022.

**Summary.** RoBERTa-base retrained on a large cybersecurity corpus to capture domain connotations (homographs like "virus," "worm," "honeypot") that general-English encoders miss — either OOV jargon or words carrying a different meaning than in general English.

**Method.** Built on RoBERTa-base (12 layers, 12 heads, 768 hidden). Two components: (1) a custom BPE tokenizer of the same size as RoBERTa's (50,265 tokens) — 32,592 shared with RoBERTa, 17,673 cybersecurity-unique (firewall, ransomware, phishing, mysql, obfuscated); (2) a weight-adjustment scheme adding zero-mean Gaussian noise (σ=0.01) to RoBERTa's embedding weights for shared tokens, biasing them away from general-English meaning without discarding it, while new tokens get Xavier init. Pretraining corpus: 1.1B words from blogs/news, articles, survey papers, reports, books, Wikipedia-cyber, videos. Dynamic MLM, RoBERTa hyperparameters, 250,000 steps / ~100h on 8 V100s, batch 18.

**Findings.** MLM (17,341-record MITRE-derived test set): SecureBERT beats RoBERTa-base, RoBERTa-large, and SciBERT on noun/verb hit-rate@topN — including the 355M RoBERTa-large. Ablation shows the weight adjustment is what drives cyber-correct homograph predictions. General-English retention (Rotten Tomatoes sentiment): SecureBERT-modified 67.23% acc / 67.10 F1, within ~2.2% of RoBERTa-base (69.46 / 69.12). NER on MalwareTextDB (39 APT reports, 4 tags Action/Subject/Object/Modifier): SecureBERT-modified P85.24/R88.10/**F86.65** — best of the four vs RoBERTa-base (86.20), SciBERT (84.49).

**Relevance.** First of the survey's three §5.3 domain-pretrained encoders, and the backbone of this project's best fine-tuned model (SecureBERT, 0.71 strict F1 on the LLM gold — the capstone's headline). The tokenizer-plus-noise recipe and the paper's own NER evidence are load-bearing for §5.3, not just background. Note the paper's own NER benchmark uses a general APT-report tagging scheme (Action/Subject/Object/Modifier), not CTI entity types (CVE, malware family, TTPs) — the gap this project's LLM-gold pipeline targets.

**Artifacts.** GitHub: github.com/ehsanaghaei/SecureBERT (footnote 3). No license stated in extracted text.

---

## 2212.02974 — CySecBERT: A Domain-Adapted Language Model for the Cybersecurity Domain
Markus Bayer, Philipp Kuehn, Ramin Shanehsaz, Christian Reuter (PEASEC, TU Darmstadt). arXiv 2022.

**Summary.** bert-base-uncased further pretrained (DAPT) on a curated multi-source cybersecurity corpus, explicitly engineered to balance domain adaptation against catastrophic forgetting; evaluated on 15 domain tasks plus SuperGLUE against BERT and CyBERT (Ranade et al. 2021).

**Method.** DAPT on bert-base-uncased. Corpus combines four stylistically diverse sources: blogs (151k posts, 169M tokens), arXiv cs.CR papers (16k papers, 167M tokens), NVD vulnerability descriptions (171k entries, 12M tokens, unfiltered as expert text), Twitter (~4M tweets, 179M tokens). Total 528M tokens / 4.3M entries — deliberately kept to ~10% of BERT's pretraining size to mitigate forgetting. LR 2e-5, 30 epochs, batch 64 on 4 V100s, 10k warmup steps.

**Findings.** Word similarity (cloze F1): BERT 0.4382, CyBERT 0.4861, CySecBERT **0.6382**. NER on NVD-derived tagging (software version/name, attack complexity): CySecBERT best on all three (SV 0.9302, SN 0.8871, AC 0.3472) — but AC is weak for all models on limited data. Relevance classification (CySecAlert): CySecBERT 0.8883 vs BERT 0.8779. Specialized CTI (MS Exchange): 0.8869 (+0.027 over BERT). Catastrophic-forgetting check (SuperGLUE): 0.5468 vs BERT 0.6010, a ~-0.05 drop judged non-catastrophic.

**Relevance.** Second of the §5.3 domain encoders. Pretrained on a deliberately heterogeneous corpus (blogs + arXiv + NVD + Twitter) and built on vanilla BERT rather than SecureBERT's RoBERTa base — a genuinely different corpus-and-base choice for the comparison table. **Framing correction: the extracted text never mentions SecureBERT** — CySecBERT is benchmarked only against CyBERT and vanilla BERT. Do not assert a CySecBERT-vs-SecureBERT comparison without an independent source. NER evidence is present but narrow (NVD-field tagging, AC F1 as low as 0.33).

**Artifacts.** Abstract states dataset and model are "made publicly available"; no repository URL/name/license in the extracted text — record as stated-available, no confirmable link.

---

## 2305.08596 — DarkBERT: A Language Model for the Dark Side of the Internet
Youngjin Jin, Seungwon Shin (KAIST); Eugene Jang, Jian Cui, Jin-Woo Chung, Yongjae Lee (S2W Inc.). arXiv 2023.

**Summary.** RoBERTa-base pretrained on a large filtered Dark Web (Tor) corpus, motivated by lexical/structural divergence of Dark Web text from Surface Web pretraining data; evaluated on Dark Web page/thread classification and cyber use cases — not span NER.

**Method.** Initialized from roberta-base; pretrained on Tor pages seeded from Ahmia + onion lists (6.1M pages raw). Filtering: character-count (500–10k chars) → 5.43M; category balancing via a 9-category CoDA-trained classifier (pornography was 41.7% of raw), reducing the smallest:largest category ratio from 70-fold to 7-fold; minhash dedup. Final corpus 1,732,529 pages / 5.83GB. Sensitive identifiers (emails, URLs, IPs, crypto addresses, 38+-char strings incl. hashes) masked for ethics. Two variants (raw vs preprocessed), ~20k steps / ~15 days each on 4 A100 80GB.

**Findings.** Dark Web activity classification (CoDA cased): DarkBERT-preprocessed **94.29** F1 vs RoBERTa 93.31, BERT-uncased 92.75. Ransomware leak-site detection: DarkBERT-preprocessed F1 **84.11** vs RoBERTa 44.31 (sharp drop), BERT-uncased 70.77. Noteworthy-thread detection: DarkBERT-preprocessed F1 **54.17** vs RoBERTa 18.71. **The paper evaluates no span-level NER anywhere** — all extrinsic tasks are page/thread-level classification plus a fill-mask keyword task.

**Relevance.** Third of the §5.3 domain encoders and the clearest case of within-family domain divergence: pretrained on Tor HTML text, so its lexical strengths (drug slang inference) are orthogonal to CTI-report language. Given the total absence of NER evaluation, cite it in the survey as a domain-adaptation *methodology* comparison (corpus filtering/dedup/category-balancing pipeline), not as NER evidence.

**Artifacts.** Access-restricted by design: only the preprocessed model was to be released (deferred to conference time); the Dark Web corpus is explicitly not released; DUTA/CoDA eval sets available on request for academic use only. No GitHub/HF link named in the extracted text.

---

## 2204.05754 — CyNER: A Python Library for Cybersecurity Named Entity Recognition
Md Tanvirul Alam, Dipkamal Bhusal, Nidhi Rastogi (RIT); Youngja Park (IBM T. J. Watson). arXiv 2022.

**Summary.** Open-source Python library for cybersecurity NER combining transformer classifiers, regex heuristics for IOCs, and off-the-shelf generic NER (Flair, spaCy) with configurable priority merging; ships with an annotated corpus.

**Method.** ~60 threat-intel reports (2018–2021, MITRE ATT&CK "software" category, Android malware), manually BRAT-annotated by trained graduate students. Five classes: malware, indicator, system, organization, vulnerability. Split 40/10/10 docs; 106,991 tokens, 4,530 tagged entities, BIO. Models: BERT/RoBERTa/XLM-RoBERTa (base+large) fine-tuned via tner (20 epochs, seq 128, single V100). Heuristic layer: regex for FilePath/Email/SHA/CVE/IPv4; default merge order Heuristic > Transformer > Flair > spaCy.

**Findings.** Test span micro-F1: XLM-RoBERTa-large P75.30/R78.07/**F76.66** (best); BERT-large 73.07; BERT-base 69.77; RoBERTa-base collapses to 39.69 (and RoBERTa-large 38.91). Per-class (XLM-R-large): Vulnerability F88.89, Indicator F82.27, Malware F77.39, System F74.84, Organization F64.98 (weakest).

**Relevance.** Feeds §4 (Datasets) and §3 (schema fragmentation) — a compact five-class ontology distinct from other CTI schemas, illustrating taxonomy divergence. Its dataset is one of the four merged by the label-unification (2507.13870) and CyberNER (2510.26499) harmonization studies, and is the CyNER corpus used by the hard/easy-discrimination paper (Sensors 25(24):7627).

**Artifacts.** github.com/aiforsec/CyNER (pip-installable), demo video on YouTube. No license stated in extracted text.

---

## acl-P17-1143 — MalwareTextDB: A Database for Annotated Malware Articles
Swee Kiat Lim, Aldrian Obaja Muis, Wei Lu (SUTD); Chen Hui Ong (DSO National Laboratories). ACL 2017 (pp. 1557–1567).

**Summary.** First database of annotated malware reports, built around the MAEC vocabulary, plus five downstream tasks (sentence relevance, token/relation/attribute-label prediction, malware-signature prediction) with baselines.

**Method.** 39 APT reports from APTnotes (of 384 available, 2014), 6,819 sentences (2,080 relevant). BRAT annotation in three cumulative stages: token labels (Action/Subject/Object/Modifier), relation labels (SubjAction/ActionObj/ActionMod/ModObj), and 444 MAEC attribute labels across ActionName (211), Capability (20), StrategicObjectives (65), TacticalObjectives (148). Models: SVM/Naive Bayes (relevance, attributes), CRF++ (token labels, Brown clusters from 126 reports), rule-based (relations). 60/20/20 doc split, 5 runs.

**Findings.** Token-label inter-annotator Cohen's κ = 0.36 ("rather difficult"). Task 1 relevance: NB F63.2, SVM F60.5. Task 2 token labels (strict): best avg F40.3. Task 3 relations (rule-based, 38 test docs): avg **F89.3**. Task 4 attributes: best category Capability F41.8; of 444 labels, 190 never occur and 50 occur once — extreme sparsity. Task 5 signatures: annotation features beat text (SVM F59.2 vs 47.2).

**Relevance.** Foundational dataset/schema paper for §4; its four-tier MAEC-derived scheme (token/relation/attribute) is a relation-and-capability-centric structure that broadens the §3 fragmentation discussion beyond flat label sets. On licensing, the paper states only intent for "public release" and points to statnlp.org/research/re/ — no explicit license, consistent with AnnoCTR's Table-1 observation that MalwareTextDB's license is unclear. This repo holds MalwareTextDB-1.0 locally at `data/evals/` for cross-domain eval.

**Artifacts.** Intended for public release; details at statnlp.org/research/re/. No explicit license in extracted text.

---

## aaai-CASIE — CASIE: Extracting Cybersecurity Event Information from Text
Taneeya Satyapanich, Francis Ferraro, Tim Finin (UMBC). AAAI 2020.

**Summary.** Neural system extracting cybersecurity *events* (not flat entities) from news text for eventual KG integration; introduces a richly event-annotated corpus and a four-stage pipeline (nugget detection, argument detection, role linking, realis).

**Method.** ~5,000 Cyberwire articles (2017–2019); ~1,000 event-mentioning articles annotated by three experts with majority vote. Five event subtypes — Attack.Databreach, Attack.Phishing, Attack.Ransom, Discover.Vulnerability, Patch.Vulnerability — with 20 argument role types (Attacker, Victim, Tool, CVE, Vulnerable-System, etc.). Model: hybrid BiLSTM-CRF for nugget/argument detection with location attention, fed CoreNLP + DBpedia Spotlight + Wikidata features and four embedding variants (incl. BERT-base); separate FC net for role linking; two-step realis classifier. 8-fold CV, 900 train / 100 test, TAC span-overlap metric.

**Findings.** Cohen's κ = 0.81; all five event types have >1,000 instances (vs 70% of ACE-2005 types under 100). Best nugget detection (pre-built BERT) P79.60/R80.28/**F79.94**; best argument detection **F74.76**. Per-argument extremes: Money F93.3, CVE F88.0, Patch F81.3 (high); GPE F44.7, Capabilities F51.2 (low). Realis micro-avg F77.65.

**Relevance.** CASIE is EVENT extraction, not NER — the survey's boundary case defining the scope edge. Present it as the point where flat span-labeling (CyNER, MalwareTextDB, Bridges) gives way to structured event frames with semantic roles and a realis dimension, motivating why it's discussed but excluded from head-to-head NER-model comparisons.

**Artifacts.** Corpus, annotations, and code stated public at github.com/Ebiquity/CASIE. No explicit license in extracted text.

---

## 1308.4941 — Automatic Labeling for Entity Extraction in Cyber Security
Robert A. Bridges, Corinne L. Jones, Michael D. Iannacone, Kelly M. Testa, John R. Goodall (Oak Ridge National Laboratory). arXiv 2013.

**Summary.** Automated ("distant"/database-linked) labeling that generates a large cybersecurity NER training corpus by matching text to structured vulnerability-database records (NVD, MS Security Bulletin, Metasploit), then trains a fast Maximum Entropy tagger — explicitly a response to the cost of manual annotation.

**Method.** Sources linked via CVE-ID: NVD descriptions (2010–2013, the bulk), MS Security Bulletin fields, Metasploit exploit descriptions. Labeling = database-field matching + heuristic regex (version ranges, filenames, camelCase identifiers) + a CWE-mined term gazetteer ("buffer overflow," "execute arbitrary code," "XSS"). Label set: software vendor/product/version/language, vulnerability name (CVE-ID), software symbol, vulnerability relevant term; IOB-tagged. Corpus >850,000 tokens. Model: history-based MaxEnt (averaged perceptron, greedy decode), Python then Apache OpenNLP, two chained classifiers. Supervised experiments on a 15,192-description NVD subset, 5-fold 80/20.

**Findings.** Auto-labeling accuracy vs hand-labeled samples (excluding the dictionary "relevant term" to avoid inflation): NVD P99%/R77.8%/**F.875**; MS-Bulletin F.778; Metasploit F.691. Supervised tagger at full data: OpenNLP domain-labels P0.989/R0.993/F0.991/Acc0.994, training <29s. Vs Joshi et al.'s hand-labeled CRF baseline (~1/30th the data): F1 .799 — attributed partly to the larger auto-produced training set.

**Relevance.** The earliest auto-labeling / distant-supervision work in security NER in this bibliography — direct ancestor of the BOND-style weak supervision the survey covers in §5.4. Labels came entirely from structured DB fields (via CVE-ID) plus regex and a CWE gazetteer, no LLM or human seed. Its own reported auto-labeling accuracy (P 95.3–99.4%, R 54.3–77.8% across the three sources) is a useful early data point for the survey's silver-label-reliability discussion — contrast with this project's finding that dictionary/distant silver labels were too noisy to evaluate against directly.

**Artifacts.** Corpus (>850k tokens) + Python/OpenNLP code stated public at github.com/stucco/auto-labeled-corpus. No explicit license in extracted text.

---

## usenix-2025-Buechel — SoK: Automated TTP Extraction from CTI Reports — Are We There Yet?
Marvin Büchel, Tommaso Paladini, Stefano Longari, Michele Carminati, Stefano Zanero, Hodaya Binyamini, Gal Engelberg, Dan Klein, Giancarlo Guizzardi, Marco Caselli, Andrea Continella, Maarten van Steen, Andreas Peter, Thijs van Ede (Oldenburg; Politecnico di Milano; NEC Labs Europe; U. Twente; Accenture Labs; Siemens). USENIX Security 2025.

**Summary.** SoK on automated TTP extraction from CTI reports, systematizing 40+ papers across NER, classification, and generative-LLM families. Because prior work uses incomparable custom ontologies and private data, the authors reimplement each family's *core methods* and benchmark them in one unified setting (shared ATT&CK ontology, shared public datasets, shared metric).

**Method.** Collection: DBLP + Scholar, post-2015 → 1223 papers → 440 relevant → +38 via citation expansion. Three families: (1) NER — rule/hybrid pipelines (Table 1: AttacKG, Extractor, TTPDrill, CASIE, ThreatKG, etc.); (2) Classification — embedder + classifier head (labeled) or STS (unlabeled), Table 2 ~24 works; (3) Generative — prompt-based (FSP, RAG) vs weight-based (SFT), Table 3, 9 works. Empirical harness: ATT&CK Enterprise v14.1 on TRAM2 (150 CTRs, 50 technique labels) and AnnoCTR (120 CTRs, 133 labels, word-level). Metric: per-document multi-label P/R/F1. Generation via Llama3.1-8B-Instruct+LoRA and RAG via Qwen2-7B; also reproduces three published systems (AttacKG, LADDER, aCTIon).

**Findings.** Headline: even for the top-50 most common TTPs the best solutions reach ~80% precision at ~66% recall; for rarer TTPs precision drops below 40% in realistic settings. Closed-set (TRAM2): NER F1 62.19%, Classification 71.41%, Generation 72.50% (Generation edges Classification by +1.09%). Open-set (AnnoCTR, growing label sets): both Generation and Classification are inferior to NER on every subset — the ranking *inverts* vs closed-set. "Traditional NLP approaches still notably outperform modern embedder-based and generative NLP approaches" in realistic settings. CTI-domain pretraining is not consistently better (best TRAM2 = a general model; best AnnoCTR = a CTI model). Reproduction check: their core-method reimplementations generally beat the originals' reported numbers on AnnoCTR, so published optimizations "do not seem to generalize well." Conclusion: TTP extraction "cannot yet realistically cover the entire ATT&CK framework... held back not by a lack of innovation... but by a lack of high quality datasets."

**Relevance.** The comparative-evaluation anchor for the survey's §6 — it covers all three families the section positions against, and its "are we there yet?" answer is explicitly negative (no family reliably breaks a ~70% F1 ceiling; realistic open-set is worse; traditional NER *beats* generative/embedder methods once labels aren't pre-constrained). This resolves the survey's "(watch list)" parenthetical: Büchel is USENIX Security 2025. **Framing correction: it does NOT release a dataset called "CTIfecta"** — that string is absent from the text; its contribution is a unified empirical harness over pre-existing TRAM2 + AnnoCTR plus reimplementations. Any claim that Büchel releases CTIfecta should be dropped (CTIfecta belongs to the Haque et al. 2604.07470 replication).

**Artifacts.** Source code, models, and datasets public at doi.org/10.5281/zenodo.15608555 (stated open-science release).

---

## fruct-2025-Yadulla — Enhanced Cybersecurity Entity Recognition Using DeBERTa, Transformer-CNN Hybrids, and BiLSTM-Softmax
Akhila Reddy Yadulla, Vinay Kumar Kasula, Abdullah Alshboul (University of the Cumberlands). FRUCT'37, 2025.

**Summary.** A DeBERTa-TransformerCNN-BiLSTM architecture for cybersecurity entity recognition (six types), replacing the usual CRF output layer with BiLSTM-Softmax + Viterbi decoding, benchmarked against 12 baseline NER architectures. The paper's own numbers are internally inconsistent between its results table and its prose (documented below).

**Method.** DeBERTa char embeddings → Transformer-CNN hybrid (residual + batchnorm) → BiLSTM-Softmax BIO tagging → Viterbi at inference. Adadelta, Leaky ReLU, dropout 0.3, 6 residual blocks, batch 128, 256 feature maps, TensorFlow. Dataset: a **custom** corpus from Wooyun Vulnerability DB, Freebuf, and NVD — **not** AttackER (AttackER is cited only as reference [4]). Six types PER/LOC/ORG/SW/RT/VUL-ID (Table I header says "Real-Time" for RT, prose says "Relevant Term" — inconsistent as printed). 154,802 entities (107,733/15,676/31,393), 70/10/20 split. 12 baselines (6 word2vec + 6 BERT-char).

**Findings.** Proposed model: Accuracy 98.17% (highest of 13) but Precision 88.98/Recall 89.43/**F1 87.21** — **loses on F1/recall** to plain BERT-LSTM-CRF (F1 90.60) and BERT-RDCNN-CRF (F1 90.41). Weakest baselines: CRF F78.42, LSTM F82.16. **Documented internal inconsistency:** §V prose cites BERT-LSTM-CRF at "recall 91.07% / F1 89.88%" and claims deltas of +0.89% recall / +0.22% F1 vs the proposed model — neither matches the quoted values nor Table III's 92.15/90.60 row. SW and VUL-ID are the hardest categories (SW best precision only ~50.26%). Reported as printed, not reconciled.

**Relevance.** A recent §5.3 architecture comparison — but **not** AttackER-based (custom Wooyun/Freebuf/NVD corpus, non-standard 6-label schema not mapping onto this project's 16 labels). The finding of interest is negative: a more complex hybrid *underperforms* a simpler BERT+LSTM+CRF on the primary NER metrics. Given "Indian embeddings"/"Indian characters" terminology (almost certainly a mistranslation of "Chinese," matching the Chinese source sites) and the table-vs-prose arithmetic mismatch, cite cautiously and flag the discrepancy if used.

**Artifacts.** Code stated "available for download on GitHub" — no URL/name in extracted text.

---

## 2508.01059 — Llama-3.1-FoundationAI-SecurityLLM-8B-Instruct Technical Report
Weerawardhena, Kassianik, Nelson, Saglam, Vellore, Priyanshu, Vijay, et al. (Foundation AI — Cisco; Yale; Carnegie Mellon). Technical report, arXiv 2508.01059, 2025.

**Summary.** Instruction-tuned, chat-capable cybersecurity LLM (SFT + preference tuning) on the authors' continual-pretrained Foundation-Sec-8B base (Llama 3.1-8B). Outperforms Llama 3.1-8B-Instruct on CTI benchmarks, competitive with GPT-4o-mini, and best-in-class among cybersecurity LLMs on general instruction-following/human-preference benchmarks.

**Method.** Llama 3.1-8B-based; base-model pretraining corpus size lives in the prior report (arXiv:2504.21039), not this one; post-training data described only qualitatively (synthetic data, rejection sampling, difficulty grading, verification). The report also audits cybersecurity-content proportions and benchmark contamination in eight open post-training datasets. Eval: security benchmarks (CTIBench MCQA/RCM/VSP, CyberMetric-500, SecBench, SecEval) at temp 0.3 over 10 trials; general via OLMES; persona via PersonaGym; safety via 400 HarmBench prompts.

**Findings.** CTIBench-RCM 0.692 (↑24% vs Llama-3.1-8B-Instruct), beating GPT-4o-mini (0.655) and Llama-3.1-70B-Instruct (0.623); CTIBench-MCQA 0.644; CTIBench-VSP 0.802. AlpacaEval 2 35.45 (↑45%; "next-best cyber model has less than half the win-rate"); IFEval 0.811. MMLU 0.602 (↓11%). PersonaGym 4.58 — highest of all compared incl. Claude 3.5 Sonnet (4.51). Safety: 92% alone / 99% with LlamaGuard. Contamination audit validates the method (Primus-Reasoning shows 79–91% overlap with CTIBench-RCM; other datasets <5%).

**Relevance.** A security-domain continual-pretraining LLM (Llama-3.1 base) — the generative-side analogue of encoder-family domain pretraining (SecureBERT), an 8B open-weights "domain-adapt then specialize" comparator for §5.6. Important: **it does not evaluate NER/extraction** — NER appears only in §2.2's related-work framing, where the authors call existing cyber benchmarks skewed toward "narrowly scoped tasks like classification... NER... and summarization" and position their own suite as broader. Useful as a domain-LLM economics baseline, supplies no direct NER numbers.

**Artifacts.** Model public at huggingface.co/fdtn-ai/Foundation-Sec-8B-Instruct.

---

## 2408.06272 — A RAG-Based Question-Answering Solution for Cyber-Attack Investigation and Attribution
Sampath Rajapaksha, Ruby Rani, Erisa Karafili (University of Southampton). arXiv 2408.06272, 2024.

**Summary.** First RAG-based QA system for cyber-attack investigation and attribution, using AttackER's underlying document corpus (with entity annotations stripped) as the retrieval base and an open-source LLM (Mistral) as generator; evaluated against GPT-3.5 and GPT-4o, reported more reliable because it cites sources and avoids their outdated-knowledge/hallucination failures.

**Method.** Knowledge base: 202 documents from AttackER (Deka et al.) — Mandiant, Malwarebytes, Talos, MITRE, Securelist, Trend Micro — keeping only site/URL/text, "removing the annotated entities." SBERT embeddings in FAISS, top-k cosine retrieval, Mistral-7B generator (Llama-2-7b-chat, Zephyr-7b also supported), Streamlit app on HF Spaces. 280 QA pairs (factual/contrastive/inferential), 170 evaluated with RAGAS (faithfulness, answer relevancy, context precision/recall, correctness).

**Findings.** Few-shot vs zero-shot: Answer Relevancy 0.9171 vs 0.8593; Faithfulness 0.6249 vs 0.5638; Answer Correctness 0.4356 vs 0.4081; slight context-precision trade-off. Vs GPT (qualitative): "GPT-3.5 exhibited more susceptibility to hallucination compared to GPT-4o" — a CVE-2023-34362 example where GPT-3.5 first correctly declined (knowledge cutoff) then fabricated on re-run. Authors conclude their RAG QA "outperforms GPT-3.5 and GPT-4o due to its reliable answers and minimal model hallucination," crediting source provision.

**Relevance.** Same author group as the AttackER NER dataset (Rajapaksha, Rani, Karafili), and it explicitly reuses AttackER — but only the raw document text, with entity annotations deliberately discarded to repurpose the corpus as a RAG knowledge base. A clean illustration of the survey's KG/downstream boundary: an NER-annotated CTI corpus repurposed for downstream QA/attribution once the entity layer is stripped, rather than an NER method itself.

**Artifacts.** Code: github.com/sampathrajapaksha/RAG-based-QA. App: huggingface.co/spaces/rubypnchl/Question_Answer_Engine.

---

## 2304.10428 — GPT-NER: Named Entity Recognition via Large Language Models
Shuhe Wang, Xiaofei Sun, Xiaoya Li, Rongbin Ouyang, Fei Wu, Tianwei Zhang, Jiwei Li, Guoyin Wang (Peking U.; Shannon.AI; Zhejiang U.; NTU; Amazon). arXiv 2304.10428, 2023.

**Summary.** Reformulates NER as text generation to close the gap between LLMs' generative nature and NER's sequence-labeling framing: entities are marked in-place with `@@...##` tokens rather than via position indices or per-token labels. A self-verification stage asks the LLM to confirm each extracted span, countering over-confident hallucination on NULL inputs.

**Method.** GPT-3 (davinci-003), temp 0. Prompt = task description + few-shot demonstrations (`@@##` marker format) + input; each entity type queried separately (N-class → N queries) due to the 4,096-token limit. Three demonstration-retrieval strategies: random, sentence-level (SimCSE) kNN, entity-level embedding kNN. Self-verification prompt ("Is 'X' a location entity?") with its own kNN demos, zero- and few-shot. Evaluated on CoNLL2003, OntoNotes5.0 (flat), ACE2004/2005, GENIA (nested), plus a CoNLL2003 low-resource study (8/100/1K/10K sentences).

**Findings.** Full CoNLL2003: random 72.62 → sentence-level 84.36 → entity-level 89.97 → +self-verification (few-shot) 90.91; supervised SOTA 94.6. Full OntoNotes: 61.58 → 81.73 → 82.20. Nested ACE2004: 48.4 → 73.62 → 74.2. **Output-format ablation (CoNLL2003, 32-shot): the `@@##` scheme scores F1 92.68 vs BMES 29.75 vs Entity+Position 38.73** — the other formats collapse on correctly-aligned/indexed output. Low-resource: with 8 training sentences GPT-NER F1 ≈ 60 while the supervised baseline is ≈ 0. (Note: the text's zero/few-shot self-verification pair 84.97/85.91 does not match Table 2's 89.97/90.91 few-shot row — reproduced verbatim, inconsistency unresolved in source.)

**Relevance.** The canonical generative-NER reformulation for §5.6: entity-marker output format, kNN demonstration retrieval (entity-level dominates), and self-verification as hallucination mitigation. Its format ablation (92.68 vs 29.75 vs 38.73 on identical data) is direct, quantified support for the survey's output-format-sensitivity thread — and converges with the generative-NER format finding in 2601.17898 (offset-based output collapses). The low-resource result (F1 ≈60 at 8 examples) anchors the few-shot generalization narrative.

**Artifacts.** Code: github.com/ShuheWang1998/GPT-NER.

---

## acl-2022.bionlp-1.17 — Named Entity Recognition for Cancer Immunology Research Using Distant Supervision
Hai-Long Trieu, Makoto Miwa, Sophia Ananiadou (AIRC/AIST; Toyota Technological Institute; U. Manchester NaCTeM). BioNLP Workshop @ ACL 2022.

**Summary.** An automatically annotated NER dataset for cancer-immunology entities (cell_type, cytokine, transcription factor) built by dictionary matching against UniProtKB, since manual data is scarce (the TCRE eval set has only 89 documents). A span-based SciBERT NER model is trained on the distant data and evaluated on TCRE, with and without adding the small supervised set.

**Method.** Two auto datasets from a UniProtKB-derived dictionary: KB-T-cell (386 docs; cytokine/TF by strict dictionary match, cell_type by a JNLPBA-trained NER model) and Dic-T-cell (761 docs; re-annotating JNLPBA proteins as cytokine/TF via the dictionary). Eval set TCRE 89 docs. Model: span-based classifier over SciBERT sub-word representations, 3-fold CV, entity-level micro P/R/F.

**Findings.** Enhanced-KB-NER (distant + TCRE) beats Supervised-NER by 2–5 F-points across folds (e.g. Fold-1 73.26 vs 67.78). Distant-only models underperform supervised by ~5–7 points but beat the pure dictionary Matching-NER baseline (F 49.76/50.17/49.12) by 11–15 points. Per-type gains skew to transcription factor (+11–22 points). Merging both datasets (KB-Dic-NER) *decreases* performance vs KB-NER alone despite ~2× data. TF/CY from distant-only models are weak/unstable (some folds predict zero correct TF).

**Relevance.** A clean cross-domain analogue to CTI's low-resource problem for §5.4: few manual docs for specialized types (89-doc TCRE ≈ scarce CTI gold), a domain KB (UniProtKB) substituting for hand annotation, noisy auto-labels framed as acceptable scaffolding that — combined with a small supervised seed — beats supervised-only training. **Framing correction: this paper does NOT build on or extend BOND** — it cites Liang et al. 2020 once in Related Work as adjacent prior art. It is a UniProtKB distant-supervision method in its own right, not a BOND adaptation.

**Artifacts.** None found in extracted text (only a UniProt query URL and a third-party BERT-dependency GitHub link, not the paper's own data/code).

---

## 2411.05057 — A Brief History of Named Entity Recognition
Monica Munnangi (University of Massachusetts, Amherst). Survey (arXiv 2411.05057; the text notes the survey was performed in 2020).

**Summary.** Short survey tracing NER from its 1996 origin (Grishman) through rule-based, feature-engineered ML, and deep-learning approaches, plus evaluation metrics, datasets/tools, and semi-/unsupervised directions. Background/positioning material, not a method paper.

**Method.** N/A (survey) — synthesizes prior literature; no original experiments.

**Findings (periodization).** Rule-based → feature-engineered ML (from ~2007) → deep learning (RNN/BiLSTM-CRF, transformer pretraining). Rule-based methods "result in high precision and low recall" and "cannot be used in cross domains," yet are cited as still used by 67% of industry vendors (IBM study, Chiticariu et al. 2013). Deep-learning models "proved to be more robust to new domains and new data" but need large, expensive manual annotation. The survey stops at BiLSTM-CRF/transformer pretraining and does not discuss LLM-era NER — its §7 Future Directions instead gestures at semi-supervised, active-learning, domain-adaptation, and zero/few-shot methods.

**Relevance.** Background for §2.2 (method eras): confirms a rule-based → statistical → deep-learning periodization, with a fourth "future" era of semi-/few-shot methods gestured at but not realized. Cite only for pre-LLM boundary framing — it predates and does not cover the LLM era. Keep the citation short: positioning, not a method contribution.

**Artifacts.** None (references third-party tools NeuroNER, AllenNLP, CoreNLP, spaCy, but no artifact of its own).

---

# November 2026 update (23 works, published 2026-05 to 2026-11)

Found by forward citations of `survey.bib` (OpenAlex, via `just citing --bib` in `research_arxiv_knowledge_base`), an OpenAlex keyword sweep, and arXiv monitoring. Notes are from abstracts read through OpenAlex unless full-text verification is noted (`2610.39433`, `2611.07486`). Non-arXiv entries use the DOI in the heading.

---

## 2607.23312 — Structuring CTI Reports: A STIX 2.1-Aligned Dataset with MITRE ATT&CK Mappings
Das, Banik, Islam, Rahman. IEEE ICICN 2026, pp. 298–303.

**Summary.** Manually built dataset of 150 English CTI reports, each a STIX 2.1 graph. **Method.** 25 reports independently assessed by two researchers, disagreements adjudicated into a gold sample; four local open-weight LLMs evaluated as judges against it. **Findings.** 4,777 entities, 5,817 relationships, 1,273 attack-pattern objects mapped to 269 ATT&CK techniques; "substantial" inter-rater agreement; best judge Qwen3.6 27B reaches kappa 0.803, micro-F1 > 92%, FPR < 5%. LLMs help find annotation inconsistencies but do not replace experts. **Relevance.** §4 corpora table and LLM-assisted annotation; §7 RE gap. Cites CTINexus, ThreatKG, AnnoCTR, AttacKG. **Artifacts.** Not confirmed.

---

## 10.3390/jcp6060190 — CTI-Rationale: Expert-Annotated Dataset for Evidence-Grounded ATT&CK Mapping
Resul, Bouruc, Rughiniș, Văduva, Țurcanu. J. Cybersecurity & Privacy 6(6):190, 2026.

**Summary.** Treats each technique mapping as an argument (evidence span, warrant, rejected alternatives). **Method.** 1,740 human-written paragraph–technique mappings from 100 public reports; no AI-generated rationale content. **Findings.** Paragraph Jaccard 0.421 overall, 0.780 where both annotators mapped; 10.4% of one-sided mappings are conflicts; capture–recapture completeness 84.2–88.0%. Annotation bundle beats an equal-volume label-only control by +0.024 micro-F1 (also under campaign-, publisher-, and TRAM2 transfer splits); ATT&CK definition text recovers about two-thirds of the gain; retrieved demonstrations raise a small LM from 0.367 to 0.500 micro-F1. **Relevance.** §4 annotation methodology; §6. **Artifacts.** Not confirmed.

---

## 10.3390/jcp6060188 — A Lightweight Approach for Adaptation of LMs for Cybersecurity NER
Srivastava, Gupta, Paul, Sahoo. J. Cybersecurity & Privacy 6(6):188, 2026.

**Summary.** Adds domain terms to a general LM's WordPiece vocabulary before fine-tuning instead of domain pretraining. **Method.** Terms grouped by split count, ranked by TF-IDF, budget searched over 20 configurations. **Findings.** 250 terms (5+ pieces) into BERT-large-cased: STUCCO-CNC 5-fold F1 96.66 to 96.91; 80/20 split 97.20 to 97.63 (CySecBERT 97.45, SecureBERT 97.83). CyberNER-STIX entity F1 +~1.0 to 80.10 (prior published 72.30, BERT-base). No pretraining (SecureBERT used ~1.07B tokens); 1.5 h on one 24 GB GPU. Gains small, not statistically established; selection rule beats random only on CyberNER-STIX. **Relevance.** §5.3 (tokenizer as third axis). Cites AttackER. **Artifacts.** None found.

---

## 10.3390/electronics15163749 — AraCTI-NER: Arabic CTI NER Dataset and Benchmark
Alghamdi, Meshoul. Electronics 15(16):3749, 2026.

**Summary.** First Arabic CTI NER corpus. **Method.** LLM-assisted pipeline seeded with Arabic cybersecurity articles, structurally validated and rebalanced by targeted generation; 8 STIX-inspired types; 7 encoders x 3 seeds, strict entity metrics. **Findings.** 10,312 samples, 275,530 tokens, 42,360 spans. 408-sentence expert-audited test subset (ATS-gold), second-expert IAA 0.878 entity F1. XLM-R Large 0.7603 (0.7674 on gold), AraBERTv2 0.7491, English cyber encoders ~0.63. ~3 F1 drop silver to gold, mostly Vulnerability and TTP. Authentic Arabic news: best 0.5429 vs IAA 0.616. **Relevance.** §4 corpora + LLM-assisted annotation; §5.3 multilingual; §5.7 synthetic span data; §9. Same method family as this repo's LLM-proposed, human-curated gold. **Artifacts.** ATS-gold release stated; URL not confirmed.

---

## 10.1007/978-3-032-32643-0_17 — From Zero-Shot to Domain Precision: Synthetic Data Fine-Tuning for Robust NER
Zafar, Nowaczyk, Sarmadi. LNCS (Springer), pp. 200–212, 2026.

No abstract available in OpenAlex; Springer page blocked automated fetch. Cited by title only (§5.5). Cites GLiNER. **Artifacts.** Unknown.

---

## 10.1109/sp63933.2026.00215 - APT to Disagree on Attribution in Commercial TI
Ethembabaoglu, van Wegberg, Zhauniarovich, van Eeten (Delft University of Technology). IEEE Symposium on Security and Privacy (S&P) 2026, pp. 4769-4787.

**Summary.** Longitudinal comparative measurement of threat-actor attribution across seven leading commercial CTI vendors over 14 years from 2011 to 2025, covering 13.5 million attributed IOCs. **Method.** Raw vendor feeds are normalized into comparable indicator records and reconciled against an evaluated and augmented MISP Threat Actor Galaxy (MISP TAG); inter-vendor agreement on overlapping indicators is scored with Krippendorff's alpha at both threat-actor and country-of-origin levels. **Findings.** Multi-vendor IOC overlap holds near 1%, and most tracked threat actors appear in only a single vendor's reporting; on shared indicators, Krippendorff's alpha is moderate at the actor level and substantially higher at country of origin. **Relevance.** §2.3 instance-level naming fragmentation alongside Hesperus; §9 fragmentation complex and source overlap. **Artifacts.** Evaluated/augmented MISP TAG mapping; commercial TI feeds proprietary.

---

## 10.5281/zenodo.21939890 — Relation Extraction for Cyber-Attack Attribution (AttackER-RE)
Oyenuga. Zenodo dataset (MSc, University of Southampton), 2026.

**Summary.** RE layer over AttackER: 9 STIX-aligned relation types plus no_relation, as directed triples. **Method.** Train/dev labels from GPT-4o as silver annotator; test set manually annotated gold; fine-tuned CySecBERT RE model released. **Relevance.** §4, §7 RE gap, §9. **Artifacts.** doi.org/10.5281/zenodo.21939890; underlying text under AttackER's license.

---

## 10.1186/s42400-025-00480-4 — VIB-NER: OOV Recognition in CTI via Variational Bottleneck
Wang, Liu, Zhang, Xu, Zhao, Sun, Wang. Cybersecurity 9(1), 2026.

**Findings.** F1 79%, R 77%, P 80% on CTI entity extraction; 4–8% over E-NER and similar; 50% less time per training batch. **Relevance.** §5.3. **Artifacts.** None found.

---

## 10.14801/jkiit.2026.24.8.45 — Hybrid LLM-BERT Framework for TTP Extraction from CTI (Korean)
Kim, Jung. J. KIIT 24(8):45–55, 2026.

**Method.** Noise removal (URLs, IOCs) on TRAM2 and AnnoCTR; Kanana-1.5 2.1B proposes TTP candidates, CySecBERT verifies. **Findings.** Rule-based noise removal best on TRAM2, URL removal best on AnnoCTR; hybrid improves F1 on both, mainly precision. **Relevance.** §6.

---

## 10.1109/compsac69091.2026.11743430 — LoRA-Driven CTI Triple Extraction and KG Construction
Mitchell, Doğdu, Choupani. IEEE COMPSAC 2026, pp. 3335–3340.

**Method.** Semantic chunking; Gemma 2 9B with separate LoRA NER and RE adapters; canonicalization with Markov entity-type smoothing. **Findings.** Deduplicated DNRTI: NER micro-F1 0.7515, RE 0.9970, above SecureBERT. CTI-HAL (71 docs): chunking +51% extraction density, +70% graph density; largest component ratio 0.81. **32.5% of the original DNRTI test set duplicates training sentences.** **Relevance.** §5.6, §7, §8, §9. **Artifacts.** None confirmed.

---

## 10.1007/978-981-92-6837-5_3 — LLM-ETKG: Event-Centric, Evidence-Grounded CTI KG Construction
Wang, Du, Li, Hu, Pan, Wang. LNCS (Springer), pp. 43–62, 2026.

No abstract available in OpenAlex. Cited by title only (§7). Cites AttacKG.

---

## 2606.21890 — Many-Shot In-Context Learning for NER
Zhang, Lan, Caragea, Latecki, Dragut. arXiv 2026.

**Findings.** Hundreds of demonstrations let LLMs match or beat fully supervised BERT; ~100 human-labeled demonstrations used for in-context annotation yield ~10 absolute F1 over prior SOTA when the labels fine-tune BERT for low-resource NER. **Relevance.** §4 LLM-assisted annotation.

---

## 2610.00007 — On-Device NER: A Deployability Study
Chaganti. arXiv 2026.

**Method.** 9 systems (spaCy; GLiNER 166–460M; local Qwen3 0.6–4B and DeepSeek-R1 1.5/8B) on 3 datasets; silver gold from a cross-family LLM judge panel, then full human re-validation. **Findings.** Gold provenance flips paradigm ranking: human gold raises every encoder and lowers every generative model. 4B instruct competitive on accuracy; GLiNER matches or slightly trails at 1/9–1/24 the size, ms–s latency, zero malformed output; small generators up to 27% invalid output on long inputs. GLiNER confidence AUROC 0.76–0.86, ECE 0.24–0.47 (halved by temperature scaling). **Relevance.** §4, §5.5, §8, §9; directly relevant to this repo's LLM-gold vs fine-tuned comparison and latency axis.

---

## 2610.37678 — Partner Selection for Selective Span Tagging
Kotte. arXiv 2026.

**Findings.** Choosing the second model by held-out accuracy on the primary's errors recovers 82% of the best partner's gain (vs 69–70% for span F1 or random); replicated on a fourth dataset; scoring the predictive distribution beats hard labels. **Relevance.** §4 (spending the human audit budget).

---

## 10.19678/j.issn.1000-3428.0070621 — Review of Information Extraction in the Field of CTI (Chinese)
Gao, Feng. Computer Engineering, 2026.

Competing review: IE for CTI by ML, DL, and LLM method families, KG construction as main application. **Relevance.** §6 positioning.

---

## 2606.18166 — Open-Source LLMs for Multi-Label ATT&CK Classification on CTI Reports
Ryan, Noor, Erfan, Mitra, Mittal, Rahman. arXiv 2026.

**Findings.** 2,076 human-annotated sentences (1,281 positive) from 83 reports, 114 techniques, kappa 0.68. Best of seven open LLMs (8B–236B) micro-F1 0.22; size correlates with F1; prompt strategy and temperature no significant gain. **Relevance.** §6, §9. **Artifacts.** Dataset release stated; URL not confirmed.

---

## 10.5753/sbseg_estendido.2026.29364 — IoC Mapping and Detection in Threat Intelligence Reports (Portuguese)
Caxias, Santana. SBSeg 2026 (extended proceedings), pp. 532–542.

Hybrid regex + NER for IPs, URLs, hashes including obfuscated forms; reduces false positives on real CTI reports. **Relevance.** §5.1.

---

## 10.5753/sbseg.2026.29054 — MulitaMiner: Multi-Version Evaluation of LLM Vulnerability Report Extraction
Machado, Lautert, Kapelinski, Kreutz, Ferrão, de Oliveira. SBSeg 2026, pp. 801–816.

Five LLMs held fixed across three pipeline versions on OpenVAS PDFs (450 runs): exact record match 37.5% to 90.4%, omission 20.5% to 1.7%, cross-model variance 41.8 to 2.9 pp. **Relevance.** §5.6.

---

## 2610.39433 - ARBITRA Document-Level ATT&CK Extraction via Multi-Expert Argumentation
Jin, Shin. arXiv 2026 (full text verified).

**Summary.** Two-phase multi-expert framework for document-level MITRE ATT&CK extraction from full unsegmented CTI reports. **Method.** Phase 1 runs three reasoning-distilled small-model SFT specialists (`GPT-4.1-mini` and `GPT-4o-mini` trained on `GPT-5.4-mini` rationales for verbatim evidence grounding, sibling-technique contrast, and chronological attack-flow inference), accepting unanimous picks and routing split-vote candidates to Phase 2. Phase 2 builds a rooted Quantitative Bipolar Argumentation Framework (QBAF) tree per disputed candidate and scores final strength deterministically under DF-QuAD gradual semantics. **Findings.** Reaches 0.722 precision, 0.635 recall, and 0.649 macro-F1 on TRAM2 (31 test reports), surpassing sentence-level NER pipelines (0.614), TTPrint (0.494), TTPXHunter (0.328), CTINexus (0.246), and single-pass GPT-5.5 (0.411) at 28% of GPT-5.5's output token cost (USD 0.0214 vs USD 0.0760 per report); lifts zero-shot CTIBench-ATE by +5.0 F1 points without fine-tuning; across three black-box adversarial CTI report attacks (conflicting TTP injection, cross-report contamination, targeted semantic poisoning), holds mean relative precision loss to 7.0% versus 14.0% on GPT-5.5 and 12.2% on GPT-5.4. **Relevance.** §6 report-scale TTP verification; §8 adversarial perturbation robustness. **Artifacts.** Code release deferred until peer-reviewed publication.

---

## 2606.08700 — AutoSUT: The Environment Semantics Gap in Structured CTI
Barbieri, Ferraz, Pereira Júnior. arXiv 2026.

97.6% of ATT&CK Enterprise software objects lack version indicators and CPE identifiers; platform tags near-universal. **Relevance.** §2.3.

---

## 10.1109/eurospw72509.2026.00027 — ATT&CK TTP Adoption and Semantic Ambiguity (WIP)
Suarez-Roman, Caballero, Tapiador. IEEE EuroS&PW 2026, pp. 181–186.

CTICore dataset, 9,359 reports: low, uneven TTP adoption; substantial overlap in names and descriptions of distinct techniques. Same authors as the CTI Echo Chamber paper. **Relevance.** §6.

---

## 10.1016/j.neucom.2026.134365 — NLP in Cybersecurity: Advances, Applications, Future Directions
Alsirhani, Ali, Humayun, Sahito, Alzahrani. Neurocomputing 699:134365, 2026.

Broad review of NLP for threat reports and dark-web data (NER, sentiment, topic modeling, LLMs). **Relevance.** §6 positioning.

---

## 2611.07486 — MEvince: Knowledge-Constrained LLM Reasoning for Technique Identification from Malware Reports
She, He, Xie, Liu, Qian, Qin, Cavallaro (Zhejiang University + UCL). arXiv 2026 (full text verified).

**Summary.** Two-stage knowledge-constrained reasoning framework for report-level MITRE ATT&CK technique identification that grounds predictions in source spans and official specification constraints without fine-tuning model weights. **Method.** Evaluated on 610 MITRE ATT&CK-referenced malware reports (555 train/adaptation, 55 test) across 651 Enterprise v19.2 techniques and sub-techniques against 11 baselines from four method families (encoder classifiers, RAG, multi-stage prompting, agentic workflows). Stage 1 extracts behavioral units into four typed primitives (`Action`, `Object`, `Goal`, `Mechanism`) linked directly to report spans. Stage 2 pairs concept-aligned contrastive retrieval against known confusers with deterministic requirement validation and offline agentic policy refinement. **Findings.** Raises gold exact-ID candidate coverage from 31.6% to 47.9%, reaches exact-ID macro-F1 0.310 (+17.4% over Llama-3.1-70B at 0.264), and doubles exact-ID precision over standard RAG (0.384 vs 0.191). **Relevance.** §6 (span-linked behavioral grounding for implicit techniques, contrastive ATT&CK disambiguation, and verification without weight updates). **Artifacts.** Not confirmed in preprint text.
