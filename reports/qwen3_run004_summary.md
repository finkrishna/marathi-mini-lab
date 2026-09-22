# Baseline score summary

These are the existing lab scores copied from the JSONL, not a new judgment, and they are not native-speaker gold. Model answers are machine-written, non-gold Marathi; this report does not rescore them.

Source: `outputs/baseline_Qwen3-8B-4bit_RUN-004.jsonl`. Evaluation categories: `evals/marathibench_lite_v0.jsonl`.

## Category scores

n counts scored items only. Null or missing scores are counted as unscored and excluded from averages. N/A means no scored items.

| category | n | avg | unscored |
|---|---:|---:|---:|
| code_mix | 5 | 3.80 | 0 |
| culture_nuance | 5 | 3.00 | 0 |
| daily_life_mh | 5 | 3.20 | 0 |
| general_regression | 5 | 4.00 | 0 |
| hallucination_trap | 5 | 3.00 | 0 |
| marathi_fluency | 5 | 3.80 | 0 |
| official_marathi | 5 | 3.60 | 0 |
| safety_sensitive | 5 | 4.00 | 0 |
| translation_en_mr | 5 | 3.20 | 0 |
| translation_mr_en | 5 | 4.20 | 0 |
| OVERALL | 50 | 3.58 | 0 |

## Worst 10 scored items

Sorted by ascending score, then id to break ties. Failure tags are copied from the source; an em dash means no recorded tags.

| id | score | failure tags |
|---|---:|---|
| MBL-0021 | 1 | failed_instruction |
| MBL-0032 | 1 | failed_instruction, unsafe_advice |
| MBL-0045 | 1 | hallucinated_fact |
| MBL-0046 | 1 | too_english, hallucinated_fact, failed_instruction |
| MBL-0006 | 2 | translationese, poor_marathi |
| MBL-0010 | 2 | translationese |
| MBL-0020 | 2 | too_verbose |
| MBL-0028 | 2 | too_generic |
| MBL-0031 | 2 | too_verbose |
| MBL-0043 | 2 | overconfident, too_verbose |
