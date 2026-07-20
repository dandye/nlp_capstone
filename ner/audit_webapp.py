"""
Local web app for judging the gold audit sample — a faster, less error-prone
alternative to hand-editing paper/capstone/gold_audit.csv in a spreadsheet.

Zero new dependencies (stdlib http.server only). Reads/writes the same CSV
ner/score_audit.py already consumes, so nothing else in the pipeline
needs to change. Blinding is enforced at the data layer, not just by
convention: the server never loads or serves gold_audit.key.json, so there
is no code path that could leak model identity to the browser.

Every judgment is written to disk immediately (atomic temp-file + rename) —
there is no separate "save" step and no in-memory-only state to lose.

Usage:
    PYTHONPATH=. python3 -m ner.audit_webapp
    PYTHONPATH=. python3 -m ner.audit_webapp --csv paper/capstone/gold_audit.csv --port 8765

Then open http://localhost:8765 in a browser.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FIELDNAMES = ["item_id", "predicted_label", "context", "correct_Y_N", "notes"]


def load_rows(csv_path: Path) -> list[dict]:
    with open(csv_path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save_rows(csv_path: Path, rows: list[dict]) -> None:
    """Atomic write: temp file in the same directory, then rename."""
    fd, tmp_path = tempfile.mkstemp(
        dir=csv_path.parent, prefix=f".{csv_path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp_path, csv_path)
    except BaseException:
        os.unlink(tmp_path)
        raise


PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Gold Audit</title>
<style>
  :root { color-scheme: light dark; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 780px; margin: 2rem auto; padding: 0 1rem;
    background: #fafafa; color: #1a1a1a;
  }
  @media (prefers-color-scheme: dark) {
    body { background: #1a1a1a; color: #eee; }
    .card { background: #2a2a2a !important; border-color: #444 !important; }
    select, input[type=text] { background: #333; color: #eee; border-color: #555; }
    .pill { background: #3a3a5a !important; color: #cde !important; }
  }
  h1 { font-size: 1.3rem; margin-bottom: 0.2rem; }
  #progress-wrap { background: #ddd; border-radius: 6px; height: 10px; overflow: hidden; margin: 0.5rem 0 1rem; }
  #progress-bar { background: #4a7; height: 100%; width: 0%; transition: width 0.2s; }
  #progress-text { font-size: 0.85rem; color: #777; margin-bottom: 1rem; }
  .toolbar { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; }
  select, input[type=text] {
    padding: 0.4rem 0.6rem; border-radius: 6px; border: 1px solid #ccc; font-size: 0.9rem;
  }
  .card {
    border: 1px solid #ddd; border-radius: 10px; padding: 1.5rem;
    background: white; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .pill {
    display: inline-block; background: #eef; color: #446; padding: 0.2rem 0.7rem;
    border-radius: 999px; font-size: 0.85rem; font-weight: 600; margin-bottom: 1rem;
  }
  .context { font-size: 1.05rem; line-height: 1.6; margin-bottom: 1.2rem; }
  .context mark {
    background: #ffe066; color: #000; padding: 0.1rem 0.2rem; border-radius: 3px; font-weight: 600;
  }
  .buttons { display: flex; gap: 0.6rem; margin-bottom: 1rem; }
  button {
    font-size: 1rem; padding: 0.6rem 1.4rem; border-radius: 8px; border: none;
    cursor: pointer; font-weight: 600;
  }
  #btn-y { background: #2a7; color: white; }
  #btn-y.active { outline: 3px solid #163; }
  #btn-n { background: #d55; color: white; }
  #btn-n.active { outline: 3px solid #822; }
  #btn-prev, #btn-next { background: #eee; color: #333; }
  @media (prefers-color-scheme: dark) { #btn-prev, #btn-next { background: #444; color: #eee; } }
  .notes-row { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
  .notes-row input { flex: 1; }
  .status { font-size: 0.85rem; color: #888; min-height: 1.2rem; }
  .status.saved { color: #2a7; }
  .nav-row { display: flex; justify-content: space-between; margin-top: 1.2rem; }
  .item-id { font-family: monospace; color: #999; font-size: 0.85rem; }
  .hint { font-size: 0.8rem; color: #999; margin-top: 1.5rem; text-align: center; }
  kbd { background: #eee; border-radius: 4px; padding: 0.1rem 0.4rem; font-family: monospace; }
  @media (prefers-color-scheme: dark) { kbd { background: #444; } }
</style>
</head>
<body>
  <h1>Gold Audit — Blind Judgment</h1>
  <div id="progress-wrap"><div id="progress-bar"></div></div>
  <div id="progress-text">Loading...</div>

  <div class="toolbar">
    <label>Filter: <select id="filter-label"><option value="">All labels</option></select></label>
    <label><input type="checkbox" id="filter-unjudged" checked> Unjudged only (jump target)</label>
  </div>

  <div class="card">
    <div class="item-id" id="item-id"></div>
    <div class="pill" id="pred-label"></div>
    <div class="context" id="context"></div>
    <div class="buttons">
      <button id="btn-y">Y — correct</button>
      <button id="btn-n">N — incorrect</button>
    </div>
    <div class="notes-row">
      <input type="text" id="notes" placeholder="optional note (e.g. 'PDF footer noise', 'real entity wrong type')">
    </div>
    <div class="status" id="status"></div>
    <div class="nav-row">
      <button id="btn-prev">&larr; Previous</button>
      <button id="btn-next">Next &rarr;</button>
    </div>
  </div>

  <div class="hint">
    <kbd>Y</kbd> correct &nbsp; <kbd>N</kbd> incorrect &nbsp; <kbd>&larr;</kbd> <kbd>&rarr;</kbd> navigate &nbsp;
    marking Y/N auto-saves and advances to the next unjudged item
  </div>

<script>
let items = [];
let idx = 0;

async function loadItems() {
  const res = await fetch('/api/items');
  items = await res.json();
  const labels = [...new Set(items.map(i => i.predicted_label))].sort();
  const sel = document.getElementById('filter-label');
  for (const l of labels) {
    const opt = document.createElement('option');
    opt.value = l; opt.textContent = l;
    sel.appendChild(opt);
  }
  idx = items.findIndex(i => !i.correct_Y_N);
  if (idx === -1) idx = 0;
  render();
}

function visibleIndices() {
  const labelFilter = document.getElementById('filter-label').value;
  const unjudgedOnly = document.getElementById('filter-unjudged').checked;
  return items
    .map((it, i) => ({it, i}))
    .filter(({it}) => !labelFilter || it.predicted_label === labelFilter)
    .filter(({it}) => !unjudgedOnly || !it.correct_Y_N)
    .map(({i}) => i);
}

function render() {
  const item = items[idx];
  document.getElementById('item-id').textContent = item.item_id;
  document.getElementById('pred-label').textContent = item.predicted_label;
  const ctx = item.context
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace('&gt;&gt;&gt; ', '<mark>').replace(' &lt;&lt;&lt;', '</mark>');
  document.getElementById('context').innerHTML = ctx;
  document.getElementById('notes').value = item.notes || '';
  document.getElementById('btn-y').classList.toggle('active', item.correct_Y_N === 'Y');
  document.getElementById('btn-n').classList.toggle('active', item.correct_Y_N === 'N');
  document.getElementById('status').textContent = '';
  document.getElementById('status').className = 'status';

  const judged = items.filter(i => i.correct_Y_N).length;
  const pct = Math.round(100 * judged / items.length);
  document.getElementById('progress-bar').style.width = pct + '%';
  document.getElementById('progress-text').textContent =
    `${judged} / ${items.length} judged (${pct}%) — viewing ${item.item_id}`;
}

async function judge(verdict) {
  const item = items[idx];
  item.correct_Y_N = verdict;
  item.notes = document.getElementById('notes').value;
  const statusEl = document.getElementById('status');
  statusEl.textContent = 'saving...';
  const res = await fetch('/api/judge', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({item_id: item.item_id, correct_Y_N: verdict, notes: item.notes})
  });
  if (res.ok) {
    statusEl.textContent = 'saved';
    statusEl.className = 'status saved';
  } else {
    statusEl.textContent = 'SAVE FAILED — check server log';
  }
  render();
  setTimeout(advance, 250);
}

function advance() {
  const vis = visibleIndices();
  const pos = vis.indexOf(idx);
  if (pos !== -1 && pos + 1 < vis.length) { idx = vis[pos + 1]; render(); return; }
  // fall back: first unjudged anywhere
  const nextUnjudged = items.findIndex(i => !i.correct_Y_N);
  if (nextUnjudged !== -1) { idx = nextUnjudged; render(); }
}

function step(delta) {
  const vis = visibleIndices();
  let pos = vis.indexOf(idx);
  if (pos === -1) pos = 0;
  pos = Math.max(0, Math.min(vis.length - 1, pos + delta));
  if (vis.length) { idx = vis[pos]; render(); }
}

document.getElementById('btn-y').onclick = () => judge('Y');
document.getElementById('btn-n').onclick = () => judge('N');
document.getElementById('btn-prev').onclick = () => step(-1);
document.getElementById('btn-next').onclick = () => step(1);
document.getElementById('notes').addEventListener('change', () => {
  const item = items[idx];
  if (item.correct_Y_N) judge(item.correct_Y_N);  // re-save with updated note
});
document.getElementById('filter-label').onchange = () => { render(); };
document.getElementById('filter-unjudged').onchange = () => { render(); };

window.addEventListener('keydown', (e) => {
  if (document.activeElement.tagName === 'INPUT') return;
  if (e.key === 'y' || e.key === 'Y') judge('Y');
  else if (e.key === 'n' || e.key === 'N') judge('N');
  else if (e.key === 'ArrowLeft') step(-1);
  else if (e.key === 'ArrowRight') step(1);
});

loadItems();
</script>
</body>
</html>
"""


def make_handler(csv_path: Path):
    rows = load_rows(csv_path)
    row_by_id = {r["item_id"]: r for r in rows}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # quiet; avoid spamming the terminal for a local single-user tool

        def _send_json(self, obj, status=200):
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
            elif self.path == "/api/items":
                self._send_json(rows)
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path != "/api/judge":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length))
                item_id = payload["item_id"]
                verdict = payload["correct_Y_N"]
                notes = payload.get("notes", "")
                if verdict not in ("Y", "N"):
                    raise ValueError(f"bad verdict {verdict!r}")
                if item_id not in row_by_id:
                    raise KeyError(f"unknown item_id {item_id!r}")
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
                return

            row_by_id[item_id]["correct_Y_N"] = verdict
            row_by_id[item_id]["notes"] = notes
            save_rows(csv_path, rows)  # atomic write-through on every judgment
            self._send_json({"ok": True})

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--csv", default="paper/capstone/gold_audit.csv")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true",
                    help="Don't auto-open a browser tab on startup")
    args = ap.parse_args()

    csv_path = Path(args.csv).resolve()
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    n_rows = len(load_rows(csv_path))
    handler = make_handler(csv_path)
    server = ThreadingHTTPServer(("localhost", args.port), handler)
    url = f"http://localhost:{args.port}"
    print(f"Gold audit webapp: {n_rows} items loaded from {csv_path}")
    print(f"Serving at {url} — writes go straight back to that CSV file.")
    print("Ctrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
