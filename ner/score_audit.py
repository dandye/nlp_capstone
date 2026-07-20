"""
Score a completed gold_audit.csv against gold_audit.key.json: computes honest
per-model precision from the hand judgments, independent of the (silver,
possibly noisy) automated gold labels the aggregate F1 numbers rely on.

Only run this after the audit is fully judged — it's what un-blinds which
model produced each row.

Usage:
    python3 -m ner.score_audit \
        --csv paper/capstone/gold_audit.csv \
        --key paper/capstone/gold_audit.key.json
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--csv", default="paper/capstone/gold_audit.csv")
    ap.add_argument("--key", default="paper/capstone/gold_audit.key.json")
    args = ap.parse_args()

    key = json.loads(Path(args.key).read_text(encoding="utf-8"))
    rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))

    unjudged = [r["item_id"] for r in rows if r["correct_Y_N"].strip() == ""]
    if unjudged:
        print(f"WARNING: {len(unjudged)} rows still unjudged "
              f"(e.g. {unjudged[:5]}) — results below are partial.\n")

    by_model = defaultdict(lambda: Counter())
    by_model_label = defaultdict(lambda: defaultdict(lambda: Counter()))

    for row in rows:
        verdict = row["correct_Y_N"].strip().upper()
        if verdict not in ("Y", "N"):
            continue
        span = key[row["item_id"]]
        model = span["model_tag"]
        label = span["pred_label"]
        by_model[model]["Y" if verdict == "Y" else "N"] += 1
        by_model_label[model][label]["Y" if verdict == "Y" else "N"] += 1

    print("=== Hand-audited precision, by model (blind judgment) ===\n")
    for model in sorted(by_model):
        y, n = by_model[model]["Y"], by_model[model]["N"]
        total = y + n
        precision = y / total if total else 0.0
        print(f"{model}: {y}/{total} correct = {precision:.3f} precision "
              f"(n={total})")

    print("\n=== Per-label breakdown ===\n")
    all_labels = sorted({l for m in by_model_label.values() for l in m})
    header = f"{'label':<28}" + "".join(
        f"{m:>20}" for m in sorted(by_model_label)
    )
    print(header)
    for label in all_labels:
        row_str = f"{label:<28}"
        for model in sorted(by_model_label):
            c = by_model_label[model][label]
            y, n = c["Y"], c["N"]
            total = y + n
            if total == 0:
                row_str += f"{'--':>20}"
            else:
                row_str += f"{f'{y}/{total} ({y/total:.2f})':>20}"
        print(row_str)

    print(f"\nTotal judged: {sum(v['Y']+v['N'] for v in by_model.values())} "
          f"/ {len(rows)}")


if __name__ == "__main__":
    main()
