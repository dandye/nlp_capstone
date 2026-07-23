# Runbook: gemma3:27b frontier NER run (overnight)

**Status when this was written (2026-07-22):** exploratory. gemma3:27b is
**not needed for the capstone paper** — the paper's frontier comparison is
Gemini 3.5 Flash vs SecureBERT only, and it is frozen. This run adds a
local-27B data point for interest, not for publication. Do **not** edit
`paper/capstone/capstone.tex` or any paper file from this run, and do **not**
`git push`.

This runbook is self-contained. It assumes a fresh session with no prior
context. Follow it top to bottom.

---

## What already exists (and why it's insufficient)

`data/frontier_results/gemma3-27b-entities.jsonl` (8 docs, 290 raw entities)
is a **partial, truncated** stage-1 output from an earlier abandoned run. It
was almost certainly produced with 4000-char truncation, not full-document
chunking: Gemini over the same 8 docs produced **732** raw entities. Scoring
the truncated file would understate gemma unfairly. **This runbook re-runs
inference from scratch with chunking to match how Gemini was run**, so the
three models are compared on equal footing.

The frontier pipeline has **three stages**: `frontier_infer` (LLM →
entities) → `frontier_extract` (entities → character spans) → `frontier_score`
(spans → P/R/F1 vs gold). The old run only did stage 1.

---

## Preconditions (verify before the long run)

1. **Working directory:** `/Users/elwood/Projects/nlp_capstone`
2. **Python venv:** use **`.venv`** (CPU). Note: `CLAUDE.md` mentions a
   `.venv-ml` for ML work — that venv **does not exist on disk**; `.venv`
   carries torch/transformers and is correct. All commands below use
   `.venv/bin/python3`.
3. **Ollama running** with the model pulled:
   ```bash
   ollama list | grep gemma3:27b        # expect: gemma3:27b ... 17 GB
   ollama ps                            # if the daemon isn't up, start Ollama.app or `ollama serve`
   ```
   `--models gemma3-27b` maps internally to Ollama's `gemma3:27b`
   (see `ner/frontier_infer.py` `model_map`). No API keys are needed — this
   is a fully local run, zero API cost.
4. **Gold + split** (already present, no action needed):
   - split: `data/gold_v2/split_full.json` (its `test` list is the 8 docs)
   - gold:  `data/gold_v2/eval.jsonl`
   The 8 test slugs: aa23-129a, aa23-158a, aa23-193a, aa23-352a, aa25-022a,
   aa25-141b, aa25-163a, aa25-343a.

---

## Step 0 — preserve the old partial file, then smoke-test one stage

```bash
cd /Users/elwood/Projects/nlp_capstone
mv data/frontier_results/gemma3-27b-entities.jsonl \
   data/frontier_results/gemma3-27b-entities.truncated-old.jsonl
```

Smoke-test that Ollama answers before committing to the full run — this
hits the model once and should return in well under a minute if the daemon
is warm:

```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"gemma3:27b","prompt":"Reply with the single word OK.","stream":false}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('response','NO RESPONSE')[:80])"
```
If that prints something (ideally "OK"), proceed. If it errors or hangs,
the Ollama daemon is not serving `gemma3:27b` — fix that first.

---

## Step 1 — inference (the slow, overnight-worthy stage)

Full-document **chunked** inference (4000-char windows, 500-char overlap),
matching Gemini's methodology. Run it in the background and log to a file so
you can walk away:

```bash
cd /Users/elwood/Projects/nlp_capstone
PYTHONPATH=. nohup .venv/bin/python3 -m ner.frontier_infer \
    --split data/gold_v2/split_full.json \
    --markdown-dir data/alerts \
    --output-dir data/frontier_results \
    --models gemma3-27b \
    --subset test \
    --chunk-size 4000 \
    > data/frontier_results/gemma3-27b-infer.log 2>&1 &
echo "infer PID $!"
```

**Why `--chunk-size 4000` matters:** without it the module truncates each
advisory to 4000 chars and silently drops everything past that (the cause of
the old 290-entity file). `--chunk-size 4000` instead covers the whole
document in overlapping windows and merges the results.

**Time expectation:** gemma3:27b on local CPU/Metal is slow — plausibly many
minutes per document, and long advisories become several chunks each. Budget
hours, not minutes. This is why it's an overnight job. Monitor with:
```bash
tail -f data/frontier_results/gemma3-27b-infer.log
```

### Stage-1 verification gate (do NOT proceed until this passes)

```bash
python3 -c "
import json
rows=[json.loads(l) for l in open('data/frontier_results/gemma3-27b-entities.jsonl')]
n=sum(len(r['entities']) for r in rows)
print('docs:', len(rows), '| raw entities:', n)
assert len(rows)==8, 'expected 8 docs — inference did not finish'
assert n > 290, 'entity count <= old truncated run — chunking did NOT engage; check --chunk-size'
print('PASS: 8 docs, chunking produced more entities than the truncated baseline')
"
```
A healthy chunked run should land closer to Gemini's order of magnitude
(hundreds of entities), well above the old 290. If it fails the assert,
the chunking flag didn't take effect — re-check the Step-1 command.

---

## Step 2 — extract character spans

Fast (CPU, string matching against the source text). The truncation bug that
once corrupted this stage is already fixed (commit a50de67).

```bash
cd /Users/elwood/Projects/nlp_capstone
PYTHONPATH=. .venv/bin/python3 -m ner.frontier_extract \
    --entities data/frontier_results/gemma3-27b-entities.jsonl \
    --markdown-dir data/alerts \
    --output-file data/frontier_results/gemma3-27b-spans.jsonl
```

Verify the spans file is non-empty and has all 8 docs:
```bash
python3 -c "
import json
rows=[json.loads(l) for l in open('data/frontier_results/gemma3-27b-spans.jsonl')]
print('span-doc rows:', len(rows))
assert len(rows)>=8, 'fewer than 8 docs — extraction incomplete'
print('PASS')
"
```

---

## Step 3 — score against human-verified gold

```bash
cd /Users/elwood/Projects/nlp_capstone
PYTHONPATH=. .venv/bin/python3 -m ner.frontier_score \
    --predictions data/frontier_results/gemma3-27b-spans.jsonl \
    --data data/gold_v2/eval.jsonl \
    --split data/gold_v2/split_full.json \
    --subset test \
    --output data/frontier_results/gemma3-27b-scores.json
```

Read off the headline strict micro-F1:
```bash
python3 -c "
import json
d=json.load(open('data/frontier_results/gemma3-27b-scores.json'))
s=d['strict']; m=s.get('micro') or s
print('gemma3:27b strict micro P/R/F1:',
      round(s['micro']['P'],3) if 'micro' in s else '?',
      round(s['micro']['R'],3) if 'micro' in s else '?',
      round(s['micro']['F1'],3) if 'micro' in s else '?')
print('(full breakdown in the scores JSON)')
"
```

### Interpreting the result

Compare to the paper's frozen numbers on the identical 8-doc test set:
- **Gemini 3.5 Flash: 0.795 strict F1** (zero-shot cloud)
- **SecureBERT: 0.712 strict F1** (fine-tuned local, best in paper)
- gemma3:27b is zero-shot local — a different point on the cost/quality
  map (free + offline like SecureBERT, but no fine-tuning like Gemini).

This is a data point, not a paper claim. Note where gemma lands relative to
those two and whether its per-label profile resembles Gemini's (strong on
structured types, weaker on open-vocabulary ones).

---

## Finishing up

Three new files land in `data/frontier_results/`:
`gemma3-27b-entities.jsonl`, `-spans.jsonl`, `-scores.json`.

- **Committing is optional and your call.** If you want them tracked:
  ```bash
  git add data/frontier_results/gemma3-27b-*.jsonl data/frontier_results/gemma3-27b-scores.json
  git commit -m "Add exploratory gemma3:27b frontier run (not used in paper)"
  ```
  You can also `git rm --cached` / delete `gemma3-27b-entities.truncated-old.jsonl`
  once the fresh run is confirmed good.
- **Do NOT** `git push` without explicit go-ahead.
- **Do NOT** touch the paper. `capstone.tex` currently has uncommitted
  edits (an em-dash removal pass); leave them alone — they're unrelated to
  this run.

## If something goes wrong

- **Ollama hang / connection refused:** daemon not running or model not
  loaded. `ollama ps`, restart Ollama, re-run the Step-0 smoke test.
- **Stage-1 gate fails on entity count:** `--chunk-size 4000` didn't take;
  confirm the flag is present and re-run Step 1.
- **`frontier_score` KeyError / empty scores:** the `--data`/`--split`
  defaults in the module are stale (`data/gliner_train.jsonl`,
  `data/split_slugs.json`). Always pass the explicit
  `data/gold_v2/eval.jsonl` + `data/gold_v2/split_full.json` shown above.
- **Slugs mismatch:** the entities/spans slugs must equal the `test` list in
  `split_full.json` (the 8 listed under Preconditions). If they differ,
  `--subset test` and the split file are out of sync.
