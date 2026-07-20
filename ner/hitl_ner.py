"""
hitl_ner — human-in-the-loop NER gold curation webapp
(companion to the read-only data/gold_v2/review.html).

Curation actions, all persisted immediately to
data/gold_v2/proposals/{slug}.json:

  PROPOSE  select text -> label palette -> click a label (or UNK).
           Stored as {"text", "label"} — same schema as the gold files,
           so accepted proposals merge with no conversion. UNK marks
           "clearly an entity, no fitting label"; UNK rows get clustered
           later to propose new label types.
  REJECT   click an existing gold highlight -> "reject as FP". Stored as
           {"text", "label", "reject": true}; renders struck-through.
           The merge step treats it as a deletion from gold.
  UNDO     click a rejected highlight to restore it; remove proposals
           via the sidebar x (or click them in the text).

Zero dependencies (stdlib http.server), same pattern as audit_webapp.py.

Usage:
    PYTHONPATH=. python3 -m ner.hitl_ner          # port 8766
    open http://localhost:8766
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import os
import re
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .frontier_llm_utils import LABELS, load_clean_text

ALL_LABELS = list(LABELS) + ["UNK"]

LABEL_COLORS = [
    "#ffd6a5", "#fdffb6", "#caffbf", "#9bf6ff", "#a0c4ff", "#bdb2ff",
    "#ffc6ff", "#ffadad", "#d0f4de", "#fcf6bd", "#e4c1f9", "#a9def9",
    "#ede7b1", "#f6c8c8", "#c8e7f6", "#d8f8c8", "#ff5d5d",  # UNK = red
]


def atomic_write(path: Path, content: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def make_handler(gold_dir: Path, proposals_dir: Path, markdown_dir: Path,
                 slugs: list[str]):
    proposals_dir.mkdir(parents=True, exist_ok=True)

    def load_proposals(slug: str) -> list[dict]:
        p = proposals_dir / f"{slug}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _json(self, obj, status=200):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                body = PAGE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/api/slugs":
                self._json(slugs)
            elif self.path.startswith("/api/doc/"):
                slug = self.path.split("/api/doc/")[1]
                if slug not in slugs:
                    self._json({"error": "unknown slug"}, 404)
                    return
                text = load_clean_text(slug, markdown_dir) or ""
                gold_path = gold_dir / f"{slug}.json"
                gold = (json.loads(gold_path.read_text(encoding="utf-8"))
                        if gold_path.exists() else [])
                self._json({"slug": slug, "text": text, "gold": gold,
                            "proposals": load_proposals(slug)})
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length))
                slug = payload["slug"]
                assert slug in slugs, f"unknown slug {slug!r}"
            except Exception as e:
                self._json({"error": str(e)}, 400)
                return

            props = load_proposals(slug)
            if self.path == "/api/propose":
                text, label = payload.get("text", "").strip(), payload.get("label", "")
                reject = bool(payload.get("reject", False))
                if not text or label not in ALL_LABELS:
                    self._json({"error": "need text + valid label"}, 400)
                    return
                key = (text.lower(), label, reject)
                seen = {(p["text"].lower(), p["label"], bool(p.get("reject")))
                        for p in props}
                if key not in seen:
                    entry = {"text": text, "label": label}
                    if reject:
                        entry["reject"] = True
                    props.append(entry)
            elif self.path == "/api/delete":
                # match on text+label+reject so removing a rejection can't
                # accidentally remove a same-valued proposal (or vice versa)
                tgt = (payload.get("text"), payload.get("label"),
                       bool(payload.get("reject", False)))
                props = [p for p in props
                         if (p["text"], p["label"], bool(p.get("reject"))) != tgt]
            else:
                self.send_response(404)
                self.end_headers()
                return
            atomic_write(proposals_dir / f"{slug}.json",
                         json.dumps(props, indent=1))
            self._json({"ok": True, "proposals": props})

    return Handler


PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>HITL NER — gold curation</title>
<style>
  body { font-family: -apple-system, sans-serif; margin: 0; display: flex; }
  #sidebar { width: 280px; min-width: 280px; height: 100vh; overflow-y: auto;
             background: #f4f4f4; padding: 1rem; box-sizing: border-box; }
  #sidebar ul { list-style: none; padding-left: 0.4rem; }
  #sidebar li { margin: 0.15rem 0; font-size: 0.85rem; }
  #sidebar a.active { font-weight: 700; }
  #main { flex: 1; height: 100vh; overflow-y: auto; padding: 1.5rem 2rem;
          box-sizing: border-box; }
  .text { line-height: 2.1; max-width: 75rem; white-space: pre-wrap; }
  mark { border-radius: 3px; padding: 0 0.15rem; }
  mark .tag { font-size: 0.62rem; font-weight: 700; color: #333;
              opacity: 0.65; margin-left: 0.25rem; vertical-align: super;
              user-select: none; }  /* tags must never leak into selections */
  mark.prop { outline: 2px solid #d00; font-weight: 600; }
  mark.rej { text-decoration: line-through 2px #900;
             opacity: 0.55; cursor: pointer; }
  mark { cursor: pointer; }
  %LABEL_STYLES%
  #entmenu { position: absolute; display: none; background: white;
             border: 1px solid #999; border-radius: 10px; padding: 0.4rem;
             box-shadow: 0 4px 16px rgba(0,0,0,0.25); z-index: 11; }
  #entmenu button { display: block; width: 100%; margin: 0.15rem 0;
             padding: 0.35rem 0.7rem; font-size: 0.8rem; border: none;
             border-radius: 6px; cursor: pointer; background: #f2f2f2;
             text-align: left; }
  #entmenu button:hover { background: #dde; }
  #palette { position: absolute; display: none; background: white;
             border: 1px solid #999; border-radius: 10px; padding: 0.5rem;
             box-shadow: 0 4px 16px rgba(0,0,0,0.25); z-index: 10;
             max-width: 430px; }
  #palette button { margin: 0.12rem; padding: 0.3rem 0.6rem; font-size: 0.78rem;
             border: 1px solid #ccc; border-radius: 999px; cursor: pointer;
             background: #fafafa; }
  #palette button:hover { background: #dde; }
  #palette button.unk { background: #ff5d5d; color: white; font-weight: 700; }
  #plist { font-size: 0.82rem; }
  #plist li { margin: 0.2rem 0; }
  #plist .del { color: #c00; cursor: pointer; margin-left: 0.4rem;
                font-weight: 700; }
  #plist .unklabel { color: #c00; font-weight: 700; }
  .hint { font-size: 0.78rem; color: #888; }
</style></head><body>
<div id="sidebar">
  <h2 style="font-size:1rem">HITL NER</h2>
  <p class="hint"><b>Select text</b> → label palette (UNK = entity with no
  fitting label). <b>Click a gold highlight</b> → reject as FP
  (struck-through). <b>Click a struck/red one</b> → undo.</p>
  <h3>documents</h3><ul id="doclist"></ul>
  <h3>curation (this doc)</h3><ul id="plist"></ul>
</div>
<div id="main"><div class="text" id="doctext">loading…</div></div>
<div id="palette"></div>
<div id="entmenu"></div>
<script>
const LABELS = %LABELS%;
let cur = null, curDoc = null;

async function loadSlugs() {
  const slugs = await (await fetch('/api/slugs')).json();
  const ul = document.getElementById('doclist');
  slugs.forEach(s => {
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = '#'; a.textContent = s;
    a.onclick = ev => { ev.preventDefault(); loadDoc(s, a); };
    li.appendChild(a); ul.appendChild(li);
  });
  if (slugs.length) loadDoc(slugs[0], ul.querySelector('a'));
}

function esc(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function escRe(s) { return s.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&'); }

// whitespace-normalized key: selections spanning a line wrap yield '\\n'
// where the document may have spaces (and vice versa) — match flexibly
function normKey(s) { return s.toLowerCase().replace(/\\s+/g, ' ').trim(); }

function render() {
  const d = curDoc;
  // value -> {cls, label, kind, entry}; later writers win:
  // gold < rejection-of-gold < proposal
  const entries = new Map();
  d.gold.forEach(e => entries.set(normKey(e.text),
    {cls: 'l' + LABELS.indexOf(e.label), label: e.label,
     kind: 'gold', entry: e}));
  d.proposals.filter(p => p.reject).forEach(p => {
    const k = normKey(p.text);
    entries.set(k, {cls: 'rej l' + LABELS.indexOf(p.label),
      label: p.label + ' (rejected FP)', kind: 'rej', entry: p});
  });
  d.proposals.filter(p => !p.reject).forEach(p => entries.set(normKey(p.text),
    {cls: 'prop l' + LABELS.indexOf(p.label),
     label: p.label + ' (proposed)', kind: 'prop', entry: p}));
  const keys = [...entries.keys()].sort((a,b) => b.length - a.length);
  let html;
  if (keys.length) {
    // any run of whitespace in the entity matches any run in the document;
    // word-boundary guards so gold 'ping' never highlights inside
    // 'developing'. Uses a trailing lookahead (widely supported) plus a
    // post-match check of the preceding char (avoids lookbehind, which
    // older Safari lacks). Guards apply only where the entity edge is a
    // word char, so values like '[.]com' or '.vmsn' still match after
    // punctuation.
    const branch = k => {
      let b = escRe(k).replace(/ /g, '\\\\s+');
      if (/[a-z0-9]$/i.test(k)) b = b + '(?![A-Za-z0-9])';
      return b;
    };
    const re = new RegExp(keys.map(branch).join('|'), 'gi');
    let out = [], last = 0, m;
    while ((m = re.exec(d.text)) !== null) {
      const startsWord = /^[a-z0-9]/i.test(m[0]);
      const prevChar = m.index > 0 ? d.text[m.index - 1] : '';
      if (startsWord && /[A-Za-z0-9]/.test(prevChar)) {
        // left edge is inside a larger word (e.g. 'ping' in 'developing')
        out.push(esc(d.text.slice(last, m.index + 1)));
        last = m.index + 1;
        re.lastIndex = last;
        continue;
      }
      out.push(esc(d.text.slice(last, m.index)));
      const ent = entries.get(normKey(m[0]));
      if (!ent) { out.push(esc(m[0])); last = m.index + m[0].length; continue; }
      out.push('<mark class="' + ent.cls + '" data-key="' +
               esc(normKey(m[0])) + '" title="' + esc(ent.label) +
               '">' + esc(m[0]) +
               '<span class="tag">' + esc(ent.label) + '</span></mark>');
      last = m.index + m[0].length;
    }
    out.push(esc(d.text.slice(last)));
    html = out.join('');
  } else html = esc(d.text);
  document.getElementById('doctext').innerHTML = html;
  document.getElementById('doctext').querySelectorAll('mark').forEach(mk => {
    mk.addEventListener('click', ev => onMarkClick(ev, mk));
  });

  const pl = document.getElementById('plist');
  pl.innerHTML = '';
  d.proposals.forEach(p => {
    const li = document.createElement('li');
    const lbl = p.label === 'UNK'
      ? '<span class="unklabel">UNK</span>' : esc(p.label);
    const kind = p.reject ? ' <span class="unklabel">[FP]</span>' : '';
    li.innerHTML = esc(p.text) + ' — ' + lbl + kind +
      ' <span class="del" title="remove">×</span>';
    li.querySelector('.del').onclick = async () => {
      const r = await fetch('/api/delete', { method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({slug: d.slug, text: p.text, label: p.label,
                              reject: !!p.reject})});
      curDoc.proposals = (await r.json()).proposals;
      render();
    };
    pl.appendChild(li);
  });
}

const entmenu = document.getElementById('entmenu');

function onMarkClick(ev, mk) {
  // a click at the end of a text selection also fires here — ignore those
  if (window.getSelection().toString().trim()) return;
  ev.stopPropagation();
  const key = mk.dataset.key;
  const d = curDoc;
  const rejEntry = d.proposals.find(p => p.reject && normKey(p.text) === key);
  const propEntry = d.proposals.find(p => !p.reject && normKey(p.text) === key);
  const goldEntry = d.gold.find(e => normKey(e.text) === key);

  entmenu.innerHTML = '';
  const add = (txt, fn) => {
    const b = document.createElement('button');
    b.textContent = txt; b.onclick = fn; entmenu.appendChild(b);
  };
  if (rejEntry) {
    add('\\u21a9 Un-reject "' + rejEntry.text + '"', async () => {
      entmenu.style.display = 'none';
      const r = await fetch('/api/delete', { method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({slug: d.slug, text: rejEntry.text,
                              label: rejEntry.label, reject: true})});
      curDoc.proposals = (await r.json()).proposals;
      render();
    });
  } else if (propEntry) {
    add('\\u00d7 Remove proposal "' + propEntry.text + '"', async () => {
      entmenu.style.display = 'none';
      const r = await fetch('/api/delete', { method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({slug: d.slug, text: propEntry.text,
                              label: propEntry.label, reject: false})});
      curDoc.proposals = (await r.json()).proposals;
      render();
    });
  } else if (goldEntry) {
    add('\\u2717 Reject "' + goldEntry.text + '" (' + goldEntry.label +
        ') as FP', async () => {
      entmenu.style.display = 'none';
      const r = await fetch('/api/propose', { method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({slug: d.slug, text: goldEntry.text,
                              label: goldEntry.label, reject: true})});
      curDoc.proposals = (await r.json()).proposals;
      render();
    });
  } else return;
  const rect = mk.getBoundingClientRect();
  entmenu.style.left = Math.min(rect.left, window.innerWidth - 380) + 'px';
  entmenu.style.top = (rect.bottom + window.scrollY + 6) + 'px';
  entmenu.style.display = 'block';
}

async function loadDoc(slug, link) {
  curDoc = await (await fetch('/api/doc/' + slug)).json();
  document.querySelectorAll('#doclist a').forEach(a =>
    a.classList.remove('active'));
  if (link) link.classList.add('active');
  render();
}

const palette = document.getElementById('palette');
LABELS.forEach(l => {
  const b = document.createElement('button');
  b.textContent = l;
  if (l === 'UNK') b.classList.add('unk');
  b.onclick = async () => {
    palette.style.display = 'none';
    if (!cur) return;
    const r = await fetch('/api/propose', { method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({slug: curDoc.slug, text: cur, label: l}) });
    curDoc.proposals = (await r.json()).proposals;
    cur = null;
    render();
  };
  palette.appendChild(b);
});

document.getElementById('main').addEventListener('mouseup', () => {
  const sel = window.getSelection();
  // collapse internal whitespace/newlines so the stored value matches the
  // document under whitespace-flexible rendering and merges cleanly later
  const t = sel.toString().replace(/\\s+/g, ' ').trim();
  if (!t || t.length > 120) { palette.style.display = 'none'; return; }
  cur = t;
  const rect = sel.getRangeAt(0).getBoundingClientRect();
  palette.style.left = Math.min(rect.left, window.innerWidth - 450) + 'px';
  palette.style.top = (rect.bottom + window.scrollY + 6) + 'px';
  palette.style.display = 'block';
});
document.addEventListener('mousedown', ev => {
  if (!palette.contains(ev.target)) palette.style.display = 'none';
  if (!entmenu.contains(ev.target)) entmenu.style.display = 'none';
});

loadSlugs();
</script></body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--gold-dir", default="data/gold_v2")
    ap.add_argument("--proposals-dir", default="data/gold_v2/proposals")
    ap.add_argument("--markdown-dir", default="data/alerts")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    gold_dir = Path(args.gold_dir)
    slugs = sorted(
        f.stem for f in gold_dir.glob("*.json")
        if not f.name.endswith(".dropped.json")
        and not f.stem.startswith(("rescored", "full-rescored", "split"))
    )
    if not slugs:
        raise SystemExit(f"no gold files in {gold_dir}")

    global PAGE
    label_styles = "\n".join(
        f"  mark.l{i} {{ background: {LABEL_COLORS[i % len(LABEL_COLORS)]}; }}"
        for i in range(len(ALL_LABELS))
    )
    PAGE = (PAGE.replace("%LABELS%", json.dumps(ALL_LABELS))
                .replace("%LABEL_STYLES%", label_styles))

    handler = make_handler(gold_dir, Path(args.proposals_dir),
                           Path(args.markdown_dir), slugs)
    server = ThreadingHTTPServer(("localhost", args.port), handler)
    url = f"http://localhost:{args.port}"
    print(f"hitl_ner: {len(slugs)} docs | curation -> {args.proposals_dir}")
    print(f"Serving at {url} — Ctrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
