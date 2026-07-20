"""
Span-level NER evaluation for GLiNER checkpoints on the CTI corpus.

Fixes the two evaluation flaws in the original finetune_gliner.py test loop:
  1. Char/token mismatch — GLiNER returns character offsets; gold spans are
     token indices. This module aligns them properly.
  2. Per-record label leakage — the old loop passed each record's own gold
     labels to predict_entities, leaking which types were present. Here every
     prediction uses the same fixed label set.

Evaluation is document-level: chunks of one advisory are merged back to
document-global token indices (via "chunk_start"), so entities in chunk
overlap regions are not double-counted.

Reports per-label and micro/macro P/R/F1 under two matching regimes:
  strict  — (start, end, label) exact match
  relaxed — same label + span overlap (greedy 1:1 matching)

Usage (ML venv — needs torch + gliner):
    PYTHONPATH=. .venv-ml/bin/python3 -m ner.evaluate \\
        --model urchade/gliner_medium-v2.1 \\
        --data data/gliner_train.jsonl \\
        --split data/split_slugs.json --subset test \\
        --output data/results_zeroshot.json

    PYTHONPATH=. .venv-ml/bin/python3 -m ner.evaluate \\
        --model models/gliner-cti-v1 ... --output data/results_finetuned.json

The split manifest (data/split_slugs.json) is written by finetune_gliner.py;
both models MUST be evaluated with the same manifest.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

Span = tuple[int, int, str]  # (start_tok, end_tok_inclusive, label)


def load_records(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def token_char_offsets(tokens: list[str]) -> list[tuple[int, int]]:
    """Char [start, end) of each token in ' '.join(tokens)."""
    offsets = []
    pos = 0
    for tok in tokens:
        offsets.append((pos, pos + len(tok)))
        pos += len(tok) + 1
    return offsets


def char_span_to_token_span(
    char_start: int, char_end: int, offsets: list[tuple[int, int]]
) -> tuple[int, int] | None:
    """Map a char span to the (first, last) token indices it overlaps."""
    first = last = None
    for i, (ts, te) in enumerate(offsets):
        if ts < char_end and te > char_start:  # overlap
            if first is None:
                first = i
            last = i
    if first is None:
        return None
    return first, last


def predict_document_spans(
    model,
    doc_records: list[dict],
    labels: list[str],
    threshold: float,
) -> set[Span]:
    """Run the model over each chunk; return document-global span set."""
    spans: set[Span] = set()
    for rec in doc_records:
        tokens = rec["tokenized_text"]
        base = rec["chunk_start"]
        text = " ".join(tokens)
        offsets = token_char_offsets(tokens)
        for pred in model.predict_entities(text, labels, threshold=threshold):
            tok_span = char_span_to_token_span(
                pred["start"], pred["end"], offsets
            )
            if tok_span is None:
                continue
            spans.add((base + tok_span[0], base + tok_span[1], pred["label"]))
    return spans


def gold_document_spans(doc_records: list[dict]) -> set[Span]:
    spans: set[Span] = set()
    for rec in doc_records:
        base = rec["chunk_start"]
        for s, e, label in rec["ner"]:
            spans.add((base + s, base + e, label))
    return spans


def match_relaxed(gold: set[Span], pred: set[Span]) -> int:
    """Greedy 1:1 overlap matching within each label; returns match count."""
    matched = 0
    by_label_gold: dict[str, list[Span]] = defaultdict(list)
    by_label_pred: dict[str, list[Span]] = defaultdict(list)
    for g in gold:
        by_label_gold[g[2]].append(g)
    for p in pred:
        by_label_pred[p[2]].append(p)
    for label, gspans in by_label_gold.items():
        pspans = sorted(by_label_pred.get(label, []))
        used = [False] * len(pspans)
        for gs, ge, _ in sorted(gspans):
            for j, (ps, pe, _) in enumerate(pspans):
                if not used[j] and ps <= ge and pe >= gs:
                    used[j] = True
                    matched += 1
                    break
    return matched


class Scorer:
    def __init__(self) -> None:
        self.tp: dict[str, int] = defaultdict(int)
        self.fp: dict[str, int] = defaultdict(int)
        self.fn: dict[str, int] = defaultdict(int)

    def add_strict(self, gold: set[Span], pred: set[Span]) -> None:
        for g in gold:
            if g in pred:
                self.tp[g[2]] += 1
            else:
                self.fn[g[2]] += 1
        for p in pred:
            if p not in gold:
                self.fp[p[2]] += 1

    def add_relaxed(self, gold: set[Span], pred: set[Span]) -> None:
        labels = {s[2] for s in gold | pred}
        for label in labels:
            g = {s for s in gold if s[2] == label}
            p = {s for s in pred if s[2] == label}
            m = match_relaxed(g, p)
            self.tp[label] += m
            self.fn[label] += len(g) - m
            self.fp[label] += len(p) - m

    def report(self) -> dict:
        per_label = {}
        for label in sorted(set(self.tp) | set(self.fp) | set(self.fn)):
            tp, fp, fn = self.tp[label], self.fp[label], self.fn[label]
            p = tp / (tp + fp) if tp + fp else 0.0
            r = tp / (tp + fn) if tp + fn else 0.0
            f = 2 * p * r / (p + r) if p + r else 0.0
            per_label[label] = {
                "P": round(p, 4), "R": round(r, 4), "F1": round(f, 4),
                "support": tp + fn,
            }
        tp = sum(self.tp.values())
        fp = sum(self.fp.values())
        fn = sum(self.fn.values())
        micro_p = tp / (tp + fp) if tp + fp else 0.0
        micro_r = tp / (tp + fn) if tp + fn else 0.0
        micro_f = (
            2 * micro_p * micro_r / (micro_p + micro_r)
            if micro_p + micro_r else 0.0
        )
        f1s = [v["F1"] for v in per_label.values()]
        return {
            "per_label": per_label,
            "micro": {
                "P": round(micro_p, 4), "R": round(micro_r, 4),
                "F1": round(micro_f, 4),
            },
            "macro_F1": round(sum(f1s) / len(f1s), 4) if f1s else 0.0,
        }


def print_table(name: str, report: dict) -> None:
    print(f"\n{name}")
    print(f"  {'label':<30} {'P':>6} {'R':>6} {'F1':>6} {'support':>8}")
    for label, m in sorted(
        report["per_label"].items(), key=lambda x: -x[1]["support"]
    ):
        print(f"  {label:<30} {m['P']:>6.2f} {m['R']:>6.2f} "
              f"{m['F1']:>6.2f} {m['support']:>8}")
    mi = report["micro"]
    print(f"  {'MICRO':<30} {mi['P']:>6.2f} {mi['R']:>6.2f} {mi['F1']:>6.2f}")
    print(f"  {'MACRO F1':<30} {'':>6} {'':>6} {report['macro_F1']:>6.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a GLiNER checkpoint on the CTI test split."
    )
    parser.add_argument("--model", required=True,
                        help="HF id or local checkpoint dir")
    parser.add_argument("--data", default="data/gliner_train.jsonl")
    parser.add_argument("--split", default="data/split_slugs.json",
                        help="Split manifest written by finetune_gliner.py")
    parser.add_argument("--subset", default="test",
                        choices=["train", "val", "test"])
    parser.add_argument("--threshold", type=float, default=0.4)
    parser.add_argument("--output", help="Write full results JSON here")
    args = parser.parse_args()

    records = load_records(Path(args.data))
    split = json.loads(Path(args.split).read_text(encoding="utf-8"))
    subset_slugs = set(split[args.subset])

    by_doc: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        if rec["slug"] in subset_slugs:
            by_doc[rec["slug"]].append(rec)

    if not by_doc:
        print("No records matched the split subset — check --data/--split.",
              file=sys.stderr)
        sys.exit(1)

    labels = sorted({l for rec in records for _, _, l in rec["ner"]})
    print(f"Model: {args.model}")
    print(f"Subset: {args.subset} — {len(by_doc)} documents, "
          f"{sum(len(v) for v in by_doc.values())} chunks")
    print(f"Labels ({len(labels)}): {', '.join(labels)}")
    print(f"Threshold: {args.threshold}")

    from gliner import GLiNER
    model = GLiNER.from_pretrained(args.model)

    strict = Scorer()
    relaxed = Scorer()
    for i, (slug, doc_records) in enumerate(sorted(by_doc.items()), 1):
        gold = gold_document_spans(doc_records)
        pred = predict_document_spans(
            model, doc_records, labels, args.threshold
        )
        strict.add_strict(gold, pred)
        relaxed.add_relaxed(gold, pred)
        print(f"  [{i}/{len(by_doc)}] {slug}: "
              f"{len(gold)} gold, {len(pred)} pred", file=sys.stderr)

    strict_report = strict.report()
    relaxed_report = relaxed.report()
    print_table("STRICT (exact span + label)", strict_report)
    print_table("RELAXED (overlap + label)", relaxed_report)

    if args.output:
        out = {
            "model": args.model,
            "subset": args.subset,
            "threshold": args.threshold,
            "n_documents": len(by_doc),
            "labels": labels,
            "strict": strict_report,
            "relaxed": relaxed_report,
        }
        Path(args.output).write_text(
            json.dumps(out, indent=2), encoding="utf-8"
        )
        print(f"\nResults written to {args.output}")


if __name__ == "__main__":
    main()
