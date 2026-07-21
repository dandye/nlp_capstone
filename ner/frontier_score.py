"""
Frontier LLM scoring — compute P/R/F1 from extracted spans.

Loads spans JSONL from frontier_extract.py, compares against gold test
spans from training data, and outputs per-label and micro metrics.

Usage:
    PYTHONPATH=. python3 -m ner.frontier_score \\
        --predictions data/frontier_results/gemini-3.5-flash-spans.jsonl \\
        --data data/gliner_train.jsonl \\
        --split data/split_slugs.json \\
        --output data/frontier_results/gemini-3.5-flash-scores.json

Output:
    JSON file with:
    {
      "model": "gemini-3.5-flash",
      "subset": "test",
      "n_documents": 8,
      "strict": { "per_label": {...}, "micro": {...} },
      "latency": {
        "total_sec": 123.45,
        "avg_per_doc_sec": 15.43,
        "total_tokens": 45000
      }
    }
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from .evaluate import Scorer, gold_document_spans, print_table
from .frontier_llm_utils import Span, load_records, load_split


def load_predictions(path: Path) -> list[dict]:
    """Load predictions JSONL from frontier_infer.py."""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def spans_from_tuples(spans_list: list[list]) -> set[Span]:
    """Convert list of [start, end, label] tuples to set of Span tuples."""
    return {(s, e, l) for s, e, l in spans_list}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score frontier LLM spans against gold test set."
    )
    parser.add_argument("--predictions", required=True,
                        help="Spans JSONL from frontier_extract.py (or predictions JSONL for legacy)")
    parser.add_argument("--data", default="data/gliner_train.jsonl",
                        help="Training data with gold spans")
    parser.add_argument("--split", default="data/split_slugs.json",
                        help="Train/val/test split manifest")
    parser.add_argument("--subset", default="test",
                        choices=["train", "val", "test"])
    parser.add_argument("--output", help="Write scores JSON here")
    args = parser.parse_args()

    # Load data
    records = load_records(Path(args.data))
    split = load_split(Path(args.split))
    subset_slugs = set(split[args.subset])
    predictions = load_predictions(Path(args.predictions))

    if not predictions:
        print("No predictions loaded.", file=sys.stderr)
        sys.exit(1)

    model_name = predictions[0]["model"]
    print(f"Model: {model_name}")
    print(f"Subset: {args.subset}")
    print(f"Predictions file: {args.predictions}")
    print()

    # Group records by document
    by_doc: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        if rec["slug"] in subset_slugs:
            by_doc[rec["slug"]].append(rec)

    # Score document-by-document into a shared accumulator -- the same
    # pattern ner/evaluate.py's own main() uses for every other model, so
    # this is literally the same scoring code, not a parallel
    # reimplementation that merely computes the same formulas.
    pred_by_slug = {p["slug"]: p for p in predictions}
    model_latencies = []
    model_tokens = 0

    strict = Scorer()
    relaxed = Scorer()
    for slug, doc_records in sorted(by_doc.items()):
        gold_spans = gold_document_spans(doc_records)

        if slug in pred_by_slug:
            pred_record = pred_by_slug[slug]
            pred_spans = spans_from_tuples(pred_record["pred_spans"])
            model_latencies.append(pred_record["latency_sec"])
            model_tokens += pred_record.get("tokens", 0)

            # Restrict gold to the token window the model actually saw. With
            # --chunk-size inference (full-document coverage), token_count
            # covers the whole document and this is a no-op; it only bites
            # for the older single-window truncation mode, where tokens
            # beyond token_count were never shown to the model.
            window = pred_record.get("token_count")
            if window:
                gold_spans = {s for s in gold_spans if s[1] < window}
        else:
            pred_spans = set()

        strict.add_strict(gold_spans, pred_spans)
        relaxed.add_relaxed(gold_spans, pred_spans)

    strict_report = strict.report()
    relaxed_report = relaxed.report()
    print_table("STRICT (exact span + label)", strict_report)
    print_table("RELAXED (overlap + label)", relaxed_report)

    # Print latency stats
    if model_latencies:
        print(f"\nLatency:")
        print(f"  Total: {sum(model_latencies):.1f}s")
        print(f"  Average per advisory: {sum(model_latencies) / len(model_latencies):.2f}s")
        print(f"  Total tokens: {model_tokens}")

    # Write output
    if args.output:
        out = {
            "model": model_name,
            "subset": args.subset,
            "n_documents": len(by_doc),
            "strict": strict_report,
            "relaxed": relaxed_report,
            "latency": {
                "total_sec": round(sum(model_latencies), 1),
                "avg_per_doc_sec": round(
                    sum(model_latencies) / len(model_latencies), 3
                ) if model_latencies else 0,
                "total_tokens": model_tokens,
            },
        }
        Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"\nScores written to {args.output}")


if __name__ == "__main__":
    main()
