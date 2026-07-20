# Naming Conventions

Canonical reference for how documents, files, and derived artifacts are
named across the pipeline. Two layers matter: the **slug** (the key for an
advisory everywhere) and the **files inside** each advisory bundle.

## The slug

Every advisory is keyed by its **slug** — CISA's own advisory identifier,
lowercased. It is the primary key throughout: the `data/alerts/{slug}/`
directory name, the SQLite `advisories.slug` column, the `slug` field in
every training/eval record, split manifests, gold filenames, and model
results all key on it.

### Structure

Format: `{type}{YY}-{NNN}{letter}` — for example `aa23-352a`:

| Part | Value | Meaning |
|------|-------|---------|
| `aa` | type prefix | advisory type (see table below) |
| `23` | year | 2023 |
| `352` | sequence | 352nd of that type/year |
| `a` | revision | first release (`b`, `c`… for updates) |

### Type prefixes

The full scrape (`data/advisories.db`, ~5,000 rows) contains **many**
prefixes (`ci`, `mi`, `ap`, `ad`, `go`, `or`, …) covering CISA's whole
`/news-events/` output. The **annotated ML corpus** (`data/alerts/`, the
subset that feeds NER training) is deliberately just two advisory types,
scraped via `scraper/alerts.py --type`:

| Prefix | CISA advisory type | `--type` id | In `data/alerts/` |
|--------|--------------------|-------------|-------------------|
| `aa`   | Cybersecurity Advisory / joint Alert | 93 | 172 |
| `ar`   | Analysis Report (MAR — Malware Analysis Report) | 65 | 132 |

`aa` advisories are prose threat write-ups (TTPs, IOCs, attribution);
`ar`/MAR documents are malware dissections (hashes, YARA rules, static
analysis). This is why the two read so differently and why per-label
entity distributions differ between them.

### Non-standard slugs (10 docs)

A handful of CISA publications aren't advisories and carry descriptive
slugs instead of the ID pattern:

```
barriers-secure-ot-communication-why-johnny-cant-authenticate
cisa-adds-{one,two,three,four,seven}-known-exploited-vulnerabilities-catalog
cisa-publishes-infographic-layering-network-security-through-segmentation
preparing-critical-infrastructure-post-quantum-cryptography
supply-chain-compromises-impact-nx-console-and-github-repositories
```

Most have only a `meta.json` (no PDF → no annotation) and are skipped by
the pipeline. A few (e.g. `barriers-secure-ot-…`) do have a PDF and get a
`.clean.md`, but they are edge cases — not part of the 82-advisory
annotated set.

## Files inside `data/alerts/{slug}/`

Document files share a `{base}` stem that **docling derives from the source
PDF filename** — so it is longer and messier than the slug (e.g.
`aa23-352a-stopransomware-play-ransomware_2_revised`). Do not assume
`{base} == {slug}`; find the original with a glob that excludes derived
suffixes (below).

| File | Content | Producer |
|------|---------|----------|
| `{base}.pdf` | Original advisory PDF | `scraper/alerts.py` |
| `{base}.md` | docling conversion **with** inline annotation markup | docling + `annotate_iocs.py` |
| `{base}.clean.md` | **Canonical model-facing text** — annotation markup stripped, then normalized (page furniture deduped, pagination dropped, split hashes rejoined) | `emit_versions.py --all` |
| `{base}.gemini.md` | Gemini predictions rendered as markup | `emit_versions.py --entities …` |
| `{base}.gliner.md` | Fine-tuned GLiNER predictions rendered as markup | `emit_gliner_versions.py` |
| `*stix*.json` / `*STIX*.json` | STIX 2.1 bundle (abandoned as a gold source 2026-07-19) | scraped |
| `meta.json` | Scraped metadata: title, advisory_type, alert_code, release_date, CVEs | `scraper/alerts.py` |

### The derived-suffix rule (load-bearing)

`.clean.md`, `.gemini.md`, and `.gliner.md` are **derived** files that live
alongside the original in the same directory. Every `glob("*.md")` in the
pipeline **must** exclude them, or a derived file can be mistaken for the
original (non-deterministically, since glob order is unspecified). The
canonical exclusion:

```python
derived = (".clean.md", ".gemini.md", ".gliner.md")
originals = [f for f in slug_dir.glob("*.md") if not f.name.endswith(derived)]
```

`frontier_llm_utils.is_derived_md()` and the globs in
`create_training_data.py`, `ner_annotate.py`, and `emit_versions.py` all
enforce this. `load_clean_text(slug, …)` reads the pre-generated
`{base}.clean.md` directly rather than re-deriving it — see
[the annotation pipeline docs](../pipeline/annotation.md).

## Gold-label outputs

### Weak-supervision training data (original pipeline)

| Path | Content |
|------|---------|
| `data/gliner_train.jsonl` | Token-span records, all splits, one line per chunk: `{slug, chunk_start, tokenized_text[], ner[[start,end,label]…]}` |
| `data/split_slugs.json` | `{train:[…], val:[…], test:[…]}` — document-level split manifest, keyed by slug |

### LLM gold (`data/gold_v2/`, current direction)

Introduced 2026-07-19 when the MITRE/STIX dictionary was abandoned in favor
of LLM-primary annotation. Keyed by slug, split by purpose:

| Path | Content |
|------|---------|
| `data/gold_v2/{slug}.json` | Kept gold entities `[{text, label}]` — **val/test** docs |
| `data/gold_v2/{slug}.dropped.json` | Proposals the gates rejected, with reasons |
| `data/gold_v2_train/{slug}.json` | Same, for the **66 train** docs |
| `data/gold_v2/proposals/{slug}.json` | Human curation: proposals `{text,label}` and FP rejections `{text,label,reject:true}` — written by `hitl_ner` |
| `data/gold_v2/eval.jsonl` | Converted token-span JSONL for the eval harness (`gold_to_training.py`) |
| `data/gold_v2/split_full.json` | Split manifest for the LLM-gold eval set |

The `{text, label}` schema is shared between the gold files, the LLM
proposals, and the human curation, so accepted proposals merge into gold
with no format conversion.

> **Housekeeping note:** `data/gold_v2/` currently also holds pipeline
> artifacts (`rescored-*.json`, `full-rescored-*.json`, `split*.json`,
> `review.html`, `RESCORE_FINDINGS.md`). Tooling filters these by prefix,
> but they'd be cleaner in a subdirectory; slated for the merge-step
> cleanup.

## Model checkpoints & results

| Path | Content |
|------|---------|
| `models/gliner-cti-v1-best/` | Fine-tuned GLiNER checkpoint |
| `models/roberta-cti-{base,large,securebert}/best/` | Fine-tuned RoBERTa-family checkpoints |
| `data/roberta_results/{name}.json` | Per-model P/R/F1 (strict + relaxed, per-label + micro/macro) |
| `data/results_{zeroshot,finetuned}.json` | GLiNER zero-shot / fine-tuned scores |
| `data/frontier_results/{model}-{entities,spans,scores}.{jsonl,json}` | Frontier LLM eval, three-stage pipeline |
