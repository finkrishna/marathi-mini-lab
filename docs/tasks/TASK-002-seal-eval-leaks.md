# TASK-002 — Remove two training prompts that leak the eval set

Owner: Claude. Worktree: `/Users/krishnaiyer/AI/marathi-mini-lab-claude`. Branch: `feature/claude-eval-seal`.

## Why

`DPO-0011` is the same prompt as eval item `MBL-0010`. `DPO-0013` shares a long prefix with `MBL-0009`. Any later fine-tune would be scored on text it was trained on. Fix only those two records, and add a check that fails if this happens again.

## In

- Edit only records `DPO-0011` and `DPO-0013` inside `data/dpo_pairs_v0.jsonl`. Do not reorder or rewrap other lines.
- Create `scripts/check_train_eval_overlap.py`.
- Create `tests/test_train_eval_overlap.py`.
- Create `reports/dpo_leak_fix.md` describing the old prompt, the new prompt, and why the new one is not a paraphrase of the eval item.
- Create `08_agent_reports/TASK-002-report.md`.

## Out

Do not edit `evals/`, `data/sft_seed_v0.jsonl`, scoring scripts, or model outputs. Do not add a 26th pair. Do not start the judge task in this task.

## Replacement rules

- `DPO-0011`: replace the doctor-dosage prompt with a different formal-English instruction (school fee receipt or office leave). Keep a plausible rejected answer that is literal/wrong and a chosen answer in natural formal Marathi. Update `why_chosen_is_better`. Keep id `DPO-0011`.
- `DPO-0013`: do not mention the monsoon or "first week of June". Change the situation (for example a winter exam timetable). Keep id `DPO-0013`.
- Neither new prompt may share a 48-character prefix with any eval prompt after whitespace is collapsed.

## Checker

`python3 scripts/check_train_eval_overlap.py` reads:

- `evals/marathibench_lite_v0.jsonl` field `prompt`
- `data/sft_seed_v0.jsonl` user message contents
- `data/dpo_pairs_v0.jsonl` field `prompt`

Normalize by stripping, collapsing internal whitespace, and casefolding. Exit 1 if any training prompt equals an eval prompt, or if any two share a prefix of 48 normalized characters. Exit 0 otherwise. Print the offending ids. Stdlib only.

The test must show the checker fails on a fixture that copies the monsoon prefix pair, and passes on a fixture with unrelated prompts. Also run the checker on the real files after your edit and record the exit code.

## Done

Real checker exits 0. Unittest exits 0. `python3 scripts/validate_jsonl.py data/dpo_pairs_v0.jsonl --fields id,prompt,chosen,rejected,why_chosen_is_better --require-ids-unique` exits 0. Commit on `feature/claude-eval-seal` only. Do not push.
