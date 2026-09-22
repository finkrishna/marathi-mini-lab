# TASK-004 — Failure-targeted seed candidates (non-gold)

Owner: OSS via OpenCode. Worktree: `/Users/krishnaiyer/AI/marathi-mini-lab-oss`. Branch: `feature/oss-failure-seeds`.

## Why

The scored Qwen3-8B run (n=50, average 3.58) fails mainly by rambling (`too_verbose`, 10), not following the ask (`failed_instruction`, 3), inventing facts (`hallucinated_fact`, 3), and word-for-word English-to-Marathi (`translationese`, 3). Weak categories: culture nuance, hallucination traps, Maharashtra daily life, English-to-Marathi. Do not add generic chat.

## In

Create only:

- `data/sft_candidates_failure_v1.jsonl` — 8 objects
- `data/dpo_candidates_failure_v1.jsonl` — 8 objects
- `tests/test_failure_seed_candidates.py`
- `docs/failure_seed_notes.md`
- `08_agent_reports/TASK-004-report.md`

## Out

Do not edit `data/sft_seed_v0.jsonl`, `data/dpo_pairs_v0.jsonl`, `evals/`, or any script that already exists. Do not copy an eval prompt. Do not claim the rows are gold.

## Shape

SFT object, chat style, plus provenance:

```json
{"id":"SFTC-0001","messages":[{"role":"system","content":"..."},{"role":"user","content":"..."},{"role":"assistant","content":"..."}],"tags":["too_verbose"],"provenance":"non-gold","author":"oss-opencode","target_failure":"too_verbose"}
```

DPO object:

```json
{"id":"DPOC-0001","prompt":"...","chosen":"...","rejected":"...","why_chosen_is_better":"...","tags":["translationese"],"provenance":"non-gold","author":"oss-opencode","target_failure":"translationese"}
```

Use the same system string as `data/sft_seed_v0.jsonl` for every SFT row.

Coverage, at least one row each: `too_verbose`, `failed_instruction`, `translationese`, `hallucinated_fact`. Chosen/assistant text should be short enough that a `too_verbose` target is visibly shorter than its rejected text. A `hallucinated_fact` chosen answer admits uncertainty instead of inventing a date or office. A `translationese` rejected answer is literal; the chosen answer is natural formal or colloquial Marathi, matching the ask.

## Forbidden overlap

Load every `prompt` in `evals/marathibench_lite_v0.jsonl`. After collapsing whitespace and casefolding, no candidate user prompt or DPO prompt may equal an eval prompt or share a 48-character prefix with one. The known leaks you must not recreate are the doctor-dosage sentence in `MBL-0010` and the monsoon sentence in `MBL-0009`.

## Tests you must run

```
python3 scripts/validate_jsonl.py data/sft_candidates_failure_v1.jsonl --fields id,messages,tags,provenance,author,target_failure --require-ids-unique
python3 scripts/validate_jsonl.py data/dpo_candidates_failure_v1.jsonl --fields id,prompt,chosen,rejected,why_chosen_is_better,provenance --require-ids-unique
python3 -m unittest tests/test_failure_seed_candidates.py
```

The unittest must fail if a candidate prompt is replaced with `MBL-0009`'s prompt. Assert that on a fixture, not by hoping. All three commands exit 0 on your real files.

## Done

Commit on `feature/oss-failure-seeds` only. Do not push. Notes must say the rows are non-gold drafts from the OpenCode model and still need a Marathi speaker.
