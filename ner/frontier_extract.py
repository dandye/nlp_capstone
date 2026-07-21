"""
Frontier LLM span extraction — char→token mapping and label normalization.

Reads raw entity JSON from frontier_infer.py output, applies:
  1. Label normalization (e.g., "EMAIL" → "email address")
  2. Character→token span mapping
  3. Filtering to valid entity types

Output is {model}-spans.jsonl: one line per advisory with pred_spans list.

Usage:
    PYTHONPATH=. python3 -m ner.frontier_extract \\
        --entities data/frontier_results/gemini-3.5-flash-entities.jsonl \\
        --markdown-dir data/alerts \\
        --output-file data/frontier_results/gemini-3.5-flash-spans.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .frontier_llm_utils import (
    extract_entities_from_response,
    load_clean_text,
)


def load_entities_jsonl(path: Path) -> list[dict]:
    """Load entities JSONL file from frontier_infer.py."""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract spans from raw frontier LLM entities."
    )
    parser.add_argument("--entities", required=True,
                        help="Entities JSONL file from frontier_infer")
    parser.add_argument("--markdown-dir", default="data/alerts",
                        help="Directory with {slug}/{slug}.md files")
    parser.add_argument("--output-file", required=True,
                        help="Output spans JSONL file")
    args = parser.parse_args()

    # Load entities
    entities_records = load_entities_jsonl(Path(args.entities))
    if not entities_records:
        print("No entities loaded from input file", file=sys.stderr)
        sys.exit(1)

    markdown_dir = Path(args.markdown_dir)
    spans_records = []

    print(f"Extracting spans from {len(entities_records)} advisories...")

    for i, record in enumerate(entities_records, 1):
        slug = record["slug"]

        # Load clean markdown (same stripping + truncation as inference)
        full_text = load_clean_text(slug, markdown_dir)
        if not full_text:
            print(f"  ⚠ {slug}: markdown not found, skipping", file=sys.stderr)
            continue

        # Match against the FULL document text, not a truncated window --
        # frontier_infer.py's --chunk-size mode runs inference over the
        # entire document in overlapping windows, so entities can legitimately
        # come from anywhere in the text. Matching against a truncated
        # `inference_text` (this used to default to the first 4000 chars,
        # mirroring the old single-window truncation mode) silently dropped
        # every entity found past that point AND miscomputed token offsets
        # for the ones that did match, since they were indexed into the
        # truncated string instead of the full-document token space gold
        # spans use. Matching against full_text is correct in both modes:
        # it's a superset of whatever text was actually sent to the model.
        entities = record.get("entities", [])
        pred_spans = extract_entities_from_response(full_text, entities)

        # Write spans record
        spans_records.append(
            {
                "slug": slug,
                "model": record["model"],
                "full_text_len": len(full_text),
                "token_count": len(full_text.split()),
                "entities_count": len(entities),
                "pred_spans": sorted([(s, e, l) for s, e, l in pred_spans]),
                "spans_count": len(pred_spans),
                "latency_sec": record.get("latency_sec", 0),
                "tokens": record.get("tokens", 0),
            }
        )

        print(f"  [{i}/{len(entities_records)}] {slug}: "
              f"{len(entities)} entities → {len(pred_spans)} spans")

    # Write output
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in spans_records:
            f.write(json.dumps(record) + "\n")

    print(f"\n✓ Extracted spans written to {args.output_file}")
    print(f"  Total advisories: {len(spans_records)}")
    total_entities = sum(r["entities_count"] for r in spans_records)
    total_spans = sum(r["spans_count"] for r in spans_records)
    print(f"  Total entities: {total_entities}")
    print(f"  Total spans extracted: {total_spans}")
    print(f"  Extraction rate: {100*total_spans/total_entities:.1f}%")


if __name__ == "__main__":
    main()
