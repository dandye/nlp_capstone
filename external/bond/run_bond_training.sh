#!/bin/bash
set -e

# BOND two-stage training on the distant-supervision weak labels.
#   Stage I  — fit roberta-base to the noisy distant labels (early-stopping regime)
#   Stage II — self-train with soft teacher pseudo-labels to denoise
#
# Uses a BOND-local venv (external/bond/.venv), NOT the shared .venv-ml.
# The ported code subclasses transformers internals in ways only compatible
# with transformers==4.46.3 (confirmed: 5.13+ renames an attribute BOND's
# RobertaForTokenClassification_v2 subclass depends on, breaking model load).
# gliner (also in .venv-ml, used by the other 4 architectures) requires
# transformers>=4.51.3 — the two floors are irreconcilable in one venv, so
# BOND gets its own, exactly like the sibling scrape_cisa project did for the
# same reason. Set up with:
#   python3.12 -m venv external/bond/.venv
#   external/bond/.venv/bin/pip install "torch>=2.2" "transformers==4.46.3" "tensorboardX>=2.6"
#
# self_training_begin_step scaling (mirrors the reference ~epoch-8 rule):
#   train sentences = 1885 (convert_distant.py), effective batch = 64
#   steps/epoch = ceil(1885 / 64) = 30
#   begin at ~epoch 8 -> 8 * 30 = 240
# Recompute and update this value if the distant dataset's train size changes.
#
# --no_cuda forces CPU. Confirmed via bisection: training on MPS silently
# corrupts weights to NaN by global_step=2 regardless of attention backend
# (eager vs SDPA) or AdamW's foreach/non-foreach path — both ruled out by
# direct gradient-level instrumentation (gradients were finite going into
# optimizer.step(); the corruption happens inside it, MPS-only). CPU training
# with the identical config completes cleanly (Stage I test F1 0.7212, on
# par with the original scrape_cisa run's 0.7208). Slower, but correct.

BOND_DIR="$(cd "$(dirname "$0")" && pwd)"     # .../external/bond
VENV="$BOND_DIR/.venv/bin/python3"

cd "$BOND_DIR/ported"

echo "════════════════════════════════════════════════════════════════"
echo "BOND Training — Stage I + Stage II (distant CTI labels)"
echo "════════════════════════════════════════════════════════════════"

TRAIN_COMMON="--data_dir ../dataset/cti_distant/ \
  --model_type roberta --model_name_or_path roberta-base \
  --learning_rate 1e-5 --weight_decay 1e-4 \
  --adam_epsilon 1e-8 --adam_beta1 0.9 --adam_beta2 0.98 \
  --warmup_steps 200 \
  --per_gpu_train_batch_size 64 --per_gpu_eval_batch_size 64 \
  --logging_steps 100 --save_steps 100000 --no_cuda \
  --do_train --do_eval --do_predict --evaluate_during_training \
  --cache_dir ../pretrained_model \
  --seed 0 --max_seq_length 256 --overwrite_output_dir"

echo ""
echo "Stage I: RoBERTa baseline (25 epochs)"
echo "────────────────────────────────────────────────────────────────"
$VENV run_ner.py \
  $TRAIN_COMMON \
  --num_train_epochs 25 \
  --output_dir ../outputs/cti_baseline

echo ""
echo "✅ Stage I complete"
echo ""
echo "Stage II: BOND self-training (20 epochs)"
echo "────────────────────────────────────────────────────────────────"
$VENV run_self_training_ner.py \
  $TRAIN_COMMON \
  --num_train_epochs 20 \
  --output_dir ../outputs/cti_bond \
  --self_training_reinit 0 --self_training_begin_step 240 \
  --self_training_label_mode soft --self_training_period 100 \
  --self_training_hp_label 7.9

echo ""
echo "✅ Stage II complete"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Stage I test results:"
cat ../outputs/cti_baseline/test_results.txt
echo ""
echo "✅ BOND training finished at $(date)"
