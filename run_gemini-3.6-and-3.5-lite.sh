#!/bin/bash
# Parallel inference for gemini-3.6-flash and gemini-3.5-flash-lite, then extract+score

set -a && source .env && set +a

cd /Users/elwood/Projects/nlp_capstone
MODELS=("gemini-3.6-flash" "gemini-3.5-flash-lite")
START_EPOCH=$(date +%s)

echo "════════════════════════════════════════════════════════════════════════"
echo "Gemini 3.6 + 3.5-lite Frontier NER Run"
echo "Start: $(date)"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# ============================================================================
# PHASE 1: Parallel Inference
# ============================================================================

echo "=== Phase 1: Parallel Inference ==="
for MODEL in "${MODELS[@]}"; do
  echo "Starting $MODEL..."
  nohup bash -c "
    cd /Users/elwood/Projects/nlp_capstone
    set -a && source .env && set +a
    PYTHONPATH=. .venv/bin/python3 -m ner.frontier_infer \
        --split data/gold_v2/split_full.json \
        --markdown-dir data/alerts \
        --output-dir data/frontier_results \
        --models $MODEL \
        --subset test \
        --chunk-size 4000 \
    > data/frontier_results/${MODEL}-infer.log 2>&1
  " > /dev/null 2>&1 &

  echo "  PID \$! → data/frontier_results/${MODEL}-infer.log"
done

echo ""
echo "Waiting for inference to complete (checking every 30s)..."
echo ""

# Poll for both models to complete
while true; do
  ALL_DONE=1
  ELAPSED=$(($(date +%s) - START_EPOCH))

  for MODEL in "${MODELS[@]}"; do
    ENTITY_FILE="data/frontier_results/${MODEL}-entities.jsonl"
    if [ ! -f "$ENTITY_FILE" ]; then
      echo "[$((ELAPSED/3600))h$((($ELAPSED%3600)/60))m] $MODEL: waiting for file..."
      ALL_DONE=0
      continue
    fi

    DOC_COUNT=$(python3 -c "import json; rows=[json.loads(l) for l in open('$ENTITY_FILE')]; print(len(rows))" 2>/dev/null || echo "0")
    ENTITY_COUNT=$(python3 -c "import json; rows=[json.loads(l) for l in open('$ENTITY_FILE')]; n=sum(len(r['entities']) for r in rows); print(n)" 2>/dev/null || echo "0")

    if [ "$DOC_COUNT" != "8" ] || [ "$ENTITY_COUNT" -le 290 ]; then
      echo "[$((ELAPSED/3600))h$((($ELAPSED%3600)/60))m] $MODEL: $DOC_COUNT/8 docs, $ENTITY_COUNT entities"
      ALL_DONE=0
    else
      echo "[$((ELAPSED/3600))h$((($ELAPSED%3600)/60))m] $MODEL: ✓ complete (8 docs, $ENTITY_COUNT entities)"
    fi
  done

  if [ "$ALL_DONE" = "1" ]; then
    echo ""
    echo "✓ All inference complete"
    break
  fi

  sleep 30
done

# ============================================================================
# PHASE 2: Extract + Score
# ============================================================================

echo ""
echo "=== Phase 2: Extract Spans ==="

EXTRACT_START=$(date +%s)
for MODEL in "${MODELS[@]}"; do
  echo "  $MODEL..."
  PYTHONPATH=. .venv/bin/python3 -m ner.frontier_extract \
      --entities data/frontier_results/${MODEL}-entities.jsonl \
      --markdown-dir data/alerts \
      --output-file data/frontier_results/${MODEL}-spans.jsonl 2>&1 | grep -v "^$"
done
EXTRACT_END=$(date +%s)

echo ""
echo "=== Phase 3: Score ==="

SCORE_START=$(date +%s)
for MODEL in "${MODELS[@]}"; do
  echo "  $MODEL..."
  PYTHONPATH=. .venv/bin/python3 -m ner.frontier_score \
      --predictions data/frontier_results/${MODEL}-spans.jsonl \
      --data data/gold_v2/eval.jsonl \
      --split data/gold_v2/split_full.json \
      --subset test \
      --output data/frontier_results/${MODEL}-scores.json 2>&1 | tail -1
done
SCORE_END=$(date +%s)

# ============================================================================
# PHASE 4: Compare all Gemini models
# ============================================================================

TOTAL_END=$(date +%s)
TOTAL_DURATION=$((TOTAL_END - START_EPOCH))

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "Results: Gemini 3.x Comparison"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

python3 << 'EOF'
import json
import glob
import os

results_dir = "data/frontier_results"
results = []

# Collect all gemini score files
for score_file in sorted(glob.glob(os.path.join(results_dir, "gemini-*-scores.json"))):
    try:
        with open(score_file) as f:
            d = json.load(f)
            model_name = os.path.basename(score_file).replace("-scores.json", "")

            strict = d["strict"]["micro"]
            relaxed = d["relaxed"]["micro"]
            latency = d.get("latency", {})

            results.append({
                "model": model_name,
                "f1_strict": strict["F1"],
                "p_strict": strict["P"],
                "r_strict": strict["R"],
                "f1_relaxed": relaxed["F1"],
                "total_sec": latency.get("total_sec", 0),
                "avg_per_doc": latency.get("avg_per_doc_sec", 0),
                "tokens": latency.get("total_tokens", 0),
            })
    except Exception as e:
        print(f"Error reading {score_file}: {e}")

# Sort by F1 descending
results.sort(key=lambda x: x["f1_strict"], reverse=True)

print("STRICT MICRO (exact span match):")
print("─" * 95)
print(f"{'Model':<25} {'F1':<8} {'Precision':<12} {'Recall':<12} {'Time':<15} {'Tokens':<12}")
print("─" * 95)

for r in results:
    time_h = r['total_sec'] / 3600
    time_str = f"{time_h:.2f}h" if time_h >= 1 else f"{r['total_sec']:.0f}s"
    tokens_str = f"{r['tokens']:,}" if r['tokens'] > 0 else "—"

    print(f"{r['model']:<25} {r['f1_strict']:.3f}     "
          f"{r['p_strict']:.3f}         {r['r_strict']:.3f}         "
          f"{time_str:<15} {tokens_str:<12}")

print("─" * 95)
print()
print("RELAXED (partial overlap):")
print("─" * 30)
for r in results:
    print(f"{r['model']:<25} F1: {r['f1_relaxed']:.3f}")

print()
print("Comparison to baselines:")
print(f"  SecureBERT (fine-tuned):     0.712 F1 (seconds, no API cost)")
print(f"  gemma3:27b (zero-shot):      0.240 F1 (6.92h local)")

EOF

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "Timing Summary"
echo "════════════════════════════════════════════════════════════════════════"
echo "Phase 1 (inference):  $((EXTRACT_START - START_EPOCH))s"
echo "Phase 2 (extract):    $((SCORE_START - EXTRACT_START))s"
echo "Phase 3 (score):      $((SCORE_END - SCORE_START))s"
echo "─────────────────────────────────"
echo "Total:                $((TOTAL_DURATION/3600))h $((($TOTAL_DURATION%3600)/60))m $((TOTAL_DURATION%60))s"
echo ""
echo "End: $(date)"
echo "════════════════════════════════════════════════════════════════════════"
