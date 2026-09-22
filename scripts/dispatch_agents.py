#!/usr/bin/env python3
"""Bounded headless dispatcher for Marathi Mini Lab.

One checkout. Do not create sibling directories or extra worktrees.
Run one agent at a time so writers cannot clobber each other.
A zero exit without the required report status is not success.
Does not dispatch a task whose report is already AGENT_COMPLETE,
BLOCKED, or PARTIAL unless PM feedback says REWORK.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".agent_dispatch"
LOGS = STATE / "logs"

LANES = {
    "codex": {
        "cwd": ROOT,
        "task": "TASK-005",
        "task_file": "docs/tasks/TASK-005-judge-agreement.md",
        "timeout": 1800,
    },
    "claude": {
        "cwd": ROOT,
        "task": "TASK-002",
        "task_file": "docs/tasks/TASK-002-seal-eval-leaks.md",
        "timeout": 1800,
    },
    "oss": {
        "cwd": ROOT,
        "task": "TASK-004",
        "task_file": "docs/tasks/TASK-004-failure-seed-candidates.md",
        "timeout": 1800,
    },
}


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def report_path(cwd: Path, task: str) -> Path:
    return cwd / "08_agent_reports" / f"{task}-report.md"


def rework_authorized(task: str) -> bool:
    path = ROOT / "docs" / "dispatch" / f"{task}-PM-FEEDBACK.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return bool(re.search(r"^## Next lifecycle state\s+REWORK\s*$", text, flags=re.MULTILINE))


def report_state(cwd: Path, task: str) -> str | None:
    path = report_path(cwd, task)
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^## Status\s+([A-Z_]+)\s*$", text, flags=re.MULTILINE)
    return match.group(1) if match else "UNKNOWN"


def append_event(event: dict) -> None:
    STATE.mkdir(exist_ok=True)
    path = STATE / "events.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def prompt_for(agent: str, lane: dict) -> str:
    return (
        f"You are {agent}, an executor on Marathi Mini Lab. The PM is Grok. "
        f"The product owner authorized this headless run. "
        f"Read docs/AGENT_RULES.md and {lane['task_file']} in {lane['cwd']}. "
        f"Execute {lane['task']} now. This is an execution turn: write the files, "
        f"run the tests named in the task, and write 08_agent_reports/{lane['task']}-report.md. "
        f"Do not stop after a plan. Do not edit files outside the task's In list. "
        f"Do not talk to other agents. Do not push. Do not touch main. "
        f"If you cannot finish, write status PARTIAL or BLOCKED with what is actually on disk."
    )


def command(agent: str, lane: dict) -> list[str]:
    prompt = prompt_for(agent, lane)
    cwd = str(lane["cwd"])
    if agent == "codex":
        return [
            "codex", "exec",
            "-C", cwd,
            "--approve-for-me",
            prompt,
        ]
    if agent == "claude":
        return [
            "claude", "--print", prompt,
            "--permission-mode", "acceptEdits",
            "--allowedTools",
            "Read", "Edit", "Write", "Grep", "Glob",
            "Bash(python3 *)",
            "Bash(python3 -m unittest *)",
            "Bash(git add *)",
            "Bash(git commit *)",
            "Bash(git status *)",
            "Bash(git diff *)",
            "Bash(git log *)",
            "--output-format", "text",
            "--no-session-persistence",
        ]
    if agent == "oss":
        return [
            "opencode", "run",
            "--dir", cwd,
            "--model", "nvidia/google/gemma-4-31b-it",
            "--auto",
            "--title", "TASK-004 failure seeds",
            prompt,
        ]
    raise SystemExit(f"unknown agent {agent}")


def run_agent(agent: str, timeout: int, dry_run: bool) -> int:
    lane = LANES[agent]
    STATE.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    lock_path = STATE / f"{agent}.lock"
    task = lane["task"]
    cwd = lane["cwd"]
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            append_event({"at": now(), "agent": agent, "task": task, "event": "already_running"})
            return 0
        state = report_state(cwd, task)
        if state in {"AGENT_COMPLETE", "BLOCKED", "PARTIAL"} and not rework_authorized(task):
            append_event({
                "at": now(), "agent": agent, "task": task,
                "event": "not_dispatched", "report_state": state,
            })
            return 0
        cmd = command(agent, lane)
        if dry_run:
            print(json.dumps({
                "agent": agent, "cwd": str(cwd), "task": task,
                "argv0": cmd[0], "timeout": timeout or lane["timeout"],
            }))
            return 0
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = LOGS / f"{stamp}-{agent}-{task.lower()}.log"
        limit = timeout or lane["timeout"]
        append_event({
            "at": now(), "agent": agent, "task": task, "event": "started",
            "log": str(log_path.relative_to(ROOT)), "timeout": limit,
        })
        try:
            with log_path.open("w", encoding="utf-8") as log_handle:
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    text=True,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    timeout=limit,
                    check=False,
                )
            final = report_state(cwd, task)
            append_event({
                "at": now(), "agent": agent, "task": task, "event": "finished",
                "exit_code": result.returncode, "report_state": final,
                "log": str(log_path.relative_to(ROOT)),
            })
            if result.returncode != 0:
                return result.returncode
            return 0 if final else 2
        except subprocess.TimeoutExpired:
            with log_path.open("a", encoding="utf-8") as log_handle:
                log_handle.write("\nTIMEOUT\n")
            append_event({
                "at": now(), "agent": agent, "task": task, "event": "timeout",
                "log": str(log_path.relative_to(ROOT)),
            })
            return 124


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", choices=("codex", "claude", "oss", "all"), default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=0)
    args = parser.parse_args()
    agents = list(LANES) if args.agent == "all" else [args.agent]
    jobs = []
    for agent in agents:
        if not LANES[agent]["cwd"].is_dir():
            print(f"missing worktree for {agent}", file=sys.stderr)
            return 2
        jobs.append(agent)
    if len(jobs) > 1 and not args.dry_run:
        print("this repo has one checkout; pass --agent codex, claude, or oss", file=sys.stderr)
        return 2
    if args.dry_run or len(jobs) == 1:
        worst = 0
        for agent in jobs:
            worst = max(worst, run_agent(agent, args.timeout_seconds, args.dry_run))
        return worst
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        results = list(pool.map(lambda agent: run_agent(agent, args.timeout_seconds, False), jobs))
    return max(results)


if __name__ == "__main__":
    raise SystemExit(main())
