# TASK-003 — Blind judge of the Qwen3-8B baseline

Owner: Claude. Worktree: `/Users/krishnaiyer/AI/marathi-mini-lab-claude`. Branch: `feature/claude-eval-seal`.

Start this only after TASK-002 is `AGENT_COMPLETE`. Do not read human scores.

## Why

We need to know whether an LLM judge agrees with the lab scores already on disk before anyone uses a judge on the unscored Qwen2.5-7B run. You do not compute that agreement. You only write a fresh judgment. The PM compares it later.

## In

Read only:

- `outputs/blind_qwen3_run004.jsonl` (id, prompt, model, answer)
- `evals/scoring_rubric.md`
- `evals/failure_tags.md`
- `evals/marathibench_lite_v0.jsonl` for category and `expected_behavior` only

Write:

- `results/judge_claude_run004.jsonl` — one object per input id, same order
- `reports/judge_claude_run004_notes.md` — how you judged, not a comparison
- `08_agent_reports/TASK-003-report.md`

## Out

Do not open `outputs/baseline_Qwen3-8B-4bit_RUN-004.jsonl` or any file whose name contains `RUN-004` other than the blind file. Do not open the main repo at `/Users/krishnaiyer/AI/marathi-mini-lab`. Do not judge RUN-005. Do not edit data or evals.

## Record schema

```json
{"id":"MBL-0001","model":"Qwen3-8B-4bit","score":3.5,"failure_tags":["too_verbose"],"notes":"one sentence","judge":"claude-blind-v1"}
```

- `score` is 1–5, halves allowed, from the rubric.
- `failure_tags` only from the canonical list. Empty list if none.
- 50 records. Every blind id exactly once.
- `notes` must mention a concrete flaw or a concrete success, not "looks fine".

## Self-check

A short stdlib command, pasted in the report, must show: 50 lines, 50 unique ids, every score in {1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5}, every tag in the canonical set. If you cannot finish all 50, write the lines you did finish and set status `PARTIAL`. Do not invent the rest.

`results/` is gitignored. Commit the notes and the report, not the JSONL. Do not push.
