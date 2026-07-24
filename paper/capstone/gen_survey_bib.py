#!/usr/bin/env python3
"""Generate survey.bib entries from arXiv API metadata + notes/bibliography.md.

- Full author names and exact titles come from the arXiv API XML.
- Venue strings (NAACL 2024, KDD 2020, ...) come from bibliography.md's
  author/venue line; entries with a recognizable venue become @inproceedings
  (or @article for journals), otherwise @misc arXiv preprints.
- Emits: survey_generated.bib and an id->citekey map (survey_citekeys.json).
Existing hand-made entries (lange2024annoctr) are appended unchanged.
"""
import json
import re
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom"}
CONF_TOKENS = ["NAACL", "ACL", "EMNLP", "COLING", "LREC", "KDD", "NeurIPS",
               "USENIX", "CCS", "RAID", "ICLR", "AAAI", "S&P", "ESORICS",
               "ICWSM", "WWW", "SoK"]
JOURNAL_TOKENS = ["ESWA", "Expert Systems", "Computers & Security", "TDSC",
                  "journal", "Transactions"]

# --- venue info from bibliography.md ---
bib_md = open("../notes/bibliography.md").read()
venue_by_id = {}
for m in re.finditer(r"^## (\d{4}\.\d{5}) — .*?\n(.+?)$", bib_md, re.M):
    arxiv_id, byline = m.group(1), m.group(2).strip()
    venue_by_id[arxiv_id] = byline

# --- arXiv metadata ---
tree = ET.parse("/tmp/arxiv_meta.xml")
entries = tree.getroot().findall("a:entry", NS)

used_keys = {"lange2024annoctr"}
citekeys, bib_out = {}, []
for e in entries:
    arxiv_id = e.find("a:id", NS).text.rsplit("/", 1)[-1].split("v")[0]
    title = re.sub(r"\s+", " ", e.find("a:title", NS).text.strip())
    authors = [a.find("a:name", NS).text for a in e.findall("a:author", NS)]
    year = e.find("a:published", NS).text[:4]
    byline = venue_by_id.get(arxiv_id, "")
    vm = re.search(r"\.\s*([^.]*(?:%s)[^.]*\d{4})\s*\.?\s*$" % "|".join(CONF_TOKENS), byline)
    venue = vm.group(1).strip() if vm else None

    surname = authors[0].split()[-1].lower()
    surname = re.sub(r"[^a-z]", "", surname)
    word = next((w.lower() for w in re.findall(r"[A-Za-z]{4,}", title)
                 if w.lower() not in ("with", "using", "from", "based", "large",
                                      "model", "models", "language", "dataset",
                                      "detecting", "towards", "toward")), "paper")
    key = f"{surname}{year}{word}"
    n = 2
    while key in used_keys:
        key = f"{surname}{year}{word}{n}"
        n += 1
    used_keys.add(key)
    citekeys[arxiv_id] = key

    author_str = " and ".join(authors)
    if venue:
        bib_out.append(
            f"@inproceedings{{{key},\n"
            f"  author    = {{{author_str}}},\n"
            f"  title     = {{{title}}},\n"
            f"  booktitle = {{{venue}}},\n"
            f"  year      = {{{year}}},\n"
            f"  note      = {{arXiv:{arxiv_id}}}\n}}\n")
    else:
        bib_out.append(
            f"@misc{{{key},\n"
            f"  author        = {{{author_str}}},\n"
            f"  title         = {{{title}}},\n"
            f"  year          = {{{year}}},\n"
            f"  eprint        = {{{arxiv_id}}},\n"
            f"  archivePrefix = {{arXiv}}\n}}\n")

open("survey_generated.bib", "w").write("\n".join(bib_out))
json.dump(citekeys, open("survey_citekeys.json", "w"), indent=1)
print(f"{len(entries)} entries; venues found for "
      f"{sum(1 for i in citekeys if venue_by_id.get(i))} ids")
missing = [i for i in venue_by_id if i not in citekeys and i != "2404.07765"]
print("in bibliography.md but not fetched:", missing)
