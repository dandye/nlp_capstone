#!/usr/bin/env python3
"""RETIRED (2026-07-24): survey.tex is now hand-edited; survey.md is deprecated.
Running this would clobber hand edits. Kept for provenance only.

Convert survey.md to survey.tex (acmart sigconf,nonacm, matching capstone.tex).

One-shot conversion helper. Citation keys stay inline as arXiv IDs per the
draft's own editorial plan (bib formatting is a later phase).
"""
import re
import sys
sys.exit("RETIRED: survey.tex is hand-edited now; this script would clobber it.")

SRC = "survey.md"
DST = "survey.tex"


def esc(s: str) -> str:
    s = s.replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")
    s = s.replace("_", r"\_")
    s = s.replace("≈", r"$\approx$")
    s = s.replace("−", "$-$")   # − minus sign
    s = s.replace("×", r"$\times$")
    s = s.replace("→", r"$\rightarrow$")
    s = s.replace("≤", r"$\leq$").replace("≥", r"$\geq$")
    s = s.replace("~", r"$\sim$")
    s = s.replace("<", r"$<$").replace(">", r"$>$")
    def _code(m):
        inner = m.group(1)
        if "/" in inner or inner.count(".") >= 1:
            return "\\path{%s}" % inner.replace("\\_", "_")
        return "\\texttt{%s}" % inner
    s = re.sub(r"`([^`]+)`", _code, s)
    # bare URLs/paths in prose and table cells: make them breakable
    s = re.sub(r"(?<![{\w])((?:github\.com|zenodo\.org|hf\.co|huggingface\.co)/[\w./\\-]+)",
               lambda m: "\\path{%s}" % m.group(1).replace("\\_", "_"), s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"\*([^*]+)\*", r"\\emph{\1}", s)
    return s


PREAMBLE = r"""\pdfoutput=1
\documentclass[sigconf,nonacm]{acmart}
\settopmatter{printfolios=true}

\title{Named Entity Recognition for Information Security and Cyber Threat
Intelligence: A Survey}
\titlenote{Complete draft v1.0. All 41 corpus papers read and synthesized.
Citation keys are arXiv identifiers (plus one DOI); all resolve to entries in
the repository's \texttt{notes/bibliography.md}. Next editorial phase:
principal review, citation formatting.}

\author{Daniel Dye}
\affiliation{%
  \institution{Bellini College of Artificial Intelligence, Cybersecurity, and Computing, University of South Florida}
  \city{Tampa}
  \state{Florida}
  \country{USA}}
\email{ddye@usf.edu}

\begin{document}
\sloppy
% displaCy-style inline entity annotation: highlighted span + small-caps label
\newcommand{\ent}[3]{\colorbox{#1}{\strut #2\,{\tiny\textsc{#3}}}}
"""

CORPUS_TABLE = r"""\begin{table*}[t]
\centering
\footnotesize
\begin{tabular}{p{3.4cm}p{2.7cm}p{2.4cm}p{2.6cm}p{1.8cm}p{3.2cm}}
\toprule
%s
\bottomrule
\end{tabular}
\caption{CTI NER corpora. First-generation corpora are characterized by
small document counts, custom schemas, and absent or unclear licensing;
second-generation corpora optimize legal reusability, interoperability, and
evaluation realism.}
\label{tab:corpora}
\end{table*}
"""

ARTIFACT_TABLE = r"""\begin{table*}[t]
\centering
\footnotesize
\begin{tabular}{p{4.2cm}p{2.6cm}p{7.2cm}p{2.2cm}}
\toprule
%s
\bottomrule
\end{tabular}
\caption{Reproducibility index for method and dataset papers (gates baseline
selection; ``none'' = no release found in source text, verify before
excluding).}
\label{tab:artifacts}
\end{table*}
"""


def table_rows(buf):
    rows = []
    for i, line in enumerate(buf):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue  # separator row
        cells = [esc(c) for c in cells]
        row = " & ".join(cells) + r" \\"
        rows.append(row)
        if i == 0:
            rows.append(r"\midrule")
    return "\n".join(rows)


out = [PREAMBLE]
lines = open(SRC).read().split("\n")
i = 0
table_idx = 0
in_abstract = False
while i < len(lines):
    line = lines[i]
    if line.startswith("# "):  # document title, already in preamble
        i += 1
        continue
    if line.startswith("**Status:"):  # status note, already a titlenote
        i += 1
        continue
    if line.startswith("## Abstract"):
        in_abstract = True
        out.append("\\begin{abstract}")
        i += 1
        continue
    if line.startswith("## ") and in_abstract:
        in_abstract = False
        out.append("\\end{abstract}\n\\maketitle")
        # fall through to section handling
    if line.startswith("## Appendix"):
        title = re.sub(r"^## Appendix [A-Z]\.\s*", "", line)
        out.append("\\appendix\n\\section{%s}" % esc(title))
        i += 1
        continue
    if line.startswith("## References"):
        out.append("\\section*{References}")
        i += 1
        continue
    if line.startswith("## "):
        title = re.sub(r"^## (\d+\.\s*)?", "", line)
        out.append("\\section{%s}" % esc(title))
        i += 1
        continue
    if line.startswith("### "):
        title = re.sub(r"^### (\d+\.\d+\s*)?", "", line)
        out.append("\\subsection{%s}" % esc(title))
        i += 1
        continue
    if line.strip() == "<!--latex":
        i += 1
        while i < len(lines) and lines[i].strip() != "-->":
            out.append(lines[i])
            i += 1
        i += 1  # skip closing -->
        continue
    if line.startswith("|"):
        buf = []
        while i < len(lines) and lines[i].startswith("|"):
            buf.append(lines[i])
            i += 1
        tmpl = CORPUS_TABLE if table_idx == 0 else ARTIFACT_TABLE
        out.append(tmpl % table_rows(buf))
        table_idx += 1
        continue
    out.append(esc(line))
    i += 1

out.append("\\end{document}")
open(DST, "w").write("\n".join(out) + "\n")
print(f"wrote {DST}, {table_idx} tables")
