"""
Fine-tune GLiNER on the CTI training dataset produced by gold_to_training.py.

Uses GLiNER's built-in trainer. Requires the ML venv (torch + gliner):
    .venv-ml/bin/python3

Quick-start:
    cd nlp_capstone
    PYTHONPATH=. .venv-ml/bin/python3 -m ner.finetune_gliner \\
        --train data/gliner_train.jsonl \\
        --output models/gliner-cti-v1

Strategy:
  - Base model: urchade/gliner_medium-v2.1 (already downloaded)
  - 80/10/10 train/val/test split at the DOCUMENT level (by advisory slug,
    seeded) — chunk-level splits leak overlap regions across train/test.
    The split manifest is written to data/split_slugs.json so evaluate.py
    scores every checkpoint against the same held-out advisories.
  - 5 epochs, LR 5e-5, batch 8, gradient accumulation 4 (effective batch 32)
  - Best checkpoint selected by val loss (the GLiNER Trainer computes no
    eval F1). Span-level P/R/F1 lives in ner/evaluate.py.
"""

import argparse
import json
import random
import sys
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def split_by_slug(
    records: list[dict],
    val_frac: float = 0.1,
    test_frac: float = 0.1,
    seed: int = 42,
) -> tuple[list[dict], list[dict], list[dict], dict[str, list[str]]]:
    """Document-level split: all chunks of one advisory stay together."""
    slugs = sorted({rec["slug"] for rec in records})
    rng = random.Random(seed)
    rng.shuffle(slugs)
    n = len(slugs)
    n_test = max(1, int(n * test_frac))
    n_val  = max(1, int(n * val_frac))
    split = {
        "test":  sorted(slugs[:n_test]),
        "val":   sorted(slugs[n_test: n_test + n_val]),
        "train": sorted(slugs[n_test + n_val:]),
    }
    member = {s: name for name, ss in split.items() for s in ss}
    buckets: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for rec in records:
        buckets[member[rec["slug"]]].append(rec)
    return buckets["train"], buckets["val"], buckets["test"], split


def to_trainer_format(records: list[dict]) -> list[dict]:
    """GLiNER's collator expects only tokenized_text + ner."""
    return [
        {"tokenized_text": r["tokenized_text"], "ner": r["ner"]}
        for r in records
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fine-tune GLiNER on CTI training data."
    )
    parser.add_argument("--train",    default="data/gliner_train.jsonl",
                        help="Training JSONL from gold_to_training.py")
    parser.add_argument("--output",   default="models/gliner-cti-v1")
    parser.add_argument("--base",     default="urchade/gliner_medium-v2.1")
    parser.add_argument("--epochs",   type=int,   default=5)
    parser.add_argument("--lr",       type=float, default=5e-5)
    parser.add_argument("--batch",    type=int,   default=8)
    parser.add_argument("--grad-acc", type=int,   default=4,
                        help="Gradient accumulation steps (effective batch = batch × grad_acc)")
    parser.add_argument("--seed",     type=int,   default=42)
    parser.add_argument("--cpu",      action="store_true",
                        help="Force CPU training. MPS leaks memory on DeBERTa's "
                             "dynamic shapes (MPSGraph kernel cache) and OOMs "
                             "mid-epoch; CPU is slower but reliable.")
    parser.add_argument("--split-out", default="data/split_slugs.json",
                        help="Where to write the document-level split manifest")
    parser.add_argument("--split-in", default=None,
                        help="Reuse an existing {train,val,test} slug manifest "
                             "instead of computing a fresh random split — use "
                             "this to pin val/test to the same documents other "
                             "models were scored on, so results are comparable.")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Print dataset stats and exit without training")
    args = parser.parse_args()

    train_path = Path(args.train)
    out_dir    = Path(args.output)

    if not train_path.exists():
        print(f"Training file not found: {train_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {train_path}…")
    records = load_jsonl(train_path)

    if args.split_in:
        split = json.loads(Path(args.split_in).read_text(encoding="utf-8"))
        member = {s: name for name, ss in split.items() for s in ss}
        buckets: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
        unmatched = set()
        for rec in records:
            name = member.get(rec["slug"])
            if name is None:
                unmatched.add(rec["slug"])
                continue
            buckets[name].append(rec)
        if unmatched:
            print(f"WARNING: {len(unmatched)} slugs in {train_path} not present "
                  f"in {args.split_in}, excluded from training: "
                  f"{sorted(unmatched)[:5]}{'...' if len(unmatched) > 5 else ''}",
                  file=sys.stderr)
        train, val, test = buckets["train"], buckets["val"], buckets["test"]
        print(f"Split (reused from {args.split_in}): "
              f"{len(split['train'])} train / {len(split['val'])} val / "
              f"{len(split['test'])} test documents "
              f"({len(train)}/{len(val)}/{len(test)} chunks)")
    else:
        train, val, test, split = split_by_slug(records, seed=args.seed)
        print(f"Split (by advisory): "
              f"{len(split['train'])} train / {len(split['val'])} val / "
              f"{len(split['test'])} test documents "
              f"({len(train)}/{len(val)}/{len(test)} chunks)")

    split_path = Path(args.split_out)
    split_path.parent.mkdir(parents=True, exist_ok=True)
    split_path.write_text(json.dumps(split, indent=2), encoding="utf-8")
    print(f"Split manifest → {split_path}")

    # Label distribution in train set
    label_counts: dict[str, int] = {}
    for rec in train:
        for _, _, label in rec["ner"]:
            label_counts[label] = label_counts.get(label, 0) + 1
    print("\nTrain label distribution:")
    for label, n in sorted(label_counts.items(), key=lambda x: -x[1]):
        print(f"  {label:<35} {n:5d}")

    if args.dry_run:
        return

    # ── GLiNER fine-tuning ────────────────────────────────────────────────
    import torch
    from transformers import TrainerCallback

    from gliner import GLiNER
    from gliner.data_processing.collator import SpanDataCollator
    from gliner.training import Trainer, TrainingArguments

    class MPSCacheCallback(TrainerCallback):
        """MPS fragments across steps and eventually OOMs mid-epoch;
        flushing the cache each step keeps allocations flat."""

        def on_step_end(self, args, state, control, **kwargs):
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()

    print(f"\nLoading base model: {args.base}")
    model = GLiNER.from_pretrained(args.base)

    out_dir.mkdir(parents=True, exist_ok=True)

    collator = SpanDataCollator(
        model.config,
        data_processor=model.data_processor,
        prepare_labels=True,
    )

    training_args = TrainingArguments(
        output_dir=str(out_dir),
        learning_rate=args.lr,
        weight_decay=0.01,
        others_lr=1e-5,
        others_weight_decay=0.01,
        lr_scheduler_type="linear",
        warmup_ratio=0.1,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch,
        gradient_accumulation_steps=args.grad_acc,
        num_train_epochs=args.epochs,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        save_total_limit=2,
        logging_steps=50,
        seed=args.seed,
        fp16=False,   # MPS/CPU-safe; enable if running on CUDA
        dataloader_num_workers=0,
        report_to="none",
        remove_unused_columns=False,
        use_cpu=args.cpu,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=to_trainer_format(train),
        eval_dataset=to_trainer_format(val),
        data_collator=collator,
        callbacks=[MPSCacheCallback()],
    )

    print(f"\nFine-tuning for {args.epochs} epochs "
          f"(effective batch {args.batch * args.grad_acc})…")
    trainer.train()

    print(f"\nSaving best checkpoint → {out_dir}")
    model.save_pretrained(str(out_dir))

    print(
        "\nNext: span-level evaluation on the held-out test documents:\n"
        f"  PYTHONPATH=. .venv-ml/bin/python3 -m ner.evaluate "
        f"--model {out_dir} --split {args.split_out} --subset test"
    )


if __name__ == "__main__":
    main()
