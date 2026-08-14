"""
LLM-primary gold annotation pilot (2026-07-19).

Direction change from the ensemble pipeline: no MITRE dictionary, no STIX
bundles. Claude reads the clean advisory text and proposes gold entities
directly; a human reviews the rendered result before anything downstream
uses it. Quality-first on a handful of documents, not scale-first on 82.

Differences from the frontier-eval prompt (frontier_infer.call_claude):
  - Recall-oriented: the eval prompt says "prefer precision over recall"
    because it is scored as a model under test. Here Claude is the
    ANNOTATOR — misses become permanent gold gaps (the old pipeline's 50%
    recall gap came exactly from annotator blind spots), while spurious
    proposals get caught by the verbatim/validator gates and the human
    review pass. So: exhaustive extraction, every mention, lists included.
  - No character offsets requested: LLM offsets verify against text only
    ~7% of the time (measured here; independently confirmed by Zhan et
    al. 2601.17898 — offset output is the worst extraction contract).
    Spans are located by verbatim text search instead.

Gates applied to every proposal (drops are reported, not silent):
  - verbatim: proposed text must appear in the document exactly, compared
    whitespace-insensitively (line wraps / multiple spaces collapse; the
    2026-07-26 fix — the old raw-substring test flakily rejected entities
    that were merely line-wrapped in clean.md)
  - validator: structured types must satisfy their format grammar
    (span_validators; defanged forms accepted)
  - label: must be one of the 16 canonical labels

Output:
  data/gold_v2/{slug}.json        — gated entity list [{text, label}]
  data/gold_v2/{slug}.dropped.json — what the gates rejected, and why
  data/gold_v2/review.html         — human review page (highlights,
                                     per-label toggles, value tables)

Usage:
    PYTHONPATH=. python3 -m ner.llm_gold \
        --slugs aa23-284a,aa25-163a,aa23-352a \
        --model claude-sonnet-5
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from .annotation_text import contains_verbatim, ws_normalize
from .frontier_llm_utils import LABELS, load_clean_text
from .span_validators import validate

CHUNK_SIZE = 15000
CHUNK_OVERLAP = 500

GOLD_PROMPT = """You are annotating a cybersecurity advisory to create a \
gold-standard named-entity dataset. Extract EVERY entity mention of the \
following types:

{label_list}

Rules:
- Be EXHAUSTIVE. Every tool named in a list, every hash in a table, every \
CVE, every file name — a missed entity becomes a permanent gap in the \
dataset. When in doubt whether something qualifies, include it.
- "hacking tool" includes legitimate software abused by attackers \
(remote-admin/RMM tools, LOLbins like PsExec or certutil) when the text \
describes attacker use.
- Defanged indicators (1.2.3[.]4, user@dom[.]com, hxxp://...) are real \
entities — extract them exactly as written.
- text must be VERBATIM from the document (exact characters, including \
brackets in defanged forms). Do not normalize, defang, or re-fang.
- label must be EXACTLY one of the listed types (lowercase).
- Extract the entity itself, not surrounding words ("LockBit 3.0", not \
"the LockBit 3.0 ransomware").

Text:
{text}

Return ONLY a JSON array:
[{{"text": "...", "label": "..."}}, ...]
"""


def call_gold_llm(text: str, model_id: str, api_key: str) -> list[dict]:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    prompt = GOLD_PROMPT.format(label_list="\n".join(f"- {l}" for l in LABELS),
                                text=text)
    kwargs = dict(model=model_id, max_tokens=16384,
                  messages=[{"role": "user", "content": prompt}])
    try:
        resp = client.messages.create(temperature=0.0, **kwargs)
    except anthropic.BadRequestError as e:
        if "temperature" in str(e).lower():
            resp = client.messages.create(**kwargs)
        else:
            raise
    out = "".join(b.text for b in resp.content if b.type == "text").strip()
    if "```json" in out:
        out = out.split("```json")[1].split("```")[0].strip()
    elif "```" in out:
        out = out.split("```")[1].split("```")[0].strip()
    # strict=False: entity texts can legitimately contain control chars
    # (tabs/newlines inside file paths, commands, YARA fragments) and the
    # model emits them raw inside JSON strings — strict parsing crashes on
    # the first such document (hit on the first train batch, 2026-07-19)
    try:
        ents = json.loads(out, strict=False)
    except json.JSONDecodeError:
        # salvage 1: largest [-to-] slice (handles prose before/after array)
        ents = None
        m = re.search(r"\[.*\]", out, re.DOTALL)
        if m:
            try:
                ents = json.loads(m.group(0), strict=False)
            except json.JSONDecodeError:
                pass
        if ents is None:
            # salvage 2: output truncated mid-array (max_tokens) — recover
            # every COMPLETE {...} object individually; only the entity cut
            # off mid-string is lost
            ents = []
            for om in re.finditer(r"\{[^{}]*\}", out, re.DOTALL):
                try:
                    ents.append(json.loads(om.group(0), strict=False))
                except json.JSONDecodeError:
                    continue
            print(f"    truncated/malformed JSON: salvaged {len(ents)} "
                  f"complete objects", file=sys.stderr)
    return [e for e in ents if isinstance(e, dict)]


def annotate_document(slug: str, markdown_dir: Path, model_id: str,
                      api_key: str) -> tuple[list[dict], list[dict]]:
    text = load_clean_text(slug, markdown_dir)
    if not text:
        raise FileNotFoundError(f"no clean text for {slug}")

    chunks = []
    pos = 0
    while pos < len(text):
        chunks.append(text[pos:pos + CHUNK_SIZE])
        if pos + CHUNK_SIZE >= len(text):
            break
        pos += CHUNK_SIZE - CHUNK_OVERLAP

    proposals: dict[tuple[str, str], dict] = {}
    for ci, chunk in enumerate(chunks, 1):
        t0 = time.time()
        ents = call_gold_llm(chunk, model_id, api_key)
        print(f"    chunk {ci}/{len(chunks)}: {len(ents)} proposals "
              f"({time.time()-t0:.0f}s)", file=sys.stderr)
        for e in ents:
            t, l = str(e.get("text", "")).strip(), str(e.get("label", "")).strip().lower()
            if t and l:
                proposals.setdefault((t.lower(), l), {"text": t, "label": l})

    kept, dropped = [], []
    # Whitespace-normalized comparison space: a raw substring test rejects
    # entities that are merely line-wrapped in clean.md, even though the
    # downstream span locator (find_token_span) places them fine.
    text_norm = ws_normalize(text).lower()
    for (tl, label), ent in sorted(proposals.items()):
        if label not in LABELS:
            dropped.append({**ent, "reason": f"unknown label {label!r}"})
        elif not contains_verbatim(text_norm, ent["text"]):
            dropped.append({**ent, "reason": "not verbatim in document"})
        elif not validate(label, ent["text"]):
            dropped.append({**ent, "reason": "failed format validator"})
        else:
            kept.append(ent)
    return kept, dropped


# ── review page ───────────────────────────────────────────────────────────────

LABEL_COLORS = [
    "#ffd6a5", "#fdffb6", "#caffbf", "#9bf6ff", "#a0c4ff", "#bdb2ff",
    "#ffc6ff", "#ffadad", "#d0f4de", "#fcf6bd", "#e4c1f9", "#a9def9",
    "#ede7b1", "#f6c8c8", "#c8e7f6", "#d8f8c8",
]


def render_review(docs: dict[str, tuple[str, list[dict], list[dict]]],
                  out_path: Path, model_id: str) -> None:
    label_idx = {l: i for i, l in enumerate(LABELS)}
    sections, sidebar = [], []
    for slug, (text, kept, dropped) in docs.items():
        by_text: dict[str, list[str]] = defaultdict(list)
        for e in kept:
            by_text[e["text"].lower()].append(e["label"])
        # longest-first alternation, all occurrences, case-insensitive
        pat = re.compile("|".join(
            re.escape(t) for t in sorted(by_text, key=len, reverse=True)
        ), re.IGNORECASE) if by_text else None

        pieces, last = [], 0
        if pat:
            for m in pat.finditer(text):
                pieces.append(html.escape(text[last:m.start()]))
                labels_here = by_text[m.group(0).lower()]
                li = label_idx[labels_here[0]]
                conflict = " conflict" if len(set(labels_here)) > 1 else ""
                tag = "/".join(sorted(set(labels_here)))
                pieces.append(
                    f'<mark class="l{li}{conflict}" title="{html.escape(tag)}">'
                    f'{html.escape(m.group(0))}<span class="tag">'
                    f'{html.escape(tag)}</span></mark>')
                last = m.end()
        pieces.append(html.escape(text[last:]))

        per_label = Counter(e["label"] for e in kept)
        value_rows = "".join(
            f"<tr><td>{html.escape(e['label'])}</td>"
            f"<td>{html.escape(e['text'][:70])}</td></tr>"
            for e in sorted(kept, key=lambda x: (x["label"], x["text"].lower()))
        )
        drop_rows = "".join(
            f"<tr><td>{html.escape(d['label'])}</td>"
            f"<td>{html.escape(d['text'][:70])}</td>"
            f"<td>{html.escape(d['reason'])}</td></tr>"
            for d in dropped
        )
        stat = ", ".join(f"{l}: {n}" for l, n in per_label.most_common())
        sections.append(
            f'<section id="doc-{slug}" class="doc" hidden>'
            f'<h2>{slug}</h2>'
            f'<p class="meta">{len(kept)} unique entities kept, '
            f'{len(dropped)} dropped by gates<br>'
            f'<span class="perlabel">{html.escape(stat)}</span></p>'
            f'<details><summary>entity list ({len(kept)})</summary>'
            f'<table><tr><th>label</th><th>text</th></tr>{value_rows}</table>'
            f'</details>'
            f'<details><summary>dropped by gates ({len(dropped)})</summary>'
            f'<table><tr><th>label</th><th>text</th><th>reason</th></tr>'
            f'{drop_rows}</table></details>'
            f'<div class="text">{"".join(pieces)}</div></section>')
        sidebar.append(f'<li><a href="#" data-doc="doc-{slug}">{slug}</a> '
                       f'<small>{len(kept)}</small></li>')

    legend = "".join(
        f'<span class="leg l{label_idx[l]}" data-label="l{label_idx[l]}">'
        f'{html.escape(l)}</span>' for l in LABELS)
    styles = "\n".join(
        f'mark.l{i} {{ background: {LABEL_COLORS[i % len(LABEL_COLORS)]}; }}\n'
        f'.leg.l{i} {{ background: {LABEL_COLORS[i % len(LABEL_COLORS)]}; }}'
        for i in range(len(LABELS)))

    page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>LLM Gold Pilot — {model_id}</title>
<style>
  body {{ font-family: -apple-system, sans-serif; margin: 0; display: flex; }}
  #sidebar {{ width: 260px; min-width: 260px; height: 100vh; overflow-y: auto;
             background: #f4f4f4; padding: 1rem; box-sizing: border-box; }}
  #sidebar ul {{ list-style: none; padding-left: 0.4rem; }}
  #main {{ flex: 1; height: 100vh; overflow-y: auto; padding: 1.5rem 2rem;
           box-sizing: border-box; }}
  .text {{ line-height: 2.1; max-width: 75rem; white-space: pre-wrap; }}
  mark {{ padding: 0.1rem 0.25rem; border-radius: 4px; }}
  mark.conflict {{ outline: 2px dashed #d00; }}
  mark .tag {{ font-size: 0.62rem; font-weight: 700; opacity: 0.65;
               margin-left: 0.25rem; vertical-align: super; }}
  mark.dim {{ background: transparent !important; }}
  mark.dim .tag {{ display: none; }}
  .leg {{ display: inline-block; padding: 0.2rem 0.6rem; margin: 0.15rem;
          border-radius: 999px; font-size: 0.8rem; cursor: pointer; }}
  .leg.off {{ opacity: 0.3; }}
  .meta {{ color: #777; font-size: 0.85rem; }}
  table {{ border-collapse: collapse; font-size: 0.82rem; margin: 0.5rem 0; }}
  td, th {{ border: 1px solid #ccc; padding: 0.2rem 0.55rem; }}
</style><style>{styles}</style></head><body>
<div id="sidebar">
  <h2 style="font-size:1rem">LLM Gold Pilot</h2>
  <p style="font-size:0.78rem;color:#666">model: {html.escape(model_id)}<br>
  dashed red outline = label conflict<br>click pills to toggle labels</p>
  <div>{legend}</div>
  <h3>documents</h3><ul>{"".join(sidebar)}</ul>
</div>
<div id="main">{"".join(sections)}</div>
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
    leg.classList.toggle('off');
    const off = leg.classList.contains('off');
    document.querySelectorAll('mark.' + leg.dataset.label).forEach(m =>
      m.classList.toggle('dim', off));
  }}));
</script></body></html>"""
    out_path.write_text(page, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--slugs", required=True,
                    help="Comma-separated advisory slugs")
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--markdown-dir", default="data/alerts")
    ap.add_argument("--out-dir", default="data/gold_v2")
    args = ap.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("Set ANTHROPIC_API_KEY")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir = Path(args.markdown_dir)

    docs = {}
    for slug in [s.strip() for s in args.slugs.split(",")]:
        out_json = out_dir / f"{slug}.json"
        if out_json.exists():
            # resume: don't re-pay for completed docs after a crash/rerun
            kept = json.loads(out_json.read_text(encoding="utf-8"))
            dropped_path = out_dir / f"{slug}.dropped.json"
            dropped = (json.loads(dropped_path.read_text(encoding="utf-8"))
                       if dropped_path.exists() else [])
            print(f"{slug}: already annotated ({len(kept)} kept), skipping",
                  file=sys.stderr)
        else:
            print(f"{slug}:", file=sys.stderr)
            kept, dropped = annotate_document(slug, markdown_dir, args.model, api_key)
            out_json.write_text(json.dumps(kept, indent=1), encoding="utf-8")
            (out_dir / f"{slug}.dropped.json").write_text(
                json.dumps(dropped, indent=1), encoding="utf-8")
            print(f"  -> {len(kept)} kept, {len(dropped)} dropped", file=sys.stderr)
        text = load_clean_text(slug, markdown_dir)
        docs[slug] = (text, kept, dropped)

    review = out_dir / "review.html"
    render_review(docs, review, args.model)
    print(f"\nreview page: {review}")


if __name__ == "__main__":
    main()
