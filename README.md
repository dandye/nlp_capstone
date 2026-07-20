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

```bash
python3 -m venv .venv     && .venv/bin/pip install -r requirements.txt
python3 -m venv .venv-ml  && .venv-ml/bin/pip install -r requirements-ml.txt

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

- https://huggingface.co/pzryathzsdhc/cti-ner-roberta-large
- https://huggingface.co/pzryathzsdhc/cti-ner-securebert
