# Scoring Rubric (MarathiBench-lite v0)

How model responses are scored against `evals/marathibench_lite_v0.jsonl`.
Designed to be enforceable by a simple script (`scripts/score_baseline.py`),
no LLM-as-judge.

## Per-prompt pass/fail

Apply these checks in order. First failure = result for that prompt.

1. **Non-empty** — trimmed response length > 0. Else `empty`.
2. **No English dump** — response must contain a Devanagari word. Pure
   English answers fail as `english_dump`.
3. **Devanagari script** — every Marathi-content line is `\u0900-\u097F`
   + punctuation/whitespace/digits. Latin letters in Marathi content fail
   as `latin_script`. (Latin is allowed only in code/identifiers, which the
   eval prompts do not require.)
4. **No refusal** — must not match `/I can't|cannot|unable|मदत करू|शकत नाही/`.
   Else `refusal`.
5. **No Hindi/Hinglish leakage** — no Devanagari tokens drawn from Hindi
   register when a Marathi equivalent exists (e.g. `हम` vs `मी`, `क्या` vs
   `काय`). Flag as `hindi_leakage`.
6. **Reference match (if `reference` present)**
   - Translation tasks: normalized exact (lowercase, strip punctuation,
     collapse whitespace, map common anusvara/nasal variants) equals
     `reference`, OR substring of reference for partial-credit prompts.
   - QA tasks: `reference` is a set of required tokens; all must appear.
     Else `wrong_answer`.
7. **Task-shape** — answers the requested format (list count, single
   sentence, etc.). Else `shape_violation`.

A prompt with no candidate fail passes as `ok`. Each prompt carries
exactly one result tag.

## Aggregation

Per category in `marathibench_lite_v0.jsonl`:
- `accuracy = ok / total`
- failure-tag histogram across non-ok prompts

Report (`reports/baseline_<model>_v0.json`):
- overall accuracy
- per-category accuracy
- per-failure-tag counts
- optional: list of prompt ids failing step 3 (script) vs step 6
  (semantic) to separate surface vs knowledge gaps

## Normalization rules

- Trim leading/trailing whitespace.
- Collapse internal whitespace runs to single spaces.
- Delete punctuation for translation exact-match; keep for QA token check.
- Map `LangDevanagari` anusvara `ं` and candrabindu `ँ` to a canonical
  nasal form for match only (not for display).
- Lowercase Latin before any `latin_script` regex (catches mixed case).
- Compare Unicode code points; do not NFC-normalize unless the eval set
  uses NFC.

## Out of scope (defer to a later judge)

- Semantic correctness with no reference
- Fluency rating beyond binary non-empty + script
- Stylistic register (formal vs colloquial)

These become a Stage 2 rubric once the surface checks are green.
