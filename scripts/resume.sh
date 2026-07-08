#!/usr/bin/env bash
# Resumes the Marathi Mini Lab mission on a schedule.
#
# opencode agents do not self-schedule — they only run when invoked.
# This script is the scheduler side. It fires off an opencode run with
# the /resume command every 10 minutes, so the agent can push the next
# incomplete step forward and stop.
#
# Usage:
#   ./scripts/resume.sh                 # loop forever, 10 min cadence
#   ./scripts/resume.sh --once          # single run, then exit
#   ./scripts/resume.sh --interval 5    # custom cadence (minutes)
#
# Logs to ./outputs/resume.log (git-ignored).
# Safe to Ctrl-C; the next invocation picks up where the agent left off.

set -euo pipefail

INTERVAL_MIN=10
ONCE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --once) ONCE=1; shift ;;
    --interval) INTERVAL_MIN="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
cd "$REPO_ROOT"

mkdir -p outputs
LOG="outputs/resume.log"
INTERVAL_SEC=$((INTERVAL_MIN * 60))

echo "[resume] repo=$REPO_ROOT interval=${INTERVAL_MIN}m once=$ONCE log=$LOG" | tee -a "$LOG"

iteration=0
while true; do
  iteration=$((iteration + 1))
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "[resume] --- iteration $iteration @ $ts ---" | tee -a "$LOG"

  if command -v opencode >/dev/null 2>&1; then
    opencode run --agent resume "Resume the Marathi Mini Lab mission. Read AGENT_PLAN.md, find the first incomplete step in the priority order, do that one step, show the diff, stop and report. Do not commit." 2>&1 | tee -a "$LOG" || true
  else
    echo "[resume] opencode CLI not found on PATH; skipping iteration." | tee -a "$LOG"
  fi

  if [ "$ONCE" -eq 1 ]; then
    echo "[resume] --once set; exiting after single run." | tee -a "$LOG"
    break
  fi

  echo "[resume] sleeping ${INTERVAL_SEC}s before next iteration..." | tee -a "$LOG"
  sleep "$INTERVAL_SEC"
done
