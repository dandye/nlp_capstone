# CLAUDE.md

This file guides Claude Code when working in the `nlp_capstone` repository.

## Project Overview

CTI (Cyber Threat Intelligence) named-entity recognition on CISA
advisories, with **LLM-primary gold annotation**. A frontier LLM (Claude
Sonnet) reads the clean advisory text and proposes gold entities directly;
a human reviews and curates; models (RoBERTa, SecureBERT, GLiNER) are
trained and evaluated against that gold.

Gold quality is the whole point: a human-audited comparison found that
dictionary-based labeling was too noisy to evaluate against, which is why
gold now originates from an LLM and is human-curated. See `paper/capstone/`
for the analysis.

## The 16 entity labels

affected software product, attack technique id, attack technique name,
cve identifier, cwe identifier, email address, file hash, file name,
file path, hacking tool, ip address, malware family, tactic,
threat actor group, tlp classification, yara rule name.

Plus `UNK` in the curation webapp only — for real entities that fit no
current label; UNK spans are clustered to propose new label types. `UNK`
is never a training/eval label.

## Environments

Two Python environments, deliberately self-contained (no cross-project
venv paths):

- **`.venv`** (project default, CPU): the scraper, text normalization,
  gold conversion, webapps, span validators, census. `requirements.txt`.
- **`.venv-ml`**: `torch`, `transformers`, `gliner`, `docling`,
  `anthropic`. Everything that trains, runs a model, converts PDFs, or
  calls the LLM. `requirements-ml.txt`.

```bash
python3 -m venv .venv     && .venv/bin/pip install -r requirements.txt
python3 -m venv .venv-ml  && .venv-ml/bin/pip install -r requirements-ml.txt
```

Run ML modules with the ML venv explicitly, e.g.
`PYTHONPATH=. .venv-ml/bin/python3 -m ner.finetune_roberta ...`.
There is NO dependency on any external venv — any cross-project or
absolute venv path is a refactor leftover and should be removed.

Python 3.9 in the CPU venv: `from __future__ import annotations`, no
runtime `X | Y` unions.

## Two packages

- **`scraper/`** — the CISA scraper (cli, alerts, fetcher, listing,
  detail, downloader, pdf_extract, db, models). Produces
  `data/alerts/{slug}/{base}.pdf` + `meta.json`.
- **`ner/`** — everything for the LLM-gold NER pipeline (below). The two
  packages are decoupled: `ner/` never imports `scraper/` and vice versa.

## Pipeline

```
CISA PDF  ──scraper──▶  data/alerts/{slug}/{base}.pdf + meta.json
   │
   └─docling (ML venv)─▶  {base}.md  ──emit_versions──▶  {base}.clean.md
                                          (markup-strip + normalize:
                                           dedupe page furniture, drop
                                           pagination, rejoin split hashes)
   clean.md
   │
   ├─ner.llm_gold (Claude Sonnet, ML venv)──▶ data/gold_v2[_train]/{slug}.json
   │      exhaustive extraction; verbatim + span-validator + label gates;
   │      dropped proposals logged to {slug}.dropped.json
   │
   ├─ner.hitl_ner (webapp)──▶ data/gold_v2/proposals/{slug}.json
   │      human curation: propose new entities, UNK, reject FPs
   │
   ├─ner.gold_to_training──▶ data/gold_v2/*.jsonl  (token-span records)
   │
   └─ner.finetune_roberta / finetune_gliner (ML venv)──▶ models/...
          scored by ner.evaluate (strict + relaxed span F1)
```

`data/alerts/{slug}/{base}.clean.md` is the canonical model-facing text and
is treated as a **committed source artifact** (deterministic docling +
normalize output). The raw `{base}.md` and PDF are not tracked (see
`.gitignore`); regenerate them by re-running the scraper if needed.

## Common commands

```bash
# Generate clean.md for every advisory (idempotent; needs raw .md present)
PYTHONPATH=. .venv-ml/bin/python3 -m ner.emit_versions --all

# LLM-annotate gold (resumable; skips completed slugs)
PYTHONPATH=. .venv-ml/bin/python3 -m ner.llm_gold \
    --slugs aa23-284a,aa25-163a --model claude-sonnet-5
#   train docs -> --out-dir data/gold_v2_train

# Human curation webapp (propose entities, UNK, reject FPs)
PYTHONPATH=. python3 -m ner.hitl_ner            # http://localhost:8766

# Read-only gold viewer
PYTHONPATH=. python3 -m ner.visualize_gold      # -> data/gold_review.html

# Defect census (acceptance test for label quality)
PYTHONPATH=. python3 -m ner.label_census

# Convert gold -> training/eval JSONL (default = every gold file in gold-dir)
PYTHONPATH=. python3 -m ner.gold_to_training \
    --gold-dir data/gold_v2 --output data/gold_v2/eval.jsonl

# Train a token classifier (ML venv)
PYTHONPATH=. .venv-ml/bin/python3 -m ner.finetune_roberta \
    --model-name roberta-base --output-dir models/roberta-cti-base
#   eval an existing checkpoint against gold:
#   ... --eval-only models/roberta-cti-base/best --data data/gold_v2/eval.jsonl \
#       --split data/gold_v2/split_full.json
```

## Data layout

```
data/
├── alerts/{slug}/          meta.json + {base}.clean.md  (model-facing input)
├── gold_v2/                val/eval gold: {slug}.json (+ {slug}.dropped.json)
│   ├── proposals/          human curation output
│   ├── split.json          train/val/test partition (small set)
│   ├── split_full.json     train/val/test partition (full set)
│   ├── split_full_gliner.json  same split + 66 train slugs filled in,
│   │                       for finetune_gliner.py --split-in
│   └── results/            regenerable scoring/training artifacts —
│                           mix of old-label and current LLM-gold results;
│                           filename prefix disambiguates (see below)
├── gold_v2_train/          train-doc gold: {slug}.json (66 docs)
├── papers/                 reference-paper library backing paper/survey.md
│                           and the capstone bibliography: {arxiv-id}-{slug}.md
│                           (docling-converted, tracked) + matching .pdf
│                           (gitignored, 85MB, copied from scrape_cisa)
└── evals/                  external benchmark (MalwareTextDB-1.0) for
                            cross-domain eval; not yet wired into any module
```

`data/gold_v2/results/` filename convention: `trained-*.json` = model retrained
on current LLM gold and scored on it (the numbers the paper reports);
`rescored-*.json` / `full-rescored-*.json` = an *old*, dictionary-silver-trained
checkpoint merely rescored against current gold (RQ1's circularity
demonstration, not a fair architecture comparison on its own).

A gold file is a JSON **list** of `{text, label}` entities; config/result
files in the same dir are JSON objects. `gold_to_training` distinguishes by
shape (see `_is_gold_file`) — never by slug pattern, because real gold
includes non-standard slugs (`aa23-108`, title-slugged reports).

## Key modules (`ner/`)

- `llm_gold.py` — Claude annotation; chunked, resumable, JSON-salvage for
  truncated/control-char responses; verbatim + validator + label gates.
- `hitl_ner.py` — human curation webapp (propose / UNK / reject-FP), writes
  `{text, label[, reject]}`, same schema as gold so accepted edits merge.
- `span_validators.py` — per-label format grammars (hash length, IP/email
  incl. defanged, CVE/CWE/T-code/TLP); a generation gate, not a flag.
- `text_normalize.py` — page-furniture dedupe, pagination drop, split-hash
  rejoin, code-region detection. Applied when building clean.md.
- `gold_to_training.py` — gold JSON -> gliner-format token-span JSONL;
  fused-token span matching (em-dashes/quotes/paths).
- `annotation_text.py` — shared text utils (tokenize, find_token_span,
  split_into_chunks, strip_annotations, parse_annotations). The
  strip/parse pair is depth-aware (handles nested annotations).
- `evaluate.py` — `Scorer`; document-level span reconstruction via
  chunk_start; strict (exact) + relaxed (overlap) P/R/F1.
- `finetune_roberta.py` / `finetune_gliner.py` — training; wordpiece-budget
  sliding windows so long/hash-heavy chunks aren't truncated;
  length-grouped batching. `--eval-only` takes label space from the
  checkpoint config, not the eval data. `finetune_roberta_colab.py` is a
  self-contained Colab fork.
- `frontier_infer.py` / `frontier_extract.py` / `frontier_score.py` —
  frontier-LLM baseline (Gemini/Claude/Ollama) vs the fine-tuned fleet:
  infer entities -> extract spans -> P/R/F1. `frontier_debug.py` traces one
  advisory through the three stages.
- `label_census.py` — repeatable defect census / acceptance test.
- `emit_versions.py` — writes `{base}.clean.md` (strip + normalize).
- `audit_webapp.py` / `score_audit.py` — blind human audit tooling that
  produced the finding motivating this whole approach.

## Conventions

- **Slug** = CISA advisory id, lowercased: `{type}{YY}-{NNN}{letter}`
  (`aa` = Cybersecurity Advisory, `ar` = Analysis Report/MAR). Primary key
  everywhere. See `docs/reference/naming-conventions.md`.
- **Derived files** (`{base}.clean.md`, `.gemini.md`, `.gliner.md`) live
  beside the original in `data/alerts/{slug}/`. Every `glob("*.md")` MUST
  exclude them (glob order is unspecified). `clean.md` is the canonical
  model-facing text and is treated as a committed source artifact.
- **Gold schema** is `{"text": str, "label": str}` (plus optional
  `"reject": true` in proposals). Shared across LLM gold, human proposals,
  and merges — never introduce a divergent shape.

## Critical invariants (learned the hard way)

1. **Never send annotation markup to a model.** Models read
   `{base}.clean.md` (markup stripped). Leaking gold markup into model
   input contaminates the eval. `strip_annotations` is depth-aware — a
   single-pass regex silently corrupted ~50% of the corpus before this was
   caught.
2. **Structured-type gold must pass its validator at generation time**
   (hash length, CVE/CWE/T-code/IP/email grammar, defanged forms ok).
3. **Eval label space comes from the checkpoint**, not the eval file — an
   eval subset exercising fewer labels otherwise shifts every tag id.
4. **Evaluation must use human-verified gold.** Both training labels and
   eval candidates originate from Sonnet, so the human curation pass over
   val/test is what makes the eval defensible; state that provenance in
   the paper.

## Testing & validation

There is **no unit-test suite** (no `pytest`, no `tests/`). Quality is
validated empirically, not by asserting on functions:

- `ner.label_census` — repeatable **defect census / acceptance test** for
  gold quality. Run it after any gold or pipeline change.
- `ner.evaluate` (`Scorer`) — strict + relaxed span P/R/F1 for model runs.

Don't go looking for a test runner; those two modules are the checks.

## Training notebooks & published models

- `notebooks/` — self-contained Colab notebooks that mirror the local
  trainers for GPU runs: `RoBERTa_Large_CTI_Colab.ipynb`,
  `SecureBERT_CTI_Colab.ipynb`, `gliner_cti_colab.ipynb`. The paired
  `ner/finetune_roberta_colab.py` is the script form.
- Checkpoints are gitignored (`models/`) and published to HF Hub;
  retraining repopulates them. All three published models are trained on
  the **clean LLM gold** (re-pushed 2026-07-24; each model card carries its
  measured scores): `huggingface.co/pzryathzsdhc/cti-ner-securebert`
  (strict micro F1 0.71), `.../cti-ner-roberta-large` (0.63; the paper's
  committed 0.648 is an earlier identical-recipe run — seed variance), and
  `.../cti-ner-gliner` (0.560). The exact training corpus is committed as
  `data/gliner_train.jsonl` + `data/split_slugs.json` (same bytes as the
  notebooks' embedded copy).

## Deliverable

`paper/capstone/` — the ACL-format capstone paper. `paper/survey.md` (41-paper
literature synthesis) and `paper/notes/` (bibliography, reading log,
discovery log, taxonomy) back it; `data/papers/` holds the underlying
reference PDFs + docling `.md` conversions.

All four architectures (RoBERTa-base, RoBERTa-large, SecureBERT, GLiNER)
are now trained and scored on the current LLM-gold pipeline — see
`data/gold_v2/results/trained-*.json`, no numbers in the paper are stale.

Headline finding, revised: SecureBERT (0.71 strict F1) is the best
performer; GLiNER (0.56), once fairly retrained on the identical gold, is
the *weakest* of the four — the opposite of this project's earlier working
hypothesis. That earlier hypothesis (span-matching retains zero-shot
generalization better than a softmax head) came from comparing an
*un*retrained GLiNER checkpoint against retrained token classifiers
(`data/gold_v2/results/RESCORE_FINDINGS.md`) — a training-data confound,
not an architecture effect. Do not cite the old hypothesis as the paper's
finding; it's now the paper's RQ1/RQ4 cautionary example instead.

No open items remain. The frontier-LLM comparison is done
(`data/frontier_results/`, Gemini 0.795 strict F1 vs SecureBERT 0.712).
The blind gold audit turned out to be already human-judged (pre-repo,
scrape_cisa era — the principal's own 300 judgments arrived in the initial
import inside `gold_audit.csv`); it was scored via `ner.score_audit` on
2026-07-21: 50.2% of silver-flagged false positives were correct entities
(59% finetuned / 43% zeroshot), the quantitative basis for RQ1. The paper
frames the dictionary-silver pipeline as a *studied baseline*, not project
history, and states plainly that the current LLM gold has no blind audit
(val/test curation only). `gold_audit.fable5.*` is a separate LLM triage
(82% agreement with the human judgments) — never cite it as the human
audit. The paper is ACM format (acmart sigconf,nonacm) with an Artifact
Availability section linking the repo and HF checkpoints.
