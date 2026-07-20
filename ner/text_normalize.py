"""
Text normalization for the model-facing clean corpus (.clean.md).

Applied by emit_versions.py AFTER annotation stripping, BEFORE anything
downstream (training-data generation, frontier LLM inference) reads the
text. Targets the three mechanical noise sources the 300-span gold audit
identified in the training labels (2026-07-19):

  1. strip_boilerplate — docling repeats per-page furniture at every page
     break: 'TLP:CLEAR' banners (74x in one doc), 'Page N of M | Product
     ID' pagination, org banners ('FBI | CISA | ACSC'), and the report
     title (25x in ar25-261a). These generated 1,105 'Page'-as-malware
     training spans (9.4% of ALL training signal) and phone-as-email FPs.
  2. rejoin_split_hashes — PDF line wrap splits hashes across lines in
     IOC tables ('...834E80ADEEC8 84AEBC55ECCBF7'); fragments then get
     annotated as (invalid-length) hashes, and models learn to emit
     fragments.
  3. code_regions — MAR advisories embed scripts; regex annotators
     hallucinate file paths / emails / hashes inside them
     ('os.path.join(', 'PGPASSWORD={};echo'). This module only DETECTS
     code; suppression policy lives with the annotators (see
     llm_gold.py's span gates).

Design constraints learned from the corpus (do not "simplify" these away):
  - Dedupe must compare RAW lines, not digit-normalized ones: IOC tables
    contain dozens of lines identical up to digits ('Ipv4 1.2.3[.]4' x48
    in aa25-022a) that are DISTINCT real indicators.
  - Lines inside code regions are exempt from dedupe: '}', 'else:' etc.
    legitimately repeat and removing them mutilates script content.
  - Repeated furniture is dropped keep-FIRST, not remove-all, so one
    'TLP:CLEAR' banner and one title line survive per document (TLP
    remains a learnable label; the document keeps its title).
"""

from __future__ import annotations

import re

# Raw-identical line must appear at least this many times (outside code)
# to be treated as page furniture.
DEDUPE_MIN_REPEATS = 4
# ...and must have at least this many alphabetic characters (protects
# short structural lines like '}' or '---' from dedupe).
DEDUPE_MIN_ALPHA = 4

# Pagination furniture: dropped wherever it appears (page numbers differ
# per instance, so raw-dedupe can't catch these).
PAGINATION_RE = re.compile(
    r"^\s*page\s+\d+(\s+of\s+\d+)?\s*(\||tlp:|product\s+id|$)", re.IGNORECASE
)

_HEX_FRAGMENT_RE = re.compile(r"\b([0-9a-fA-F]{8,127})\s+([0-9a-fA-F]{4,63})\b")
_VALID_HASH_LENS = frozenset({32, 40, 64, 128})

_CODE_SYMBOLS = set("(){}[]=|$;`<>\\")
_CODE_KEYWORD_RE = re.compile(
    r"^\s*(def |import |from |if |elif |else:|for |while |return |try:|except"
    r"|echo |export |grep |cut |cat |sudo |chmod |curl |wget |\$|#!|rule \w+)"
)


def _is_codey_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if _CODE_KEYWORD_RE.match(stripped):
        return True
    symbol_count = sum(1 for c in stripped if c in _CODE_SYMBOLS)
    return symbol_count / len(stripped) > 0.15


def code_regions(text: str) -> list[tuple[int, int]]:
    """Return [start_line, end_line) ranges of probable code/script blocks.

    A region is a run of >= 2 consecutive codey lines (symbol-dense or
    starting with a code keyword). Single codey lines in prose are NOT
    masked — an inline mention of a path or command in a sentence is
    legitimate annotation territory; multi-line script blocks are not.
    """
    lines = text.splitlines()
    codey = [_is_codey_line(l) for l in lines]
    regions = []
    start = None
    for i, c in enumerate(codey):
        if c and start is None:
            start = i
        elif not c and start is not None:
            if i - start >= 2:
                regions.append((start, i))
            start = None
    if start is not None and len(lines) - start >= 2:
        regions.append((start, len(lines)))
    return regions


def code_region_text(text: str) -> str:
    """Concatenated text of all code regions (for value-level suppression:
    'does this candidate entity appear only inside code?')."""
    lines = text.splitlines()
    parts = []
    for start, end in code_regions(text):
        parts.extend(lines[start:end])
    return "\n".join(parts)


def strip_boilerplate(text: str) -> str:
    """Remove docling page furniture: pagination lines (dropped entirely)
    and raw-identical repeated banner/title lines (keep first occurrence).
    Lines inside code regions are never touched."""
    lines = text.splitlines()
    in_code: set[int] = set()
    for start, end in code_regions(text):
        in_code.update(range(start, end))

    # Count raw-identical repeats among non-code, alpha-bearing lines
    counts: dict[str, int] = {}
    for i, line in enumerate(lines):
        if i in in_code:
            continue
        raw = line.strip()
        if sum(1 for c in raw if c.isalpha()) >= DEDUPE_MIN_ALPHA:
            counts[raw] = counts.get(raw, 0) + 1

    seen: set[str] = set()
    out = []
    for i, line in enumerate(lines):
        raw = line.strip()
        if i not in in_code:
            if raw and PAGINATION_RE.match(raw):
                continue  # pagination: drop all occurrences
            if counts.get(raw, 0) >= DEDUPE_MIN_REPEATS:
                if raw in seen:
                    continue  # furniture repeat: keep first only
                seen.add(raw)
        out.append(line)
    return "\n".join(out)


def rejoin_split_hashes(text: str) -> str:
    """Rejoin hex runs that PDF line wrap split across whitespace, when
    (a) the concatenation has a valid hash length (MD5/SHA1/SHA256/SHA512)
    and (b) the FIRST fragment alone does NOT — two adjacent complete
    hashes (e.g. an MD5 column next to another) must never be merged.

    Deliberately repairs TWO-fragment splits only (every split observed
    in the corpus is two-fragment). Multi-fragment splits whose pairwise
    sums don't land exactly on a valid length are left untouched — any
    heuristic clever enough to resolve them can also merge unrelated
    adjacent hex runs in IOC tables, which is the worse failure. The
    orphan fragments that remain are then rejected by the span
    validators, so they cost recall on one hash, not label correctness."""
    prev = None
    while prev != text:
        prev = text

        def _join(m: re.Match) -> str:
            a, b = m.group(1), m.group(2)
            if len(a) in _VALID_HASH_LENS:
                return m.group(0)  # first part is already a complete hash
            if len(a) + len(b) in _VALID_HASH_LENS:
                return a + b
            return m.group(0)

        text = _HEX_FRAGMENT_RE.sub(_join, text)
    return text


def normalize_clean_text(text: str) -> str:
    """Full normalization pipeline for .clean.md: boilerplate first (so
    furniture never participates in hash joining), then hash repair."""
    return rejoin_split_hashes(strip_boilerplate(text))
