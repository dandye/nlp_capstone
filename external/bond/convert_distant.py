"""Convert the distant-supervision weak labels to BOND's dataset format.

Reads data/gold_v2/distant.jsonl (chunked records from ner.distant_labels:
tokenized_text + inclusive token spans) and writes BOND-style
dataset/cti_distant/{train,dev,test}.json + tag_to_id.json.

BOND record shape (the only fields its loader reads):
    {"str_words": [tok, ...], "tags": [tag_id, ...]}

Split policy: DOCUMENT-LEVEL 80/10/10 — a slug's chunks never straddle two
splits (otherwise near-duplicate overlapping chunks leak between train and
test). Deterministic: slugs are sorted, then shuffled with a fixed seed (0),
so the partition is identical on every run with no wall-clock dependence.

Run with any python3 (no ML deps needed):
    python3 external/bond/convert_distant.py
"""
from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DISTANT_JSONL = REPO / "data/gold_v2/distant.jsonl"
OUT_DIR = Path(__file__).resolve().parent / "dataset/cti_distant"

SPLIT_SEED = 0
TRAIN_FRAC = 0.8
DEV_FRAC = 0.1  # test gets the remainder

# Same 16 labels as ner.frontier_llm_utils.LABELS.
LABELS = [
    "affected software product", "attack technique id", "attack technique name",
    "cve identifier", "cwe identifier", "email address", "file hash",
    "file name", "file path", "hacking tool", "ip address", "malware family",
    "tactic", "threat actor group", "tlp classification", "yara rule name",
]


def build_tag_map() -> dict:
    tag_to_id = {"O": 0}
    for label in LABELS:
        tag_to_id[f"B-{label}"] = len(tag_to_id)
        tag_to_id[f"I-{label}"] = len(tag_to_id)
    # BOND's reference datasets carry these sentinels; keep for fidelity.
    tag_to_id["<START>"] = len(tag_to_id)
    tag_to_id["<STOP>"] = len(tag_to_id)
    return tag_to_id


def record_to_bio(rec: dict, tag_to_id: dict) -> "dict | None":
    tokens = rec["tokenized_text"]
    if not tokens:
        return None
    tags = [0] * len(tokens)
    # Longest spans first so overlaps resolve to the more specific entity.
    spans = sorted(rec["ner"], key=lambda s: -(s[1] - s[0]))
    for start, end, label in spans:  # end is inclusive
        if start >= len(tokens) or end >= len(tokens) or start > end:
            continue
        if any(tags[i] != 0 for i in range(start, end + 1)):
            continue  # overlap with an already-assigned span
        b, i_ = tag_to_id.get(f"B-{label}"), tag_to_id.get(f"I-{label}")
        if b is None:
            continue
        tags[start] = b
        for i in range(start + 1, end + 1):
            tags[i] = i_
    return {"str_words": tokens, "tags": tags}


def assign_splits(slugs: list) -> dict:
    """Deterministic document-level 80/10/10 slug -> split assignment."""
    ordered = sorted(slugs)
    random.Random(SPLIT_SEED).shuffle(ordered)
    n = len(ordered)
    n_train = int(n * TRAIN_FRAC)
    n_dev = int(n * DEV_FRAC)
    assignment = {}
    for i, slug in enumerate(ordered):
        if i < n_train:
            assignment[slug] = "train"
        elif i < n_train + n_dev:
            assignment[slug] = "dev"
        else:
            assignment[slug] = "test"
    return assignment


def main() -> None:
    records_by_slug = defaultdict(list)
    with open(DISTANT_JSONL, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            records_by_slug[rec["slug"]].append(rec)

    slug_split = assign_splits(list(records_by_slug))
    tag_to_id = build_tag_map()
    out = {"train": [], "dev": [], "test": []}
    entity_counts = Counter()

    for slug, recs in records_by_slug.items():
        subset = slug_split[slug]
        for rec in recs:
            bio = record_to_bio(rec, tag_to_id)
            if bio is None:
                continue
            out[subset].append(bio)
            entity_counts[subset] += sum(
                1 for t in bio["tags"] if t != 0 and t % 2 == 1  # B- ids are odd
            )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "tag_to_id.json").write_text(json.dumps(tag_to_id, indent=1))
    n_docs = Counter(slug_split.values())
    for subset in ("train", "dev", "test"):
        (OUT_DIR / f"{subset}.json").write_text(json.dumps(out[subset]))
        print(f"  {subset}: {n_docs[subset]} docs, {len(out[subset])} sentences, "
              f"{entity_counts[subset]} entities")

    print(f"-> {OUT_DIR} ({len(tag_to_id)} tags)")


if __name__ == "__main__":
    main()
