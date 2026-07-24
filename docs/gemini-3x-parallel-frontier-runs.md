# Runbook: Gemini 3.x frontier NER comparison (parallel runs)

**Goal:** Expand frontier comparison to include other Gemini 3.x models (3.0-flash, 3.0-pro, etc.) for cross-model timing & quality analysis.

**Status:** gemini-3.5-flash is complete (0.795 F1); this runbook runs other variants in parallel.

---

## Preconditions

1. **Working directory:** `/Users/elwood/Projects/nlp_capstone`
2. **API key:** `GOOGLE_API_KEY` or `GEMINI_API_KEY` environment variable set
   - Billing must have sufficient quota for multiple parallel calls
   - Rough estimate: gemini-3.5-flash was ~350k tokens total; 3.0 models will be similar
3. **Modified frontier_infer.py:** The module now accepts model names as parameters (commit: passed model name to call_gemini)
4. **Split + gold already present:**
   - split: `data/gold_v2/split_full.json` (test subset = 8 docs)
   - gold: `data/gold_v2/eval.jsonl`

---

## Step 1: List available Gemini 3.x models

```bash
python3 << 'EOF'
from google import genai
import os

api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
models = client.models.list()

gemini_3x = [m.name for m in models if 'gemini-3' in m.name]
print("Available Gemini 3.x models:")
for m in sorted(gemini_3x):
    print(f"  {m}")
EOF
```

Expected output (at least one of):
- `models/gemini-3.0-flash-001`
- `models/gemini-3.0-pro-001`
- `models/gemini-3.5-flash-002` (already run)
- `models/gemini-3.5-pro-002`

---

## Step 2: Define models to run

Based on Step 1 output, pick which to run (avoid re-running gemini-3.5-flash).
For this runbook, assume we want:
- `gemini-3.0-flash`
- `gemini-3.0-pro` (if available)

Adjust `MODELS` array below to match your environment.

---

## Step 3: Run all models in parallel

Each model gets its own background process with independent log files. Use `nohup` so they survive terminal close.

```bash
cd /Users/elwood/Projects/nlp_capstone

# Define which models to run (adjust to your available set)
MODELS=("gemini-3.0-flash" "gemini-3.0-pro")

for MODEL in "${MODELS[@]}"; do
  echo "Starting $MODEL..."
  
  nohup bash -c "
    cd /Users/elwood/Projects/nlp_capstone
    PYTHONPATH=. .venv/bin/python3 -m ner.frontier_infer \
        --split data/gold_v2/split_full.json \
        --markdown-dir data/alerts \
        --output-dir data/frontier_results \
        --models $MODEL \
        --subset test \
        --chunk-size 4000 \
    > data/frontier_results/${MODEL}-infer.log 2>&1
    
    echo \"[$MODEL] Inference complete at \$(date)\"
  " > /dev/null 2>&1 &
  
  echo "  PID \$! (logging to data/frontier_results/${MODEL}-infer.log)"
done

echo "All models running in parallel"
```

---

## Step 4: Monitor progress

Check logs as they update (one per model):

```bash
tail -f data/frontier_results/gemini-3.0-flash-infer.log
tail -f data/frontier_results/gemini-3.0-pro-infer.log
```

---

## Step 5: Extract spans + score (when inference completes)

Once **all** inference logs show completion, run extraction + scoring for each model:

```bash
cd /Users/elwood/Projects/nlp_capstone
MODELS=("gemini-3.0-flash" "gemini-3.0-pro")

for MODEL in "${MODELS[@]}"; do
  echo "=== $MODEL: Extract ===" 
  PYTHONPATH=. .venv/bin/python3 -m ner.frontier_extract \
      --entities data/frontier_results/${MODEL}-entities.jsonl \
      --markdown-dir data/alerts \
      --output-file data/frontier_results/${MODEL}-spans.jsonl
  
  echo "=== $MODEL: Score ===" 
  PYTHONPATH=. .venv/bin/python3 -m ner.frontier_score \
      --predictions data/frontier_results/${MODEL}-spans.jsonl \
      --data data/gold_v2/eval.jsonl \
      --split data/gold_v2/split_full.json \
      --subset test \
      --output data/frontier_results/${MODEL}-scores.json
done
```

---

## Step 6: Compare all Gemini 3.x models

```bash
python3 << 'EOF'
import json
import os
import glob

results_dir = "data/frontier_results"
models = []

# Collect all gemini-3 score files
for score_file in sorted(glob.glob(os.path.join(results_dir, "gemini-3*-scores.json"))):
    try:
        with open(score_file) as f:
            d = json.load(f)
            model_name = os.path.basename(score_file).replace("-scores.json", "")
            strict_f1 = d["strict"]["micro"]["F1"]
            total_time = d["latency"]["total_sec"]
            avg_time_per_doc = d["latency"]["avg_per_doc_sec"]
            total_tokens = d["latency"]["total_tokens"]
            
            models.append({
                "model": model_name,
                "f1": strict_f1,
                "total_time": total_time,
                "avg_per_doc": avg_time_per_doc,
                "total_tokens": total_tokens
            })
    except Exception as e:
        print(f"Error reading {score_file}: {e}")

# Sort by F1 descending
models.sort(key=lambda x: x["f1"], reverse=True)

print("=" * 80)
print("Gemini 3.x Frontier Comparison")
print("=" * 80)
print(f"{'Model':<25} {'F1':<8} {'Total Time':<15} {'Per Doc':<12} {'Tokens':<12}")
print("-" * 80)

for m in models:
    f1_str = f"{m['f1']:.3f}"
    time_h = m['total_time'] / 3600
    time_str = f"{time_h:.2f}h" if time_h >= 1 else f"{m['total_time']:.0f}s"
    per_doc_m = m['avg_per_doc'] / 60
    per_doc_str = f"{per_doc_m:.1f}m"
    tokens_str = f"{m['total_tokens']:,}"
    
    print(f"{m['model']:<25} {f1_str:<8} {time_str:<15} {per_doc_str:<12} {tokens_str:<12}")

print("-" * 80)
print("\nComparison to other architectures:")
print("  SecureBERT (fine-tuned): 0.712 F1")
print("  gemma3:27b (zero-shot local): 0.24 F1")
EOF
```

---

## Notes

- **Parallel billing:** Multiple models run concurrently, so API costs stack. Monitor your Gemini API billing.
- **Determinism:** Each model should produce identical results on identical inputs (same seed, same prompt).
- **Token efficiency:** Cheaper models (3.0-flash) vs. premium ones (3.0-pro) show the cost/quality tradeoff.
- **Paper eligibility:** Only gemini-3.5-flash is in the paper (frozen). New runs are exploratory; document them as such if committing.

---

## If something fails

- **"Model not found":** API key OK but model doesn't exist in your region/quota. Run Step 1 again.
- **Rate limiting:** Back off interval between requests or reduce number of parallel models.
- **Inference hangs:** Check API logs; some quota/billing issues block all requests.
- **Tokenization mismatch:** New models use different tokenizers; token counts will differ from 3.5-flash even on same input.
