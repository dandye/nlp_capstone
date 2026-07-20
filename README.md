# nlp_capstone — CTI NER with LLM-primary gold annotation

Named-entity recognition for Cyber Threat Intelligence (CTI), trained and
evaluated on CISA advisories. Gold entities are proposed directly by a
frontier LLM (Claude Sonnet) reading the clean advisory text, then curated
by a human. RoBERTa, SecureBERT, and GLiNER are trained and scored against
that gold, with a frontier-LLM (Gemini) baseline for comparison.

This is a clean extraction of the LLM-gold approach from the older
`../scrape_cisa` project, which also carried an abandoned
dictionary-ensemble pipeline (MITRE ATT&CK + STIX + regex ∩ zero-shot
GLiNER). A 300-span blind human audit showed that ensemble's gold was too
noisy to evaluate against — ~50% of its "false positives" were real
entities and ~10% of its gold was footer/boilerplate noise — which is what
motivated moving to LLM+human gold. See `paper/capstone/`.

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
scraper/    the CISA scraper (unchanged), produces data/alerts/{slug}/
data/       gold_v2 (val), gold_v2_train (train), alerts (clean.md + meta.json)
models/     checkpoints (gitignored; published to HF Hub)
paper/      capstone/ — the ACL-format deliverable
notebooks/  Colab training notebooks (RoBERTa-large, SecureBERT, GLiNER)
docs/       reference docs
```

## Published models

Fine-tuned on the earlier (noisy) labels; numbers will be regenerated on the
clean gold:

- https://huggingface.co/pzryathzsdhc/cti-ner-roberta-large
- https://huggingface.co/pzryathzsdhc/cti-ner-securebert
