#!/usr/bin/env python3
"""Run baseline model outputs against the MarathiBench-lite eval set.

Loads a model via MLX (Apple Silicon), generates answers for prompts from
evals/marathibench_lite_v0.jsonl, and writes one JSONL record per prompt to
outputs/baseline_<model>_<run_id>.jsonl.

Each output record matches the schema expected by scripts/score_outputs.py:
    id, prompt, model, answer, score, failure_tags, notes
(score, failure_tags, notes are left empty for human/judge scoring.)

Usage:
    python3 scripts/run_baseline_eval.py --model <hf-model-id> --n 5
    python3 scripts/run_baseline_eval.py --model Qwen/Qwen2.5-0.5B-Instruct --n 50 \
        --run-id RUN-001 --max-tokens 512

Stdlib + mlx_lm only. Output goes to outputs/ (git-ignored).
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_FILE = REPO_ROOT / "evals" / "marathibench_lite_v0.jsonl"
OUTPUT_DIR = REPO_ROOT / "outputs"

DEFAULT_SYSTEM = (
    "You are a helpful assistant that can answer naturally in Marathi, "
    "English, or Marathi-English code-mix depending on the user's language."
)


def read_evals(path: Path, limit=None):
    """Yield eval prompt dicts."""
    with path.open("r", encoding="utf-8") as fh:
        for i, raw in enumerate(fh, start=1):
            if raw.strip() == "":
                continue
            if limit is not None and i > limit:
                break
            yield json.loads(raw)


def load_model(model_id, quant=None):
    """Load (model, tokenizer) via mlx_lm. Lazily imported so --help is fast."""
    from mlx_lm import load, generate  # noqa: F401
    if quant:
        # Builds a quantized model id suffix if provided (e.g. "4bit")
        full_id = model_id if "-4bit" in model_id else f"{model_id}-4bit"
        return load(full_id)
    return load(model_id)


def run_generation(model, tokenizer, prompt_text, system_text, max_tokens, temp):
    """Generate one answer from a single user prompt."""
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler
    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": prompt_text},
    ]
    template_kwargs = {}
    # Qwen3 models accept enable_thinking=False via the chat template
    # to skip the thinking trace and answer directly. Harmless on non-Qwen3.
    template_kwargs["enable_thinking"] = False
    try:
        prompt_str = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, **template_kwargs
        )
    except Exception:
        # Fallback: try without enable_thinking, then plain concat.
        try:
            prompt_str = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            prompt_str = f"{system_text}\n\n{prompt_text}\n"
    sampler = make_sampler(temp)
    response = generate(
        model, tokenizer, prompt=prompt_str, max_tokens=max_tokens, sampler=sampler
    )
    return response


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True,
                        help="HuggingFace model id, e.g. Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--n", type=int, default=5,
                        help="number of eval prompts to run (default 5)")
    parser.add_argument("--eval-file", default=str(EVAL_FILE),
                        help=f"eval JSONL path (default {EVAL_FILE})")
    parser.add_argument("--run-id", default=None,
                        help="run id for output filename, e.g. RUN-001")
    parser.add_argument("--max-tokens", type=int, default=512,
                        help="max tokens to generate (default 512)")
    parser.add_argument("--temp", type=float, default=0.3,
                        help="sampling temperature (default 0.3)")
    parser.add_argument("--system", default=DEFAULT_SYSTEM,
                        help="system prompt (default matches SFT seed system prompt)")
    parser.add_argument("--quant", action="store_true",
                        help="use the -4bit quantized variant if available")
    args = parser.parse_args(argv)

    eval_path = Path(args.eval_file)
    if not eval_path.is_file():
        print(f"error: eval file not found: {eval_path}", file=sys.stderr)
        return 2

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model_label = args.model.split("/")[-1] + ("-4bit" if args.quant else "")
    run_id = args.run_id or f"RUN-{int(time.time())}"
    out_name = f"baseline_{model_label}_{run_id}.jsonl"
    out_path = OUTPUT_DIR / out_name

    print(f"Loading model: {args.model}", file=sys.stderr)
    try:
        model, tokenizer = load_model(args.model, quant=args.quant)
    except Exception as e:
        print(f"error: failed to load model: {e}", file=sys.stderr)
        return 2
    print(f"Model loaded. Writing outputs to {out_path}", file=sys.stderr)

    n_ok = 0
    n_err = 0
    start = time.time()
    with out_path.open("w", encoding="utf-8") as out_fh:
        for eval_obj in read_evals(eval_path, limit=args.n):
            eval_id = eval_obj.get("id", "")
            prompt_text = eval_obj.get("prompt", "")
            print(f"  [{eval_id}] generating...", file=sys.stderr, end="", flush=True)
            t0 = time.time()
            try:
                answer = run_generation(
                    model, tokenizer, prompt_text, args.system,
                    args.max_tokens, args.temp,
                )
            except Exception as e:
                n_err += 1
                print(f" ERROR: {e}", file=sys.stderr)
                record = {
                    "id": eval_id,
                    "prompt": prompt_text,
                    "model": model_label,
                    "answer": f"<GENERATION_ERROR: {e}>",
                    "score": None,
                    "failure_tags": [],
                    "notes": "",
                }
                out_fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                continue
            dt = time.time() - t0
            print(f" {dt:.1f}s ({len(answer)} chars)", file=sys.stderr)
            record = {
                "id": eval_id,
                "prompt": prompt_text,
                "model": model_label,
                "answer": answer,
                "score": None,
                "failure_tags": [],
                "notes": "",
            }
            out_fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_fh.flush()
            n_ok += 1

    total = time.time() - start
    print(f"\nDone. {n_ok} ok, {n_err} errors in {total:.1f}s.", file=sys.stderr)
    print(f"Output: {out_path}", file=sys.stderr)
    print(f"Schema fields: id, prompt, model, answer, score, failure_tags, notes", file=sys.stderr)
    print(f"Next: edit score/failure_tags/notes in the file, then run "
          f"`python3 scripts/score_outputs.py {out_path}`", file=sys.stderr)
    return 0 if n_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
