# TASK-005 — Agreement between a human score file and a judge file

Owner: Codex. Worktree: `/Users/krishnaiyer/AI/marathi-mini-lab-codex`. Branch: `feature/codex-judge-agreement`.

## Why

A blind judge of Qwen3 is coming later. The comparison must be a script with a known answer on fixtures, not a hand count. Do not judge any answers in this task.

## In

Create only:

- `scripts/judge_agreement.py`
- `tests/test_judge_agreement.py`
- `08_agent_reports/TASK-005-report.md`

## Out

Do not edit `scripts/score_by_category.py`, data, evals, reports, or outputs. Do not read `outputs/blind_qwen3_run004.jsonl` to invent scores. Do not create a judge JSONL of real model answers.

## Behaviour

```
python3 scripts/judge_agreement.py <human.jsonl> <judge.jsonl>
```

Stdlib only. Join on `id`.

- Every human id must appear exactly once in the judge file. A missing or duplicate judge id: print it to stderr and exit 1. Do not skip it and still print a happy average.
- Scores are numbers. Booleans and non-numeric scores exit 1.
- Print: `n`, `mae` (mean absolute error), `exact` (count of equal scores), `within_half` (count where abs(diff) <= 0.5).
- Print tag precision and recall. Human tags are the reference. Precision = |intersection| / |judge tags| over all items pooled, recall = |intersection| / |human tags|. If a denominator is 0, print `n/a`, do not invent 0 or 1.
- Round mae, precision, and recall to 3 decimal places.
- Exit 0 only when the join is complete and scores are numeric.

## Tests

Use temp fixtures, not the real baseline.

1. Two items, scores (5, 3) vs (4, 3). Absolute gaps are 1 and 0. MAE must be 0.5. exact must be 1. within_half must be 1, because only a gap of 0.5 or less counts. A test that expects 2 is wrong. Assert the literals 0.5, 1, and 1.
2. A missing judge id must make the process exit 1 and must not print `mae`.
3. Human tags {a, b} and judge tags {b, c} on one item: precision 0.5, recall 0.5.
4. Both sides have no tags: precision and recall are `n/a`, and exit is still 0.

## Done

Unittest exits 0. Commit on `feature/codex-judge-agreement` only. Do not push.
