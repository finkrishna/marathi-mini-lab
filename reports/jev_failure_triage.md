# Jev failure triage

Jev chose a next data action for each Qwen3-8B lab score at or below 2. This is not a Marathi quality score, not gold, and not permission to train.

| id | category | lab score | next action | native review | prompt defect |
|---|---|---|---|---|---|
| MBL-0021 | official_marathi | 1 | add_sft | no | no |
| MBL-0032 | culture_nuance | 1 | add_sft | yes | no |
| MBL-0045 | hallucination_trap | 1 | add_sft | no | no |
| MBL-0046 | general_regression | 1 | add_sft | no | no |
| MBL-0006 | translation_en_mr | 2 | add_sft | yes | no |
| MBL-0010 | translation_en_mr | 2 | add_sft | yes | no |
| MBL-0020 | code_mix | 2 | add_sft | no | no |
| MBL-0028 | daily_life_mh | 2 | add_sft | no | no |
| MBL-0031 | culture_nuance | 2 | rewrite_eval_prompt | no | yes |
| MBL-0043 | hallucination_trap | 2 | add_sft | no | no |

Raw answers, usage, and billed cost are in `reports/jev_failure_triage.json`.
