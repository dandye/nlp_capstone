"""
Convert LLM gold annotations (data/gold_v2/{slug}.json) to the gliner-format
training/eval JSONL the whole model fleet consumes.

Reuses annotation_text's exact tokenize / find_token_span /
split_into_chunks machinery, so records are format- and token-space-
identical to the ensemble pipeline's output — finetune_roberta.py,
finetune_gliner.py, and ner/evaluate.py all work unchanged. The only
difference is the entity source: the human-reviewed LLM gold file instead
of the dict∩NER ensemble.

Usage:
    # all slugs with a gold_v2 file:
    PYTHONPATH=. python3 -m ner.gold_to_training \
        --output data/gold_v2/eval.jsonl

    # specific slugs:
    ... --slugs aa25-163a,aa23-352a
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .annotation_text import (
    find_token_span,
    split_into_chunks,
    tokenize,
)
from .frontier_llm_utils import load_clean_text

_STRIP = ".,;:!?\"'()[]{}<>"
# em/en dashes and curly quotes fuse tokens in docling output
# ('tools—Splashtop', '“DragonForce'); treat them as strippable/splittable
_FUSED = "—–“”‘’"


def find_token_span_fuzzy(tokens: list[str], entity: str) -> list[tuple[int, int]]:
    """find_token_span, then a fallback for entities whose boundary tokens
    are fused to neighbors by dashes/quotes or path/sentence context:
    a token MATCHES an entity token if it equals it after stripping, OR
    contains it as a proper substring split on fused-punctuation/slashes
    (e.g. token 'tools—Splashtop' contains entity token 'Splashtop';
    token '/SimpleHelp/configuration/serverconfig.xml.' contains
    'serverconfig.xml'). Exact matching is tried first so the fallback
    can never change a span exact matching would have found."""
    exact = find_token_span(tokens, entity)
    if exact:
        return exact

    ent_toks = [t.lower().strip(_STRIP + _FUSED) for t in entity.split()]
    m = len(ent_toks)

    def tok_matches(tok: str, ent_tok: str) -> bool:
        t = tok.lower().strip(_STRIP + _FUSED)
        if t == ent_tok:
            return True
        for sep in list(_FUSED) + ["/"]:
            if sep in t and ent_tok in t.split(sep):
                return True
        return False

    spans = []
    for i in range(len(tokens) - m + 1):
        if all(tok_matches(tokens[i + j], ent_toks[j]) for j in range(m)):
            spans.append((i, i + m - 1))
    return spans


def convert_slug(slug: str, gold_dir: Path, markdown_dir: Path) -> list[dict]:
    entities = json.loads((gold_dir / f"{slug}.json").read_text(encoding="utf-8"))
    text = load_clean_text(slug, markdown_dir)
    if not text:
        raise FileNotFoundError(f"no clean text for {slug}")
    tokens = tokenize(text)

    # All-occurrence projection, longest-first so multi-token entities win
    # overlaps (same policy as the ensemble pipeline).
    all_spans: list[tuple[int, int, str]] = []
    occupied: set[int] = set()
    for ent in sorted(entities, key=lambda e: -len(e["text"])):
        for s, e in find_token_span_fuzzy(tokens, ent["text"]):
            if any(i in occupied for i in range(s, e + 1)):
                continue
            occupied.update(range(s, e + 1))
            all_spans.append((s, e, ent["label"]))

    unlocated = [
        ent["text"] for ent in entities
        if not find_token_span_fuzzy(tokens, ent["text"])
    ]
    if unlocated:
        print(f"  {slug}: {len(unlocated)} gold entities not locatable "
              f"in token space: {unlocated[:5]}", file=sys.stderr)

    records = []
    for chunk_start, chunk_tokens in split_into_chunks(tokens):
        lo, hi = chunk_start, chunk_start + len(chunk_tokens)
        ner = [
            [s - lo, e - lo, label]
            for s, e, label in all_spans
            if s >= lo and e < hi
        ]
        records.append({
            "slug": slug,
            "chunk_start": chunk_start,
            "tokenized_text": chunk_tokens,
            "ner": sorted(ner),
        })
    return records


def _is_gold_file(path: Path) -> bool:
    """A gold file is a JSON *list* of {text, label} entities. Config/result
    artifacts that may share the gold dir (split.json, rescored-*.json,
    trained-*.json, ...) are JSON objects, so shape alone distinguishes them —
    a slug-name pattern would wrongly drop real gold with non-standard slugs
    (e.g. aa23-108, title-slugged reports)."""
    try:
        with open(path, encoding="utf-8") as fh:
            return isinstance(json.load(fh), list)
    except (json.JSONDecodeError, OSError):
        return False


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--gold-dir", default="data/gold_v2")
    ap.add_argument("--markdown-dir", default="data/alerts")
    ap.add_argument("--slugs", default=None,
                    help="Comma-separated; default = every {slug}.json in gold-dir")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    gold_dir = Path(args.gold_dir)
    markdown_dir = Path(args.markdown_dir)
    if args.slugs:
        slugs = [s.strip() for s in args.slugs.split(",")]
    else:
        slugs = sorted(
            f.stem for f in gold_dir.glob("*.json")
            if not f.name.endswith(".dropped.json") and _is_gold_file(f)
        )

    all_records = []
    for slug in slugs:
        recs = convert_slug(slug, gold_dir, markdown_dir)
        n_spans = sum(len(r["ner"]) for r in recs)
        print(f"  {slug}: {len(recs)} chunks, {n_spans} spans", file=sys.stderr)
        all_records.extend(recs)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(all_records)} records -> {out}")


if __name__ == "__main__":
    main()
