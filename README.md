# Marathi Mini Lab

A small, opinionated sandbox for learning the **post-training workflow** —
eval set → SFT seed → DPO pairs → baseline runs → scoring — applied to
Marathi-isation of open-source models.

The goal is **not** to ship the perfect Marathi model. The goal is to build
the project discipline: define what "better Marathi behaviour" means, make a
small eval set, make seed training data, run baselines, score them with a
practical rubric, and compare before/after — all without contaminating the
repo with unverified or auto-generated gold data.

> Status: sandbox phase. Baselines are directional only (n=5 per run).
> Treat generated outputs as non-gold unless a native Marathi speaker has
> signed off.

## What's in the box

```
marathi-mini-lab/
├── AGENT_PLAN.md           # The full spec (read this first)
├── evals/
│   ├── scoring_rubric.md        1–5 rubric, 7 dimensions, half-scores allowed
│   ├── failure_tags.md          15 canonical tags, mapped to rubric dimensions
│   └── marathibench_lite_v0.jsonl   50 prompts, 10 categories × 5 each
├── data/
│   ├── sft_seed_v0.jsonl        25 supervised fine-tuning chat examples
│   └── dpo_pairs_v0.jsonl       25 preference pairs (chosen vs rejected)
├── scripts/
│   ├── validate_jsonl.py        stdlib JSONL + field validator
│   ├── run_baseline_eval.py     MLX-based model runner (Apple Silicon)
│   ├── interactive_score.py     terminal-based scorer (no more broken JSON)
│   └── score_outputs.py         summarise scored runs (avg/tag histogram/worst N)
├── reports/
│   ├── baseline_model_comparison.md   template for the run comparison table
│   └── run_notes.md            per-run lab log template
└── outputs/                # git-ignored — your local run outputs land here
```

Everything in `scripts/` is **Python standard library only**, except
`run_baseline_eval.py` which uses `mlx_lm` for Apple Silicon inference.

## Quick start

### 1. Clone and validate the data

```bash
git clone https://github.com/finkrishna/marathi-mini-lab.git
cd marathi-mini-lab

# Confirm all JSONL files are well-formed (stdlib only)
python3 scripts/validate_jsonl.py evals/marathibench_lite_v0.jsonl --eval --require-ids-unique
python3 scripts/validate_jsonl.py data/sft_seed_v0.jsonl --fields id,messages,tags --require-ids-unique
python3 scripts/validate_jsonl.py data/dpo_pairs_v0.jsonl --fields id,prompt,chosen,rejected --require-ids-unique
```

Each should print `status: OK`.

### 2. (Optional) Run a baseline on Apple Silicon

`run_baseline_eval.py` loads a quantised model via [MLX](https://github.com/ml-explore/mlx-lm)
and writes one JSONL record per prompt, ready for scoring. You'll need an
Apple Silicon Mac (M1+), Python 3.9+, and a few GB of disk for the model weights.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install mlx-lm transformers

# Smoke test: 5 prompts against Qwen3-8B (4-bit, fits comfortably in 16GB)
python3 scripts/run_baseline_eval.py \
    --model mlx-community/Qwen3-8B-4bit \
    --n 5 --run-id RUN-001 --max-tokens 512
```

Output lands in `outputs/baseline_<model>_<run-id>.jsonl` (git-ignored).

Specs: the script probes the tokenizer for a Qwen3-style `enable_thinking`
flag and disables thinking mode to keep answers concise. Other instruct
models that expose a HuggingFace chat template work too — pass `--help`
for all flags.

### 3. Score the outputs

Use the interactive scorer so you don't have to hand-write JSON:

```bash
python3 scripts/interactive_score.py outputs/baseline_Qwen3-8B-4bit_RUN-001.jsonl
```

For each record you see the prompt and the model's answer, then type:

| Field         | What to enter                                            |
|---------------|----------------------------------------------------------|
| `score`       | a number 1–5 (per `evals/scoring_rubric.md`)             |
| `failure tags`| comma-separated names from `evals/failure_tags.md`       |
| `notes`       | a short justification                                    |
| `q`           | (at the score prompt) save and quit                     |
| `s`           | (at the score prompt) skip this record                   |

The script handles JSON quoting — no more `[tag]` syntax errors. Resume
from any record:

```bash
python3 scripts/interactive_score.py outputs/baseline_*.jsonl --start 31 --skip-scored
```

### 4. Summarise

```bash
python3 scripts/score_outputs.py outputs/baseline_Qwen3-8B-4bit_RUN-001.jsonl
```

Prints average score by model, a failure-tag histogram, and the worst N
examples. Run it across multiple files by concatenating them first:

```bash
cat outputs/run1.jsonl outputs/run2.jsonl > outputs/combined.jsonl
python3 scripts/score_outputs.py outputs/combined.jsonl --worst 20
```

## The eval set — MarathiBench-lite v0

Fifty prompts across ten categories, five prompts each. Designed to probe
real Marathi-isation failure modes, not benchmark-tune:

1. **marathi_fluency** — rewriting / grammar correction
2. **translation_en_mr** — English → Marathi
3. **translation_mr_en** — Marathi → English
4. **code_mix** — Marathi-English mixed register
5. **official_marathi** — formal / bureaucratic register
6. **daily_life_mh** — Maharashtra-context everyday request
7. **culture_nuance** — register and social nuance
8. **safety_sensitive** — refuses unsafe asks gracefully
9. **hallucination_trap** — admits uncertainty instead of inventing
10. **general_regression** — general capability check (no Marathi regression)

See `evals/marathibench_lite_v0.jsonl` for the prompts.

## Scoring

- **Overall 1–5** score per response, half-scores allowed (e.g. 3.5)
- **7 dimensions** (fluency, instruction-following, factual correctness,
  MH/India context, tone, safety, concision) — record when relevant
- **15 canonical failure tags** (`poor_marathi`, `translationese`,
  `too_hindi_like`, `wrong_register`, `hallucinated_fact`, …) — see
  `evals/failure_tags.md` for the full list and what each maps to

Keyword/regex scoring is **not** used: Marathi agglutination, sandhi, and
the shared Devanagari block with Hindi make surface matching unreliable.
Humans or an LLM judge do the scoring; `score_outputs.py` only summarises
judgments already made.

## What this repo is **not**

- Not a trained model. No checkpoints are stored.
- Not a gold dataset. All generated data is treated as non-gold unless
  explicitly marked as human/native-verified.
- Not a benchmark. Fifty prompts is enough to spot directional signal, not
  to rank models. A 0.1 average difference is noise.
- Not for production. It's a learning sandbox.

## Project rules

The agent (and any contributor) follows the rules in `AGENT_PLAN.md`:

- One small change at a time, diff shown after every edit
- Never commit on the agent's behalf — the human commits manually
- No secrets, API keys, tokens, or credentials
- Keep generated outputs under `outputs/`, `runs/`, or `results/`
  (all git-ignored)
- Treat machine-translated data as non-gold
- Prefer simple JSONL + small Python scripts
- Keep the project understandable to a non-expert learner

See `AGENT_PLAN.md` for the full mission spec, milestone breakdown, and
the "Definition of Done" checklist for the sandbox phase.

## Licence

This is a personal learning sandbox. No explicit licence yet — open an
issue if you want to reuse something specific.

## Acknowledgements

- [MLX](https://github.com/ml-explore/mlx) and
  [mlx-lm](https://github.com/ml-explore/mlx-lm) by Apple — local inference
  on Apple Silicon that makes this kind of experimentation possible on a
  laptop.
- [mlx-community](https://huggingface.co/mlx-community) for the quantised
  model weights used in baselines.
- The Qwen team for the open-weight Qwen2.5 and Qwen3 instruct models.
