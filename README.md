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
`uv`-, python.org-, Homebrew-, or pyenv-installed interpreter, and
upgrade pip inside the venv before installing so dependencies land as
prebuilt wheels.

If you have no modern Python on the machine, pyenv is the least
invasive way to get one on macOS (it installs per-user, touches no
system files, and pins the version per-directory):

```bash
brew install pyenv                       # https://github.com/pyenv/pyenv
echo 'eval "$(pyenv init -)"' >> ~/.zshrc && exec zsh
pyenv install 3.12                       # build a supported interpreter
pyenv local 3.12                         # pin it for this repo (writes
                                         # .python-version); `python3`
                                         # now resolves to 3.12 here
python3 --version                        # sanity check: 3.12.x
```

`pyenv local` only affects commands run inside this directory; outside
the repo your shell keeps whatever Python it had. With the pin in
place, plain `python3` below is safe — otherwise spell out
`python3.12`:

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

## Layout

```
ner/        LLM-gold NER pipeline (annotation, curation, training, eval)
scraper/    CISA advisory scraper, produces data/alerts/{slug}/
data/       gold_v2 (val), gold_v2_train (train), alerts (clean.md + meta.json)
models/     checkpoints (gitignored; published to HF Hub)
paper/      capstone/ — the ACL-format deliverable
notebooks/  Colab training notebooks + HF demo (see "Notebooks" below)
docs/       reference docs
```

## Notebooks

Four self-contained notebooks under `notebooks/` reproduce the training
runs and demonstrate the published checkpoints. None of them needs this
repo's venvs — each installs its own pinned dependencies in the first
cell.

- **`RoBERTa_Large_CTI_Colab.ipynb`** — trains `roberta-large` on the
  LLM-gold corpus and scores it with the paper's document-level span
  harness (strict + relaxed F1). Fully standalone: the training corpus
  (`gliner_train.jsonl` + `split_slugs.json`) is embedded in the
  notebook as a base64 tarball, `transformers` is pinned to the
  training environment (4.46.3), and seeds are fixed. Needs a **GPU
  runtime** (T4/L4/A100; hard-stops otherwise) and includes an OOM
  fallback cell for smaller GPUs. Exports `results.json` and a
  checkpoint zip.
- **`SecureBERT_CTI_Colab.ipynb`** — identical harness, trains
  `ehsanaghaei/SecureBERT` instead. Same embedded corpus, same pins,
  same GPU requirement. This reproduces the paper's best model
  (strict micro F1 0.71).
- **`gliner_cti_colab.ipynb`** — fine-tunes `urchade/gliner_medium-v2.1`
  (pinned `gliner==0.2.26`, seed 42) and reports the zero-shot baseline
  next to the fine-tuned scores. Not fully embedded: when prompted,
  upload `data/gliner_train.jsonl` and `data/split_slugs.json` from
  this repo (using the committed split keeps Colab results comparable
  to local runs — do not resplit). GPU strongly recommended; also runs
  on Colab TPU.
- **`hf_models_demo.ipynb`** — downloads the published checkpoints from
  the HF Hub and runs windowed inference (the same 510-wordpiece
  sliding-window scheme as the eval harness) on real CISA advisory
  sentences, with a color-highlighted rendering per model. CPU is
  fine; no data files needed. This is a qualitative demo — it shows
  the models working but does not compute F1.

Expect training reruns to land near, not exactly on, the committed
numbers: training is seeded but GPU kernels are not bit-deterministic,
and an identical-recipe rerun has shifted strict micro F1 by ~0.02
(the paper's 0.648 vs. a later 0.63 for RoBERTa-large).

## Published models

All trained on the clean LLM gold (Claude Sonnet 5-proposed, human-curated
eval); each model card carries its measured scores:

- https://huggingface.co/pzryathzsdhc/cti-ner-securebert (strict micro F1 0.71)
- https://huggingface.co/pzryathzsdhc/cti-ner-roberta-large (0.63)
- https://huggingface.co/pzryathzsdhc/cti-ner-gliner (0.560)
