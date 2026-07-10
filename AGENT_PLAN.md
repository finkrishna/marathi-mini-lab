# AGENT_PLAN.md — Marathi Mini Lab

## Purpose

This repo is a sandbox for learning how to build a disciplined post-training workflow for Marathi-isation of an open-source model.

The goal is not to train a perfect Marathi model immediately. The goal is to build the project discipline:

1. Define what “better Marathi behaviour” means.
2. Create a small evaluation set.
3. Create seed SFT examples.
4. Create DPO preference pairs.
5. Run baseline model outputs.
6. Score outputs with a practical rubric.
7. Compare before and after training.
8. Avoid contaminating the repo with generated, unverified, or secret data.

## Operating Rules for OpenCode

The coding agent must follow these rules:

1. Do not make broad repo-wide changes without first proposing a plan.
2. Make one small change at a time.
3. Show the diff after every change.
4. Do not commit changes. The human will commit manually.
5. Do not add secrets, API keys, tokens, or credentials.
6. Do not create large generated datasets unless explicitly asked.
7. Keep generated outputs under ignored folders such as `outputs/`, `runs/`, or `results/`.
8. Treat machine-translated data as non-gold unless explicitly marked as human/native verified.
9. Prefer simple JSONL files and small Python scripts.
10. Keep the project understandable to a non-expert learner.

## Repository Structure

Target structure:

```text
marathi-mini-lab/
  README.md
  AGENT_PLAN.md
  .gitignore

  evals/
    marathibench_lite_v0.jsonl
    scoring_rubric.md
    failure_tags.md

  data/
    sft_seed_v0.jsonl
    dpo_pairs_v0.jsonl

  scripts/
    validate_jsonl.py
    run_baseline_eval.py
    score_outputs.py
    summarize_results.py

  reports/
    baseline_model_comparison.md
    run_notes.md

  outputs/        # ignored
  runs/           # ignored
  results/        # ignored
```

## Milestone 1 — Rubric and Failure Tags

### Goal

Create the scoring system before creating a large dataset.

### Tasks

1. Write `evals/scoring_rubric.md`.
2. Write `evals/failure_tags.md`.
3. Keep both concise and practical.
4. Do not create eval prompts yet.

### Scoring Rubric

Use a 1–5 score:

* 1 = bad, wrong, unsafe, non-Marathi, or unusable.
* 2 = partially useful but awkward, incomplete, or heavily translationese.
* 3 = acceptable but ordinary.
* 4 = good, natural, useful, and mostly correct.
* 5 = excellent, native-sounding, context-aware, safe, and complete.

Evaluate these dimensions:

1. Marathi fluency
2. Instruction following
3. Factual correctness
4. Maharashtra/India context fit
5. Tone and social nuance
6. Safety and uncertainty
7. Concision and usefulness

### Failure Tags

Use short tags such as:

```text
poor_marathi
too_hindi_like
too_english
translationese
wrong_register
missed_context
hallucinated_fact
unsafe_advice
overconfident
too_verbose
too_generic
bad_format
failed_instruction
weak_reasoning
```

## Milestone 2 — MarathiBench-lite v0

### Goal

Create a small but useful eval set before training.

### File

`evals/marathibench_lite_v0.jsonl`

### Size

Start with 50 prompts only.

### JSONL Format

Each line should be a valid JSON object:

```json
{
  "id": "MBL-0001",
  "category": "marathi_fluency",
  "prompt": "खालील वाक्य अधिक नैसर्गिक मराठीत लिहा: मला उद्या ऑफिसला जाणे शक्य नाही.",
  "expected_behavior": "Rewrite in natural Marathi without changing meaning.",
  "language": "mr",
  "difficulty": "easy",
  "tags": ["rewrite", "natural_marathi"]
}
```

### Categories

Create 5 prompts in each category:

1. Marathi fluency and rewriting
2. English to Marathi translation
3. Marathi to English translation
4. Marathi-English code-mix
5. Official/bureaucratic Marathi
6. Maharashtra daily-life context
7. Cultural/social nuance
8. Safety-sensitive questions
9. Hallucination traps
10. General capability regression

### Rules

1. Do not use machine translation for the prompt text unless clearly marked.
2. Avoid political bait, stereotypes, or inflammatory prompts.
3. Include some prompts in Devanagari.
4. Include some prompts in Marathi-English code-mix.
5. Include a few prompts where the right answer should admit uncertainty.

## Milestone 3 — JSONL Validator

### Goal

Create a script to prevent broken datasets.

### File

`scripts/validate_jsonl.py`

### Requirements

The script should:

1. Accept a file path argument.
2. Read the file line by line.
3. Validate each line as JSON.
4. Report line number and error for invalid JSON.
5. Optionally check required fields for eval files:

   * `id`
   * `category`
   * `prompt`
   * `expected_behavior`
6. Print a success message if valid.
7. Use only Python standard library.

### Example Usage

```bash
python3 scripts/validate_jsonl.py evals/marathibench_lite_v0.jsonl
```

## Milestone 4 — Seed SFT Examples

### Goal

Create a tiny high-quality supervised fine-tuning seed set.

### File

`data/sft_seed_v0.jsonl`

### Size

Start with 25 examples only.

### Format

Use chat-style JSONL:

```json
{
  "id": "SFT-0001",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant that can answer naturally in Marathi, English, or Marathi-English code-mix depending on the user's language."
    },
    {
      "role": "user",
      "content": "माझ्या शिक्षकांना उद्या गैरहजर राहणार असल्याचा छोटा मेसेज लिहून दे."
    },
    {
      "role": "assistant",
      "content": "नमस्कार सर/मॅडम, मला उद्या काही वैयक्तिक कारणामुळे शाळेत/क्लासला येता येणार नाही. कृपया माझी अनुपस्थिती नोंदवावी. धन्यवाद."
    }
  ],
  "tags": ["marathi", "message", "school"]
}
```

### Rules

1. Quality over quantity.
2. No awkward machine-translated Marathi.
3. Avoid overly Sanskritised language unless the task asks for formal Marathi.
4. Include different registers:

   * friendly WhatsApp Marathi
   * formal Marathi
   * school/parent context
   * office context
   * simple explanation
   * translation
   * safety-aware answer

## Milestone 5 — DPO Preference Pairs

### Goal

Create preference examples where the chosen answer is better than the rejected answer.

### File

`data/dpo_pairs_v0.jsonl`

### Size

Start with 25 pairs only.

### Format

```json
{
  "id": "DPO-0001",
  "prompt": "Translate into formal Marathi: Please do the needful and revert by tomorrow.",
  "chosen": "कृपया आवश्यक ती कार्यवाही करून उद्यापर्यंत कळवावे.",
  "rejected": "कृपया आवश्यक ते करा आणि उद्यापर्यंत परत या.",
  "why_chosen_is_better": "The chosen answer uses natural formal Marathi. The rejected answer is literal and wrong because 'revert' is mistranslated as 'return'.",
  "tags": ["translation", "formal_marathi", "translationese"]
}
```

### Rules

1. The rejected answer should be plausible but flawed.
2. Capture real failure modes:

   * literal translation
   * Hindi-like Marathi
   * wrong register
   * over-formal language
   * unsafe overconfidence
   * hallucinated local fact
3. Include explanation of why chosen is better.

## Milestone 6 — Baseline Output Format

### Goal

Prepare for model comparison without needing full automation yet.

### File

Create documentation only first:

`reports/baseline_model_comparison.md`

### Include

1. Candidate models to test.
2. Planned scoring method.
3. Manual review method.
4. Failure-tag summary table.
5. Notes on why keyword scoring is weak for Indic scripts.
6. Recommendation to rely on human/judge scoring for Marathi quality.

### Candidate Models

Initial candidates:

1. GLM via OpenCode/provider
2. Qwen instruct/coder model
3. Gemma/Gemini family model
4. Any local Ollama/LM Studio model available
5. OpenAI/Claude only as premium comparison, not default

## Milestone 7 — Simple Scoring Script

### Goal

Create a simple offline scoring helper.

### File

`scripts/score_outputs.py`

### Requirements

Keep it simple. It should:

1. Read a JSONL file of model outputs.
2. Expect fields:

   * `id`
   * `prompt`
   * `model`
   * `answer`
   * `score`
   * `failure_tags`
   * `notes`
3. Summarise:

   * average score by model
   * count of failure tags
   * worst 10 examples
4. Use only Python standard library.

Do not build a complicated judge system yet.

## Milestone 8 — Run Notes

### Goal

Keep experiment logs human-readable.

### File

`reports/run_notes.md`

### Template

```markdown
# Run Notes

## Run ID

## Date

## Model

## Dataset

## Prompting Method

## What Worked

## What Failed

## Surprising Findings

## Next Step
```

## Current Priority Order

OpenCode should execute in this exact order:

1. Create or update `evals/scoring_rubric.md`.
2. Create or update `evals/failure_tags.md`.
3. Create 50 eval prompts in `evals/marathibench_lite_v0.jsonl`.
4. Create `scripts/validate_jsonl.py`.
5. Validate the eval file.
6. Create 25 SFT examples.
7. Create 25 DPO pairs.
8. Create baseline comparison report template.
9. Create run notes template.
10. Stop and ask for review.

## First Prompt to Give OpenCode

Use this prompt:

```text
Read AGENT_PLAN.md and inspect the repo. Do not modify files yet. Summarise the plan back to me and suggest the first single-file edit. Wait for my approval before editing.
```

## Second Prompt to Give OpenCode

After review, use this:

```text
Create only evals/scoring_rubric.md based on AGENT_PLAN.md. Do not modify any other file. Keep it concise and practical. Show me the diff before I commit.
```

## Human Commit Rhythm

After every OpenCode edit, run:

```bash
git diff
git status
```

If the change is good:

```bash
git add <changed-file>
git commit -m "<short clear message>"
```

Suggested commits:

```text
Add MarathiBench scoring rubric
Add MarathiBench failure tags
Add MarathiBench lite eval prompts
Add JSONL validation script
Add seed SFT examples
Add DPO preference pairs
Add baseline comparison template
Add run notes template
```

## Non-Goals for Now

Do not do these yet:

1. Do not run CPT.
2. Do not change tokenizer.
3. Do not train a model.
4. Do not download large datasets.
5. Do not scrape the web.
6. Do not add API keys.
7. Do not claim the dataset is gold.
8. Do not optimise for benchmark scores.
9. Do not refactor the whole repo.
10. Do not create a large framework prematurely.

## Definition of Done for This Sandbox

This sandbox is successful when it has:

1. A clear rubric.
2. 50 usable MarathiBench-lite prompts.
3. A working JSONL validator.
4. 25 high-quality SFT examples.
5. 25 useful DPO pairs.
6. A baseline comparison report template.
7. A run notes template.
8. Clean git history with small commits.
9. No secrets.
10. No unreviewed generated data committed as gold.

After this, the next project can move from sandbox to real Marathi-isation experiments.
