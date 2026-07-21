# Discovery Log — CTI NER Survey

Tracks ISC-37..42. Forward citations via Semantic Scholar (`/graph/v1/paper/arXiv:{id}/citations`); keyword/gap searches via arXiv API. Acceptance cap: 15 papers (ISC-42). **Accepted so far: 5/15.**

## Sweep 1 — 2026-06-09 — forward citations, 5 anchors

Anchors swept: 2311.08526 (GLiNER), 2404.07765 (AnnoCTR), 2510.26499 (CyberNER), 2406.07599 (CTIBench), 2507.13870 (label unification). Filter: year ≥ 2025, CTI/NER relevance.

### Accepted (downloaded to data/papers/, PDF + AlphaXiv markdown)

| arXiv ID | Title | Via | Section gap justification |
|----------|-------|-----|---------------------------|
| 2507.16576 | From Text to Actionable Intelligence: Automating STIX Entity and Relationship Extraction | cites AnnoCTR | Methods §5.6/5.7 — STIX-targeted extraction is the survey's structuring step; extends beyond NER to relations |
| 2507.06252 | False Alarms, Real Damage: Adversarial Attacks Using LLM-based Models on Text-based CTI Systems | cites AnnoCTR | Open Problems — adversarial robustness of CTI extraction, a problem category our ledger lacked entirely |
| 2602.17458 | The CTI Echo Chamber: Fragmentation, Overlap, and Vendor Specificity in Twenty Years of Cyber Threat Reporting | cites CTIBench | Datasets/Open Problems — empirical grounding for the fragmentation thesis at the *source text* level, not just labels |
| 2602.00513 | Minerva: RL with Verifiable Rewards for Cyber Threat Intelligence LLMs | cites CTIBench | Methods §5.6 — 2026 SOTA for LLM-based CTI extraction; RLVR is a post-GLiNER supervision paradigm (ISC-41 recency) |
| 2602.18487 | The Million-Label NER: Breaking Scale Barriers with GLiNER Bi-encoder | cites GLiNER | Methods §5.5 — 2026 SOTA scaling of the span-matching family (ISC-41 recency) |

### Watch list (relevant, not on arXiv — cite as secondary if needed)

- ~~**LETNER: Label-EfficienT NER for Cyber Threat Intelligence**~~ — **RESOLVED 2026-06-09: principal provided the ESWA PDF** (PII S0957417426013837). Filed as `eswa-2026-LETNER-label-efficient-CTI-NER.{pdf,md}` (pypdf extraction), bibliography entry complete. Principal-provided papers don't count against the 15-paper discovery cap. Acceptance count remains 5/15.
- **SoK: Automated TTP Extraction from CTI Reports — Are We There Yet?** (2025, cites AnnoCTR) — an SoK overlapping our §6; MUST at least be acknowledged in related-surveys positioning. Hunt DOI/venue PDF next iteration.
- **CyBERTa: hybrid self-updating ATT&CK extraction** (2026, cites AnnoCTR) — venue-only.
- **CTIExpert: Expert-Level CTI Extraction for KG construction** (2026, cites CTIBench) — venue-only.

### Rejected (sampled; full S2 responses not retained)

- GLiNER citations in non-security domains (clinical, historical NER, PII, parliamentary debates, bioinformatics) — off-scope per Out of Scope.
- CTIBench citations that are LLM-agent/SOC benchmarks without an extraction component (ExploitBench, CyberCertBench, ThreatSage, ISPM benchmarks, model technical reports) — adjacent but not NER/extraction.
- 2510.26499 and 2507.13870 have thin citation trails so far (1–2 citing papers) — both already in corpus.

## Sweep 2 — 2026-06-09 — KG scope extension (principal-approved), arXiv keyword search

Query: `"knowledge graph" AND "cyber threat intelligence"` in cs.CR/cs.CL, newest-first. Cap raised 15→25 with principal approval. **Accepted 10 (now 15/25):** 2606.01208 (Schema-Agnostic ontology discovery), 2605.16714 (GRID), 2411.08359 (MultiKG), 2410.21060 (CTINexus), 2407.02528 (Actionable CTI KG+LLM), 2405.04753 (AttacKG+), 2212.10388 (ThreatKG), 2208.01693 (cybersec entity extraction), 2204.04769 (KG-in-cybersec review — positioning target), 2111.07093 (AttacKG).

**Rejected per ISC-48 (consumption-side, watch-list only):** 2604.11419 (Beyond RAG — graph retrieval), 2510.14670 (TITAN — graph reasoning), 2408.08088 (KGV — credibility assessment), 2503.03170 (AttackSeqBench — sequence understanding), 2410.16016 (CAV-specific modeling).

Also resolved: GLiNER-Relex (2605.10108, already in corpus) read and annotated — principal-flagged.

## Sweep 3 — 2026-06-10 — LETNER forward citations (Semantic Scholar)

LETNER resolved: DOI 10.1016/j.eswa.2026.132470, S2 paperId 0e5ecd4648d3bc2e176848cf80473195cf938377. Citation count: 0 — too recent to have citers. Re-check in a future sweep using the DOI directly.

## Sweep 4 — 2026-06-10 — taxonomy/ontology SOTA (principal-requested)

Query: CTI + ontology/taxonomy in cs.CR/cs.CL. **Accepted 4 (now 19/25):** 2103.03530 (taxonomies/standards/ontologies evaluation — section anchor), 2512.00857 (Hesperus: actor-naming taxonomy mapping at scale — thesis evidence), 2509.00081 (LLM + domain ontologies), 2605.31199 (MAECO-Lite modular malware ontology). Rejected/watch: 2604.14166 (hierarchical RAG technique annotation — TTP-mapping side, revisit in iteration 5), 2110.10540 (CACAO playbooks — cover via 2103.03530), 2103.02301 (actor type inference), 2406.13543 (IoT-specific).

## Sweep 5 — 2026-07-18 — forward citations, remaining anchors (principal-requested SOTA check)

Anchors swept: 2507.18546 (GLiNER2), 2408.05149 (AttackER), 2512.19414 (TTPrompt), 2006.15509 (BOND), 2311.08010 (CENSOR), 2511.01144 (AthenaBench), 2602.00513 (Minerva). 2602.18487 (bi-encoder) attempted twice, both 429 rate-limited — not completed this sweep.

**Not yet accepted — presented to principal for triage (see conversation); nothing added to corpus yet.**

### High relevance (directly on-topic, currently missing from corpus)

- **CyberLLaMA: A fine-tuned large language model for cybersecurity named entity recognition** (Zhang et al., 2025, cites AttackER) — directly on-topic (LLM fine-tuned specifically for CTI NER); no arXiv ID surfaced yet, venue unknown — needs a follow-up search before it can be fetched.
- **Enhanced Cybersecurity Entity Recognition Using DeBERTa, Transformer-CNN Hybrids, and BiLSTM-Softmax** (Yadulla, Kasula, Alshboul, 2025, cites AttackER) — directly on-topic architecture comparison for CTI entity recognition; no arXiv ID surfaced, venue unknown.
- **A novel ontology for cyber-attack attribution and investigation** (Gill & Karafili, 2026, cites AttackER) — direct follow-up by an AttackER author; Taxonomies §2.3 candidate; no arXiv ID surfaced.

### Medium relevance (adjacent methods or positioning value)

- **Llama-3.1-FoundationAI-SecurityLLM-8B-Instruct Technical Report** (Weerawardhena et al., 2025, arXiv:2508.01059, cites AttackER) — security-domain fine-tuned LLM; Methods §5.6 SOTA candidate.
- **A RAG-Based Question-Answering Solution for Cyber-Attack Investigation and Attribution** (Rajapaksha, Rani, Karafili, 2024, arXiv:2408.06272, cites AttackER) — same author group as AttackER; KG/downstream-use section candidate.
- **Evaluating Large Language Models in Cybersecurity: A Systematic Taxonomy and Empirical Analysis** (2026, cites AthenaBench) — broader eval-methodology survey; Evaluation §8 positioning candidate; no arXiv ID surfaced.
- **Before You Hand Over the Wheel: Evaluating LLMs for Security Incident Analysis (SIABENCH)** (2026, arXiv:2603.06422, cites AthenaBench) — agentic security-incident benchmark, broader than NER; possible Evaluation §8 mention only.

### Rejected (off-scope, sampled)

- CENSOR sweep: all 6 citers off-topic (cross-lingual NER, historical-text NER, low-resource sequence labeling generally — none cybersecurity).
- AttackER sweep, rejected: "Forewarned is Forearmed" (LLM agents in autonomous cyberattacks — offense survey, not extraction), "Generative AI and LLMs for Critical Infrastructure Protection" (too broad, review-of-reviews).
- AthenaBench sweep, rejected: Qwen3-Coder-Next Technical Report (coding model, off-topic).
- GLiNER2 sweep, rejected (already logged 2026-07-15 in the corrected bibliography pass): medical-encoder pretraining, PrionNER, chain-of-thought PII leakage, medieval-Latin GLiNER2 application — all off-domain. One near-miss worth noting: **GLiNER Guard: Unified Encoder Family for Production LLM Safety and Privacy** (Minko, Sadiekh, Kokuykin, 2026, arXiv:2605.05277) independently reuses the name "GLiGuard" for an unrelated safety-encoder system — different authors, different paper, from the GLiGuard already in this corpus (2605.07982, Zaratiana et al./Fastino). Not accepted as a new corpus entry (redundant with existing GLiGuard coverage of the same *idea* — safety-classification via a GLiNER-family encoder) but flagged here so the name collision doesn't cause confusion later.
- Minerva (2602.00513): zero citers — too recent.
- Bi-encoder (2602.18487): sweep not completed, Semantic Scholar rate-limited twice; retry in a future sweep.

## Pending sweeps

- Complete the bi-encoder (2602.18487) forward-citation sweep (rate-limited out this time).
- Locate arXiv/venue IDs for the three no-ID high-relevance candidates above (CyberLLaMA, DeBERTa/Transformer-CNN entity paper, Karafili attribution-ontology paper) so they can be fetched.
- Gap-driven keyword searches (ISC-38): source dataset papers (APTNER 2204.05943?, CyNER 2204.05754, DNRTI — verify IDs before download), domain encoders (SecureBERT), "zero-shot NER cybersecurity 2025-2026" recency sweep in cs.CR.
- arXiv API note: empty grep on piped response happened once (HTTP redirect to https) — use `curl -sL` and write to file before parsing.
- Semantic Scholar note: unauthenticated API rate-limits aggressively (429 even on single sequential requests after a burst of ~4); space sweeps by several minutes or acquire an API key for future large sweeps.
