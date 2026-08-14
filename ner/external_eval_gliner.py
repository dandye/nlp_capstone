"""
Zero-shot GLiNER evaluation for one external corpus.

Usage:
    PYTHONPATH=. .venv-ml/bin/python3 -m ner.external_eval_gliner \\
        --corpus-dir data/evals/MalwareTextDB-1.0 \\
        --model urchade/gliner_medium-v2.1 \\
        --output data/evals/MalwareTextDB-1.0/gliner-results.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

from .evaluate import (
    Scorer,
    gold_document_spans,
    load_records,
    predict_document_spans,
    print_table,
)


def load_labels(path: Path) -> list[str]:
    labels = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(labels, list) or not all(isinstance(l, str) for l in labels):
        print(f"{path} must be a JSON list of strings.", file=sys.stderr)
        sys.exit(1)
    return labels


def move_to_mps_if_available(model: object) -> None:
    try:
        import torch

        if torch.backends.mps.is_available():
            try:
                model.to(torch.device("mps"))
                print("Using MPS device for GLiNER inference.")
            except Exception as e:
                print(f"MPS move failed; falling back to CPU: {e}", file=sys.stderr)
    except Exception as e:
        print(f"MPS unavailable; using CPU: {e}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a GLiNER model zero-shot on one external corpus."
    )
    parser.add_argument("--corpus-dir", required=True,
                        help="Directory containing eval.jsonl and labels.json")
    parser.add_argument("--model", required=True,
                        help="HF id or local checkpoint dir")
    parser.add_argument("--threshold", type=float, default=0.4)
    parser.add_argument("--output", required=True,
                        help="Write full results JSON here")
    args = parser.parse_args()

    corpus_dir = Path(args.corpus_dir)
    eval_path = corpus_dir / "eval.jsonl"
    labels_path = corpus_dir / "labels.json"
    if not eval_path.exists():
        print(f"Missing required eval file: {eval_path}", file=sys.stderr)
        sys.exit(1)
    if not labels_path.exists():
        print(f"Missing required labels file: {labels_path}", file=sys.stderr)
        sys.exit(1)

    records = load_records(eval_path)
    if not records:
        print(f"No records loaded from {eval_path}", file=sys.stderr)
        sys.exit(1)
    labels = load_labels(labels_path)

    by_doc: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        by_doc[rec["slug"]].append(rec)

    print(f"Model: {args.model}")
    print(f"Corpus: {corpus_dir}")
    print(f"Sentences: {len(records)}")
    print(f"Labels ({len(labels)}): {', '.join(labels)}")
    print(f"Threshold: {args.threshold}")

    from gliner import GLiNER

    model = GLiNER.from_pretrained(args.model)
    move_to_mps_if_available(model)

    strict = Scorer()
    relaxed = Scorer()
    total_infer_sec = 0.0
    for i, (slug, doc_records) in enumerate(sorted(by_doc.items()), 1):
        gold = gold_document_spans(doc_records)
        start = time.time()
        pred = predict_document_spans(model, doc_records, labels, args.threshold)
        total_infer_sec += time.time() - start
        strict.add_strict(gold, pred)
        relaxed.add_relaxed(gold, pred)
        print(f"  [{i}/{len(by_doc)}] {slug}: "
              f"{len(gold)} gold, {len(pred)} pred", file=sys.stderr)

    strict_report = strict.report()
    relaxed_report = relaxed.report()
    sec_per_sentence = total_infer_sec / len(records)
    print_table("STRICT (exact span + label)", strict_report)
    print_table("RELAXED (overlap + label)", relaxed_report)
    print(
        f"\nStrict micro F1: {strict_report['micro']['F1']:.4f} "
        f"over {total_infer_sec:.2f}s "
        f"({sec_per_sentence:.3f}s/sentence)"
    )

    out = {
        "model": args.model,
        "corpus_dir": str(corpus_dir),
        "threshold": args.threshold,
        "n_sentences": len(records),
        "labels": labels,
        "total_infer_sec": round(total_infer_sec, 3),
        "sec_per_sentence": round(sec_per_sentence, 6),
        "strict": strict_report,
        "relaxed": relaxed_report,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nResults written to {args.output}")


if __name__ == "__main__":
    main()
