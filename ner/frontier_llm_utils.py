"""
Shared utilities for frontier LLM NER evaluation.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Optional as Opt

# Label set — must match training data labels exactly
LABELS = [
    "affected software product",
    "attack technique id",
    "attack technique name",
    "cve identifier",
    "cwe identifier",
    "email address",
    "file hash",
    "file name",
    "file path",
    "hacking tool",
    "ip address",
    "malware family",
    "tactic",
    "threat actor group",
    "tlp classification",
    "yara rule name",
]

Span = tuple[int, int, str]  # (start_tok, end_tok_inclusive, label)

# Mapping from LLM-extracted labels (case-insensitive) to canonical training labels
LABEL_MAPPING = {
    # Email/contact
    "email": "email address",
    "email address": "email address",
    # TLP classification
    "tlp": "tlp classification",
    "tlp classification": "tlp classification",
    # File/artifact identifiers
    "domain": "file path",
    "url": "file path",
    "file path": "file path",
    "filepath": "file path",
    "file name": "file name",
    "filename": "file name",
    "file hash": "file hash",
    "hash": "file hash",
    "md5": "file hash",
    "sha1": "file hash",
    "sha256": "file hash",
    "sha512": "file hash",
    # CVE/CWE identifiers
    "cve": "cve identifier",
    "cve identifier": "cve identifier",
    "cwe": "cwe identifier",
    "cwe identifier": "cwe identifier",
    # Attack/threat indicators
    "attack": "attack technique id",
    "attack technique": "attack technique id",
    "attack technique id": "attack technique id",
    "attack technique name": "attack technique name",
    "technique": "attack technique id",
    "tactic": "tactic",
    "malware": "malware family",
    "malware family": "malware family",
    "actor": "threat actor group",
    "threat actor": "threat actor group",
    "threat actor group": "threat actor group",
    "tool": "hacking tool",
    "hacking tool": "hacking tool",
    # YARA rules
    "yara": "yara rule name",
    "yara rule": "yara rule name",
    "yara rule name": "yara rule name",
    # IP addresses
    "ip": "ip address",
    "ip address": "ip address",
    "ipv4": "ip address",
    "ipv6": "ip address",
    # Software/products
    "product": "affected software product",
    "software": "affected software product",
    "affected software product": "affected software product",
    # Organizational entities (not in training data, filter out)
    "org": None,
    "organization": None,
    "country": None,
    "sector": None,
}


def normalize_label(label: str) -> Opt[str]:
    """Map LLM-extracted label to canonical training label."""
    if not label:
        return None
    normalized = label.lower().strip()
    return LABEL_MAPPING.get(normalized, None)


def load_records(path: Path) -> list[dict]:
    """Load JSONL training data."""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_split(path: Path) -> dict[str, list[str]]:
    """Load train/val/test split."""
    return json.loads(path.read_text(encoding="utf-8"))


DERIVED_MD_SUFFIXES = (".clean.md", ".gemini.md", ".gliner.md")


def is_derived_md(path: Path) -> bool:
    """True for derived comparison files (clean/gemini/gliner versions)."""
    return path.name.endswith(DERIVED_MD_SUFFIXES)


def load_markdown(slug: str, markdown_dir: Path) -> Opt[str]:
    """Load the ORIGINAL annotated markdown for a slug (skips derived versions)."""
    slug_dir = markdown_dir / slug
    if not slug_dir.exists():
        return None
    md_files = sorted(f for f in slug_dir.glob("*.md") if not is_derived_md(f))
    if md_files:
        return md_files[0].read_text(encoding="utf-8")
    return None


def load_clean_text(slug: str, markdown_dir: Path) -> Opt[str]:
    """Load the pre-generated {base}.clean.md for a slug — annotation
    markup already stripped, generated once by `emit_versions.py --all`
    rather than re-derived inline on every call.

    The .md sidecars contain gold annotations ([text](`PREFIX_value`));
    sending them to an LLM leaks the answers, and their tokens don't align
    with the training data's token space. Reading the pre-generated clean
    file guarantees this function sees exactly what gold_to_training
    tokenizes — a prior version of this function called strip_annotations()
    inline instead, and a nesting bug in that regex corrupted ~50% of the
    corpus with leftover markup for months before it was caught, because
    the bad output was never written anywhere inspectable. If clean.md is
    missing, that's a loud, actionable error, not a silent inline fallback.
    """
    slug_dir = markdown_dir / slug
    if not slug_dir.exists():
        return None
    original = sorted(f for f in slug_dir.glob("*.md") if not is_derived_md(f))
    if original:
        clean_path = original[0].with_name(original[0].stem + ".clean.md")
        if not clean_path.exists():
            raise FileNotFoundError(
                f"{clean_path} missing — run "
                f"`PYTHONPATH=. python3 -m ner.emit_versions --all` first."
            )
        return clean_path.read_text(encoding="utf-8")
    # No raw .md present: in this project clean.md is a committed source
    # artifact and the raw docling .md it was derived from is not tracked.
    # Fall back to the clean file itself (there is one per advisory).
    cleans = sorted(slug_dir.glob("*.clean.md"))
    if not cleans:
        return None
    return cleans[0].read_text(encoding="utf-8")


def text_to_tokens(text: str) -> list[str]:
    """Simple whitespace tokenization."""
    return text.split()


def token_char_offsets(tokens: list[str]) -> list[tuple[int, int]]:
    """Char [start, end) of each token in ' '.join(tokens).

    WARNING: only valid for text that is literally ' '.join(tokens). For real
    documents (newlines, runs of spaces) use tokenize_with_offsets instead.
    """
    offsets = []
    pos = 0
    for tok in tokens:
        offsets.append((pos, pos + len(tok)))
        pos += len(tok) + 1
    return offsets


def tokenize_with_offsets(text: str) -> tuple[list[str], list[tuple[int, int]]]:
    """Whitespace-tokenize text, returning char [start, end) in the ACTUAL text."""
    tokens = text.split()
    offsets = []
    pos = 0
    for tok in tokens:
        idx = text.index(tok, pos)
        offsets.append((idx, idx + len(tok)))
        pos = idx + len(tok)
    return tokens, offsets


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


def extract_entities_from_response(
    text: str, entities_json: list[dict]
) -> set[Span]:
    """
    Convert LLM JSON response to token-level spans.
    Handles:
      - Label normalization (maps extracted labels to canonical training labels)
      - Text matching (case-insensitive search for "text" field)
      - Character→token mapping
    """
    import re

    _, offsets = tokenize_with_offsets(text)
    spans: set[Span] = set()

    for ent in entities_json:
        if not isinstance(ent, dict):
            continue

        label = normalize_label(ent.get("label", ""))
        if not label or label not in LABELS:
            continue

        text_snippet = ent.get("text", "").strip()
        start_char = ent.get("start_char")
        end_char = ent.get("end_char")

        # Trust LLM char offsets only if they actually point at the entity text
        # (LLMs miscount characters routinely).
        if (
            start_char is not None
            and end_char is not None
            and text_snippet
            and text[start_char:end_char].strip().lower() == text_snippet.lower()
        ):
            tok_span = char_span_to_token_span(start_char, end_char, offsets)
            if tok_span:
                spans.add((tok_span[0], tok_span[1], label))
                continue

        # Otherwise: find ALL occurrences of the entity text (gold annotates
        # every occurrence, so pred must too for a fair span comparison).
        if text_snippet:
            pattern = re.escape(text_snippet)
            for match in re.finditer(pattern, text, re.IGNORECASE):
                tok_span = char_span_to_token_span(
                    match.start(), match.end(), offsets
                )
                if tok_span:
                    spans.add((tok_span[0], tok_span[1], label))

    return spans


def gold_document_spans(doc_records: list[dict]) -> set[Span]:
    """Extract gold spans from training records."""
    spans: set[Span] = set()
    for rec in doc_records:
        base = rec["chunk_start"]
        for s, e, label in rec["ner"]:
            spans.add((base + s, base + e, label))
    return spans


