#!/bin/bash
# Monitor gemma3:27b inference completion and run extraction + scoring

cd /Users/elwood/Projects/nlp_capstone
ENTITY_FILE="data/frontier_results/gemma3-27b-entities.jsonl"
LOG_FILE="data/frontier_results/gemma3-27b-monitor.log"
TIMING_FILE="data/frontier_results/gemma3-27b-timing.json"

START_EPOCH=$(date +%s)

{
  echo "=== gemma3:27b Frontier Run: Timing Monitor ==="
  echo "Start: $(date)"
  echo ""

  echo "=== Step 1: Waiting for Inference ==="
  STEP1_START=$(date +%s)
  echo "Polling for completion (checking every 30s)..."

  # Poll for 8 complete docs
  while true; do
    if [ ! -f "$ENTITY_FILE" ]; then
      echo "[$(date)] Waiting for $ENTITY_FILE to appear..."
      sleep 30
      continue
    fi

    DOC_COUNT=$(python3 -c "import json; rows=[json.loads(l) for l in open('$ENTITY_FILE')]; print(len(rows))" 2>/dev/null || echo "0")
    ENTITY_COUNT=$(python3 -c "import json; rows=[json.loads(l) for l in open('$ENTITY_FILE')]; n=sum(len(r['entities']) for r in rows); print(n)" 2>/dev/null || echo "0")

    ELAPSED=$(($(date +%s) - START_EPOCH))
    echo "[$((ELAPSED/3600))h$((($ELAPSED%3600)/60))m] Docs: $DOC_COUNT/8 | Raw entities: $ENTITY_COUNT"

    if [ "$DOC_COUNT" = "8" ] && [ "$ENTITY_COUNT" -gt 290 ]; then
      echo "[$((ELAPSED/3600))h$((($ELAPSED%3600)/60))m] ✓ Inference complete! (8 docs, $ENTITY_COUNT entities)"
      break
    fi

    sleep 30
  done
  STEP1_END=$(date +%s)
  STEP1_DURATION=$((STEP1_END - STEP1_START))

  echo ""
  echo "=== Step 2: Extract Spans ==="
  STEP2_START=$(date +%s)
  PYTHONPATH=. .venv/bin/python3 -m ner.frontier_extract \
      --entities data/frontier_results/gemma3-27b-entities.jsonl \
      --markdown-dir data/alerts \
      --output-file data/frontier_results/gemma3-27b-spans.jsonl

  SPANS_COUNT=$(python3 -c "import json; rows=[json.loads(l) for l in open('data/frontier_results/gemma3-27b-spans.jsonl')]; print(len(rows))" 2>/dev/null || echo "?")
  STEP2_END=$(date +%s)
  STEP2_DURATION=$((STEP2_END - STEP2_START))
  ELAPSED=$((STEP2_END - START_EPOCH))
  echo "[$((ELAPSED/3600))h$((($ELAPSED%3600)/60))m] ✓ Extraction complete ($SPANS_COUNT docs) — took ${STEP2_DURATION}s"

  echo ""
  echo "=== Step 3: Score ==="
  STEP3_START=$(date +%s)
  PYTHONPATH=. .venv/bin/python3 -m ner.frontier_score \
      --predictions data/frontier_results/gemma3-27b-spans.jsonl \
      --data data/gold_v2/eval.jsonl \
      --split data/gold_v2/split_full.json \
      --subset test \
      --output data/frontier_results/gemma3-27b-scores.json

  STEP3_END=$(date +%s)
  STEP3_DURATION=$((STEP3_END - STEP3_START))
  ELAPSED=$((STEP3_END - START_EPOCH))
  echo "[$((ELAPSED/3600))h$((($ELAPSED%3600)/60))m] ✓ Scoring complete — took ${STEP3_DURATION}s"

  echo ""
  echo "=== Results ==="
  python3 -c "
import json
d=json.load(open('data/frontier_results/gemma3-27b-scores.json'))
s=d['strict']
m=s.get('micro') or s
print('gemma3:27b strict micro P/R/F1:',
      round(s['micro']['P'],3) if 'micro' in s else '?',
      round(s['micro']['R'],3) if 'micro' in s else '?',
      round(s['micro']['F1'],3) if 'micro' in s else '?')
print()
print('Comparison:')
print('  Gemini 3.5 Flash: 0.795 F1 (zero-shot cloud)')
print('  SecureBERT: 0.712 F1 (fine-tuned local)')
print('  gemma3:27b: {} F1 (zero-shot local)'.format(round(s['micro']['F1'],3) if 'micro' in s else '?'))
"

  TOTAL_END=$(date +%s)
  TOTAL_DURATION=$((TOTAL_END - START_EPOCH))
  echo ""
  echo "=== Timing Summary ==="
  echo "Step 1 (inference — waiting):  $((STEP1_DURATION/3600))h $((($STEP1_DURATION%3600)/60))m $((STEP1_DURATION%60))s"
  echo "Step 2 (extraction):            ${STEP2_DURATION}s"
  echo "Step 3 (scoring):               ${STEP3_DURATION}s"
  echo "─────────────────────────────────────"
  echo "Total elapsed:                  $((TOTAL_DURATION/3600))h $((($TOTAL_DURATION%3600)/60))m $((TOTAL_DURATION%60))s"
  echo "End: $(date)"

  # Write timing JSON for easy parsing
  python3 << EOF
import json, time
timing = {
  "start_epoch": $START_EPOCH,
  "end_epoch": $TOTAL_END,
  "total_seconds": $TOTAL_DURATION,
  "steps": {
    "step1_inference_wait_seconds": $STEP1_DURATION,
    "step2_extraction_seconds": $STEP2_DURATION,
    "step3_scoring_seconds": $STEP3_DURATION
  }
}
with open('$TIMING_FILE', 'w') as f:
  json.dump(timing, f, indent=2)
EOF
  echo "Timing data saved to: $TIMING_FILE"

  echo ""
  echo "✓✓✓ All steps complete!"

} | tee -a "$LOG_FILE"
