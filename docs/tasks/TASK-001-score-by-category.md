# TASK-001 — Category scores and a written baseline summary

Owner: Codex. Worktree: `/Users/krishnaiyer/AI/marathi-mini-lab-codex`. Branch: `feature/codex-score-tooling`.

## Why

Qwen3-8B has 50 human scores in a gitignored JSONL. The comparison report on `main` is still an empty template, and `scripts/score_outputs.py` cannot group by eval category. This task makes that summary regenerable. It does not rescore anything.

## In

Create only:

- `scripts/score_by_category.py`
- `scripts/render_baseline_report.py`
- `tests/test_score_by_category.py`
- `reports/qwen3_run004_summary.md`
- `08_agent_reports/TASK-001-report.md`

You may read `evals/marathibench_lite_v0.jsonl`, `evals/scoring_rubric.md`, `evals/failure_tags.md`, and `outputs/baseline_Qwen3-8B-4bit_RUN-004.jsonl`. Do not modify them.

## Out

Do not edit `scripts/score_outputs.py`, `data/`, `evals/`, README, `AGENT_PLAN.md`, or any other report. Do not score or rewrite model answers. Do not train.

## Behaviour

`score_by_category.py` (stdlib only):

```
python3 scripts/score_by_category.py <scored.jsonl> --eval-file evals/marathibench_lite_v0.jsonl
```

- Join on `id`.
- A row with `score` null or missing is counted as unscored and excluded from averages.
- An id absent from the eval file is category `UNKNOWN`. Do not drop it.
- Print one row per category that appears: n, average. Then an OVERALL row of scored items only.
- Averages use float scores. Half scores are valid. Round printed averages to 2 decimal places.
- Exit 0 on success, 2 if the file is missing, 1 if a scored row has a non-numeric score.

`render_baseline_report.py` calls the same logic and writes markdown to `--out`. The markdown must say, in the first paragraph, that these are the existing lab scores copied from the JSONL, not a new judgment, and that they are not native-speaker gold.

## Acceptance

1. `python3 -m unittest tests/test_score_by_category.py` exits 0.
2. Tests use their own fixture files under `tests/fixtures/` (or temp files). They must fail if averages include a null score, or if an unknown id is dropped. Do not assert a tautology computed only inside the test.
3. Running the renderer on `outputs/baseline_Qwen3-8B-4bit_RUN-004.jsonl` must produce these scored averages (n=5 each category, overall n=50, overall average 3.58):

| category | avg |
|---|---|
| code_mix | 3.80 |
| culture_nuance | 3.00 |
| daily_life_mh | 3.20 |
| general_regression | 4.00 |
| hallucination_trap | 3.00 |
| marathi_fluency | 3.80 |
| official_marathi | 3.60 |
| safety_sensitive | 4.00 |
| translation_en_mr | 3.20 |
| translation_mr_en | 4.20 |

If your script does not reproduce this table from the file, the script is wrong. Do not edit the JSONL to make it match.

4. `reports/qwen3_run004_summary.md` contains that table and the worst items with id, score, and failure tags.

## Done

`08_agent_reports/TASK-001-report.md` status `AGENT_COMPLETE`, plus a commit on `feature/codex-score-tooling` containing only your files. Do not push.
