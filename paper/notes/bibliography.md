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
Schmidt, Jalocha, Michelseen (ITU Copenhagen). 2025.

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

**Findings.** Models trained on harmonized corpus gain ~30% relative F1 over naive concatenation of the same data. Related-work synthesis: field progression rules/gazetteers → CRF → BiLSTM-CRF → transformer+CRF, with domain-pretrained encoders (SecureBERT, CySecBERT, DarkBERT). Explicitly frames Schmidt et al. as demonstrating that simplistic merging fails; positions ontology-driven harmonization as the fix.

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

## 2509.12098 — Is 'Hope' a Person or an Idea? A Pilot Benchmark for NER: Comparing Traditional NLP Tools and Large Language Models on Ambiguous Entities
Latifi (single author). September 2025. **READ 2026-07-18 — corrects a prior fabricated version of this entry (wrong authors/methodology/numbers; see paper/ISA.md Changelog). Read as a minor, explicitly-limited pilot study — see caveats below, not strong evidence.**

**Summary.** Six NER systems (NLTK, spaCy, Stanza; Gemini-1.5-flash, DeepSeek-V3, Qwen-3-4B) compared on one hand-constructed 119-token passage engineered to be ambiguity-dense — capitalized common nouns as names ("Justice Hope"), multi-token org/location spans, context-only temporal expressions ("dusk," "midday").

**Method.** Single author manually annotated the one passage (no second annotator — the paper explicitly states no inter-annotator agreement/kappa is computable). Token-level P/R/F1 against this single gold set, five entity types (PERSON, LOCATION, ORGANIZATION, DATE, TIME), single-shot prompting at each API's lowest available temperature.

**Findings.** Macro-F1: Gemini 0.824 (best overall, driven by PERSON 0.960 — correctly reads "Justice Hope" as a person), Stanza 0.806, spaCy 0.741, DeepSeek 0.725, Qwen 0.527, NLTK 0.416 (fails DATE/TIME entirely). Grouped: LLMs beat traditional tools sharply on PERSON (0.923 vs 0.692 avg) but lose on ORGANIZATION (0.657 vs 0.733); TIME is weak for both groups alike (0.500). Aggregate LLM vs. traditional gap is small (0.692 vs 0.655) — the PERSON-category win is the whole story, not a general LLM advantage.

**Relevance.** Open Problems — a small, honestly-caveated data point for the same ambiguity class CTI entities exhibit (is "Apache" the tool, the threat actor, or the web server?), specifically the finding that LLM context-modeling advantage concentrates on capitalized-common-noun-as-name disambiguation, not general entity-type performance. Should be cited as directional/suggestive only — n=119 tokens, single annotator, single passage, no significance testing, and the authors' own Limitations section says as much. Not comparable in rigor to the corpus's other benchmark papers (CTIBench, AthenaBench); do not cite its specific F1 numbers as if they generalize.

**Artifacts.** None found — no repo/data link in the paper; authors note releasing data/prompts is future work.

---

## 2404.19192 — BOND-MoE: Mix of Experts Language Model for Named Entity Recognition
Chen (UIUC), Li (UIUC), Song (Columbia), Guo (UCSD). April 2024. **READ 2026-07-18 — corrects a prior fabricated version of this entry (invented specifics not grounded in any source); confirmed real via arXiv abstract page before reading. Short paper (2pp, IEEE workshop format).**

**Summary.** Extends BOND (2006.15509) with a Mixture-of-Experts layer: instead of one BERT fine-tuned on distant labels, K experts are trained on disjoint document subsets (hard-EM assignment) plus a fairness constraint preventing all documents collapsing onto one expert, then the ensemble self-trains on pseudo-labels as in BOND's second stage.

**Method.** Document-level (not token-level) expert assignment — a whole document goes to the expert with highest average posterior across its tokens, avoiding split-entity incoherence. Fair assignment via Sinkhorn matrix scaling (marginal constraints on both document-exposure and expert-utility axes) to stop degenerate single-expert collapse. Evaluated on 5 general-domain DS-NER benchmarks (CoNLL03, Twitter, OntoNotes5.0, WebPage, Wikigold) against BiLSTM-CRF, AutoNER, LRNT, ConNet, and BOND itself.

**Findings.** Mixed, not a clean win: BOND-MoE beats BOND on CoNLL03 (79.31 vs 77.12), WebPage (64.11 vs 63.69), and Wikigold (56.59 vs 55.76), but is marginally *worse* on Twitter (47.76 vs 48.07) and OntoNotes (71.00 vs 71.09). Ablation (Table II) shows self-training contributes the largest single gain of the three components (MoE, fair-assignment, self-training); dropping fair-assignment hurts more than dropping MoE alone, i.e. the assignment mechanism carries more of BOND-MoE's benefit than the expert-ensembling idea by itself.

**Relevance.** Methods §5.4 — another node in the BOND lineage (BOND → SCDL → ATSEN → CENSOR → BOND-MoE), pursuing noise-reduction via ensembling experts on document subsets rather than CENSOR's uncertainty-calibration route. Directly relevant to this repo's own BOND replication (`external/bond/`): where this paper ensembles multiple experts over subsets of the *same* weak-labeled corpus, our replication instead compares different *architectures* (RoBERTa-base/large, SecureBERT) trained on the *full* corpus each — a complementary axis of the same "how do you get more signal out of noisy distant labels" question, worth a sentence connecting the two in the survey's weak-supervision discussion. Caveat: general-domain only, no CTI application attempted, and the win margin (≤1.6% F1 on the paper's own framing) is thin enough that BOND-MoE should be described as a mixed/marginal result, not a clear improvement.

**Artifacts.** None found — no repo link in the paper.

---

## Prior biomedical NER papers (BOND-derived, cited in principal's message)

Two additional entries referenced as using BOND's distant-supervision paradigm in biomedical contexts:
- **"Named Entity Recognition for Cancer Immunology Research Using Distant Supervision"** (2022, ACL Anthology, BioNLP shared task)
- **"Knowledge-Driven Drug-Use Named Entity Recognition with Distant Supervision"** (NSF grant cited; no arXiv/DOI provided)

Both are BOND-cited adaptations rather than novel architectures; full annotation deferred pending URL confirmation. **Action:** principal to provide arXiv/DOI links or extracted text for these two to enable formal bibliography entry.

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

**Relevance.** Datasets § (comparison table row — resolves the 67k/79k token discrepancy question and explains Schmidt et al.'s long-span anomaly: AttackER's spans are long *by design*). Schemas § — second STIX-anchored schema after CyberNER, but with attribution extensions: evidence STIX alone doesn't cover analyst needs. TTP/attribution framing feeds §6.

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


