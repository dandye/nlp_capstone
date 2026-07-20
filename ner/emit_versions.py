"""
Emit per-advisory comparison versions of the annotated markdown.

For each slug directory in data/alerts/ this writes, alongside the original:
  {base}.clean.md   — annotation markup stripped (pdf→md conversion only)
  {base}.gemini.md  — clean text re-annotated with Gemini-extracted entities
                      (same [text](`PREFIX_value`) format as the dict pipeline)

The ORIGINAL {base}.md is raw docling output (no annotation layer in the LLM-gold pipeline)
and is left untouched.

Usage:
    # Clean versions only (no Gemini entities needed):
    PYTHONPATH=. python3 -m ner.emit_versions --slug ar26-113a

    # Clean + Gemini versions for every slug present in an entities file:
    PYTHONPATH=. python3 -m ner.emit_versions \
        --entities data/frontier_results/gemini-3.5-flash-entities.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from .annotation_text import PREFIX_TO_LABEL, strip_annotations
from .text_normalize import normalize_clean_text

# Invert PREFIX_TO_LABEL (first prefix wins for labels with multiple prefixes,
# e.g. "file hash" → HASH not MD5)
LABEL_TO_PREFIX: dict[str, str] = {}
for prefix, label in PREFIX_TO_LABEL.items():
    LABEL_TO_PREFIX.setdefault(label, prefix)


def original_md(slug_dir: Path) -> Path | None:
    """The original annotated markdown (not a derived version)."""
    md_files = sorted(
        f for f in slug_dir.glob("*.md")
        if not f.name.endswith((".clean.md", ".gemini.md", ".gliner.md"))
    )
    return md_files[0] if md_files else None


def annotate_with_entities(clean_text: str, entities: list[dict]) -> tuple[str, int]:
    """Annotate clean text with entities in [text](`PREFIX_value`) format.

    Single-pass regex over an alternation of all entity texts (longest first,
    longest-match-wins) so annotations never nest.
    """
    by_text: dict[str, str] = {}
    for ent in entities:
        text = ent.get("text", "").strip()
        label = ent.get("label", "").lower()
        prefix = LABEL_TO_PREFIX.get(label)
        if text and prefix:
            by_text.setdefault(text.lower(), prefix)

    if not by_text:
        return clean_text, 0

    ordered = sorted(by_text.keys(), key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(t) for t in ordered), re.IGNORECASE)

    count = 0

    def replace(m: re.Match) -> str:
        nonlocal count
        matched = m.group(0)
        prefix = by_text[matched.lower()]
        count += 1
        return f"[{matched}](`{prefix}_{matched}`)"

    return pattern.sub(replace, clean_text), count


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit clean/gemini markdown versions.")
    parser.add_argument("--alerts-dir", default="data/alerts")
    parser.add_argument("--slug", action="append", default=[],
                        help="Slug to process (repeatable). Clean version only unless --entities also covers it.")
    parser.add_argument("--entities",
                        help="Entities JSONL from frontier_infer; adds .gemini.md for its slugs")
    parser.add_argument("--all", action="store_true",
                        help="Process every slug directory under --alerts-dir "
                             "(clean.md only, unless --entities also covers a slug)")
    args = parser.parse_args()

    alerts_dir = Path(args.alerts_dir)

    entities_by_slug: dict[str, list[dict]] = defaultdict(list)
    if args.entities:
        with open(args.entities, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                entities_by_slug[rec["slug"]].extend(rec.get("entities", []))

    if args.all:
        slugs = sorted(d.name for d in alerts_dir.iterdir() if d.is_dir())
    else:
        slugs = list(dict.fromkeys(args.slug + list(entities_by_slug.keys())))
    if not slugs:
        print("Nothing to do: pass --slug, --entities, and/or --all", file=sys.stderr)
        sys.exit(1)

    for slug in slugs:
        slug_dir = alerts_dir / slug
        src = original_md(slug_dir) if slug_dir.exists() else None
        if src is None:
            print(f"  SKIP {slug} — no original .md")
            continue

        base = src.name[:-3]  # strip ".md"
        # clean.md = annotation markup removed, then normalized (page
        # furniture deduped, pagination dropped, split hashes rejoined) —
        # this file is the canonical model-facing text for training-data
        # generation AND frontier LLM inference (see text_normalize.py)
        clean_text = normalize_clean_text(
            strip_annotations(src.read_text(encoding="utf-8"))
        )

        clean_path = slug_dir / f"{base}.clean.md"
        clean_path.write_text(clean_text, encoding="utf-8")
        line = f"  {slug}: wrote {clean_path.name}"

        if slug in entities_by_slug:
            annotated, n = annotate_with_entities(clean_text, entities_by_slug[slug])
            gemini_path = slug_dir / f"{base}.gemini.md"
            gemini_path.write_text(annotated, encoding="utf-8")
            line += f", {gemini_path.name} ({n} annotations)"

        print(line)


if __name__ == "__main__":
    main()
