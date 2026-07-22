"""
Render the current gold labels as a single reviewable HTML page — built
for the human quality pass BEFORE retraining on a regenerated corpus
(2026-07-19 Phase 1 follow-up: verify first this time).

Defaults cover the full LLM-gold corpus: data/gold_v2/eval.jsonl (16
human-curated val/test docs) plus data/gold_v2/train.jsonl (66 LLM-only
train docs), with subsets labeled via split_full_gliner.json. Regenerate
either input with ner.gold_to_training if the gold changes.

Shows exactly what the evaluation harness sees: chunks merged back to
document-global token streams via chunk_start (same reconstruction as
ner/evaluate.py), gold spans deduplicated document-globally, then
rendered inline with per-label colors.

Review affordances:
  - sidebar: advisories grouped train/val/test with span counts
  - legend: click a label to toggle its highlights (isolate one label)
  - suspicion panel: top repeated span texts per label across the corpus
    (uniform spread across docs = probable residual noise)
  - integrity line per doc: rendered vs. skipped-overlap span counts

Usage:
    PYTHONPATH=. python3 -m ner.visualize_gold \
        [--data data/gold_v2/eval.jsonl data/gold_v2/train.jsonl] \
        [--out data/gold_review.html]
"""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter, defaultdict
from pathlib import Path

# 16 visually distinct pastel backgrounds (dark text stays readable)
LABEL_COLORS = [
    "#ffd6a5", "#fdffb6", "#caffbf", "#9bf6ff", "#a0c4ff", "#bdb2ff",
    "#ffc6ff", "#ffadad", "#d0f4de", "#fcf6bd", "#e4c1f9", "#a9def9",
    "#ede7b1", "#f6c8c8", "#c8e7f6", "#d8f8c8",
]


def rebuild_document(chunks: list[dict]) -> tuple[list[str], set[tuple[int, int, str]]]:
    """Merge overlapping chunks into a global token list + global span set
    (mirrors evaluate.py's document-global reconstruction)."""
    tokens: dict[int, str] = {}
    spans: set[tuple[int, int, str]] = set()
    for rec in chunks:
        base = rec["chunk_start"]
        for i, tok in enumerate(rec["tokenized_text"]):
            tokens[base + i] = tok
        for s, e, label in rec["ner"]:
            spans.add((base + s, base + e, label))
    if not tokens:
        return [], set()
    n = max(tokens) + 1
    return [tokens.get(i, "") for i in range(n)], spans


def select_non_overlapping(spans: set) -> tuple[list, int]:
    """Longest-first greedy selection for rendering (nested/overlapping
    duplicates are counted, not silently dropped)."""
    chosen: list[tuple[int, int, str]] = []
    occupied: set[int] = set()
    skipped = 0
    for s, e, label in sorted(spans, key=lambda x: (-(x[1] - x[0]), x[0])):
        if any(i in occupied for i in range(s, e + 1)):
            skipped += 1
            continue
        chosen.append((s, e, label))
        occupied.update(range(s, e + 1))
    chosen.sort()
    return chosen, skipped


def render_doc_html(tokens: list[str], chosen: list, label_idx: dict[str, int]) -> str:
    out = []
    starts = {s: (e, label) for s, e, label in chosen}
    i = 0
    while i < len(tokens):
        if i in starts:
            e, label = starts[i]
            body = html.escape(" ".join(tokens[i:e + 1]))
            li = label_idx[label]
            out.append(
                f'<mark class="l{li}" title="{html.escape(label)}">{body}'
                f'<span class="tag">{html.escape(label)}</span></mark>'
            )
            i = e + 1
        else:
            out.append(html.escape(tokens[i]))
            i += 1
    return " ".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--data", nargs="+",
                    default=["data/gold_v2/eval.jsonl", "data/gold_v2/train.jsonl"])
    ap.add_argument("--split", default="data/gold_v2/split_full_gliner.json")
    ap.add_argument("--out", default="data/gold_review.html")
    args = ap.parse_args()

    recs = [json.loads(l) for p in args.data for l in open(p, encoding="utf-8")]
    split = json.loads(Path(args.split).read_text(encoding="utf-8"))
    subset_of = {s: name for name in split for s in split[name]}

    by_doc: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        by_doc[r["slug"]].append(r)

    labels = sorted({l for r in recs for _, _, l in r["ner"]})
    label_idx = {l: i for i, l in enumerate(labels)}

    # global suspicion stats
    value_counts: dict[str, Counter] = defaultdict(Counter)
    value_docs: dict[str, dict[str, set]] = defaultdict(lambda: defaultdict(set))
    total_spans = 0

    doc_sections = []
    sidebar_items: dict[str, list[str]] = {"train": [], "val": [], "test": [], "?": []}

    for slug in sorted(by_doc, key=lambda s: (subset_of.get(s, "?"), s)):
        tokens, spans = rebuild_document(by_doc[slug])
        total_spans += len(spans)
        for s, e, label in spans:
            text = " ".join(tokens[s:e + 1]).lower().strip(".,;:")
            value_counts[label][text] += 1
            value_docs[label][text].add(slug)
        chosen, skipped = select_non_overlapping(spans)
        subset = subset_of.get(slug, "?")
        body = render_doc_html(tokens, chosen, label_idx)
        per_label = Counter(l for _, _, l in spans)
        stat = ", ".join(f"{l}: {n}" for l, n in per_label.most_common())
        doc_sections.append(
            f'<section id="doc-{slug}" class="doc" hidden>'
            f'<h2>{slug} <small>[{subset}]</small></h2>'
            f'<p class="meta">{len(spans)} gold spans'
            + (f' ({skipped} nested/overlapping not individually highlighted)'
               if skipped else '')
            + f'<br><span class="perlabel">{html.escape(stat)}</span></p>'
            f'<div class="text">{body}</div></section>'
        )
        sidebar_items[subset].append(
            f'<li><a href="#" data-doc="doc-{slug}">{slug}</a> '
            f'<small>{len(spans)}</small></li>'
        )

    legend = "".join(
        f'<span class="leg l{label_idx[l]}" data-label="l{label_idx[l]}">'
        f'{html.escape(l)}</span>'
        for l in labels
    )
    styles = "\n".join(
        f'mark.l{i} {{ background: {LABEL_COLORS[i % len(LABEL_COLORS)]}; }}\n'
        f'.leg.l{i} {{ background: {LABEL_COLORS[i % len(LABEL_COLORS)]}; }}'
        for i in range(len(labels))
    )

    suspicion_rows = []
    for label in labels:
        for text, n in value_counts[label].most_common(6):
            ndocs = len(value_docs[label][text])
            flag = " ⚠" if ndocs >= 8 else ""
            suspicion_rows.append(
                f"<tr><td>{html.escape(label)}</td><td>{html.escape(text[:60])}</td>"
                f"<td>{n}</td><td>{ndocs}{flag}</td></tr>"
            )

    sidebar_html = ""
    for subset in ("val", "test", "train"):
        if sidebar_items[subset]:
            sidebar_html += (f"<h3>{subset} ({len(sidebar_items[subset])})</h3>"
                             f"<ul>{''.join(sidebar_items[subset])}</ul>")

    page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Gold Label Review — {total_spans} spans</title>
<style>
  body {{ font-family: -apple-system, sans-serif; margin: 0; display: flex; }}
  #sidebar {{ width: 270px; min-width: 270px; height: 100vh; overflow-y: auto;
             background: #f4f4f4; padding: 1rem; box-sizing: border-box;
             border-right: 1px solid #ddd; }}
  #sidebar ul {{ list-style: none; padding-left: 0.4rem; margin: 0.3rem 0 1rem; }}
  #sidebar li {{ margin: 0.15rem 0; font-size: 0.85rem; }}
  #sidebar a {{ text-decoration: none; color: #246; }}
  #sidebar a.active {{ font-weight: 700; }}
  #main {{ flex: 1; height: 100vh; overflow-y: auto; padding: 1.5rem 2rem;
           box-sizing: border-box; }}
  .text {{ line-height: 2.1; max-width: 75rem; white-space: pre-wrap; }}
  mark {{ padding: 0.1rem 0.25rem; border-radius: 4px; position: relative; }}
  mark .tag {{ font-size: 0.62rem; font-weight: 700; color: #333; opacity: 0.65;
               margin-left: 0.25rem; vertical-align: super; }}
  mark.dim {{ background: transparent !important; }}
  mark.dim .tag {{ display: none; }}
  .leg {{ display: inline-block; padding: 0.2rem 0.6rem; margin: 0.15rem;
          border-radius: 999px; font-size: 0.8rem; cursor: pointer;
          border: 2px solid transparent; }}
  .leg.off {{ opacity: 0.3; }}
  .meta {{ color: #777; font-size: 0.85rem; }}
  .perlabel {{ font-size: 0.78rem; }}
  table {{ border-collapse: collapse; font-size: 0.82rem; }}
  td, th {{ border: 1px solid #ccc; padding: 0.25rem 0.6rem; }}
  details {{ margin-bottom: 1rem; }}
</style>{'<style>' + styles + '</style>'}
</head><body>
<div id="sidebar">
  <h2 style="font-size:1rem">Gold Review</h2>
  <p style="font-size:0.8rem;color:#666">{len(by_doc)} docs · {total_spans} spans<br>
  click label pills to toggle</p>
  <div id="legend">{legend}</div>
  {sidebar_html}
</div>
<div id="main">
  <details open><summary><b>Suspicion panel</b> — top span texts per label
  (⚠ = appears in ≥8 docs: check for residual furniture)</summary>
  <table><tr><th>label</th><th>span text</th><th>count</th><th>docs</th></tr>
  {''.join(suspicion_rows)}</table></details>
  {''.join(doc_sections)}
</div>
<script>
  const links = document.querySelectorAll('#sidebar a[data-doc]');
  links.forEach(a => a.addEventListener('click', ev => {{
    ev.preventDefault();
    document.querySelectorAll('.doc').forEach(d => d.hidden = true);
    document.getElementById(a.dataset.doc).hidden = false;
    links.forEach(x => x.classList.remove('active'));
    a.classList.add('active');
  }}));
  if (links.length) links[0].click();
  document.querySelectorAll('.leg').forEach(leg => leg.addEventListener('click', () => {{
    const cls = leg.dataset.label;
    leg.classList.toggle('off');
    const off = leg.classList.contains('off');
    document.querySelectorAll('mark.' + cls).forEach(m =>
      m.classList.toggle('dim', off));
  }}));
</script>
</body></html>"""

    out_path = Path(args.out)
    out_path.write_text(page, encoding="utf-8")
    print(f"{len(by_doc)} documents, {total_spans} gold spans")
    print(f"wrote {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
