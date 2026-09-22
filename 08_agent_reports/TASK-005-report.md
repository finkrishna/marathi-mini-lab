# TASK-005 report

## Status
BLOCKED

## What changed

- Created only `08_agent_reports/TASK-005-report.md`.
- `scripts/judge_agreement.py` and `tests/test_judge_agreement.py` do not exist. Implementation stopped before creating them because the brief contains contradictory acceptance requirements.

## Blocker and surprise

The Behaviour section defines `within_half` as the count where `abs(diff) <= 0.5`. Test 1 supplies human scores `(5, 3)` and judge scores `(4, 3)`, giving absolute differences `(1, 0)`. Therefore the specified metric is `1`, but the test explicitly requires the literal `2`. MAE `0.5` and exact `1` are consistent.

`docs/AGENT_RULES.md` requires: “If a premise in the brief is wrong, stop and report it. Do not silently redesign the task.” Neither the metric nor the required test was changed. PM/product-owner clarification is needed to correct the expected count or revise the metric and fixture consistently.

## Commands run and results

- `cat docs/AGENT_RULES.md docs/tasks/TASK-005-judge-agreement.md` — exit 0; read both required documents.
- `git status --short --branch; pwd; rg --files -g AGENTS.md` — overall exit 1 because no matching AGENTS.md was found. Status showed branch `feature/codex-judge-agreement` and pre-existing untracked `docs/`; cwd matched the assigned worktree.
- `ls -ld scripts tests 08_agent_reports` — exit 1; `scripts` existed, while `tests` and `08_agent_reports` did not yet exist.
- `git ls-files scripts/judge_agreement.py tests/test_judge_agreement.py 08_agent_reports/TASK-005-report.md` — exit 0; no tracked target files.
- `python3 -c 'from pathlib import Path; paths = ("scripts/judge_agreement.py", "tests/test_judge_agreement.py", "08_agent_reports/TASK-005-report.md"); print({p: Path(p).exists() for p in paths}); diffs = [abs(h - j) for h, j in zip((5, 3), (4, 3))]; print({"n": len(diffs), "mae": sum(diffs) / len(diffs), "exact": sum(d == 0 for d in diffs), "within_half": sum(d <= 0.5 for d in diffs)})'` — exit 0; all three target files were absent before this report was written; calculated `{'n': 2, 'mae': 0.5, 'exact': 1, 'within_half': 1}`.

## What was not verified

- Required unittest cases were not implemented or run; the contradictory first acceptance test prevents a compliant implementation. No passing test claim is made.
- Real baseline/model outputs were not read, scored, or judged. No Marathi content or judge JSONL was produced.
- No push, branch switch, or changes to main were performed.
