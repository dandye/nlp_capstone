"""Convert five external CTI NER corpora to this project's canonical eval shape.

Each corpus (CyNER, APTNER, AttackER, AnnoCTR, CyberNER) is emitted under
``data/evals/{Corpus}/`` as three files, so the existing zero-shot eval
machinery (ner.external_eval_gliner, the frontier pipeline) can score models
against each corpus's OWN native label schema, with no label mapping:

  eval.jsonl  one JSON object per sentence, shape
              {"slug", "chunk_start": 0, "tokenized_text": [...],
               "ner": [[start_tok, end_tok_inclusive, label], ...]}
  labels.json JSON list of the corpus's native entity types (BIO/BIOES
              prefixes stripped, deduped, sorted)
  split.json  {"train": [], "val": [], "test": [all slugs sorted]}

These corpora are pre-tokenized; their own tokens are used verbatim (never
re-tokenized). Run with the CPU venv (no ML deps):

    PYTHONPATH=. .venv/bin/python3 -m ner.external_corpus_convert

Provenance note: authored directly (Claude-family) rather than via the codex
GPT-family producer, because the codex account hit its usage cap mid-task.
Deterministic parsing against a hand-verified spec; verified empirically by
running and eyeballing real output + per-label counts.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# csv fields in CyberNER can be very long (whole sentences never, but URLs/paths).
csv.field_size_limit(10_000_000)

Span = Tuple[int, int, str]  # (start_tok, end_tok_inclusive, label)

# A valid APTNER tag: O, or a BIOES prefix on a type that may itself contain
# hyphens (real tags include S-OS, S-DOM, S-LOC-NATO).
_APTNER_TAG = re.compile(r"^[BIES]-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")


def split_tag(tag: str) -> Tuple[str, Optional[str]]:
    """Return (prefix, type) for a BIO/BIOES tag; ('O', None) for outside."""
    if tag == "O" or not tag:
        return "O", None
    if len(tag) >= 2 and tag[0] in "BIES" and tag[1] == "-":
        return tag[0], tag[2:]
    # Unprefixed / unexpected tag: treat the whole thing as a B-span type so
    # no annotated token is silently dropped.
    return "B", tag


def decode_spans(tags: List[str], break_before: Optional[Set[int]] = None) -> List[Span]:
    """Decode a BIO/BIOES tag sequence into inclusive-end token spans.

    E-X closes an open X span (like I-X then close); S-X is a single-token
    span. Any index in ``break_before`` force-closes the open span before that
    token (used for APTNER, where a skipped malformed line breaks a span).
    Defensive against broken continuations (stray I-/E- with no open span).
    """
    breaks = break_before or set()
    spans: List[Span] = []
    start: Optional[int] = None
    cur: Optional[str] = None

    def flush(end_idx: int) -> None:
        nonlocal start, cur
        if start is not None:
            spans.append((start, end_idx, cur))  # type: ignore[arg-type]
            start, cur = None, None

    for i, tag in enumerate(tags):
        if i in breaks:
            flush(i - 1)
        prefix, typ = split_tag(tag)
        if prefix == "O":
            flush(i - 1)
        elif prefix == "B":
            flush(i - 1)
            start, cur = i, typ
        elif prefix == "S":
            flush(i - 1)
            spans.append((i, i, typ))  # type: ignore[arg-type]
        else:  # I or E
            if start is not None and cur == typ:
                if prefix == "E":
                    flush(i)
                # I of same type: keep extending
            else:
                flush(i - 1)
                if prefix == "E":
                    spans.append((i, i, typ))  # type: ignore[arg-type]
                else:
                    start, cur = i, typ
    flush(len(tags) - 1)
    return spans


def _record(corpus_lower: str, idx: int, tokens: List[str], tags: List[str],
            break_before: Optional[Set[int]] = None) -> Dict:
    spans = decode_spans(tags, break_before)
    return {
        "slug": f"{corpus_lower}_test_{idx:05d}",
        "chunk_start": 0,
        "tokenized_text": tokens,
        "ner": [[s, e, l] for (s, e, l) in spans],
    }


# --- Column-format readers (CyNER, APTNER) -----------------------------------

def read_column_file(path: Path, sep: Optional[str]) -> List[Tuple[List[str], List[str]]]:
    """Read a token<sep>tag column file into (tokens, tags) sentences.

    sep=None means any-whitespace split (used for CyNER's tabs too). Blank
    lines delimit sentences; a trailing sentence with no final blank line is
    flushed. Malformed handling is caller-specific and not applied here.
    """
    sentences: List[Tuple[List[str], List[str]]] = []
    tokens: List[str] = []
    tags: List[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if tokens:
                sentences.append((tokens, tags))
                tokens, tags = [], []
            continue
        parts = line.split(sep)
        if len(parts) < 2:
            continue
        tokens.append(parts[0])
        tags.append(parts[-1])
    if tokens:
        sentences.append((tokens, tags))
    return sentences


def convert_cyner(base: Path, corpus_lower: str) -> Tuple[List[Dict], int]:
    path = base / "CyNER" / "dataset" / "mitre" / "test.txt"
    records: List[Dict] = []
    for i, (tokens, tags) in enumerate(read_column_file(path, sep="\t")):
        records.append(_record(corpus_lower, i, tokens, tags))
    return records, 0


def convert_aptner(base: Path, corpus_lower: str) -> Tuple[List[Dict], int]:
    """APTNER: space-separated BIOES; skip (and count) malformed lines.

    A line is kept iff it splits into exactly two whitespace fields and the
    tag matches the BIOES grammar (multi-hyphen types allowed). Using
    ``str.split()`` recovers cosmetically-broken lines (e.g. a stray double
    space before the tag) as real entities; only lines with genuine extra
    fields (e.g. ``Georgia S-LOC-NATO S-IDTY``) are dropped. A dropped line
    force-closes any open span (break_before).
    """
    path = base / "APTNER" / "APTNERtest.txt"
    text = path.read_text(encoding="utf-8", errors="replace")
    records: List[Dict] = []
    skipped = 0
    idx = 0

    tokens: List[str] = []
    tags: List[str] = []
    breaks: Set[int] = set()
    pending_break = False

    def flush_sentence() -> None:
        nonlocal tokens, tags, breaks, pending_break, idx
        if tokens:
            records.append(_record(corpus_lower, idx, tokens, tags, breaks))
            idx += 1
        tokens, tags, breaks = [], [], set()
        pending_break = False

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush_sentence()
            continue
        parts = line.split()
        if len(parts) == 2 and (parts[1] == "O" or _APTNER_TAG.match(parts[1])):
            if pending_break and tokens:
                breaks.add(len(tokens))
                pending_break = False
            tokens.append(parts[0])
            tags.append(parts[1])
        else:
            skipped += 1
            if tokens:
                pending_break = True
    flush_sentence()
    return records, skipped


# --- JSON-Lines readers (AttackER, AnnoCTR) ----------------------------------

def read_jsonl(path: Path) -> List[Dict]:
    records: List[Dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def convert_token_tag_jsonl(path: Path, corpus_lower: str, tag_field: str) -> Tuple[List[Dict], int]:
    records: List[Dict] = []
    mismatched = 0
    idx = 0
    for obj in read_jsonl(path):
        tokens = obj["tokens"]
        tags = obj[tag_field]
        if len(tokens) != len(tags):
            mismatched += 1
            continue
        if not tokens:
            continue
        records.append(_record(corpus_lower, idx, tokens, tags))
        idx += 1
    return records, mismatched


def convert_attacker(base: Path, corpus_lower: str) -> Tuple[List[Dict], int]:
    path = base / "AttackER" / "test.json"
    return convert_token_tag_jsonl(path, corpus_lower, "tags")


def convert_annoctr(base: Path, corpus_lower: str) -> Tuple[List[Dict], int]:
    path = base / "AnnoCTR" / "AnnoCTR" / "ner_json" / "test.json"
    return convert_token_tag_jsonl(path, corpus_lower, "ne_tags")


# --- CSV reader (CyberNER) ---------------------------------------------------

def convert_cyberner(base: Path, corpus_lower: str) -> Tuple[List[Dict], int]:
    """Whole file, grouped by Sentence_ID (first-appearance order), STIX_Tag."""
    path = base / "CyberNER" / "dataset" / "cyberner_combined_stix.csv"
    groups: "OrderedDict[str, Tuple[List[str], List[str]]]" = OrderedDict()
    empty_words = 0
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row["Sentence_ID"]
            word = row["Word"]
            tag = row["STIX_Tag"] or "O"
            if word is None or word.strip() == "":
                empty_words += 1
            if sid not in groups:
                groups[sid] = ([], [])
            groups[sid][0].append("" if word is None else word)
            groups[sid][1].append(tag)
    records: List[Dict] = []
    idx = 0
    for _sid, (tokens, tags) in groups.items():
        if not tokens:
            continue
        records.append(_record(corpus_lower, idx, tokens, tags))
        idx += 1
    return records, empty_words


CONVERTERS = OrderedDict([
    ("CyNER", ("cyner", convert_cyner, "skipped")),
    ("APTNER", ("aptner", convert_aptner, "skipped malformed lines")),
    ("AttackER", ("attacker", convert_attacker, "mismatched token/tag records")),
    ("AnnoCTR", ("annoctr", convert_annoctr, "mismatched token/tag records")),
    ("CyberNER", ("cyberner", convert_cyberner, "empty Word cells")),
])


def write_corpus(base: Path, corpus: str, records: List[Dict]) -> Tuple[int, Counter]:
    out_dir = base / corpus
    out_dir.mkdir(parents=True, exist_ok=True)

    label_counts: Counter = Counter()
    labels: Set[str] = set()
    for rec in records:
        for _s, _e, label in rec["ner"]:
            label_counts[label] += 1
            labels.add(label)

    with open(out_dir / "eval.jsonl", "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    (out_dir / "labels.json").write_text(
        json.dumps(sorted(labels), indent=2), encoding="utf-8"
    )

    slugs = sorted(rec["slug"] for rec in records)
    (out_dir / "split.json").write_text(
        json.dumps({"train": [], "val": [], "test": slugs}, indent=2),
        encoding="utf-8",
    )
    return sum(label_counts.values()), label_counts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert external CTI NER corpora to canonical eval shape."
    )
    parser.add_argument("--base-dir", default="data/evals",
                        help="Root directory containing the corpus folders")
    args = parser.parse_args()
    base = Path(args.base_dir)

    for corpus, (corpus_lower, fn, aux_label) in CONVERTERS.items():
        try:
            records, aux = fn(base, corpus_lower)
        except FileNotFoundError as e:
            print(f"[{corpus}] SKIPPED — source not found: {e}", file=sys.stderr)
            continue
        total_entities, label_counts = write_corpus(base, corpus, records)

        print(f"\n=== {corpus} ===")
        print(f"  sentences:      {len(records)}")
        print(f"  entities:       {total_entities}")
        print(f"  labels ({len(label_counts)}):")
        for label, count in sorted(label_counts.items()):
            print(f"      {label:<28} {count}")
        print(f"  {aux_label}: {aux}")


if __name__ == "__main__":
    main()
