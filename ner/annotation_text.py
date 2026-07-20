"""
Pure text utilities shared across the LLM-gold NER pipeline.

Extracted from the abandoned dictionary-ensemble builder in the old
project, so the current approach carries only the pure text helpers and
none of the dict/NER ensemble logic. Six public
symbols:

  PREFIX_TO_LABEL   — annotation prefix -> canonical label string
  strip_annotations — remove all `[display](`PREFIX_value`)` markup (depth-aware)
  parse_annotations — (clean_display, prefix) for every outermost annotation
  tokenize          — whitespace tokenization
  find_token_span   — locate an entity's token span(s) in a token list
  split_into_chunks — subword-budgeted overlapping chunking

The strip/parse pair is depth-aware (correctly resolves nested annotations);
a single-pass regex silently corrupted ~50% of the corpus before this was
fixed on 2026-07-19 — do not replace it with one.
"""

from __future__ import annotations

import re

# ── Prefix → canonical label ────────────────────────────────────────────────

PREFIX_TO_LABEL: dict[str, str] = {
    "MALWARE":   "malware family",
    "ACTOR":     "threat actor group",
    "TOOL":      "hacking tool",
    "TECHNIQUE": "attack technique name",
    "TACTIC":    "tactic",
    "PRODUCT":   "affected software product",
    "ORG":       "victim organization",
    "COUNTRY":   "country",
    "SECTOR":    "sector or industry",
    "VULN":      "named vulnerability",
    "HASH":      "file hash",
    "MD5":       "file hash",
    "SHA1":      "file hash",
    "SHA256":    "file hash",
    "SHA512":    "file hash",
    "IP":        "ip address",
    "IPV6":      "ipv6 address",
    "DOMAIN":    "domain name",
    "URL":       "url",
    "EMAIL":     "email address",
    "CVE":       "cve identifier",
    "CWE":       "cwe identifier",
    "ATTACK":    "attack technique id",
    "YARA":      "yara rule name",
    "TLP":       "tlp classification",
    "FILENAME":  "file name",
    "FILEPATH":  "file path",
    "REGKEY":    "windows registry key",
}

# ── Annotation parsing (depth-aware) ────────────────────────────────────────

_TAIL_PREFIX_RE = re.compile(r'`([A-Z0-9]+)_')


def _find_outer_annotations(text: str) -> list[tuple[int, int, str, str]]:
    """Find every OUTERMOST `[display](\`PREFIX_value\`)` annotation, correctly
    handling display text that itself contains nested `[...]` (including
    nested annotations).

    The annotation pipeline is supposed to prevent overlapping matches
    ("longest-first"), but in practice a later matcher can still insert a
    short annotation (e.g. ORG "CISA") *inside* the display span of a longer
    one already inserted earlier (e.g. EMAIL "cisa.dhs.gov") when the two come
    from different layers that don't share a suppression set — and since the
    canonical value defaults to a copy of the display text, that inner
    annotation's own backticks end up embedded in the OUTER annotation's value
    field too. A single-pass regex breaks on both fronts: `[^\\]]+` stops at
    the first `]` (the inner one), and `[^\`]+` stops at the first backtick
    (also the inner one's) — either way it silently matches a truncated,
    garbled span instead of the real outer one. This function tracks bracket
    depth for the display and paren depth for the tail instead, so it always
    finds the true outer boundaries regardless of what's nested inside either
    part.

    Returns (match_start, match_end, raw_display, prefix) tuples for the
    outermost annotations only — inner ones are not independently returned
    here (see strip_annotations/parse_annotations for how each caller decides
    what to do with them).
    """
    results = []
    i, n = 0, len(text)
    while i < n:
        if text[i] != '[':
            i += 1
            continue
        depth = 1
        j = i + 1
        while j < n and depth > 0:
            if text[j] == '[':
                depth += 1
            elif text[j] == ']':
                depth -= 1
            j += 1
        if depth != 0:
            i += 1  # unbalanced '[' — not an annotation, move on
            continue
        display_end = j - 1  # index of the matching ']'
        if j >= n or text[j] != '(':
            i += 1  # '[...]' not followed by '(' — not an annotation
            continue
        pdepth = 1
        k = j + 1
        while k < n and pdepth > 0:
            if text[k] == '(':
                pdepth += 1
            elif text[k] == ')':
                pdepth -= 1
            k += 1
        if pdepth != 0:
            i += 1  # unbalanced '(' — not an annotation
            continue
        tail_inner = text[j + 1:k - 1]  # content between the matched '(' and ')'
        if len(tail_inner) < 2 or tail_inner[0] != '`' or tail_inner[-1] != '`':
            i += 1  # tail isn't backtick-wrapped — not an annotation
            continue
        prefix_match = _TAIL_PREFIX_RE.match(tail_inner)
        if prefix_match is None:
            i += 1  # no PREFIX_ at the start of the backtick content
            continue
        raw_display = text[i + 1:display_end]
        results.append((i, k, raw_display, prefix_match.group(1)))
        i = k
    return results


def strip_annotations(text: str) -> str:
    """Remove all annotation markup, recursively resolving nested
    annotations, so the result is guaranteed free of `[...](\`...\`)`
    syntax regardless of nesting depth. This is what every NER model in
    the pipeline (fine-tuned or frontier LLM) actually reads — it must
    never contain label-leaking markup (see load_clean_text)."""
    outer = _find_outer_annotations(text)
    if not outer:
        return text
    out, pos = [], 0
    for start, end, raw_display, _prefix in outer:
        out.append(text[pos:start])
        out.append(strip_annotations(raw_display))  # resolve nesting inside the display text too
        pos = end
    out.append(text[pos:])
    return "".join(out)


def parse_annotations(text: str) -> list[tuple[str, str]]:
    """Return (clean_display_value, prefix) for every OUTERMOST annotation.

    Nested inner annotations (see _find_outer_annotations) are not emitted
    as separate entities — they're artifacts of two matchers stepping on
    each other, not intentional nested entities, consistent with this
    pipeline's longest-match-wins design. The returned display value has
    any nested annotation markup inside it stripped, so gold labels never
    contain literal markup either.
    """
    return [
        (strip_annotations(raw_display), prefix)
        for _start, _end, raw_display, prefix in _find_outer_annotations(text)
    ]


# ── Token-level span conversion ─────────────────────────────────────────────

# Chunk budget in ESTIMATED SUBWORDS, not whitespace tokens: one 64-char hash
# is ~19 subwords, so a 300-whitespace-token hash table is thousands of
# subwords and OOMs a GPU/MPS window.
MAX_SUBWORDS = 320
SUBWORD_OVERLAP = 40  # estimated subwords of overlap between adjacent chunks


def tokenize(text: str) -> list[str]:
    """Whitespace tokenization — keeps punctuation attached to words."""
    return text.split()


def find_token_span(tokens: list[str], entity: str) -> list[tuple[int, int]]:
    """
    Find all (start_tok, end_tok) spans where entity appears in the token list.
    Handles single-token and multi-token entities. Case-insensitive.
    """
    entity_tokens = entity.split()
    n, m = len(tokens), len(entity_tokens)
    spans = []
    for i in range(n - m + 1):
        if [t.lower().strip(".,;:!?\"'()[]") for t in tokens[i:i+m]] == \
           [t.lower().strip(".,;:!?\"'()[]") for t in entity_tokens]:
            spans.append((i, i + m - 1))
    return spans


def est_subwords(token: str) -> int:
    """Rough SentencePiece cost: ~4 chars per subword, minimum 1."""
    return max(1, (len(token) + 3) // 4)


def split_into_chunks(
    tokens: list[str],
    budget: int = MAX_SUBWORDS,
    overlap_budget: int = SUBWORD_OVERLAP,
) -> list[tuple[int, list[str]]]:
    """
    Split token list into overlapping chunks whose ESTIMATED subword cost
    stays within budget. Returns (start_offset, tokens) in whitespace-token
    indices. A single token over budget still gets its own chunk.
    """
    costs = [est_subwords(t) for t in tokens]
    n = len(tokens)
    chunks = []
    start = 0
    while start < n:
        end = start
        acc = 0
        while end < n and (end == start or acc + costs[end] <= budget):
            acc += costs[end]
            end += 1
        chunks.append((start, tokens[start:end]))
        if end >= n:
            break
        back = end
        acc_overlap = 0
        while back > start + 1 and acc_overlap < overlap_budget:
            back -= 1
            acc_overlap += costs[back]
        start = back
    return chunks
