# Rescoring existing checkpoints against LLM gold (Step 2, 2026-07-19)

Checkpoints trained on the OLD dictionary-ensemble silver labels, rescored
against the human-reviewed LLM gold on the 2 pilot test docs
(aa25-163a, aa23-352a; 3rd pilot doc aa23-284a is val).

## Headline — honest gold FLIPS the model ranking

| Model | vs. old silver gold (full test) | vs. LLM gold (pilot) |
|---|---|---|
| RoBERTa-base | **0.740** F1 (P 0.91 / R 0.62) | 0.382 F1 (P 0.83 / R 0.25) |
| SecureBERT | **0.755** F1 (P 0.90 / R 0.65) | 0.441 F1 (P 0.81 / R 0.30) |
| GLiNER fine-tuned | 0.666 F1 (P 0.62 / R 0.71) | **0.534** F1 (P 0.64 / R 0.46) |

Under circular silver eval, the RoBERTa family led by 7-9 points. Against
independent gold, GLiNER fine-tuned leads by 9-15 points — its recall (0.46)
is nearly double RoBERTa-base's (0.25). The mechanism is exactly GLiNER's
architectural thesis: span-matching against label NAMES retains zero-shot
generalization to entity classes the training labels never covered (products,
actors, tools), while a per-label softmax head can only ever predict classes
it saw supervised examples for. The capstone's §RQ2 architecture comparison
inverts once measurement is honest — and both findings (the RoBERTa
zero-prediction labels AND this flip) are two views of the same phenomenon.

RoBERTa-family precision holds (~0.83 — consistent with the human audit's
0.68 on harder, audit-sampled spans). Recall collapses 0.62 → 0.25.

## Why (per-label, RoBERTa-base)

Dictionary-taught structured types: still excellent against independent gold —
attack technique id 1.00, tlp 1.00, cve 0.93, file hash 0.81.

Dictionary-blind semantic types: total zero — affected software product (n=40),
tactic (27), attack technique name (16), file name (12), file path (9),
email address (6), threat actor group (6): all F1 0.00. malware family 0.05
(old labels also taught tools-as-malware, so what it learned is misaligned).

## Interpretation (paper-ready)

The old 0.74 was measured against gold that shares the training labels' blind
spots — circular evaluation. Against independently produced gold, the same
checkpoint scores 0.38. The model didn't get worse; the measurement got honest.
This is the quantified version of the audit's 50% gold-recall-gap finding, and
the strongest motivation for the LLM-gold retraining round (Steps 4-5).

Caveat: pilot = 2 docs / 244 gold spans; treat as directional until the full
16-doc eval set is scored.

## UPDATE — full 16-doc gold eval (3,935 spans; 8 test docs scored)

The pilot pattern holds at full scale; the flip is confirmed:

| Model | Old circular eval | Full honest gold eval |
|---|---|---|
| RoBERTa-base | 0.740 | 0.351 (P 0.86 / R 0.22) |
| SecureBERT | 0.755 | 0.393 (P 0.87 / R 0.25) |
| GLiNER fine-tuned | 0.666 | **0.540** (P 0.65 / R 0.46) |

GLiNER leads by 15 points against honest gold. The eval set is also 3.5x
richer than the old silver test set (3,935 vs 1,139 spans) with semantic
classes represented that the old gold structurally omitted.

These are the pre-retraining baselines the LLM-gold-trained models
(Step 5) need to beat.
