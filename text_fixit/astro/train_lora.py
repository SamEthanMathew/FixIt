#!/usr/bin/env python
"""
Stage 4 of ASTRO (arXiv:2507.00417 sec.3.1): supervised fine-tuning on the search traces, as LoRA.

WHERE THIS FOLLOWS ASTRO AND WHERE IT CANNOT
--------------------------------------------
ASTRO sec.3.1 / Appendix B.2 does a FULL fine-tune of llama-3.1-70b-instruct: one epoch, AdamW,
initial LR 3e-6 with a cosine schedule, max sequence length 8192, "train on all tokens from each
example without any masking", 64 H100s for 40 minutes.

Three of those do not transfer, and the reasons matter:

  ONE EPOCH, COSINE, ADAMW -- kept. ASTRO trains one epoch deliberately, "to provide a better
    initialization for the RL stage" rather than to maximise SFT accuracy. That is exactly our
    intent too, so the schedule carries over unchanged.

  LR 3e-6 -- NOT kept; default 1e-4. 3e-6 is a full-finetune learning rate. LoRA updates a rank-16
    adapter whose B matrix starts at zero, and at 3e-6 it would barely move in one epoch. LoRA
    practice is 1e-4 to 2e-4, which is where the default sits. This is the single largest
    deviation from the paper's hyperparameters and it is forced by the method, not a preference.

  NO MASKING -- NOT kept by default; the loss is computed on the completion only. ASTRO's prompt is
    a short math question, so training on it is nearly free. Ours is a ~2,800-token system prompt
    that is IDENTICAL in every example of the dataset. Training on it would let boilerplate
    dominate the loss and teach the model to reproduce its own instructions. `--astro-no-masking`
    restores the paper's behaviour for an ablation.

  MAX SEQ LEN 8192 -- reduced to 4096. Measured over 1,153 real text turns from the search runs:
    p50 2,827, p99 3,107, max 3,293 prompt tokens, plus at most 283 completion tokens. 4096 covers
    the observed maximum with headroom; 8192 would just pad. (The image modality measures p99
    3,988 / max 4,089, so --max-length 5120 covers it when that arm is built.)

LORA TARGETING -- THE ONE THING NOT TO GET WRONG
------------------------------------------------
`target_modules="all-linear"` would adapt the VISION TOWER as well, which re-enables its activation
graph, costs several GB, and destabilises features that no amount of our data can re-learn. The
modules are therefore enumerated explicitly: every nn.Linear under the LANGUAGE model, and nothing
under the visual one. They are DERIVED from the loaded model rather than hardcoded, so a change in
Qwen's module naming surfaces as an empty-target error instead of a silent no-op, and
`--print-targets` shows exactly what would be adapted without allocating a single weight.

    # inspect only -- no GPU, no training, no weights loaded
    python text_fixit/astro/train_lora.py --print-targets

    # required sanity gate before any real run: 32 examples must reach ~0 loss
    python text_fixit/astro/train_lora.py --data data/sft/astro_train.jsonl --overfit 32

    # the real run
    python text_fixit/astro/train_lora.py --data data/sft/astro_train.jsonl \
        --out runs_sft/astro_qwen8_text
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

DEFAULT_MODEL = os.environ.get("QWEN_MODEL", "Qwen/Qwen3-VL-8B-Instruct")

# Names of the projection layers we adapt, matched only under the language model.
LLM_LINEAR_SUFFIXES = ("q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj")
# Any module path containing one of these is part of the vision stack and must stay frozen.
VISION_MARKERS = ("visual", "vision_tower", "vision_model", "image_encoder", "merger")


# ---------------------------------------------------------------- model / targets

def load_model(model_id, dtype="bfloat16", attn="sdpa", meta=False):
    """Load the VLM. `meta=True` builds it on the meta device: structure only, no memory."""
    import torch
    from transformers import AutoConfig, AutoModelForImageTextToText

    if meta:
        from accelerate import init_empty_weights
        cfg = AutoConfig.from_pretrained(model_id, trust_remote_code=False)
        with init_empty_weights():
            return AutoModelForImageTextToText.from_config(cfg)
    return AutoModelForImageTextToText.from_pretrained(
        model_id, dtype=getattr(torch, dtype), attn_implementation=attn, device_map=None)


def lora_targets(model):
    """Every nn.Linear under the language model, by module-path suffix. Vision stack excluded.

    Returns (sorted unique suffixes, n_matched, n_vision_skipped). An empty result is an error the
    caller must surface: it means Qwen renamed its projections and a LoRA built from it would train
    nothing while reporting success.
    """
    import torch.nn as nn
    hit, skipped, names = set(), 0, []
    for name, mod in model.named_modules():
        if not isinstance(mod, nn.Linear):
            continue
        if any(m in name for m in VISION_MARKERS):
            skipped += 1
            continue
        leaf = name.rsplit(".", 1)[-1]
        if leaf in LLM_LINEAR_SUFFIXES:
            hit.add(leaf)
            names.append(name)
    return sorted(hit), len(names), skipped


def freeze_vision(model):
    """Belt and braces: even with vision modules outside target_modules, drop their grads."""
    n = 0
    for name, p in model.named_parameters():
        if any(m in name for m in VISION_MARKERS):
            p.requires_grad_(False)
            n += 1
    return n


# ---------------------------------------------------------------- data

def load_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f]


def to_dataset(rows, drop_meta=True):
    """TRL prompt-completion conversational dataset.

    `meta` is dropped: TRL infers the dataset type from the columns present, and an extra one both
    confuses that inference and is passed through to the collator.
    """
    from datasets import Dataset
    keep = [{"prompt": r["prompt"], "completion": r["completion"]} for r in rows] if drop_meta \
        else rows
    return Dataset.from_list(keep)


def split_by_base(rows, val_frac=0.05, seed=0):
    """Hold out whole SHAPES for the validation loss, never individual turns.

    Turns from one trace share a prompt prefix and turns from one shape share its geometry, so a
    random split would put near-duplicates on both sides and report a validation loss that only
    measures memorisation. This is the same by-shape protocol the held-out benchmark uses.
    """
    bases = sorted({r["meta"]["base"] for r in rows})
    rng = random.Random(seed)
    rng.shuffle(bases)
    n_val = max(1, int(len(bases) * val_frac)) if len(bases) > 1 else 0
    val_bases = set(bases[:n_val])
    train = [r for r in rows if r["meta"]["base"] not in val_bases]
    val = [r for r in rows if r["meta"]["base"] in val_bases]
    return train, val, sorted(val_bases)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--data", default="data/sft/astro_train.jsonl")
    ap.add_argument("--out", default="runs_sft/astro_qwen8_text")
    ap.add_argument("--print-targets", action="store_true",
                    help="list the LoRA target modules and exit; no weights are allocated")
    ap.add_argument("--overfit", type=int, default=0,
                    help="train on N examples only, for the loss->0 sanity gate")

    # --- ASTRO sec.3.1 / Appendix B.2, with the deviations documented in the module docstring
    ap.add_argument("--epochs", type=float, default=1.0, help="ASTRO: one epoch")
    ap.add_argument("--lr", type=float, default=1e-4, help="LoRA scale; ASTRO's 3e-6 is full-FT")
    ap.add_argument("--scheduler", default="cosine", help="ASTRO: cosine")
    ap.add_argument("--warmup-ratio", type=float, default=0.03)
    ap.add_argument("--max-length", type=int, default=4096,
                    help="measured max real text turn is 3,293 prompt + 283 completion tokens")
    ap.add_argument("--astro-no-masking", action="store_true",
                    help="ASTRO trains on ALL tokens; default here is completion-only loss")

    # --- LoRA
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--lora-alpha", type=int, default=32)
    ap.add_argument("--lora-dropout", type=float, default=0.05)

    # --- throughput / memory
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--attn", default="sdpa",
                    help="sdpa, not flash_attention_2: FA2 must be a prebuilt wheel here (a source "
                         "build needs 20-40GB transient on a 95%%-full disk), and this card is "
                         "SM 8.9 so FA3 is not an option at all")
    ap.add_argument("--no-grad-checkpointing", action="store_true")
    ap.add_argument("--val-frac", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--allow-any-split", action="store_true",
                    help="skip the train-split-only guard (throwaway experiments only)")
    ap.add_argument("--yes", action="store_true",
                    help="required to actually start training; without it this is a dry run")
    args = ap.parse_args()

    # ---------------- targets-only inspection (no GPU, no weights)
    if args.print_targets:
        print(f"model: {args.model}   (meta device -- no memory allocated)")
        model = load_model(args.model, meta=True)
        targets, n, skipped = lora_targets(model)
        print(f"\nLoRA target_modules ({len(targets)} names, matching {n} Linear layers):")
        for t in targets:
            print(f"  {t}")
        print(f"\nvision Linear layers skipped: {skipped}")
        if not targets:
            raise SystemExit("no target modules matched -- Qwen has renamed its projections; "
                             "update LLM_LINEAR_SUFFIXES before training")
        return

    import torch
    from datasets import Dataset  # noqa: F401  (imported for the error message if missing)
    from peft import LoraConfig
    from transformers import AutoProcessor
    from trl import SFTConfig, SFTTrainer

    path = args.data if os.path.isabs(args.data) else os.path.join(HERE, args.data)
    rows = load_jsonl(path)
    # Last line of defence for the held-out protocol: nothing upstream can guarantee the file on
    # disk was built split-pure, so the trainer itself refuses test-split rows.
    if not args.allow_any_split:
        bad = sorted({r["meta"].get("instance", "?") for r in rows
                      if r.get("meta", {}).get("split") != "train"})
        if bad:
            raise SystemExit(
                f"{len(bad)} training examples are not from train-split shapes (e.g. {bad[:4]}). "
                f"Refusing to train: this would void the held-out evaluation. "
                f"Pass --allow-any-split only for throwaway experiments.")
    if args.overfit:
        rows = rows[:args.overfit]
        train_rows, val_rows, val_bases = rows, [], []
    else:
        train_rows, val_rows, val_bases = split_by_base(rows, args.val_frac, args.seed)

    out = args.out if os.path.isabs(args.out) else os.path.join(HERE, args.out)

    print("=" * 72)
    print("ASTRO SFT (LoRA)")
    print("=" * 72)
    print(f"  model            {args.model}")
    print(f"  data             {path}")
    print(f"  examples         {len(train_rows)} train / {len(val_rows)} val "
          f"(held-out shapes: {val_bases or 'none'})")
    print(f"  epochs/lr/sched  {args.epochs} / {args.lr} / {args.scheduler}")
    print(f"  loss on          {'ALL tokens (ASTRO)' if args.astro_no_masking else 'completion only'}")
    print(f"  lora             r={args.lora_r} alpha={args.lora_alpha} "
          f"dropout={args.lora_dropout}")
    print(f"  max_length       {args.max_length}")
    print(f"  eff. batch       {args.batch_size} x {args.grad_accum} = "
          f"{args.batch_size * args.grad_accum}")
    print(f"  out              {out}")

    if not args.yes:
        print("\nDRY RUN -- nothing was loaded or trained. Re-run with --yes to start.")
        return

    processor = AutoProcessor.from_pretrained(args.model)
    tokenizer = getattr(processor, "tokenizer", processor)
    model = load_model(args.model, dtype=args.dtype, attn=args.attn)
    targets, n_lin, n_vis = lora_targets(model)
    if not targets:
        raise SystemExit("no LoRA target modules matched; refusing to train a no-op adapter")
    n_frozen = freeze_vision(model)
    print(f"\n  lora targets     {targets}  ({n_lin} layers)")
    print(f"  vision frozen    {n_frozen} params, {n_vis} Linear layers excluded")

    peft_cfg = LoraConfig(r=args.lora_r, lora_alpha=args.lora_alpha,
                          lora_dropout=args.lora_dropout, bias="none",
                          task_type="CAUSAL_LM", target_modules=targets)

    cfg = SFTConfig(
        output_dir=out,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        lr_scheduler_type=args.scheduler,
        warmup_ratio=args.warmup_ratio,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        gradient_checkpointing=not args.no_grad_checkpointing,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        bf16=(args.dtype == "bfloat16"),
        max_length=args.max_length,
        # TRL masks the prompt automatically on a prompt-completion dataset; the flag makes the
        # choice explicit and lets the ASTRO no-masking ablation turn it off.
        completion_only_loss=not args.astro_no_masking,
        logging_steps=5,
        save_strategy="epoch",
        eval_strategy="epoch" if val_rows else "no",
        report_to=[],
        seed=args.seed,
    )

    trainer = SFTTrainer(
        model=model,
        args=cfg,
        train_dataset=to_dataset(train_rows),
        eval_dataset=to_dataset(val_rows) if val_rows else None,
        processing_class=tokenizer,
        peft_config=peft_cfg,
    )

    # Gate 1 from the plan: the vision tower must be untouched. print_trainable_parameters is the
    # cheapest place to catch an all-linear-style mistake before burning an hour on it.
    trainer.model.print_trainable_parameters()
    for name, p in trainer.model.named_parameters():
        if p.requires_grad and any(m in name for m in VISION_MARKERS):
            raise SystemExit(f"vision parameter is trainable: {name} -- refusing to train")

    trainer.train()
    trainer.save_model(out)
    # Gate 5: save the processor beside the adapter, or inference rebuilds a different chat
    # template and every served prompt silently differs from the trained one.
    processor.save_pretrained(out)
    tokenizer.save_pretrained(out)
    with open(os.path.join(out, "astro_sft.json"), "w") as f:
        json.dump({"base_model": args.model, "data": path,
                   "n_train": len(train_rows), "n_val": len(val_rows),
                   "val_bases": val_bases, "lora": {"r": args.lora_r, "alpha": args.lora_alpha,
                                                    "dropout": args.lora_dropout,
                                                    "targets": targets},
                   "epochs": args.epochs, "lr": args.lr, "scheduler": args.scheduler,
                   "max_length": args.max_length,
                   "completion_only_loss": not args.astro_no_masking}, f, indent=2)
    print(f"\nadapter + processor -> {out}")


if __name__ == "__main__":
    main()
