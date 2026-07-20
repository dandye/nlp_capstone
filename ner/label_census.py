"""
Defect census for the training data — the acceptance test for the
Phase 1 label-quality fixes (2026-07-19 gold-audit follow-up).

Scans a gold-derived chunk JSONL (gold_to_training output) for the
mechanically-detectable defect classes the 300-span gold audit identified,
using the same span validators the generation pipeline now enforces, plus
markup-leak and blocklist checks.

Usage:
    PYTHONPATH=. python3 -m ner.label_census [--data data/gold_v2/eval.jsonl]
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from .span_validators import validate

MARKUP_RE = re.compile(r"\[[^\]]*\]\(`[A-Z0-9]+_[^`]*`\)")
FURNITURE_WORDS = {"page", "malware", "ransomware"}  # as full malware-family spans


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--data", default="data/gold_v2/eval.jsonl",
                    help="chunk-record JSONL from gold_to_training")
    ap.add_argument("--split", default="data/gold_v2/split_full.json",
                    help="{train,val,test} slug lists for per-subset bucketing")
    args = ap.parse_args()

    recs = [json.loads(l) for l in open(args.data, encoding="utf-8")]
    split = json.loads(Path(args.split).read_text(encoding="utf-8"))
    subset_of = {s: name for name in split for s in split[name]}

    defects = Counter()
    per_subset_spans = Counter()
    label_counts = Counter()
    examples = defaultdict(list)
    markup_chunks = 0

    for r in recs:
        text = " ".join(r["tokenized_text"])
        if MARKUP_RE.search(text):
            markup_chunks += 1
        subset = subset_of.get(r["slug"], "?")
        for s, e, label in r["ner"]:
            per_subset_spans[subset] += 1
            label_counts[label] += 1
            span_text = " ".join(r["tokenized_text"][s:e + 1])
            t = span_text.strip(".,;: ")
            if label == "malware family" and t.lower() in FURNITURE_WORDS:
                defects["furniture word as malware family"] += 1
                examples["furniture word as malware family"].append(t)
            elif not validate(label, span_text):
                defects[f"validator-fail: {label}"] += 1
                if len(examples[f"validator-fail: {label}"]) < 5:
                    examples[f"validator-fail: {label}"].append(span_text)

    total = sum(per_subset_spans.values())
    print(f"{len(recs)} chunks, {total} spans "
          f"({dict(per_subset_spans)})")
    print(f"chunks with annotation-markup leakage: {markup_chunks}")
    print()
    if not defects:
        print("DEFECT CENSUS CLEAN — zero mechanically-detectable defects")
    else:
        print(f"{'count':>7}  defect")
        bad = 0
        for d, n in defects.most_common():
            print(f"{n:>7}  {d}   e.g. {examples[d][:3]}")
            bad += n
        print(f"{bad:>7}  TOTAL = {bad / total:.2%} of spans")
    print()
    print("top 'malware family' span texts:")
    mf = Counter()
    for r in recs:
        for s, e, label in r["ner"]:
            if label == "malware family":
                mf[" ".join(r["tokenized_text"][s:e + 1]).lower().strip(".,;:")] += 1
    for text, n in mf.most_common(8):
        print(f"  {n:>5}x  {text!r}")


if __name__ == "__main__":
    main()
