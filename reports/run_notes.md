# Run Notes

Template for each run. Copy the block below to a new section, fill it
during or after the run, and link it from
`reports/baseline_model_comparison.md`. Keep entries short — this is
a lab log, not a thesis.

## Run ID

<!-- e.g. RUN-001 -->

## Date

<!-- YYYY-MM-DD -->

## Model

<!-- model name + version/revision + provider, e.g. glm-4-9b-chat / local -->

## Dataset

<!-- file name + version, e.g. evals/marathibench_lite_v0.jsonl -->

## Prompting Method

<!-- Decoding params and prompt template:
     - temperature, top_p, max_tokens
     - system prompt (paste the exact string, or link)
     - any few-shot preamble? (link file if too long)
-->

## What Worked

<!-- 2-4 bullets: prompts / categories where the model did well -->

## What Failed

<!-- 2-4 bullets: categories / failure_tags that recurred -->

## Surprising Findings

<!-- anything unexpected — wrong-city hallucinations, surprising code-mix fluency, etc. -->

## Next Step

<!-- Concrete hand-off, e.g.:
     - add 5 more code_mix prompts
     - try temp 0.3 instead of 0.7
     - draft SFT examples targeting `too_hindi_like`
-->
