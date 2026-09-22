#!/usr/bin/env python3
"""Fail if any training prompt leaks the eval set.

A training prompt "leaks" an eval item when, after normalization, it is
identical to an eval prompt, or the two share a long common prefix (48
normalized characters by default). Either case means a later fine-tune would
be scored on text it was trained on.

Sources read:
    - evals/marathibench_lite_v0.jsonl   field `prompt`            (eval)
    - data/sft_seed_v0.jsonl             user message contents     (train)
    - data/dpo_pairs_v0.jsonl            field `prompt`            (train)

Normalization: strip, collapse internal whitespace to single spaces, casefold.

Usage:
    python3 scripts/check_train_eval_overlap.py
    python3 scripts/check_train_eval_overlap.py --eval E.jsonl --sft S.jsonl --dpo D.jsonl
    python3 scripts/check_train_eval_overlap.py --prefix 48

Stdlib only. Exit codes:
    0  no training prompt equals or shares a 48-char prefix with an eval prompt
    1  at least one training prompt leaks an eval prompt
    2  usage error or a file was unreadable
"""

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_EVAL = "evals/marathibench_lite_v0.jsonl"
DEFAULT_SFT = "data/sft_seed_v0.jsonl"
DEFAULT_DPO = "data/dpo_pairs_v0.jsonl"
DEFAULT_PREFIX = 48

_WS = re.compile(r"\s+")


def normalize(text):
    """Strip, collapse internal whitespace, and casefold."""
    return _WS.sub(" ", text.strip()).casefold()


def _load_jsonl(path):
    """Yield parsed objects from a JSONL file, skipping blank lines."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    with p.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            if raw.strip() == "":
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path} line {line_no}: invalid JSON: {e.msg}")


def load_eval_prompts(path):
    """Return list of (id, normalized_prompt) from an eval JSONL file."""
    out = []
    for obj in _load_jsonl(path):
        prompt = obj.get("prompt")
        if isinstance(prompt, str) and prompt.strip():
            out.append((obj.get("id", "?"), normalize(prompt)))
    return out


def load_train_prompts(sft_path, dpo_path):
    """Return list of (id, normalized_prompt) from the SFT and DPO files.

    SFT contributes every user message; DPO contributes the `prompt` field.
    """
    out = []
    for obj in _load_jsonl(sft_path):
        rid = obj.get("id", "?")
        for msg in obj.get("messages", []):
            if isinstance(msg, dict) and msg.get("role") == "user":
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    out.append((f"{rid}/user", normalize(content)))
    for obj in _load_jsonl(dpo_path):
        prompt = obj.get("prompt")
        if isinstance(prompt, str) and prompt.strip():
            out.append((obj.get("id", "?"), normalize(prompt)))
    return out


def find_overlaps(train, evals, prefix_len):
    """Return list of (train_id, eval_id, kind) for equal or shared-prefix pairs."""
    offenses = []
    for t_id, t_norm in train:
        for e_id, e_norm in evals:
            if t_norm == e_norm:
                offenses.append((t_id, e_id, "equal"))
            elif (
                len(t_norm) >= prefix_len
                and len(e_norm) >= prefix_len
                and t_norm[:prefix_len] == e_norm[:prefix_len]
            ):
                offenses.append((t_id, e_id, f"shared {prefix_len}-char prefix"))
    return offenses


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", default=DEFAULT_EVAL, help="eval JSONL path")
    parser.add_argument("--sft", default=DEFAULT_SFT, help="SFT seed JSONL path")
    parser.add_argument("--dpo", default=DEFAULT_DPO, help="DPO pairs JSONL path")
    parser.add_argument(
        "--prefix",
        type=int,
        default=DEFAULT_PREFIX,
        help="normalized prefix length that counts as a leak",
    )
    args = parser.parse_args(argv)

    try:
        evals = load_eval_prompts(args.eval)
        train = load_train_prompts(args.sft, args.dpo)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    offenses = find_overlaps(train, evals, args.prefix)

    print(f"eval prompts:  {len(evals)}")
    print(f"train prompts: {len(train)}")
    print(f"prefix length: {args.prefix}")

    if not offenses:
        print("status: OK (no train/eval overlap)")
        return 0

    print("status: FAILED (train/eval overlap detected)")
    for t_id, e_id, kind in offenses:
        print(f"  train {t_id} leaks eval {e_id} ({kind})")
    return 1


if __name__ == "__main__":
    sys.exit(main())
