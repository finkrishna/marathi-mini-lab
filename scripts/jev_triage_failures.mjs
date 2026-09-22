/**
 * Ask Jev which next data action fits each weak scored item.
 * Reads scores from the main repo. Writes only under this worktree.
 * Loads AI_GATEWAY_API_KEY via node --env-file. Never prints the key.
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { experimental_evaluate as evaluate } from 'ai';
import { gateway } from '@ai-sdk/gateway';

const SCORED = process.env.SCORED_JSONL
  ?? '/Users/krishnaiyer/AI/marathi-mini-lab/outputs/baseline_Qwen3-8B-4bit_RUN-004.jsonl';
const EVALS = process.env.EVAL_JSONL
  ?? '/Users/krishnaiyer/AI/marathi-mini-lab/evals/marathibench_lite_v0.jsonl';
const OUT_DIR = new URL('../reports/', import.meta.url);

const questions = {
  nextDataAction: {
    type: 'choice',
    instructions: 'Which single data action is the best next use of this failure? Do not choose training if the prompt itself looks defective.',
    criteria: {
      add_sft: 'A short gold-style demonstration of the desired answer would teach the behaviour.',
      add_dpo: 'A chosen-versus-rejected pair would teach the contrast better than a single answer.',
      rewrite_eval_prompt: 'The prompt is ambiguous or defective; do not train on this item.',
      needs_native_review: 'The judgment depends on Marathi a text model should not settle.',
      no_train_signal: 'The failure is too thin or one-off to add data for.',
    },
  },
  nativeReviewRequired: {
    type: 'boolean',
    instructions: 'Is a Marathi speaker required before anyone treats this item as a training target?',
    criteria: {
      true: 'Fluency, register, or local usage is the actual question.',
      false: 'The failure is visible without Marathi judgment, such as a repeated prompt, English-only answer, or a false date.',
    },
  },
  promptDefectLikely: {
    type: 'boolean',
    instructions: 'Is the prompt itself a likely cause of the bad answer?',
    criteria: {
      true: 'The ask is confusing, self-contradictory, or not answerable as written.',
      false: 'A capable Marathi system could have answered this prompt.',
    },
  },
};

function loadJsonl(path) {
  return readFileSync(path, 'utf8').split('\n').filter(Boolean).map((line) => JSON.parse(line));
}

const evalById = new Map(loadJsonl(EVALS).map((row) => [row.id, row]));
const weak = loadJsonl(SCORED)
  .filter((row) => typeof row.score === 'number' && row.score <= 2)
  .sort((a, b) => a.score - b.score || a.id.localeCompare(b.id));

if (!process.env.AI_GATEWAY_API_KEY) {
  console.error('AI_GATEWAY_API_KEY is missing. Refusing to run.');
  process.exit(2);
}

const model = gateway.evaluationModel(process.env.JEV_MODEL ?? 'typesafe-ai/jev');
const rows = [];
for (const item of weak) {
  const ev = evalById.get(item.id) ?? {};
  const state = {
    id: item.id,
    category: ev.category ?? 'UNKNOWN',
    expected_behavior: ev.expected_behavior ?? '',
    human_lab_score: item.score,
    human_lab_tags: item.failure_tags ?? [],
    human_lab_notes: item.notes ?? '',
    prompt: String(item.prompt ?? '').slice(0, 700),
    answer: String(item.answer ?? '').slice(0, 700),
  };
  const started = performance.now();
  const result = await evaluate({ model, state, questions });
  const raw = JSON.parse(JSON.stringify(result));
  rows.push({
    id: item.id,
    category: state.category,
    score: item.score,
    tags: item.failure_tags ?? [],
    latencyMs: Math.round(performance.now() - started),
    answers: raw.answers ?? {},
    usage: raw.usage ?? null,
    billedCostUsd: raw.providerMetadata?.gateway?.cost ?? null,
  });
  console.error(`jev ${item.id} done`);
}

mkdirSync(OUT_DIR, { recursive: true });
const jsonPath = new URL('jev_failure_triage.json', OUT_DIR);
writeFileSync(jsonPath, JSON.stringify({
  model: process.env.JEV_MODEL ?? 'typesafe-ai/jev',
  source: SCORED,
  caveat: 'Jev triage is not a Marathi score and not a training decision. Native review still gates gold data.',
  items: rows,
}, null, 2));

const lines = [
  '# Jev failure triage',
  '',
  'Jev chose a next data action for each Qwen3-8B lab score at or below 2. This is not a Marathi quality score, not gold, and not permission to train.',
  '',
  '| id | category | lab score | next action | native review | prompt defect |',
  '|---|---|---|---|---|---|',
];
function choice(answer) {
  if (!answer || typeof answer !== 'object') return '';
  return answer.choice ?? '';
}

function flag(answer) {
  if (!answer || typeof answer !== 'object') return '';
  if (typeof answer.probability !== 'number') return '';
  return answer.probability >= 0.5 ? 'yes' : 'no';
}

for (const row of rows) {
  const a = row.answers;
  lines.push(`| ${row.id} | ${row.category} | ${row.score} | ${choice(a.nextDataAction)} | ${flag(a.nativeReviewRequired)} | ${flag(a.promptDefectLikely)} |`);
}
lines.push('', 'Raw answers, usage, and billed cost are in `reports/jev_failure_triage.json`.', '');
writeFileSync(new URL('jev_failure_triage.md', OUT_DIR), lines.join('\n'));
console.error(`wrote ${rows.length} rows`);
