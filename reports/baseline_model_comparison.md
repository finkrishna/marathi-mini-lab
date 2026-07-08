# Baseline Model Comparison — MarathiBench-lite v0

This report compares a small set of open-source / instruct models on
`evals/marathibench_lite_v0.jsonl` (50 prompts, 10 categories, 5 each).
Scores are per `evals/scoring_rubric.md` (1–5 overall + 7 dimensions).
Failure tags are per `evals/failure_tags.md` (canonical list).

> **Status:** Template. Fill in as runs are scored. Do not commit raw
> model outputs as gold unless a native Marathi speaker has signed off.

## Candidate models

Initial candidates for the sandbox:

1. **GLM** (via OpenCode / provider) — default base for this lab.
2. **Qwen** instruct / coder — multilingual instruct family.
3. **Gemma / Gemini** family — multilingual baseline.
4. **Local Ollama / LM Studio model** — if available locally.
5. **OpenAI / Claude** — premium comparison only, not the default loop.

Add or strike rows below as runs are completed. Keep one row per
`(model, dataset, run_id)` so re-runs don't overwrite history.

## Scoring method

- Each prompt's response recorded with fields: `id`, `prompt`, `model`,
  `answer`, `score` (1–5), `failure_tags` (list, may be empty), `notes`.
- A human or LLM judge assigns the 1–5 score and tags. The offline script
  `scripts/score_outputs.py` (planned) only summarises these.
- Do **not** auto-score via keyword/regex for now (see caveat below).

## Manual review method

For each run:

1. Open the raw output JSONL (in `outputs/` or `runs/`, not committed).
2. For each prompt:
   - skim the answer,
   - apply the ordered checks from `scoring_rubric.md`,
   - record score + failure_tags + 1–2 line `notes`.
3. Save scored subset as `results/<model>_<run_id>.jsonl` (git-ignored).
4. Run `scripts/score_outputs.py` to produce the per-row summary.
5. Paste the summary blocks into this report.

## Failure-tag summary table

Replace counts with run data. One column per model.

| Tag                   | GLM (TBD) | Qwen (TBD) | Gemma (TBD) | Notes              |
|---|---|---|---|---|
| `poor_marathi`        |   –  |   – |   – |                             |
| `too_hindi_like`      |   –  |   – |   – |                             |
| `too_english`         |   –  |   – |   – |                             |
| `translationese`      |   –  |   – |   – |                             |
| `wrong_register`      |   –  |   – |   – |                             |
| `missed_context`      |   –  |   – |   – |                             |
| `hallucinated_fact`   |   –  |   – |   – |                             |
| `unsafe_advice`       |   –  |   – |   – |                             |
| `overconfident`       |   –  |   – |   – |                             |
| `too_verbose`         |   –  |   – |   – |                             |
| `too_generic`         |   –  |   – |   – |                             |
| `bad_format`          |   –  |   – |   – |                             |
| `failed_instruction`  |   –  |   – |   – |                             |
| `weak_reasoning`      |   –  |   – |   – |                             |
| `refused_unnecessarily`|  –  |   – |   – |                             |

## Per-category averages

| Category                  | n | GLM avg | Qwen avg | Gemma avg |
|---|---|---|---|---|
| marathi_fluency          | 5 |   –  |   –  |   –  |
| translation_en_mr        | 5 |   –  |   –  |   –  |
| translation_mr_en        | 5 |   –  |   –  |   –  |
| code_mix                 | 5 |   –  |   –  |   –  |
| official_marathi         | 5 |   –  |   –  |   –  |
| daily_life_mh            | 5 |   –  |   –  |   –  |
| culture_nuance           | 5 |   –  |   –  |   –  |
| safety_sensitive         | 5 |   –  |   –  |   –  |
| hallucination_trap       | 5 |   –  |   –  |   –  |
| general_regression      | 5 |   –  |   –  |   –  |
| **Overall**              | 50 |   –  |   –  |   –  |

## Worst 10 examples

(List manually chosen from the lowest overall scores during the run.)

| id | model | score | failure_tags | notes |
|---|---|---|---|---|
|   |   |   |   |   |

## Caveats

- **Keyword scoring is weak for Indic scripts.** Marathi has heavy
  agglutination (one word carries many morphemes) and sandhi
  (junctions that fuse words). Plus, Marathi and Hindi share the
  Devanagari block, so "did the response contain the expected token"
  fails when the surface form looks similar to Hindi but the register
  is wrong.
- A pure regex scorer will mis-tag `too_hindi_like` (needs lexical
  judgment) and `wrong_register` (needs contextual judgment).
- For the sandbox, lean on **human or LLM-judge scoring**. Reserve the
  offline `score_outputs.py` for *summarising* judgments already made,
  not for substituting for them.

## Recommendation

- Use human scoring or an LLM judge with the rubric in
  `evals/scoring_rubric.md`.
- Treat baseline numbers as **directional only** — 50 prompts is too
  small for stable rankings. A difference of 0.1 in averages is noise.
- Surface-ẩm Run **AB comparisons on the same prompt set + same seed**
  before claiming one model is better.

## Run log

Append rows as new runs complete. Link runs back to `reports/run_notes.md`.

| run_id | date | model | dataset | avg score | notes file |
|---|---|---|---|---|---|
|   |   |   |   |   |   |
