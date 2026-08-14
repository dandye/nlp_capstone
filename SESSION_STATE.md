# Session state — 2026-07-26, context clear pending

Handoff doc for continuing this work in a fresh session. Delete once no longer needed — not permanent project documentation. **Nothing from this session has been committed yet** — see "Uncommitted changes" at the bottom before doing anything git-related.

## Background process still running RIGHT NOW

**BOND Stage II (self-training) — PID 71828**, CPU, log at `/tmp/bond_stage2.log`. Started 2026-07-26 ~10:45AM, currently epoch 12/20 (~2h05m elapsed, ~680s/epoch, ETA another ~90 min from whenever you read this — check `tail -5 /tmp/bond_stage2.log` for live progress, or `ps aux | grep run_self_training_ner` to confirm it's still alive). Command was:

```bash
cd external/bond/ported
external/bond/.venv/bin/python3 run_self_training_ner.py \
  --data_dir ../dataset/cti_distant/ --model_type roberta --model_name_or_path roberta-base \
  --learning_rate 1e-5 --weight_decay 1e-4 --adam_epsilon 1e-8 --adam_beta1 0.9 --adam_beta2 0.98 \
  --warmup_steps 200 --per_gpu_train_batch_size 64 --per_gpu_eval_batch_size 64 \
  --logging_steps 100 --save_steps 100000 --no_cuda \
  --do_train --do_eval --do_predict --evaluate_during_training --cache_dir ../pretrained_model \
  --seed 0 --max_seq_length 256 --overwrite_output_dir --num_train_epochs 20 \
  --output_dir ../outputs/cti_bond --self_training_reinit 0 --self_training_begin_step 240 \
  --self_training_label_mode soft --self_training_period 100 --self_training_hp_label 7.9
```

When it finishes, result lands at `external/bond/outputs/cti_bond/test_results.txt`. **Monitors/notifications from the old session will NOT survive a context clear** — a fresh session needs to check the log/process directly, not wait for a notification.

**Task #4 (not started yet, blocked on Stage II finishing):** Evaluate the final BOND checkpoint against `data/gold_v2/eval.jsonl` (this project's own human-curated gold, not BOND's internal distant-label test set) — needs a new bespoke script since BOND is a token-classification model, not GLiNER; `ner/evaluate.py`'s `Scorer`/`predict_document_spans` are reusable but `predict_document_spans` assumes a GLiNER-style `.predict_entities()` interface, so BOND needs its own inference wrapper (tokenize per BOND's scheme, argmax logits, decode BIO→spans, map back to `eval.jsonl`'s token indices via `chunk_start`). Output should go to `data/gold_v2/results/trained-bond.json` matching the shape of `trained-roberta-base.json` etc.

## What's fully done

1. **Distant-supervision weak labeler** (`ner/distant_labels.py`) — regex + MITRE ATT&CK gazetteer, run over the 67 non-held-out advisories → `data/gold_v2/distant.jsonl`.
2. **BOND ported + fixed** (`external/bond/`) — see "BOND root cause" below. Stage I done: **test F1 0.7212** (P 0.7165/R 0.7259), `external/bond/outputs/cti_baseline/test_results.txt`. Matches historical scrape_cisa run's 0.7208 on a totally different (current LLM-gold-derived) weak-label corpus.
3. **6 CTI corpora acquired** into `data/evals/`: AnnoCTR, AZERG, CyberNER, APTNER, AttackER, CyNER (all gitignored data, real files on disk — NOT lost, that only happened once early on when a worktree-isolated agent got auto-cleaned; everything since was done directly in the main checkout). CTIfecta (7th) is genuinely blocked by an AWS WAF bot-check — see `data/evals/CTIfecta-NOTES.md` for the two figshare URLs (found by grepping raw PDF bytes, not visible as clickable links) if you want to grab it manually.
4. **Cross-corpus eval Phase 1 (GLiNER zero-shot)** — complete, 10/10 runs (5 corpora × zeroshot/fine-tuned). Results in `data/evals/results/gliner-*.json`. Headline finding: fine-tuning on our own 16-label schema helps zero-shot transfer to 4/5 external schemas, but *hurts* on AttackER (0.169→0.111) — plausibly because AttackER deliberately uses long STIX-derived spans, a different span-length distribution than our training data.
5. **Cross-corpus eval Phase 2 (frontier LLM)** — 4/5 corpora done (CyNER, APTNER, AttackER, AnnoCTR), both claude-sonnet and gemini-3.5-flash, capped at 200 sentences/corpus (131 for AttackER, its full size). Results in `data/evals/results/frontier-*.json`. **CyberNER is incomplete** — blocked on Anthropic API credits running out mid-sweep (`Your credit balance is too low`). claude-sonnet got 175/200 through before failing; gemini-3.5-flash never started for CyberNER. `frontier_infer.py` has native resume (skips slugs already in its output jsonl) — once credits are added back, just re-run the same commands (see "Resuming CyberNER" below), no wasted spend.
6. **UCO ontology 1.5.0** downloaded into `external/uco/`.
7. **Annotation-tooling research question** written up at `paper/notes/future-work-annotation-tooling.md` — NOT part of the submitted paper, explicitly future work. Git tag `capstone-submitted-2026-07-25` marks the submission state.
8. **A CRITICAL bug was found and fixed in the frontier scoring pipeline**: when `frontier_infer.py --limit 200` samples a subset, `frontier_score.py` was originally scoring against the *full* test-split size (e.g. 748 for CyNER) instead of the 200 actually inferred — inflating false negatives for the ~550 never-attempted documents and crushing recall numbers. Fixed by rewriting each corpus's `data/evals/{Corpus}/split.json` `"test"` list to the actual sorted-first-N slugs that `--input-jsonl` mode selects. **This fix is already applied and verified correct for all 5 corpora's completed results** — nothing needs re-scoring.

## BOND root cause (the big rabbit hole this session)

Training on **MPS silently corrupts model weights inside `optimizer.step()`** — confirmed via direct instrumentation: gradients were finite going into the optimizer call (checked via `p.grad.isnan()/isinf()` on every parameter), but the very next forward pass produced NaN logits. Ruled out along the way, in order: SDPA-vs-eager attention (real effect, but insufficient alone), `AdamW(foreach=False)` (no effect), out-of-range token ids (none found), an "all-ignored-batch" `CrossEntropyLoss` edge case (ruled out — 7,688 real labels were present in the failing batch). **The only fix that actually worked was forcing CPU (`--no_cuda`)** — a full 25-epoch Stage I run on CPU completed cleanly with zero NaN and a real, good F1.

Debug instrumentation (NAN_DEBUG/GRAD_DEBUG print blocks) and the two dead-end fixes (eager attention, foreach=False) have all been **removed/reverted** from `external/bond/ported/run_ner.py` and `run_self_training_ner.py` — those files are back to clean ported code plus the one real fix (`--no_cuda`, baked into `external/bond/run_bond_training.sh`'s `TRAIN_COMMON`). One additional real bug fixed along the way: `run_ner.py`'s `--do_predict`-without-`--do_train` path had a pre-existing `UnboundLocalError` on `best_test` — fixed with a `"best_test" not in dir()` guard.

**Do NOT re-run `run_bond_training.sh` as-is** — it would redo Stage I from scratch (already done, ~4hrs on CPU) before starting Stage II. Stage II was launched directly instead (see command above). If you ever need to redo Stage I: the script is fine to run standalone now that `--no_cuda` is baked in.

## Resuming CyberNER frontier eval (once API credits are added)

```bash
cd /Users/elwood/Projects/nlp_capstone
set -a; source .env; set +a   # loads ANTHROPIC_API_KEY / GEMINI_API_KEY — NOT in the raw shell env by default

# claude-sonnet: resumes from call 176/200 automatically (skips done slugs)
PYTHONPATH=. .venv-ml/bin/python3 -m ner.frontier_infer \
  --input-jsonl data/evals/CyberNER/eval.jsonl --labels-file data/evals/CyberNER/labels.json \
  --output-dir data/evals/results/frontier_raw/cyberner --models claude-sonnet --limit 200

# gemini: hasn't started, full 200 calls
PYTHONPATH=. .venv-ml/bin/python3 -m ner.frontier_infer \
  --input-jsonl data/evals/CyberNER/eval.jsonl --labels-file data/evals/CyberNER/labels.json \
  --output-dir data/evals/results/frontier_raw/cyberner --models gemini-3.5-flash --limit 200

# then for each model: extract + score
for m in claude-sonnet gemini-3.5-flash; do
  PYTHONPATH=. .venv-ml/bin/python3 -m ner.frontier_extract \
    --entities data/evals/results/frontier_raw/cyberner/$m-entities.jsonl \
    --input-jsonl data/evals/CyberNER/eval.jsonl --labels-file data/evals/CyberNER/labels.json \
    --output-file data/evals/results/frontier_raw/cyberner/$m-spans.jsonl
  PYTHONPATH=. .venv-ml/bin/python3 -m ner.frontier_score \
    --predictions data/evals/results/frontier_raw/cyberner/$m-spans.jsonl \
    --data data/evals/CyberNER/eval.jsonl --split data/evals/CyberNER/split.json \
    --output data/evals/results/frontier-cyberner-$m.json
done
```

## Still to do

- [ ] Wait for BOND Stage II, then task #4 (evaluate BOND against `gold_v2/eval.jsonl`, write `trained-bond.json`)
- [ ] Resume + finish CyberNER frontier eval once API credits are added
- [ ] Write `data/evals/results/SUMMARY.md` — one table per corpus, rows = gliner-zeroshot/gliner-finetuned/claude-sonnet/gemini-3.5-flash, columns = strict F1/P/R/n/time/cost (per this project's standing convention of never reporting F1 without time+cost). This was originally Task 4 of the eval-pipeline brief and never got done because the pipeline agent ran out of budget before reaching it.
- [ ] Decide whether/how BOND's cross-corpus results should also run through the same 5-corpus eval (not done yet — only the 4 GLiNER/frontier-eligible architectures were swept)
- [ ] Optional: CTIfecta manual download (see NOTES.md) if wanted
- [ ] Optional: pick up the annotation-tooling future-work item (`paper/notes/future-work-annotation-tooling.md`) — cheapest next step noted there is instrumenting `hitl_ner.py` with a reject-reason field

## Uncommitted changes (nothing committed this whole session)

Modified: `.gitignore`, `ner/frontier_extract.py`, `ner/frontier_infer.py` (both got additive `--input-jsonl`/`--labels-file`/`--limit` flags, backward compatible), `requirements-ml.txt` (tightened `transformers` range to `>=4.51.3,<5.9.0` — a real pre-existing latent conflict between `gliner` and `docling`, unrelated to BOND).

New, untracked: `external/` (BOND port + UCO ontology — `external/bond/.venv` and `external/bond/outputs`/`pretrained_model` are gitignored via the generic `.venv/` pattern already in `.gitignore`, but the ported *code*, `dataset/cti_distant/*.json`, and `run_bond_training.sh` are real tracked-eligible files), `ner/distant_labels.py`, `ner/external_corpus_convert.py`, `ner/external_eval_gliner.py`, `paper/notes/future-work-annotation-tooling.md`, `data/gold_v2/distant.jsonl`.

Also present but **not mine** — pre-existing untracked files from the user's own work, don't touch: `capstone.pdf`, `data/frontier_results/gemma3-27b-entities.truncated-old.jsonl`, `data/roberta_results/`, `paper/capstone/acl2023/`, `paper/capstone/*.fdb_latexmk`/`*.fls`, `paper/capstone/capstone_acm_style.pdf`, `paper/capstone/revision.md`, `paper/capstone/time_mgmt.md`.

`data/evals/` (all 6+ corpora, all `data/evals/results/*.json`) is entirely gitignored by design (matches the pre-existing `MalwareTextDB-1.0` pattern) — nothing there needs committing, it's regenerable/reference data.
