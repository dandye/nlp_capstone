"""
Distant-supervision weak labeler for the CTI NER pipeline.

Produces NOISY, low-precision entity labels for the BOND baseline (Stage I
fits these weak labels; Stage II self-trains to denoise them). This is the
"noisy weak supervision" arm of RQ1 — the contrast against the clean,
human-curated LLM gold. It is expected and scientifically honest that some
label types come out sparse or empty here: distant supervision only fires
where a mechanical rule or a dictionary hits.

Three sources, mapped onto the current 16-label schema
(ner.frontier_llm_utils.LABELS):

  1. Regex pass over the clean text tokens:
       cve identifier, cwe identifier, attack technique id (T####/TA####),
       tlp classification, file hash (MD5/SHA1/SHA256/SHA512 by length),
       ip address (incl. defanged 1[.]2[.]3[.]4), email address (incl.
       defanged), file path (Unix/Windows), file name (known extensions),
       yara rule name (`rule <Name>` syntax).
     Structured types are gated through ner.span_validators.validate() at
     generation time, so every structured weak label passes the exact same
     grammar the evaluator uses.

  2. MITRE ATT&CK enterprise gazetteer (the GLOBAL enterprise-attack.json
     bundle, cached once to data/mitre-attack.json — this project has NO
     per-advisory STIX bundles, so gazetteer + regex + title are the only
     signals available, a deliberately weaker footprint than a STIX-backed
     pipeline; that is a documented limitation, not a bug):
       intrusion-set -> threat actor group
       tool          -> hacking tool
       malware       -> malware family
       attack-pattern technique IDs -> attack technique id
                        (deduped against the regex T-code matches)
     with the same min-length / stopword false-positive guards the
     scrape_cisa mitre_lookup used.

  3. meta.json `title` -> a primary malware/campaign candidate
     (e.g. "Hunting Russian Intelligence 'Snake' Malware" -> "Snake"),
     best-effort, low precision — this is distant supervision.

Deliberately left SPARSE (no reliable distant source, so no low-precision
guessing): `affected software product`, `attack technique name`, `tactic`.
Their near-zero coverage in --stats is expected.

Overlapping matches resolve longest-span-first (same policy as the LLM-gold
converter ner.gold_to_training and the old scrape_cisa convert_cisa).

Pure CPU module — stdlib + `requests` (with a urllib fallback) for the
one-time bundle download. It does NOT require the ML venv.

Usage:
    PYTHONPATH=. python3 -m ner.distant_labels --output data/gold_v2/distant.jsonl
    PYTHONPATH=. python3 -m ner.distant_labels --slugs aa23-129a,aa25-163a --stats

Default slug set: every advisory under --alerts-dir that has a *.clean.md,
EXCEPT the val + test slugs listed in --split-file (never held-out gold).
Output JSONL shape is identical to data/gold_v2/eval.jsonl:
    {"slug", "chunk_start", "tokenized_text": [...],
     "ner": [[start_tok, end_tok_inclusive, label], ...]}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from .annotation_text import find_token_span, split_into_chunks, tokenize
from .frontier_llm_utils import LABELS, load_clean_text
from .span_validators import validate

# ── Canonical label constants (all present in frontier_llm_utils.LABELS) ─────
LBL_CVE = "cve identifier"
LBL_CWE = "cwe identifier"
LBL_TID = "attack technique id"
LBL_TLP = "tlp classification"
LBL_HASH = "file hash"
LBL_IP = "ip address"
LBL_EMAIL = "email address"
LBL_FILEPATH = "file path"
LBL_FILENAME = "file name"
LBL_YARA = "yara rule name"
LBL_ACTOR = "threat actor group"
LBL_TOOL = "hacking tool"
LBL_MALWARE = "malware family"

# Structured labels gated by span_validators.validate(); order = first-match
# priority when scanning a single token. Grammars are mutually exclusive
# enough that order rarely matters, but it is fixed for determinism.
_STRUCTURED_LABELS = (
    LBL_HASH, LBL_IP, LBL_EMAIL, LBL_CVE, LBL_CWE, LBL_TID, LBL_TLP,
)

_LABEL_SET = frozenset(LABELS)

# ── Token punctuation stripping (mirrors annotation_text.find_token_span) ────
_STRIP = ".,;:!?\"'()[]{}<>"

# ── File path / file name / yara regexes (adapted from annotate_iocs) ────────
_UNIX_PATH_RE = re.compile(
    r"^/(?:usr|bin|etc|var|tmp|proc|sys|opt|home|root|lib|sbin|run|dev)/\S+"
)
_WIN_PATH_RE = re.compile(r"^[A-Za-z]:\\\S+")

_FILE_EXTS = (
    "exe", "dll", "ps1", "psm1", "bat", "cmd", "vbs", "vbe", "js", "jse",
    "jar", "py", "sh", "scr", "sys", "bin", "dat", "db", "tmp", "zip", "rar",
    "7z", "gz", "tar", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "pdf",
    "rtf", "lnk", "hta", "cpl", "msi", "msc", "reg", "elf", "so", "apk",
    "dmg", "iso", "img", "ova", "conf", "ini", "yar", "yara",
)
_FILENAME_RE = re.compile(
    r"^[\w][\w.\-]*\.(?:" + "|".join(_FILE_EXTS) + r")$", re.IGNORECASE
)
_YARA_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{4,}$")

# ── MITRE ATT&CK gazetteer config (ported from scrape_cisa mitre_lookup) ─────
ENTERPRISE_URL = (
    "https://raw.githubusercontent.com/mitre/cti/master/"
    "enterprise-attack/enterprise-attack.json"
)

# MITRE type -> our 16-label name.
_MITRE_TYPE_TO_LABEL = {
    "intrusion-set": LBL_ACTOR,
    "tool": LBL_TOOL,
    "malware": LBL_MALWARE,
}
_MITRE_MIN_LEN = {LBL_ACTOR: 3, LBL_TOOL: 3, LBL_MALWARE: 3, LBL_TID: 5}

# Common tokens that generate too many false positives (from mitre_lookup;
# curated by the wordlist x doc-frequency screen — 'Page'/'Expand' skipped,
# real subjects like 'Snake'/'Play'/'MEDUSA' deliberately kept).
_SKIP_VALUES = {
    "net", "at", "cmd", "ps", "sh", "reg", "sc", "wmic", "route", "ipconfig",
    "ping", "kill", "id", "pass", "page", "expand",
}

# Trailing advisory-title noise words to strip when mining a malware name.
_TITLE_NOISE_RE = re.compile(
    r"\s*(Backdoor|Malware|Analysis\s+Report|Trojan|Rootkit|Ransomware|Worm|RAT)\b.*",
    re.IGNORECASE,
)


# ── Regex / structured extraction ────────────────────────────────────────────

def _norm(tok: str) -> str:
    """Lowercase + strip wrapping punctuation, matching find_token_span."""
    return tok.lower().strip(_STRIP)


def _structured_label(token: str) -> "str | None":
    """Return the structured label whose grammar this single token satisfies,
    or None. span_validators.validate is the authority (it refangs defanged
    forms and strips wrapping punctuation), so every hit is guaranteed to pass
    the evaluator's grammar too."""
    for label in _STRUCTURED_LABELS:
        if validate(label, token):
            return label
    return None


def _path_or_filename_label(token: str) -> "str | None":
    """file path (Unix/Windows) or file name (known extension), else None."""
    stripped = token.strip(_STRIP)
    if _UNIX_PATH_RE.match(stripped) or _WIN_PATH_RE.match(stripped):
        return LBL_FILEPATH
    if len(stripped) >= 4 and _FILENAME_RE.match(stripped):
        return LBL_FILENAME
    return None


def _regex_spans(tokens: list) -> list:
    """Per-token structured + path/filename + yara spans. Each token owns its
    index, so spans are exact (start == end for these single-token types)."""
    spans = []
    n = len(tokens)
    for i, tok in enumerate(tokens):
        label = _structured_label(tok)
        if label is None:
            label = _path_or_filename_label(tok)
        if label is not None:
            spans.append((i, i, label))
            continue
        # yara rule name: `rule <Name>` — label the identifier after `rule`
        if _norm(tok) == "rule" and i + 1 < n:
            cand = tokens[i + 1].strip(_STRIP)
            if _YARA_NAME_RE.match(cand):
                spans.append((i + 1, i + 1, LBL_YARA))
    return spans


# ── MITRE ATT&CK gazetteer ───────────────────────────────────────────────────

def _download(url: str) -> bytes:
    try:
        import requests
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        return resp.content
    except ImportError:
        import urllib.request
        with urllib.request.urlopen(url, timeout=120) as r:  # noqa: S310
            return r.read()


def load_mitre_bundle(cache_path: Path) -> dict:
    """Load the cached enterprise-attack bundle, downloading (~15 MB) once."""
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    print(f"downloading MITRE ATT&CK enterprise bundle -> {cache_path}",
          file=sys.stderr)
    data = _download(ENTERPRISE_URL)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(data)
    return json.loads(data)


def build_gazetteer(bundle: dict) -> dict:
    """Return {normalized_first_token: [(alias_norm_tokens, label), ...]}.

    Aliases are keyed by their first normalized token for a single-pass
    sliding match. min-length + stopword guards mirror mitre_lookup."""
    index: dict = {}
    seen: set = set()

    def add(value: str, label: str) -> None:
        value = value.strip()
        if not value or value.lower() in _SKIP_VALUES:
            return
        if len(value) < _MITRE_MIN_LEN.get(label, 1):
            return
        norm_toks = tuple(_norm(t) for t in tokenize(value))
        norm_toks = tuple(t for t in norm_toks if t)
        if not norm_toks:
            return
        key = (label, norm_toks)
        if key in seen:
            return
        seen.add(key)
        index.setdefault(norm_toks[0], []).append((norm_toks, label))

    for obj in bundle.get("objects", []):
        if obj.get("x_mitre_deprecated") or obj.get("revoked"):
            continue
        otype = obj.get("type", "")
        label = _MITRE_TYPE_TO_LABEL.get(otype)
        if label is not None:
            name = obj.get("name") or ""
            if name:
                add(name, label)
            alias_field = "aliases" if otype == "intrusion-set" else "x_mitre_aliases"
            for alias in obj.get(alias_field, []) or []:
                add(alias, label)
        elif otype == "attack-pattern":
            for ref in obj.get("external_references", []) or []:
                if ref.get("source_name") == "mitre-attack":
                    ext_id = ref.get("external_id")
                    if ext_id:
                        add(ext_id, LBL_TID)
    return index


def _gazetteer_spans(tokens: list, gazetteer: dict) -> list:
    """Single-pass sliding match of gazetteer aliases against doc tokens."""
    norm = [_norm(t) for t in tokens]
    n = len(tokens)
    spans = []
    for i in range(n):
        candidates = gazetteer.get(norm[i])
        if not candidates:
            continue
        for alias_toks, label in candidates:
            m = len(alias_toks)
            if i + m <= n and norm[i:i + m] == list(alias_toks):
                spans.append((i, i + m - 1, label))
    return spans


# ── meta.json title mining ───────────────────────────────────────────────────

def _title_spans(slug_dir: Path, tokens: list) -> list:
    """Best-effort primary malware/campaign name from the advisory title."""
    meta_path = slug_dir / "meta.json"
    if not meta_path.exists():
        return []
    try:
        title = (json.loads(meta_path.read_text(encoding="utf-8")).get("title")
                 or "")
    except (json.JSONDecodeError, OSError):
        return []
    # Prefer a quoted codename if present ("...'Snake' Malware" -> Snake).
    quoted = re.findall(r"['‘’“”\"]([A-Za-z0-9][\w \-]{1,40}?)['‘’“”\"]", title)
    candidate = quoted[0].strip() if quoted else _TITLE_NOISE_RE.sub("", title).strip()
    if len(candidate) < 3:
        return []
    return [(s, e, LBL_MALWARE) for s, e in find_token_span(tokens, candidate)]


# ── Per-slug orchestration ───────────────────────────────────────────────────

def label_slug(slug: str, alerts_dir: Path, gazetteer: dict) -> "tuple[list, list]":
    """Return (records, doc_level_spans) for one advisory.

    records match eval.jsonl's shape; doc_level_spans are the deduped
    doc-level (start, end, label) triples for honest per-label stats."""
    text = load_clean_text(slug, alerts_dir)
    if not text:
        raise FileNotFoundError(f"no clean text for {slug}")
    tokens = tokenize(text)

    candidates = (
        _regex_spans(tokens)
        + _gazetteer_spans(tokens, gazetteer)
        + _title_spans(alerts_dir / slug, tokens)
    )

    # Longest-span-first conflict resolution (ties: earliest start, then label).
    all_spans = []
    occupied: set = set()
    for start, end, label in sorted(
        candidates, key=lambda s: (-(s[1] - s[0]), s[0], s[2])
    ):
        if label not in _LABEL_SET:
            continue
        if any(i in occupied for i in range(start, end + 1)):
            continue
        occupied.update(range(start, end + 1))
        all_spans.append((start, end, label))

    records = []
    for chunk_start, chunk_tokens in split_into_chunks(tokens):
        lo, hi = chunk_start, chunk_start + len(chunk_tokens)
        ner = [
            [s - lo, e - lo, label]
            for s, e, label in all_spans
            if s >= lo and e < hi
        ]
        records.append({
            "slug": slug,
            "chunk_start": chunk_start,
            "tokenized_text": chunk_tokens,
            "ner": sorted(ner),
        })
    return records, all_spans


# ── Slug discovery ───────────────────────────────────────────────────────────

def discover_slugs(alerts_dir: Path, held_out: set) -> list:
    """Every slug dir with a *.clean.md, minus the held-out (val+test) slugs."""
    return sorted(
        d.name for d in alerts_dir.iterdir()
        if d.is_dir() and d.name not in held_out and any(d.glob("*.clean.md"))
    )


def load_held_out(split_file: Path) -> set:
    split = json.loads(split_file.read_text(encoding="utf-8"))
    return set(split.get("val", [])) | set(split.get("test", []))


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--output", default="data/gold_v2/distant.jsonl")
    ap.add_argument("--alerts-dir", default="data/alerts")
    ap.add_argument("--split-file", default="data/gold_v2/split_full.json")
    ap.add_argument("--mitre-cache", default="data/mitre-attack.json")
    ap.add_argument("--slugs", default=None,
                    help="Comma-separated; default = all clean.md slugs minus val+test")
    ap.add_argument("--stats", action="store_true",
                    help="Print per-label entity counts")
    args = ap.parse_args()

    alerts_dir = Path(args.alerts_dir)
    held_out = load_held_out(Path(args.split_file))
    if args.slugs:
        slugs = [s.strip() for s in args.slugs.split(",") if s.strip()]
    else:
        slugs = discover_slugs(alerts_dir, held_out)

    gazetteer = build_gazetteer(load_mitre_bundle(Path(args.mitre_cache)))
    n_aliases = sum(len(v) for v in gazetteer.values())
    print(f"gazetteer: {n_aliases} aliases; {len(slugs)} slugs "
          f"({len(held_out)} held-out excluded)", file=sys.stderr)

    all_records = []
    label_counts: Counter = Counter()
    total_entities = 0
    for slug in slugs:
        records, doc_spans = label_slug(slug, alerts_dir, gazetteer)
        all_records.extend(records)
        for _s, _e, label in doc_spans:
            label_counts[label] += 1
        total_entities += len(doc_spans)
        print(f"  {slug}: {len(records)} chunks, {len(doc_spans)} entities",
              file=sys.stderr)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r) + "\n")

    print(f"\nwrote {len(all_records)} records ({total_entities} entities, "
          f"{len(slugs)} docs) -> {out}", file=sys.stderr)

    if args.stats:
        print("\nper-label entity counts (doc-level, deduped):", file=sys.stderr)
        for label in LABELS:
            n = label_counts.get(label, 0)
            flag = "  <-- near-zero (expected: no distant source)" if n <= 2 else ""
            print(f"  {label:28s} {n:6d}{flag}", file=sys.stderr)


if __name__ == "__main__":
    main()
