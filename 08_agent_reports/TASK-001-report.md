## Status
AGENT_COMPLETE

## Changes

- `scripts/score_by_category.py`: stdlib JSONL join by id, per-category and overall scored counts and float averages, explicit unscored counts, UNKNOWN retention, and required error exit codes.
- `scripts/render_baseline_report.py`: uses the same aggregation logic and writes a Markdown summary with provenance and the worst 10 scored items, ordered by score then id.
- `tests/test_score_by_category.py`: six tests using temporary fixture files, including literal expected averages and CLI output; covers null/missing scores, half scores, unknown ids, no scored items, missing files, invalid scores, and rendered provenance/tags.
- `reports/qwen3_run004_summary.md`: regenerated from the existing baseline JSONL, with all ten category averages and the worst 10 items and their recorded failure tags.
- `08_agent_reports/TASK-001-report.md`: this execution report.

## Commands and results

Python commands used `PYTHONDONTWRITEBYTECODE=1` to avoid creating files outside the allowed list.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_score_by_category.py
```

Exit 0: six tests passed. Subprocess tests also confirmed exit 2 for either missing input and exit 1 for invalid scores, including booleans, strings, and non-finite numbers.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/render_baseline_report.py outputs/baseline_Qwen3-8B-4bit_RUN-004.jsonl --eval-file evals/marathibench_lite_v0.jsonl --out reports/qwen3_run004_summary.md
```

Exit 0: wrote the required summary, including the first-paragraph disclosure.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/score_by_category.py outputs/baseline_Qwen3-8B-4bit_RUN-004.jsonl --eval-file evals/marathibench_lite_v0.jsonl
```

Exit 0: each category has n=5; OVERALL has n=50, average 3.58, unscored=0. Category averages, in alphabetical order: 3.80, 3.00, 3.20, 4.00, 3.00, 3.80, 3.60, 4.00, 3.20, 4.20. All match the task exactly.

An additional `PYTHONDONTWRITEBYTECODE=1 python3 -` assertion check exited 0: compared category names, counts and averages with the task's literal expected values; checked overall count/average; independently sorted raw JSONL records and verified all ten worst-item report rows and their source tags. The generated Markdown was also read back for inspection.

`git diff --check` exited 0. Initial `git branch --show-current` confirmed `feature/codex-score-tooling`. Initial inspection returned exit 1 only because `ls -ld scripts tests reports 08_agent_reports` found that `tests/` did not yet exist; creating the allowed test file supplied that directory.

## Decisions and surprises

- The rubric specifies worst 10 examples; equal scores are ordered by id for reproducibility.
- Categories containing only unscored records remain visible with n=0 and average N/A.
- No baseline-data discrepancy occurred. The existing untracked `docs/` directory was preserved and excluded from the commit.
- All changes are confined to the five allowed paths. No source scores, model answers, eval files, existing scripts, or other reports were edited.

## Verification limits

The report copies existing lab scores and tags; it does not verify their linguistic or factual correctness. Machine-written Marathi is non-gold, and these scores are not native-speaker gold. No rescoring, training, native-speaker assessment, or unrelated project tests were performed. PM acceptance remains with Grok.

## Version control

Delivery branch: `feature/codex-score-tooling`. The task commit contains only the five paths listed above; identify it by subject `TASK-001: add category scoring and baseline summary`. No push or checkout, merge, or commit to main was performed.

The initial `git add -- scripts/score_by_category.py scripts/render_baseline_report.py tests/test_score_by_category.py reports/qwen3_run004_summary.md 08_agent_reports/TASK-001-report.md` exited 128 because the worktree index is outside the writable sandbox. Retrying with elevated filesystem permission succeeded (exit 0). `git diff --cached --check`, `git diff --cached --stat`, and `git diff --cached --name-only` exited 0 and confirmed exactly the five allowed files.
