# Future work: annotation tooling as a distinct supervision-economics bottleneck

Status: **not part of the submitted capstone** (tagged `capstone-submitted-2026-07-25`).
Captured here for a future iteration — no code or paper changes made beyond this file.

## The theory

The survey states supervision economics are poor because "annotation requires
scarce domain expertise" (`paper/capstone/survey.tex` §2, citing 2404.07765).
Working theory: a *second*, under-examined cause is that annotation **tooling**
itself is inefficient — not just that expertise is scarce, but that the tools
experts use to spend that expertise waste it. Proposed fix pattern: an LLM
does the majority of proposal work (candidate entities/relations), and the
human's job shrinks to fast accept/reject — possibly with a structured reason
code on rejection (wrong span boundary / wrong type / not an entity /
hallucinated / duplicate) — rather than drawing spans and typing labels from
scratch.

## What this project already has

`ner/hitl_ner.py` + `ner/llm_gold.py` already implement a version of this
pattern for NER: Claude proposes gold entities (gated by verbatim-in-document
+ per-label format validator + label-set membership before a human ever sees
them), a human accepts implicitly / rejects explicitly as FP / adds missed
entities or UNK. Real gaps versus the fix pattern as theorized:

- **Binary reject only** — no structured reason-code taxonomy. A rejection
  is stored as `{"text","label","reject":true}` with no *why*.
- **Entities only** — no relation layer, no entity-pair UI, no
  STIX-relationship curation.
- **No closed loop** — rejected FPs and added UNKs feed the gold merge but
  never get mined to revise `GOLD_PROMPT` (contrast with TTPrompt's FIR,
  which automatically refines instructions from ~1% of training-data error
  signal — cited in the survey's TTP-mapping section).

## Landscape findings (from a dedicated research pass, 2026-07-25)

**General NER/span tools**: BRAT and WebAnno are effectively dead (BRAT: last
commit 2021; WebAnno: officially superseded by INCEpTION). INCEpTION, Prodigy,
Label Studio, doccano, and Argilla are all actively maintained as of
mid-2026. Of these, **Prodigy's `ner.llm.correct`** recipe is the closest
shipped match to the theorized pattern — LLM proposes, human fast-accepts —
and **Label Studio's Enterprise "Prompts"** feature does the same at scale
(Enterprise-gated, not core OSS). None of the surveyed tools ship a
structured, categorized rejection-reason field as a first-class UI element.

**CTI-specific annotation tooling**: none exists. Every CTI NER corpus
(AnnoCTR → INCEpTION, APTNER/DNRTI → BRAT, **AttackER → Prodigy with a
two-phase manual-then-model-corrects process**) was annotated in a general
tool. AttackER is the closest real precedent for "model proposes the bulk,
human corrects" *inside CTI NER* — it used a fine-tuned spaCy model as
proposer, not an LLM, but the shape is identical to what `hitl_ner.py` does
with Claude.

**RE annotation, general tools**: BRAT, INCEpTION, WebAnno, Label Studio, and
newer doccano support manual span-to-span relation linking (of varying
maturity). Prodigy's `rel.manual` supports relations but with **zero
model-assistance on the relation step itself** — only the preceding entity
step is LLM-assisted. GATE Teamware explicitly does not handle
relation/coreference annotation well.

**RE-specific tooling**: two dedicated tools exist and both are dormant —
FREDA (arXiv:2204.07150, last GitHub push 2023-05, ~5 stars) and RTE
(arXiv:2108.08184, no evidence of ongoing use). No living state of the art
for RE-specific annotation tooling. No CTI-specific or STIX-relationship
annotation tool exists at all — cyberaCTIve/STIG/KAVAS are downstream
*analysis* tools over already-structured STIX, not annotation tools that
produce STIX relationships from raw text.

**AZERG** (`data/evals/AZERG/`, 2507.16576) is directly relevant local data:
its four-subtask decomposition (entity detection → typing → related-pair
detection → relationship typing) is solved via task-specific fine-tuned LLMs
at *inference* time, not via a human annotation tool — its contribution is
automation of the extraction, not tooling to help a human correct it. Whether
AZERG's own *training* gold was produced with any particular tool was not
confirmed from available web sources (PDF section wasn't fetchable) — verify
directly from the paper before citing either way.

**Closest prior art to the full theorized pattern** (LLM-proposes +
human-reason-coded-reject + closed loop back into the prompt), ranked by
proximity:
1. **AnNER** (K-CAP 2025, ACM) — reviewer mode with accept/reject/revise +
   full provenance tracking; brand new (pushed 2026-06-21, ~1 star),
   unproven, not CTI, no reason-code taxonomy, no closed loop.
2. **"Enhancing LLM-Based Data Annotation with Error Decomposition"**
   (arXiv:2601.11920, 2026) — a reason-code-*like* taxonomy (source ×
   type of disagreement), but for subjective ordinal scoring, not NER/RE.
3. **TTPrompt's FIR** (already cited in the survey) — closes the loop from
   annotation error back into prompt revision, but automatically from
   aggregate error signal, not from a human-facing reason-code UI.

No single system or paper combines all three pieces (NER/RE scope +
human-selected reason-code UI + automatic feedback into re-prompting).

## A real risk to the optimistic framing

Xiao et al. (ACL 2025 Findings) ran a pre-registered study (350 annotators,
7,000 annotations) showing that presenting LLM label suggestions causes
**anchoring bias** — annotators shift toward the suggestion without any
measured speed gain, and downstream eval built on those anchored labels
over-reports model quality. This directly threatens the assumption that
accept/reject is cheaper-and-just-as-good as draw-from-scratch. This
project's generation-time gates (verbatim + validator, filtering bad
proposals *before* a human sees them) are a partial structural defense, but
the human curation pass itself (`hitl_ner.py`'s reject-as-FP flow) has the
same exposure the ACL paper warns about, and it has never been measured for
anchoring in this project.

## Sharpened research question

> For CTI-specific entity and relation annotation, does replacing free-text
> human rejection with a small, closed rejection-reason taxonomy
> (wrong-span-boundary / wrong-type / not-an-entity / hallucinated /
> duplicate-mention) — fed back automatically into the next annotation-prompt
> revision — measurably reduce annotator time-per-document and/or improve
> downstream model F1, relative to the binary accept/reject curation this
> project (and Prodigy's `ner.llm.correct`) already implements? And does
> extending the same pattern to relation curation close the gap AZERG
> exposes (automation exists, no human correction tool does)?

This framing: (a) doesn't claim tooling is *the* bottleneck — expertise
scarcity stays structurally binding, since reason-coding still needs a CTI
expert to make the call; (b) states the counterfactual precisely against this
project's own tool and against Prodigy, so it isn't dismissible as
already-solved; (c) is empirically testable within this project's existing
infrastructure (`hitl_ner.py` could be instrumented with a reason-code field
and timed against the current binary version); (d) explicitly extends into
the RE gap, the more clearly unaddressed half of the theory; and (e) should
address the anchoring-bias risk directly rather than assume it away.

## If picked up later

Cheapest concrete next step: add a reason-code field to `hitl_ner.py`'s
reject action (small UI + schema change, no new infra), and instrument
timing per curation decision. That alone produces the data needed to test
the RQ's first half without committing to a full formal user study up front.
