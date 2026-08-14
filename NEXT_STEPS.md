# NLP Capstone — Next Steps

*Plan date: 2026-08-14. Supersedes the "Still to do" list in `SESSION_STATE.md` (2026-07-26); retire that file once P1–P2 below are done.*

## Where the project actually stands

- Paper (Study 1) **submitted 2026-07-25** (git tag `capstone-submitted-2026-07-25`). The frontier comparison, all four architecture results, and the RQ1 audit scoring are done and committed.
- **Nothing has been committed since the submission tag.** All post-submission work — the BOND port, distant-supervision labeler, external-corpus eval tooling, the entire cross-corpus eval campaign, and the Study 2 design — exists only as uncommitted/untracked files in the working tree.
- **`paper/study2-design.md` (2026-07-26) is a complete, pre-registered design for the follow-up study** ("Redeeming Silver": document-local STIX silver + deterministic regex tier + external-corpus transfer, judged against frozen gold). It has a go/no-go Phase 0 pilot and a ~4–6 week phased timeline. Nothing beyond its feasibility censuses has been run. This is the project's main forward thread.
- **BOND Stage II (self-training) finished 2026-07-26 14:56** (`external/bond/outputs/cti_bond/test_results.txt`: test F1 0.647, P 0.701 / R 0.601; best-checkpoint F1 0.687). It was never evaluated against this project's own gold — that was the whole point of training it. (BOND + `ner/distant_labels.py` are the regenerated dictionary-silver baseline Study 2's RQ2 arm B2 needs.)
- Cross-corpus eval: GLiNER phase complete (10/10 runs), frontier phase 4/5 corpora complete. **CyberNER is stalled at 175/200 claude-sonnet calls on exhausted Anthropic API credits**; gemini never started. These corpora are also Study 2's RQ3 external-transfer source material.
- **New capability (2026-08-14): Google AlphaEvolve access.** Evolutionary code search against an automated evaluator — and this project already has the two things it needs: heuristic tiers expressed as code (regex grammars, STIX projection, alias matching) and a machine-scorable fitness function (`ner.evaluate.Scorer`). Integrated below as P3.3.
- `paper/capstone/revision.md` holds unprocessed post-submission revision notes.
- `CLAUDE.md` still says "No open items remain" and "MalwareTextDB … not yet wired into any module" — both now false.

---

## P1 — Preserve the work (do first, ~30 min)

Three weeks of uncommitted work is one bad `git clean` away from gone.

**P1.1 Commit the post-submission changeset** in logical chunks:
- Design doc: `paper/study2-design.md` — the most valuable uncommitted file in the repo.
- Modified: `.gitignore`, `ner/frontier_infer.py` / `frontier_extract.py` (additive `--input-jsonl`/`--labels-file`/`--limit` flags), `ner/annotation_text.py`, `ner/llm_gold.py`, `requirements-ml.txt` (transformers range fix for the gliner/docling conflict).
- New tooling: `ner/distant_labels.py`, `ner/external_corpus_convert.py`, `ner/external_eval_gliner.py`.
- New data: `data/gold_v2/distant.jsonl`; `external/bond/` ported code + `dataset/cti_distant/` + `run_bond_training.sh` (venv/outputs/pretrained already gitignored); `external/uco/` (decide: commit or gitignore the ontology).
- Notes: `paper/notes/future-work-annotation-tooling.md`, `paper/capstone/revision.md`, `paper/capstone/time_mgmt.md`.
- Triage the leftovers: `capstone.pdf` (root copy), `data/roberta_results/`, `data/frontier_results/gemma3-27b-entities.truncated-old.jsonl`, `paper/capstone/acl2023/` + latexmk droppings (`*.fdb_latexmk`, `*.fls`) — commit, gitignore, or delete each deliberately.
- Before committing: confirm `.env` stays ignored, and that no license-restricted external corpus data leaves the gitignored `data/evals/` zone (redistribution of NER corpora is frequently prohibited — baking one into git history is expensive to undo).
- **Done when:** `git status` is clean and each commit message says which thread it belongs to.

## P2 — Close out the cross-corpus eval campaign (~half a day + API spend)

Finishes the Study-1-adjacent loop and produces inputs Study 2 reuses.

**P2.1 Evaluate BOND against the project's own gold** (SESSION_STATE "task #4"):
- Write a BOND inference wrapper (token-classify → argmax → BIO→spans → map to `eval.jsonl` token indices via `chunk_start`; `ner.evaluate.Scorer` is reusable, `predict_document_spans` is not — it assumes a GLiNER interface).
- Score `external/bond/outputs/cti_bond` against `data/gold_v2/eval.jsonl` with `split_full.json`.
- **Done when:** `data/gold_v2/results/trained-bond.json` exists in the same shape as `trained-roberta-base.json`. Est. 2–3 h (the wrapper is the work).

**P2.2 Resume + finish the CyberNER frontier eval:**
- Blocker: add Anthropic API credits. Then run the exact resume commands preserved in `SESSION_STATE.md` § "Resuming CyberNER" (claude-sonnet resumes at 176/200 automatically; gemini runs all 200; then extract + score both).
- Comparability check at the resume seam: pin the same model snapshot the first 175 calls used, and verify no slug is double-counted or skipped across the boundary before scoring.
- **Done when:** `data/evals/results/frontier-cyberner-{claude-sonnet,gemini-3.5-flash}.json` exist. Est. 1 h wall-clock, ~25 + 200 Claude calls + 200 Gemini calls of spend.

**P2.3 Write `data/evals/results/SUMMARY.md`** — the never-delivered synthesis:
- One table per corpus (AnnoCTR, AZERG, CyberNER, APTNER, AttackER, CyNER); rows = gliner-zeroshot / gliner-finetuned / claude-sonnet / gemini-3.5-flash; columns = strict F1 / P / R / n / time / cost (standing convention: never report F1 without time + cost).
- Lead with the headline finding already in hand: fine-tuning on our 16-label schema helps zero-shot transfer on 4/5 external schemas but *hurts* AttackER (0.169 → 0.111, long-STIX-span distribution mismatch).
- **Done when:** the file renders every completed run and flags any still-missing cell. Est. 1–2 h. Depends on P2.2 for completeness (can draft before, with CyberNER cells marked pending).

**P2.4 Decide: sweep BOND through the 5-corpus eval?**
- Only the 4 GLiNER/frontier-eligible architectures were swept. Decide yes/no and record the rationale in SUMMARY.md either way (a fixed-head token classifier needs per-corpus label mapping — nontrivial).
- **Done when:** a decision + rationale is written down. Est. 15 min to decide.

## P3 — Study 2: "Redeeming Silver" (the main forward thread, ~4–6 weeks phased)

Everything is already designed in `paper/study2-design.md` — follow its own phase plan rather than re-deciding scope. The immediate, cheap step:

**P3.1 Phase 0 go/no-go pilot (no GPU, ~1 day):**
- Build the `stix_silver` generator: project each advisory's own STIX bundle onto its own `clean.md`, score the projection as predictions against curated gold on the 9 measured STIX∩eval docs with `ner.evaluate.Scorer`.
- Honor the design's **one-shot rule**: freeze the STIX→label mapping *before* the audit; no mapping revisions after seeing eval-doc results (mapping debugging only on STIX∩train projections).
- **Gate (pre-registered):** covered-class precision ≥0.80 AND recall ≥0.50 → proceed to full RQ2/RQ3; precision <0.60 → kill the doc-local arm and degrade gracefully to RQ1 + RQ3(external-only) + RQ4.
- **Done when:** the gate verdict is recorded with the measured numbers.

**P3.2 Phases 1–4 per the design's timeline** (regex tier + corpus mapping ~1 wk → A/B training arms on Colab ~1–2 wk → C/D arms ~1–2 wk → analysis + paper ~1 wk). 3 seeds on starred arms per lesson L5 (seed variance ~2 points). Don't start Phase 1 until the Phase 0 verdict is in.

**P3.3 AlphaEvolve integration** — slot into Study 2 rather than run beside it. The design's A0 arm (Tier D standalone) and RQ1a already contain the natural ablation: hand-written grammars vs evolved ones. RQ4's cost frontier gains a new point whose price is compute, not annotation.

- **P3.3.0 Onboarding spike (~half day, do alongside Phase 0):** confirm the access modality (evaluator API shape, candidate-program format, quotas, cost model). Build the fitness harness once: `ner/evolve_fitness.py` wrapping `ner.evaluate.Scorer` — candidate extractor code in, per-label strict span F1 out, computed on **train-split docs only**. **Done when:** the current `span_validators.py` grammars round-trip through the harness as a seed candidate and produce a baseline score.
- **P3.3.1 Evolve Tier D (the flagship target):** seed = the 8 closed-grammar extractors (`ner/regex_tier.py` per the design's module plan), plus the free-extension labels (domain name / url / mutex). Let evolution work on defang handling, boundary rules, and artifact-broken-hash recovery. To prevent overfitting the 66 train docs, split them into evolve/holdout folds — fitness on the evolve fold, selection on the holdout fold; the frozen eval set is scored **once**, after the winner is committed and hash-frozen. **Done when:** evolved-vs-hand-written per-label F1 lands in the RQ1a table. Est. spike + 1–2 days of evolution runs.
- **P3.3.2 (guarded) Evolve the `stix_silver` alias matching:** fitness on STIX∩train projections only, same discipline the design already imposes on mapping debugging. Declare any evolved mapping as a separate pre-registered arm (e.g. B1-evolved) *before* its single eval-doc scoring — never as a post-hoc revision of the Phase 0 mapping, which would violate the one-shot rule. Only pursue if Phase 0 passes its gate.
- **P3.3.2b Evolve the tier-arbitration / routing policy (possibly higher-value than Tier D itself):** the composition rule (D-over-N precedence, overlap resolution) plus "which sentences escalate to the expensive model" is a decision program — exactly what evolutionary search handles well, and natively multi-objective: maximize train F1 subject to ≤X LLM calls/doc. Sweeping X produces the RQ4 cost-frontier *curve as a direct output* and improves every results row, not one. Same train-only harness, no new leak surface.
- **P3.3.2c Evolve a model-agnostic span post-processor:** boundary repair, article stripping, version-number attachment, overlap resolution — evolved over frozen upstream predictions (any architecture). Boundary errors are typically a large error slice; the gain transfers to Tier D, BOND, SecureBERT, and the LLMs simultaneously at ~zero inference cost.
- **P3.3.3 (optional, cost-gated) Prompt-arm evolution** for `frontier_infer`/`llm_gold`: prefer evolving **few-shot exemplar selection** over prompt prose, with fitness run against a cheap local model (Ollama) and a single transfer test to the frontier model — smaller search space, typically bigger gain, 10–50× cheaper; state the cheap-to-frontier transfer risk explicitly. Either way, estimate total spend (candidates × generations × docs) *before* launching per the standing time/cost convention.
- **P3.3.4 (nearly free, interesting) Memorization-ceiling probe:** deliberately over-evolve Tier D on the evolve fold and report the train-fit vs holdout gap — an empirical measure of how corpus-specific "regex NER performance" is. Must be its own pre-registered arm (or holdout-only), never mixed into the headline numbers.
- **Guardrails (non-negotiable):** (1) evolution fitness never touches eval/test gold — train split only, frozen eval scored once per pre-registered arm; (2) evolved artifacts are committed and hash-frozen before that single scoring run; (3) RQ4 accounting: evolution compute is a *development* line item separate from per-doc inference cost, includes abandoned/failed arms' spend (else the frontier is cherry-picked), and counts AlphaEvolve's own internal LLM calls — an evolved regex is not "free" just because inference is.

## P4 — Paper revision thread (only if a revised Study-1 version is actually due)

First check: is there a real venue/deadline for a revision, or is `revision.md` aspirational? If no deadline, park P4 — its future-work content is largely absorbed by Study 2 anyway. If a revision IS due, declare a results-freeze point first: P2 results may enter it, but don't let in-flight Study 2 numbers drag the revision into a second rewrite.

**P4.1 Triage `paper/capstone/revision.md`** into: (a) factual fixes worth making (e.g., acknowledge CISA's in-document STIX/IoC structure as an unleveraged source — now literally Study 2's premise), (b) content that contradicts final findings — the GLiNER zero-shot-retention paragraph in revision.md restates the *refuted* hypothesis (the paper's actual finding is the reverse: GLiNER weakest at 0.56 once fairly retrained); it must not be pasted into any revision — and (c) genuine future work already covered by study2-design.md (regex pre-processing, capitalization loss, entity-frontmatter proposals).
- **Done when:** each block of revision.md is labeled fix / discard / covered-by-study2, and (a) items are applied to the LaTeX source.

## P5 — Documentation hygiene (~30 min, after P1–P2)

- **P5.1 Update `CLAUDE.md`:** remove "No open items remain"; replace the stale `data/evals/` description with the real 6-corpus + results layout; document `external/bond/` (incl. the MPS-corrupts-optimizer-step finding and the `--no_cuda` requirement), `ner/distant_labels.py`, the external-eval modules, and point to `paper/study2-design.md` as the active thread.
- **P5.2 Retire `SESSION_STATE.md`** (it says "delete once no longer needed") after its remaining content is absorbed here and into CLAUDE.md.
- **Done when:** a fresh session can orient from CLAUDE.md alone.

## P6 — Optional / stretch

- **P6.1 CTIfecta corpus:** manual download via the two figshare URLs in `data/evals/CTIfecta-NOTES.md` (AWS-WAF-blocked for bots); would make the cross-corpus sweep 7 corpora and widen Study 2's RQ3 pool.
- **P6.2 Annotation-tooling future work** (`paper/notes/future-work-annotation-tooling.md`): cheapest first step already scoped — instrument `ner/hitl_ner.py` with a reject-reason field.

---

## Suggested order

`P1.1 → P3.1 (Phase 0 pilot — cheap, gates everything) ∥ P3.3.0 (AlphaEvolve spike) → P2.1 → (credits) P2.2 → P2.3 → P2.4 → P3.3.1 (evolved Tier D, inside Phase 1) → P5 → P3.2 phases → P4 (if deadline) → P6`

P1 is insurance. P3.1 comes early because it's one CPU-day and its go/no-go verdict determines the shape of the next month; the AlphaEvolve spike runs in parallel because the fitness harness it produces is needed the moment Phase 1 starts. P2 closes the Study-1 loop and feeds Study 2. The rest is polish or stretch.
