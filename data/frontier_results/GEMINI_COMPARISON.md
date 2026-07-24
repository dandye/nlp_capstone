# Frontier NER Comparison (Gemini + Kimi)

**Date:** 2026-07-23 (regenerated programmatically from score files)
**Task:** CTI named-entity recognition, 8-doc CISA test set, 16 labels
**Gold:** human-curated LLM-proposed entities (`data/gold_v2/eval.jsonl`, split `split_full.json`)
**Baselines:** SecureBERT (fine-tuned) 0.712 strict F1; gemma3:27b (zero-shot local) 0.240

## Headline results (strict micro, exact span + label)

| Model | F1 | P | R | Macro F1 | Time/doc | Tokens (recorded) | Est. cost/doc* |
|---|---|---|---|---|---|---|---|
| gemini-3.5-flash | **0.795** | 0.739 | 0.859 | 0.791 | 1.6m | 350,277 | $0.131 |
| gemini-3.6-flash (default thinking) | **0.794** | 0.693 | 0.928 | 0.811 | 10.0m | 1,410,327 | $1.18 |
| kimi-k3 | **0.761** | 0.652 | 0.913 | 0.784 | 18.6m | 434,025 | n/a** |
| gemini-3.5-flash-lite | **0.752** | 0.694 | 0.822 | 0.762 | 0.5m | 210,533 | $0.020 |
| gemini-3.6-flash (thinking minimal) | **0.707** | 0.564 | 0.946 | 0.773 | 1.1m | 231,260 | $0.078 |
| claude-haiku-4.5 | **0.699** | 0.623 | 0.797 | 0.678 | 0.8m | 190,290 | $0.043 |
| claude-opus-4.8 | **0.420** | 0.285 | 0.795 | 0.652 | 1.9m | 247,576 | $0.28 |

\* Cost estimated from recorded per-run tokens at ACTUAL list rates
(ai.google.dev/gemini-api/docs/pricing, paid tier, 2026-07-23):
3.5-flash $1.50/$9.00 per MTok in/out; 3.6-flash $1.50/$7.50;
3.5-flash-lite $0.30/$2.50; claude-haiku-4.5 $1.00/$5.00;
claude-opus-4.8 $5.00/$25.00. Thinking tokens
bill at the output rate and ARE included in the recorded counts
(`total_token_count`). Non-thinking runs assume an 80/20 in/out split.
The default-thinking 3.6 run is decomposed differently: both 3.6 runs sent
identical prompts, so the minimal run's input estimate (~185K) is taken as
the thinking run's input, leaving ~1.23M output+thinking tokens; that
yields $9.47 for the run — a token-derived figure, independent of
account billing (which covered unrelated work and is not used here).
\** Moonshot pricing not folded in; kimi-k3 also used a different output
protocol (see below), so its cost is not directly comparable.
**claude-haiku-4.5 caveats:** (1) same-family bias — the gold was
*proposed* by Claude Sonnet (then human-curated), so a Claude-family model
may share span-boundary and label-choice conventions with the annotator;
despite that potential tailwind it still lands below SecureBERT (0.712).
(2) It near-totally ignores the `tactic` label: 1 entity emitted vs 111
gold mentions (per-label F1 0.00), the largest single-label failure of any
frontier model tested.

**claude-opus-4.8 caveat (0.420 strict F1 — read before citing):** the
collapse is a model-behavior x harness-design interaction, not raw
incapacity (macro F1 0.652; recall 0.795 is fine). Opus proposes short,
generic strings as entities — on aa23-129a (the Snake advisory, full of C
code excerpts) it emitted `'C'` as *affected software product*, which the
occurrence-locating extraction step multiplied into 372 spans; `'Windows'`,
`'RDP'`, `'PowerShell'`, `'Linux'` behave similarly. 754 deduped entities
became 5,563 spans (Haiku: 2,551). Every model runs through the identical
extract step; the others simply don't emit bare generic tokens. Same
same-family caveat as Haiku applies (Sonnet 5 gold). It also emitted 4
entities under an invalid `file_path` label (underscore variant).

**Thinking configs per run:** gemini-3.5-flash and 3.5-flash-lite ran with
`thinking_budget=0` (thinking fully off). gemini-3.6-flash rejects
`thinking_budget=0` (400 INVALID_ARGUMENT); its two rows are default
thinking vs `thinking_level="minimal"` — Google documents "minimal" as the
lowest level, not necessarily zero, so the no-thinking conditions across
model generations are close but not perfectly identical. Notably, 3.5-flash
reaches 0.795 with thinking fully off, while 3.6-flash needs default
thinking just to tie it.

**The thinking ablation (3.6-flash):** the two 3.6-flash rows are the same
model and prompt, differing only in `thinking_config`. Default thinking costs
~6x the tokens and ~9x the wall time, but buys +0.087 strict F1 — almost
entirely precision (0.693 vs 0.564; recall is flat at ~0.93–0.95). With
thinking minimal the model keeps its recall bias but stops filtering weak
candidates, collapsing precision on open-vocabulary labels
(affected software product 0.62→0.37, attack technique name 0.82→0.65,
threat actor group 0.60→0.51). So the earlier caveat's assumption that
"F1 is unaffected" was wrong: for 3.6-flash, thinking is load-bearing.
Cheap-and-fast 3.6-flash is *worse* than 3.5-flash-lite; thinking-on
3.6-flash matches 3.5-flash at ~4x the cost.

**kimi-k3 caveat:** Moonshot's API returned empty responses for any
structured-output (JSON) request, so kimi-k3 emitted free-form
`Entity | Label` lists that were located in the text by string search —
same downstream extract/score path, but the model never saw the JSON-offset
protocol the Gemini runs used. 18.6 m/doc is API latency, not compute depth.

## Reading

- **gemini-3.5-flash remains the best quality point** (0.795 F1,
  1.6 m/doc, ~$0.13/doc). 3.6-flash only ties it with default thinking
  enabled, at ~9x the estimated cost ($1.18/doc) and ~6x the wall time.
- **claude-haiku-4.5 is cheaper than 3.5-flash** (~$0.043 vs ~$0.13/doc)
  but scores 0.096 lower; 3.5-flash-lite dominates it on both cost
  and F1.
- **kimi-k3 (0.761)** slots between 3.5-flash and 3.5-flash-lite on F1 —
  above the fine-tuned SecureBERT baseline (0.712) — despite the degraded
  list-output protocol, but is by far the slowest (18.6 m/doc).
- **3.5-flash-lite** remains the value pick: 95% of flagship F1 at ~3x
  the speed and ~1/7 the cost (~$0.02 vs ~$0.13/doc).
- All Gemini runs except minimal-thinking 3.6-flash beat SecureBERT
  (0.712); both Claude models land below it (haiku 0.699, opus 0.420 —
  see the opus caveat). None approach SecureBERT's 1.8 s/doc offline
  throughput, and none are admissible for TLP:AMBER/RED material at any
  price.

## Per-label strict F1

| Label | 3.5-flash | 3.5-lite | 3.6-flash (min) | 3.6-flash (think) | kimi-k3 | haiku-4.5 | opus-4.8 | Support |
|---|---|---|---|---|---|---|---|---|
| affected software product | 0.65 | 0.51 | 0.37 | 0.62 | 0.59 | 0.47 | 0.08 | 159 |
| attack technique id | 0.99 | 0.99 | 0.99 | 0.99 | 0.98 | 0.97 | 0.98 | 297 |
| attack technique name | 0.75 | 0.72 | 0.65 | 0.82 | 0.69 | 0.44 | 0.81 | 144 |
| cve identifier | 0.96 | 0.96 | 0.96 | 0.96 | 0.96 | 0.87 | 0.87 | 55 |
| cwe identifier | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 4 |
| email address | 0.98 | 0.95 | 1.00 | 1.00 | 1.00 | 0.95 | 0.91 | 26 |
| file hash | 0.96 | 0.78 | 0.98 | 0.98 | 0.98 | 0.83 | 0.69 | 93 |
| file name | 0.73 | 0.77 | 0.73 | 0.77 | 0.69 | 0.59 | 0.47 | 89 |
| file path | 0.67 | 0.79 | 0.79 | 0.79 | 0.77 | 0.66 | 0.70 | 108 |
| hacking tool | 0.43 | 0.44 | 0.49 | 0.51 | 0.37 | 0.44 | 0.51 | 139 |
| ip address | 0.98 | 0.94 | 0.99 | 0.99 | 0.99 | 0.85 | 0.30 | 130 |
| malware family | 0.87 | 0.82 | 0.80 | 0.82 | 0.82 | 0.85 | 0.75 | 438 |
| tactic | 0.73 | 0.67 | 0.70 | 0.70 | 0.69 | 0.00 | 0.54 | 111 |
| threat actor group | 0.62 | 0.44 | 0.51 | 0.60 | 0.61 | 0.60 | 0.51 | 157 |
| tlp classification | 0.93 | 1.00 | 1.00 | 1.00 | 0.99 | 0.99 | 0.89 | 36 |
| yara rule name | 0.41 | 0.41 | 0.41 | 0.41 | 0.41 | 0.33 | 0.41 | 9 |

## Files

Per model: `{model}-entities.jsonl`, `{model}-spans.jsonl`, `{model}-scores.json`
in `data/frontier_results/`. The default-thinking 3.6-flash run is archived
under the `gemini-3.6-flash-thinking-*` prefix; the unprefixed
`gemini-3.6-flash-*` files are the clean `thinking_level="minimal"` run.
Reproduce via `ner.frontier_infer` → `ner.frontier_extract` →
`ner.frontier_score` with
`--split data/gold_v2/split_full.json --subset test --chunk-size 4000`.
kimi-k2.6 is still running (4/8 docs) and will be appended when complete.
