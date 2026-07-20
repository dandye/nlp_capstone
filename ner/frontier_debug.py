"""
Debug frontier LLM extraction: trace entities through the pipeline.

Shows raw entities from the LLM, label normalization, tokenization,
character→token mapping, and final spans for a single advisory.

Usage:
    PYTHONPATH=. python3 -m ner.frontier_debug \\
        --predictions data/frontier_results/gemini-3.5-flash-predictions.jsonl \\
        --markdown-dir data/alerts \\
        --slug aa23-129a
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .frontier_llm_utils import (
    normalize_label,
    tokenize_with_offsets,
    char_span_to_token_span,
    load_clean_text,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Debug frontier LLM extraction pipeline."
    )
    parser.add_argument("--predictions", required=True,
                        help="Predictions JSONL file")
    parser.add_argument("--markdown-dir", default="data/alerts")
    parser.add_argument("--slug", required=True,
                        help="Advisory slug to debug")
    parser.add_argument("--max-text-len", type=int, default=4000,
                        help="Max text length (must match inference)")
    args = parser.parse_args()

    # Load prediction
    predictions = []
    with open(args.predictions) as f:
        for line in f:
            predictions.append(json.loads(line))

    pred = next((p for p in predictions if p["slug"] == args.slug), None)
    if not pred:
        print(f"Slug {args.slug} not found in predictions")
        return

    # Load clean markdown (annotations stripped, same as inference)
    full_text = load_clean_text(args.slug, Path(args.markdown_dir))
    if not full_text:
        print(f"Markdown not found for {args.slug}")
        return

    # Use the same truncation as inference
    inference_text = full_text[:args.max_text_len] if len(full_text) > args.max_text_len else full_text

    print(f"=== Extraction Debug: {args.slug} ===\n")
    print(f"Full text: {len(full_text)} chars")
    print(f"Inference text (truncated): {len(inference_text)} chars")
    print(f"First 100 chars: {inference_text[:100]!r}\n")

    # Tokenization (real char offsets against the actual text)
    tokens, offsets = tokenize_with_offsets(inference_text)
    print(f"Tokens: {len(tokens)}")
    print(f"Token offsets (first 10):")
    for i, (start, end) in enumerate(offsets[:10]):
        token = tokens[i]
        print(f"  [{i:3d}] ({start:4d}–{end:4d}): {token!r}")
    print()

    # Raw entities from LLM
    entities = pred["entities"]
    print(f"Raw entities from {pred['model']}: {len(entities)}\n")

    # Process each entity
    print("Entity processing chain:")
    print(f"{'#':<3} {'Text':<30} {'Label':<25} → Normalized → Span")
    print("-" * 100)

    for i, ent in enumerate(entities[:20]):  # First 20
        text_snippet = ent.get("text", "?")[:25]
        label = ent.get("label", "?")
        normalized = normalize_label(label)

        # Character→token mapping
        start_char = ent.get("start_char")
        end_char = ent.get("end_char")
        tok_span = None

        if start_char is not None and end_char is not None:
            tok_span = char_span_to_token_span(start_char, end_char, offsets)

        status = "✓" if tok_span else "✗"
        span_str = f"[{tok_span[0]},{tok_span[1]}]" if tok_span else "—"

        print(
            f"{i:<3} {text_snippet:<30} {label:<25} "
            f"→ {str(normalized):<20} {span_str}"
        )

    # Summary
    mapped_count = sum(
        1 for ent in entities
        if normalize_label(ent.get("label")) is not None
    )
    span_count = len(pred["pred_spans"])

    print(f"\n=== Summary ===")
    print(f"Raw entities: {len(entities)}")
    print(f"After label normalization: {mapped_count}")
    print(f"Final pred_spans: {span_count}")
    print(f"Loss rate: {100 * (len(entities) - span_count) / len(entities):.1f}%")


if __name__ == "__main__":
    main()
