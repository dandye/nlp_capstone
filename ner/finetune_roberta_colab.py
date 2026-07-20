"""
Standalone GPU/TPU-optimized RoBERTa token-classification trainer for the CTI
corpus, scored with the same document-level span harness as the local
finetune_roberta.py run (strict = exact (start, end, label) match). Numbers
from this script are directly comparable to the local MPS run's results.

This is a self-contained fork of ner/finetune_roberta.py + the parts of
ner/evaluate.py it needs, meant to run with no other repo files present
(see notebooks/ for the embedding pattern this mirrors). Keep the
BIO/windowing/scoring logic in sync with finetune_roberta.py by hand if either
changes — there is no shared import between them once embedded in a notebook.

GPU/TPU-specific changes from the local MPS version:
  - Mixed precision: bf16 autocast on CUDA (if supported) or TPU/XLA, else
    fp16 autocast + GradScaler on older CUDA GPUs. No autocast on CPU.
  - Larger default batch size (32 vs the local script's 16/8) — GPU/TPU
    memory is far less constrained than the M-series MPS runs this was
    tuned for originally.
  - TPU-only fixed-length padding (--fixed-pad, auto-enabled when the XLA
    device is selected): the local script's length-grouped batching still
    produces a different padded width per batch, which is fine on
    CUDA/MPS but forces XLA to retrace and recompile its graph for every
    new shape on TPU — in the worst case this makes TPU *slower* than GPU
    despite more raw FLOPs. Fixed-pad trades some wasted compute (every
    batch pads to the same MAX_WORDPIECES+2 width) for a single stable
    XLA graph. If you don't pass --fixed-pad explicitly the script still
    forces it on when device is "xla", since running length-grouped
    batches unmodified on TPU has not been validated here and is known to
    be pathological for XLA — treat the TPU path as less battle-tested
    than the CUDA path in general.

Usage — in-kernel from a notebook (the Colab notebooks paste these functions
into a cell and call run() directly, so nothing depends on a `python3` on
PATH or a `/content` working dir):

    run(
        model_name="roberta-large",
        data="gliner_train.jsonl",
        split="split_slugs.json",
        output_dir="models/roberta-cti-large",
        device="cuda",
        epochs=8,
        batch_size=32,
    )

There is also a thin CLI (`python3 finetune_roberta_colab.py --help`) that
just forwards to run(); the notebooks do not use it.
"""

from __future__ import annotations

import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

MAX_WORDPIECES = 510  # 512 minus <s> </s>
WINDOW_OVERLAP_WORDS = 50

# ── evaluation harness (embedded subset of ner/evaluate.py) ────────────────

Span = tuple[int, int, str]  # (start_tok, end_tok_inclusive, label)


def load_records(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def gold_document_spans(doc_records: list[dict]) -> set[Span]:
    spans: set[Span] = set()
    for rec in doc_records:
        base = rec["chunk_start"]
        for s, e, label in rec["ner"]:
            spans.add((base + s, base + e, label))
    return spans


def match_relaxed(gold: set[Span], pred: set[Span]) -> int:
    """Greedy 1:1 overlap matching within each label; returns match count."""
    matched = 0
    by_label_gold: dict[str, list[Span]] = defaultdict(list)
    by_label_pred: dict[str, list[Span]] = defaultdict(list)
    for g in gold:
        by_label_gold[g[2]].append(g)
    for p in pred:
        by_label_pred[p[2]].append(p)
    for label, gspans in by_label_gold.items():
        pspans = sorted(by_label_pred.get(label, []))
        used = [False] * len(pspans)
        for gs, ge, _ in sorted(gspans):
            for j, (ps, pe, _) in enumerate(pspans):
                if not used[j] and ps <= ge and pe >= gs:
                    used[j] = True
                    matched += 1
                    break
    return matched


class Scorer:
    def __init__(self) -> None:
        self.tp: dict[str, int] = defaultdict(int)
        self.fp: dict[str, int] = defaultdict(int)
        self.fn: dict[str, int] = defaultdict(int)

    def add_strict(self, gold: set[Span], pred: set[Span]) -> None:
        for g in gold:
            if g in pred:
                self.tp[g[2]] += 1
            else:
                self.fn[g[2]] += 1
        for p in pred:
            if p not in gold:
                self.fp[p[2]] += 1

    def add_relaxed(self, gold: set[Span], pred: set[Span]) -> None:
        labels = {s[2] for s in gold | pred}
        for label in labels:
            g = {s for s in gold if s[2] == label}
            p = {s for s in pred if s[2] == label}
            m = match_relaxed(g, p)
            self.tp[label] += m
            self.fn[label] += len(g) - m
            self.fp[label] += len(p) - m

    def report(self) -> dict:
        per_label = {}
        for label in sorted(set(self.tp) | set(self.fp) | set(self.fn)):
            tp, fp, fn = self.tp[label], self.fp[label], self.fn[label]
            p = tp / (tp + fp) if tp + fp else 0.0
            r = tp / (tp + fn) if tp + fn else 0.0
            f = 2 * p * r / (p + r) if p + r else 0.0
            per_label[label] = {
                "P": round(p, 4), "R": round(r, 4), "F1": round(f, 4),
                "support": tp + fn,
            }
        tp = sum(self.tp.values())
        fp = sum(self.fp.values())
        fn = sum(self.fn.values())
        micro_p = tp / (tp + fp) if tp + fp else 0.0
        micro_r = tp / (tp + fn) if tp + fn else 0.0
        micro_f = (
            2 * micro_p * micro_r / (micro_p + micro_r)
            if micro_p + micro_r else 0.0
        )
        f1s = [v["F1"] for v in per_label.values()]
        return {
            "per_label": per_label,
            "micro": {
                "P": round(micro_p, 4), "R": round(micro_r, 4),
                "F1": round(micro_f, 4),
            },
            "macro_F1": round(sum(f1s) / len(f1s), 4) if f1s else 0.0,
        }


def print_table(name: str, report: dict) -> None:
    print(f"\n{name}")
    print(f"  {'label':<30} {'P':>6} {'R':>6} {'F1':>6} {'support':>8}")
    for label, m in sorted(
        report["per_label"].items(), key=lambda x: -x[1]["support"]
    ):
        print(f"  {label:<30} {m['P']:>6.2f} {m['R']:>6.2f} "
              f"{m['F1']:>6.2f} {m['support']:>8}")
    mi = report["micro"]
    print(f"  {'MICRO':<30} {mi['P']:>6.2f} {mi['R']:>6.2f} {mi['F1']:>6.2f}")
    print(f"  {'MACRO F1':<30} {'':>6} {'':>6} {report['macro_F1']:>6.2f}")


# ── label space ───────────────────────────────────────────────────────────────

def build_tag_maps(labels: list[str]) -> tuple[dict[str, int], dict[int, str]]:
    tag_to_id = {"O": 0}
    for label in labels:
        tag_to_id[f"B-{label}"] = len(tag_to_id)
        tag_to_id[f"I-{label}"] = len(tag_to_id)
    return tag_to_id, {v: k for k, v in tag_to_id.items()}


def spans_to_bio(n_words: int, spans: list, tag_to_id: dict[str, int]) -> list[int]:
    tags = [0] * n_words
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
        if end == start:
            end = start + 1
        windows.append((start, end))
        if end >= n:
            break
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
    """Shuffled batches drawn from length-sorted buckets (CUDA/CPU only —
    see --fixed-pad for why TPU bypasses this and pads to a constant width
    instead)."""

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


def collate(batch: list[dict], pad_id: int, fixed_width: int | None = None) -> dict:
    width = fixed_width or max(len(b["input_ids"]) for b in batch)
    ids = torch.full((len(batch), width), pad_id, dtype=torch.long)
    mask = torch.zeros((len(batch), width), dtype=torch.long)
    labels = torch.full((len(batch), width), -100, dtype=torch.long)
    for i, b in enumerate(batch):
        n = min(len(b["input_ids"]), width)
        ids[i, :n] = torch.tensor(b["input_ids"][:n])
        mask[i, :n] = 1
        labels[i, :n] = torch.tensor(b["labels"][:n])
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


# ── device / precision setup ─────────────────────────────────────────────────

def setup_device(force: str | None):
    """Returns (device, kind, autocast_dtype). kind in {'cuda','xla','cpu'}.

    A forced device that isn't available is a HARD ERROR (fail fast + noisy)
    rather than a silent CPU/TPU fallback — a run that silently lands on the
    wrong accelerator wastes hours before anyone notices. The Colab notebook
    passes --device cuda, so a TPU or CPU runtime stops here immediately.
    """
    if force in ("cpu",):
        return torch.device("cpu"), "cpu", None
    if force in ("cuda", "gpu"):
        if not torch.cuda.is_available():
            raise SystemExit(
                "ERROR: --device cuda requested but no CUDA GPU is visible. "
                "This notebook/script is GPU-only. In Colab: Runtime -> "
                "Change runtime type -> GPU (T4/L4/A100). TPU and CPU "
                "runtimes are not supported."
            )
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        return torch.device("cuda"), "cuda", dtype
    if force in ("xla", "tpu"):
        raise SystemExit(
            "ERROR: TPU/XLA is not supported. This workload uses variable-"
            "length, length-grouped batches; XLA recompiles its graph per "
            "input shape, making TPU slower than a T4 GPU here despite more "
            "FLOPs. Use a GPU runtime (Runtime -> Change runtime type -> GPU)."
        )
    # force is None (auto): GPU only, else hard error.
    if torch.cuda.is_available():
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        return torch.device("cuda"), "cuda", dtype
    raise SystemExit(
        "ERROR: no CUDA GPU visible and this script is GPU-only. In Colab: "
        "Runtime -> Change runtime type -> GPU (T4/L4/A100)."
    )


# ── main ──────────────────────────────────────────────────────────────────────

def run(model_name: str = "roberta-large",
        output_dir: str = "models/roberta-cti-large",
        data: str = "gliner_train.jsonl",
        split: str = "split_slugs.json",
        epochs: int = 8, lr: float = 2e-5, batch_size: int = 32,
        grad_accum: int = 1, warmup_frac: float = 0.1, seed: int = 0,
        device: str | None = None, fixed_pad: bool = False,
        eval_only: str | None = None, results: str | None = None) -> None:
    """Train (or, with eval_only=<checkpoint>, just evaluate) a token
    classifier. Call this directly with plain keyword args — from a notebook
    or any Python — e.g.:

        run(model_name="roberta-large", data="gliner_train.jsonl",
            split="split_slugs.json", output_dir="models/roberta-cti-large",
            device="cuda")
    """
    from types import SimpleNamespace
    args = SimpleNamespace(
        model_name=model_name, output_dir=output_dir, data=data, split=split,
        epochs=epochs, lr=lr, batch_size=batch_size, grad_accum=grad_accum,
        warmup_frac=warmup_frac, seed=seed, device=device,
        fixed_pad=fixed_pad, eval_only=eval_only, results=results)

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    device, kind, autocast_dtype = setup_device(args.device)
    fixed_pad = args.fixed_pad or kind == "xla"
    print(f"device: {device} (kind={kind}, autocast={autocast_dtype}, "
          f"fixed_pad={fixed_pad})")
    if kind == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}, "
              f"{torch.cuda.get_device_properties(0).total_memory/1e9:.0f}GB")

    from transformers import (
        AutoModelForTokenClassification,
        AutoTokenizer,
        get_linear_schedule_with_warmup,
    )

    records = load_records(Path(args.data))
    split = json.loads(Path(args.split).read_text(encoding="utf-8"))
    labels = sorted({l for rec in records for _, _, l in rec["ner"]})
    tag_to_id, id_to_tag = build_tag_maps(labels)
    print(f"labels: {len(labels)} -> {len(tag_to_id)} BIO tags")

    model_src = args.eval_only or args.model_name
    tokenizer = AutoTokenizer.from_pretrained(model_src, add_prefix_space=True)
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

    collate_width = (MAX_WORDPIECES + 2) if fixed_pad else None
    scaler = None
    if kind == "cuda" and autocast_dtype == torch.float16:
        scaler = torch.cuda.amp.GradScaler()

    if not args.eval_only:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        train_chunks = [c for cs in by_subset["train"].values() for c in cs]
        train_ds = WindowDataset(train_chunks)
        lengths = [train_ds.piece_len(i) for i in range(len(train_ds))]
        sampler = LengthGroupedSampler(lengths, args.batch_size, seed=args.seed)
        loader = DataLoader(
            train_ds,
            batch_size=args.batch_size,
            sampler=sampler,
            drop_last=(kind == "xla"),  # XLA wants uniform batch count/shape
            collate_fn=lambda b: collate(b, tokenizer.pad_token_id, collate_width),
        )

        if kind == "xla":
            import torch_xla.distributed.parallel_loader as pl
            loader = pl.MpDeviceLoader(loader, device)

        steps_total = (len(loader) // args.grad_accum) * args.epochs
        optim = torch.optim.AdamW(model.parameters(), lr=args.lr,
                                  weight_decay=0.01)
        sched = get_linear_schedule_with_warmup(
            optim, int(steps_total * args.warmup_frac), steps_total
        )
        best_f1 = -1.0
        log_every = max(1, len(loader) // 5)
        for epoch in range(1, args.epochs + 1):
            model.train()
            t0, running = time.time(), 0.0
            for step, batch in enumerate(loader, 1):
                if kind != "xla":
                    batch = {k: v.to(device) for k, v in batch.items()}
                if autocast_dtype is not None and kind != "xla":
                    with torch.autocast(device_type=kind, dtype=autocast_dtype):
                        loss = model(**batch).loss / args.grad_accum
                elif kind == "xla":
                    with torch.autocast(device_type="xla", dtype=torch.bfloat16):
                        loss = model(**batch).loss / args.grad_accum
                else:
                    loss = model(**batch).loss / args.grad_accum

                if scaler is not None:
                    scaler.scale(loss).backward()
                else:
                    loss.backward()
                running += loss.item() * args.grad_accum

                if step % args.grad_accum == 0:
                    if scaler is not None:
                        scaler.unscale_(optim)
                        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                        scaler.step(optim)
                        scaler.update()
                    elif kind == "xla":
                        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                        import torch_xla.core.xla_model as xm
                        xm.optimizer_step(optim)
                    else:
                        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
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

    results_path = Path(args.results or f"{args.output_dir}/results.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps({
        "model": args.model_name,
        "checkpoint": checkpoint,
        "device_kind": kind,
        "subset": "test",
        "n_documents": len(by_subset["test"]),
        "harness": "ner.evaluate (document-level, strict span+label) "
                   "— embedded copy, kept in sync by hand",
        "windowing": {
            "max_wordpieces": MAX_WORDPIECES,
            "overlap_words": WINDOW_OVERLAP_WORDS,
            "fixed_pad": fixed_pad,
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


def main() -> None:
    """CLI wrapper around run(). Not used by the notebooks — they call run()
    directly with keyword args."""
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--model-name", default="roberta-large")
    ap.add_argument("--output-dir", default="models/roberta-cti-large")
    ap.add_argument("--data", default="gliner_train.jsonl")
    ap.add_argument("--split", default="split_slugs.json")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--grad-accum", type=int, default=1)
    ap.add_argument("--warmup-frac", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", choices=["cuda", "xla", "tpu", "cpu"], default=None)
    ap.add_argument("--fixed-pad", action="store_true")
    ap.add_argument("--eval-only", metavar="CHECKPOINT")
    ap.add_argument("--results", default=None)
    a = ap.parse_args()
    run(model_name=a.model_name, output_dir=a.output_dir, data=a.data,
        split=a.split, epochs=a.epochs, lr=a.lr, batch_size=a.batch_size,
        grad_accum=a.grad_accum, warmup_frac=a.warmup_frac, seed=a.seed,
        device=a.device, fixed_pad=a.fixed_pad, eval_only=a.eval_only,
        results=a.results)


if __name__ == "__main__":
    main()
