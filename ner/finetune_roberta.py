"""
RoBERTa token-classification baseline for the CTI corpus, scored with the
SAME document-level span harness as the GLiNER/Gemini evaluations
(ner.evaluate.Scorer — strict = exact (start, end, label) on
chunk_start-offset token indices). Numbers from this script are directly
comparable to data/results_finetuned.json / frontier results.

Design notes:
  - Whole-word BIO tagging: gold spans are word-level; the first wordpiece of
    each word carries the tag, continuations are masked (-100).
  - Sliding windows by wordpiece budget: chunks reach 292 words and hash
    tokens explode into many wordpieces, so a fixed 512 truncation silently
    drops spans (BOND's max_seq_length=256 run shows the resulting recall
    hit). Windows of <=510 wordpieces with 50-word overlap cover every word;
    at prediction time each word takes its tag from the window where it is
    most interior.
  - Self-contained training loop (bond venv has no accelerate/datasets).

Usage (.venv-ml — torch 2.13 + transformers 4.46):
    PYTHONPATH=. .venv-ml/bin/python3 -m ner.finetune_roberta \\
        --model-name roberta-base --output-dir models/roberta-cti-base

    # variants
    ... --model-name roberta-large --batch-size 8 --grad-accum 4
    ... --model-name ehsanaghaei/SecureBERT

    # evaluate an existing checkpoint only
    ... --eval-only models/roberta-cti-base/best
"""

from __future__ import annotations

import argparse
import gc
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from ner.evaluate import (
    Scorer,
    Span,
    gold_document_spans,
    load_records,
    print_table,
)

MAX_WORDPIECES = 510  # 512 minus <s> </s>
WINDOW_OVERLAP_WORDS = 50


# ── label space ───────────────────────────────────────────────────────────────

def build_tag_maps(labels: list[str]) -> tuple[dict[str, int], dict[int, str]]:
    tag_to_id = {"O": 0}
    for label in labels:
        tag_to_id[f"B-{label}"] = len(tag_to_id)
        tag_to_id[f"I-{label}"] = len(tag_to_id)
    return tag_to_id, {v: k for k, v in tag_to_id.items()}


def spans_to_bio(n_words: int, spans: list, tag_to_id: dict[str, int]) -> list[int]:
    tags = [0] * n_words
    # longest-first so overlaps resolve to the more specific entity
    for start, end, label in sorted(spans, key=lambda s: -(s[1] - s[0])):
        if start < 0 or end >= n_words or start > end:
            continue
        if any(tags[i] != 0 for i in range(start, end + 1)):
            continue
        tags[start] = tag_to_id[f"B-{label}"]
        for i in range(start + 1, end + 1):
            tags[i] = tag_to_id[f"I-{label}"]
    return tags


def bio_to_spans(word_tags: list[str]) -> list[tuple[int, int, str]]:
    """Decode BIO tags (with standard I-after-O repair) to inclusive spans."""
    spans = []
    start, label = None, None
    for i, tag in enumerate(word_tags):
        if tag.startswith("B-") or (
            tag.startswith("I-") and (label is None or tag[2:] != label)
        ):
            if label is not None:
                spans.append((start, i - 1, label))
            start, label = i, tag[2:]
        elif tag == "O" and label is not None:
            spans.append((start, i - 1, label))
            start, label = None, None
    if label is not None:
        spans.append((start, len(word_tags) - 1, label))
    return spans


# ── windowing ─────────────────────────────────────────────────────────────────

def make_windows(word_piece_counts: list[int]) -> list[tuple[int, int]]:
    """[start_word, end_word) windows fitting MAX_WORDPIECES, overlapping."""
    n = len(word_piece_counts)
    windows = []
    start = 0
    while start < n:
        budget, end = 0, start
        while end < n and budget + word_piece_counts[end] <= MAX_WORDPIECES:
            budget += word_piece_counts[end]
            end += 1
        if end == start:  # single pathological word longer than the budget
            end = start + 1
        windows.append((start, end))
        if end >= n:
            break
        # overlap adapts to window length so piece-heavy windows still stride
        overlap = min(WINDOW_OVERLAP_WORDS, (end - start) // 4)
        start = max(start + 1, end - overlap)
    return windows


class ChunkWindows:
    """Tokenized sliding windows for one corpus chunk record."""

    def __init__(self, rec: dict, tokenizer, tag_to_id: dict[str, int]):
        self.rec = rec
        words = rec["tokenized_text"]
        self.n_words = len(words)
        self.word_pieces = [
            tokenizer(w, add_special_tokens=False)["input_ids"] or
            [tokenizer.unk_token_id]
            for w in words
        ]
        self.gold_bio = spans_to_bio(self.n_words, rec["ner"], tag_to_id)
        self.windows = make_windows([len(p) for p in self.word_pieces])
        self.cls = tokenizer.cls_token_id
        self.sep = tokenizer.sep_token_id

    def encode(self, w_start: int, w_end: int) -> dict:
        input_ids, labels, word_index = [self.cls], [-100], [-1]
        for wi in range(w_start, w_end):
            pieces = self.word_pieces[wi][: MAX_WORDPIECES]
            input_ids.extend(pieces)
            labels.extend([self.gold_bio[wi]] + [-100] * (len(pieces) - 1))
            word_index.extend([wi] + [-1] * (len(pieces) - 1))
        input_ids.append(self.sep)
        labels.append(-100)
        word_index.append(-1)
        return {"input_ids": input_ids, "labels": labels,
                "word_index": word_index, "window": (w_start, w_end)}


class WindowDataset(Dataset):
    def __init__(self, chunks: list[ChunkWindows]):
        self.items = [
            (c, ws, we) for c in chunks for ws, we in c.windows
        ]

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, i: int) -> dict:
        c, ws, we = self.items[i]
        return c.encode(ws, we)

    def piece_len(self, i: int) -> int:
        c, ws, we = self.items[i]
        return sum(len(c.word_pieces[wi]) for wi in range(ws, we)) + 2


class LengthGroupedSampler(torch.utils.data.Sampler):
    """Shuffled batches drawn from length-sorted buckets.

    Random shuffling pairs short and long sequences in the same batch,
    padding every item to the longest — with chunk lengths ranging 22-292
    words (and hash-heavy chunks fragmenting into many more wordpieces),
    that wastes most of a batch's compute on padding. Sorting into
    bucket_mult*batch_size buckets and shuffling only within each bucket
    keeps batches length-homogeneous while still varying per epoch.
    """

    def __init__(self, lengths: list[int], batch_size: int,
                bucket_mult: int = 50, seed: int = 0):
        self.lengths = lengths
        self.batch_size = batch_size
        self.bucket_size = batch_size * bucket_mult
        self.seed = seed
        self.epoch = 0

    def __len__(self) -> int:
        return len(self.lengths)

    def __iter__(self):
        rng = random.Random(self.seed + self.epoch)
        self.epoch += 1
        order = sorted(range(len(self.lengths)), key=lambda i: self.lengths[i])
        batches = []
        for start in range(0, len(order), self.bucket_size):
            bucket = order[start:start + self.bucket_size]
            rng.shuffle(bucket)
            for bstart in range(0, len(bucket), self.batch_size):
                batches.append(bucket[bstart:bstart + self.batch_size])
        rng.shuffle(batches)
        return iter(i for batch in batches for i in batch)


def collate(batch: list[dict], pad_id: int) -> dict:
    width = max(len(b["input_ids"]) for b in batch)
    ids = torch.full((len(batch), width), pad_id, dtype=torch.long)
    mask = torch.zeros((len(batch), width), dtype=torch.long)
    labels = torch.full((len(batch), width), -100, dtype=torch.long)
    for i, b in enumerate(batch):
        n = len(b["input_ids"])
        ids[i, :n] = torch.tensor(b["input_ids"])
        mask[i, :n] = 1
        labels[i, :n] = torch.tensor(b["labels"])
    return {"input_ids": ids, "attention_mask": mask, "labels": labels}


# ── prediction ────────────────────────────────────────────────────────────────

@torch.no_grad()
def predict_chunk_spans(
    model, chunk: ChunkWindows, id_to_tag: dict[int, str], device,
) -> set[Span]:
    """Per-word tags from the window where the word is most interior."""
    best_margin = [-1] * chunk.n_words
    word_tag = ["O"] * chunk.n_words
    for ws, we in chunk.windows:
        enc = chunk.encode(ws, we)
        ids = torch.tensor([enc["input_ids"]], device=device)
        mask = torch.ones_like(ids)
        logits = model(input_ids=ids, attention_mask=mask).logits[0]
        pred = logits.argmax(-1).tolist()
        for pos, wi in enumerate(enc["word_index"]):
            if wi < 0:
                continue
            margin = min(wi - ws, we - 1 - wi)
            if margin > best_margin[wi]:
                best_margin[wi] = margin
                word_tag[wi] = id_to_tag[pred[pos]]
    base = chunk.rec["chunk_start"]
    return {
        (base + s, base + e, label)
        for s, e, label in bio_to_spans(word_tag)
    }


def evaluate_subset(
    model, chunks_by_doc: dict[str, list[ChunkWindows]],
    id_to_tag: dict[int, str], device, verbose: bool = False,
) -> tuple[dict, dict]:
    model.eval()
    strict, relaxed = Scorer(), Scorer()
    for i, (slug, chunks) in enumerate(sorted(chunks_by_doc.items()), 1):
        gold = gold_document_spans([c.rec for c in chunks])
        pred: set[Span] = set()
        for c in chunks:
            pred |= predict_chunk_spans(model, c, id_to_tag, device)
        strict.add_strict(gold, pred)
        relaxed.add_relaxed(gold, pred)
        if verbose:
            print(f"  [{i}/{len(chunks_by_doc)}] {slug}: "
                  f"{len(gold)} gold, {len(pred)} pred", file=sys.stderr)
    return strict.report(), relaxed.report()


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--model-name", default="roberta-base")
    ap.add_argument("--output-dir", default=None)
    ap.add_argument("--data", default="data/gliner_train.jsonl")
    ap.add_argument("--split", default="data/split_slugs.json")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--grad-accum", type=int, default=1)
    ap.add_argument("--warmup-frac", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", choices=["cuda", "mps", "cpu"], default=None)
    ap.add_argument("--eval-only", metavar="CHECKPOINT",
                    help="Skip training; evaluate this checkpoint on test")
    ap.add_argument("--results", default=None,
                    help="Results JSON path (default data/roberta_results/"
                         "{basename(output-dir or checkpoint)}.json)")
    args = ap.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = torch.device(args.device) if args.device else torch.device(
        "cuda" if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available() else "cpu"
    )
    print(f"device: {device}")

    from transformers import (
        AutoModelForTokenClassification,
        AutoTokenizer,
        get_linear_schedule_with_warmup,
    )

    records = load_records(Path(args.data))
    split = json.loads(Path(args.split).read_text(encoding="utf-8"))

    model_src = args.eval_only or args.model_name
    tokenizer = AutoTokenizer.from_pretrained(model_src, add_prefix_space=True)
    if args.eval_only:
        # Label space MUST come from the checkpoint, not the eval data — an
        # eval file that happens to exercise fewer labels would otherwise
        # derive a smaller tag set and shift every tag id (classifier-head
        # size mismatch at best, silently wrong label decoding at worst).
        model = AutoModelForTokenClassification.from_pretrained(model_src).to(device)
        tag_to_id = dict(model.config.label2id)
        id_to_tag = {int(i): t for i, t in model.config.id2label.items()}
        labels = sorted({t[2:] for t in tag_to_id if t != "O"})
        print(f"labels from checkpoint: {len(labels)} -> {len(tag_to_id)} BIO tags")
    else:
        labels = sorted({l for rec in records for _, _, l in rec["ner"]})
        tag_to_id, id_to_tag = build_tag_maps(labels)
        print(f"labels: {len(labels)} -> {len(tag_to_id)} BIO tags")
        model = AutoModelForTokenClassification.from_pretrained(
            model_src,
            num_labels=len(tag_to_id),
            id2label={i: t for t, i in tag_to_id.items()},
            label2id=tag_to_id,
        ).to(device)

    by_subset: dict[str, dict[str, list[ChunkWindows]]] = {
        s: defaultdict(list) for s in ("train", "val", "test")
    }
    slug_subset = {
        slug: s for s in ("train", "val", "test") for slug in split[s]
    }
    t0 = time.time()
    n_windows = 0
    for rec in records:
        s = slug_subset.get(rec["slug"])
        if s is None:
            continue
        cw = ChunkWindows(rec, tokenizer, tag_to_id)
        n_windows += len(cw.windows)
        by_subset[s][rec["slug"]].append(cw)
    multi = sum(
        1 for docs in by_subset.values() for cs in docs.values()
        for c in cs if len(c.windows) > 1
    )
    print(f"tokenized in {time.time()-t0:.0f}s — "
          f"{n_windows} windows, {multi} chunks need >1 window")

    if not args.eval_only:
        out_dir = Path(args.output_dir
                       or f"models/roberta-cti-{Path(args.model_name).name}")
        out_dir.mkdir(parents=True, exist_ok=True)
        train_chunks = [
            c for cs in by_subset["train"].values() for c in cs
        ]
        train_ds = WindowDataset(train_chunks)
        lengths = [train_ds.piece_len(i) for i in range(len(train_ds))]
        sampler = LengthGroupedSampler(lengths, args.batch_size, seed=args.seed)
        loader = DataLoader(
            train_ds,
            batch_size=args.batch_size,
            sampler=sampler,
            drop_last=False,
            collate_fn=lambda b: collate(b, tokenizer.pad_token_id),
        )
        steps_total = (len(loader) // args.grad_accum) * args.epochs
        optim = torch.optim.AdamW(model.parameters(), lr=args.lr,
                                  weight_decay=0.01, eps=1e-6)
        sched = get_linear_schedule_with_warmup(
            optim, int(steps_total * args.warmup_frac), steps_total
        )
        best_f1 = -1.0
        log_every = max(1, len(loader) // 5)
        skipped_nonfinite = 0
        for epoch in range(1, args.epochs + 1):
            model.train()
            t0, running = time.time(), 0.0
            for step, batch in enumerate(loader, 1):
                batch = {k: v.to(device) for k, v in batch.items()}
                raw_loss = model(**batch).loss
                if not torch.isfinite(raw_loss):
                    # Sporadic non-finite forward pass (observed intermittently
                    # on the MPS backend with roberta-large, not reproducible
                    # with a fixed batch order — a real op glitch, not a data
                    # artifact). Backpropagating this would set every
                    # parameter to NaN permanently, so drop the whole
                    # accumulation window rather than let one bad step
                    # destroy the run.
                    skipped_nonfinite += 1
                    print(f"  epoch {epoch} step {step}/{len(loader)}: "
                          f"non-finite loss ({raw_loss.item()}), skipping "
                          f"accumulation window (total skipped: "
                          f"{skipped_nonfinite})", flush=True)
                    optim.zero_grad()
                    # raw_loss.backward() never ran, so its autograd graph
                    # (all forward-pass activations) is still referenced —
                    # and has reference cycles refcounting alone won't
                    # collect. Free explicitly or repeated skips leak MPS
                    # memory until the process OOMs.
                    del raw_loss, batch
                    gc.collect()
                    torch.mps.empty_cache()
                    continue
                loss = raw_loss / args.grad_accum
                loss.backward()
                running += loss.item() * args.grad_accum
                if step % args.grad_accum == 0:
                    grad_norm = torch.nn.utils.clip_grad_norm_(
                        model.parameters(), 1.0)
                    if not torch.isfinite(grad_norm):
                        skipped_nonfinite += 1
                        print(f"  epoch {epoch} step {step}/{len(loader)}: "
                              f"non-finite grad norm, skipping optimizer "
                              f"step (total skipped: {skipped_nonfinite})",
                              flush=True)
                        optim.zero_grad()
                        continue
                    optim.step()
                    sched.step()
                    optim.zero_grad()
                if step % log_every == 0 or step == len(loader):
                    print(f"  epoch {epoch} step {step}/{len(loader)} "
                          f"({time.time()-t0:.0f}s, seq_len {batch['input_ids'].shape[1]}) "
                          f"loss {running/step:.4f}", flush=True)
            val_strict, _ = evaluate_subset(
                model, by_subset["val"], id_to_tag, device
            )
            f1 = val_strict["micro"]["F1"]
            marker = ""
            if f1 > best_f1:
                best_f1 = f1
                model.save_pretrained(out_dir / "best")
                tokenizer.save_pretrained(out_dir / "best")
                marker = "  <- saved best"
            print(f"epoch {epoch}/{args.epochs}: "
                  f"loss {running/len(loader):.4f}, "
                  f"val strict F1 {f1:.4f} "
                  f"({time.time()-t0:.0f}s){marker}")
        # reload best for the test pass
        model = AutoModelForTokenClassification.from_pretrained(
            out_dir / "best"
        ).to(device)
        checkpoint = str(out_dir / "best")
    else:
        checkpoint = args.eval_only

    print("\nevaluating on test...")
    strict_report, relaxed_report = evaluate_subset(
        model, by_subset["test"], id_to_tag, device, verbose=True
    )
    print_table("STRICT (exact span + label)", strict_report)
    print_table("RELAXED (overlap + label)", relaxed_report)

    results_path = Path(
        args.results
        or f"data/roberta_results/{Path(checkpoint).parent.name or Path(checkpoint).name}.json"
    )
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps({
        "model": args.model_name,
        "checkpoint": checkpoint,
        "subset": "test",
        "n_documents": len(by_subset["test"]),
        "harness": "ner.evaluate (document-level, strict span+label)",
        "windowing": {
            "max_wordpieces": MAX_WORDPIECES,
            "overlap_words": WINDOW_OVERLAP_WORDS,
        },
        "hyperparams": {
            "epochs": args.epochs, "lr": args.lr,
            "batch_size": args.batch_size, "grad_accum": args.grad_accum,
            "seed": args.seed,
        },
        "labels": labels,
        "strict": strict_report,
        "relaxed": relaxed_report,
    }, indent=2), encoding="utf-8")
    print(f"\nresults written to {results_path}")


if __name__ == "__main__":
    main()
