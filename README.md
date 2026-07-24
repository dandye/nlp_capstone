# nlp_capstone — CTI NER with LLM-primary gold annotation

Named-entity recognition for Cyber Threat Intelligence (CTI), trained and
evaluated on CISA advisories. Gold entities are proposed directly by a
frontier LLM (Claude Sonnet) reading the clean advisory text, then curated
by a human. RoBERTa, SecureBERT, and GLiNER are trained and scored against
that gold, with a frontier-LLM (Gemini) baseline for comparison.

The headline finding: against honest LLM+human gold, GLiNER's span-matching
architecture retains zero-shot generalization to entity classes the training
labels never covered, while a softmax head predicts only what it saw. See
`paper/capstone/` for the full write-up.

## Quick start

**Python version:** use Python 3.11–3.14 (the reference environment is
3.14). On macOS, do **not** use the system `python3` — the Command Line
Tools interpreter is Python 3.9 with pip 21, which resolves ancient
package versions and then fails to compile `pyobjc-core` from source
under current clang (`-Wdefault-const-init-var-unsafe` errors). Use a
`uv`-, python.org-, or Homebrew-installed interpreter, and upgrade pip
inside the venv before installing so dependencies land as prebuilt
wheels:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements.txt

python3.12 -m venv .venv-ml
.venv-ml/bin/pip install -U pip
.venv-ml/bin/pip install -r requirements-ml.txt

# defect census over the current gold (CPU)
PYTHONPATH=. .venv/bin/python3 -m ner.label_census

# convert gold -> eval JSONL (CPU)
PYTHONPATH=. .venv/bin/python3 -m ner.gold_to_training \
    --gold-dir data/gold_v2 --output data/gold_v2/eval.jsonl

# train a token classifier (ML venv)
PYTHONPATH=. .venv-ml/bin/python3 -m ner.finetune_roberta \
    --model-name roberta-base --output-dir models/roberta-cti-base
```

See `CLAUDE.md` for the full pipeline, module map, data layout, and the
critical invariants.

## Layout

```
ner/        LLM-gold NER pipeline (annotation, curation, training, eval)
scraper/    CISA advisory scraper, produces data/alerts/{slug}/
data/       gold_v2 (val), gold_v2_train (train), alerts (clean.md + meta.json)
models/     checkpoints (gitignored; published to HF Hub)
paper/      capstone/ — the ACL-format deliverable
notebooks/  Colab training notebooks (RoBERTa-large, SecureBERT, GLiNER)
docs/       reference docs
```

## Published models

All trained on the clean LLM gold (Claude Sonnet 5-proposed, human-curated
eval); each model card carries its measured scores:

- https://huggingface.co/pzryathzsdhc/cti-ner-securebert (strict micro F1 0.71)
- https://huggingface.co/pzryathzsdhc/cti-ner-roberta-large (0.63)
- https://huggingface.co/pzryathzsdhc/cti-ner-gliner (0.560)
