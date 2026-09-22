# Standing rules — Marathi Mini Lab

Read once. Briefs do not repeat these.

## Branching and isolation

- Stay inside this repository directory. Do not create a sibling checkout or a new worktree. One writer at a time.
- Commit only on the branch you were given. Never checkout, merge, or commit to `main` or `integration`. Never force-push. Do not push unless the brief says to.
- Prefer new files. If the brief allows an edit to a shared file, list every edited path in the report.
- Do not edit a path the brief assigns to someone else.
- Do not commit `outputs/`, `runs/`, `results/`, `.agent_dispatch/`, `.env`, or bus files (`PM_TO_*.md`, `*_TO_PM.md`).

## Honesty

- Never invent a score, a tag count, or a Marathi sentence you did not actually produce.
- Machine-written Marathi is non-gold. Say so in the file and in the report.
- Do not treat model output as a native-speaker judgment.
- If a premise in the brief is wrong, stop and report it. Do not silently redesign the task.
- Never weaken or delete a test to make it pass. A test that cannot fail is not a test.

## Tests

- Run the commands in the brief yourself. Paste the command and the exit code in the report.
- Stdlib Python only, unless the brief names another dependency.

## When to stop

Stop with status `BLOCKED` or `PARTIAL` rather than guessing when the brief is ambiguous, a product choice would change the data, or you cannot finish the required checks. A partial file on disk plus an honest report is better than a fabricated completion.

## Report

Write `08_agent_reports/<TASK-ID>-report.md` with:

- `## Status` then exactly one of `AGENT_COMPLETE`, `PARTIAL`, `BLOCKED`
- what changed (paths)
- commands run and results
- anything that surprised you
- what you did not verify
