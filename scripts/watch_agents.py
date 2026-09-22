#!/usr/bin/env python3
"""Live view of agents working in this checkout. Stdlib only.

    python3 scripts/watch_agents.py

Ctrl-C to quit. Refreshes every 2 seconds.
"""

from __future__ import annotations

import json
import os
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS = os.path.join(ROOT, ".agent_dispatch", "events.jsonl")
LOGS = os.path.join(ROOT, ".agent_dispatch", "logs")
NEEDLES = ("codex exec", "claude --print", "opencode run", "dispatch_agents.py")


def run(cmd):
    try:
        result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"(command failed: {exc})"
    return (result.stdout or result.stderr or "").rstrip()


def report_status():
    folder = os.path.join(ROOT, "08_agent_reports")
    if not os.path.isdir(folder):
        return "no report"
    lines = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith("-report.md"):
            continue
        status = "?"
        try:
            with open(os.path.join(folder, name), encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if line.startswith("## Status"):
                        status = next(handle, "").strip() or "?"
                        break
        except OSError:
            status = "unreadable"
        lines.append(f"{name[:-3]} {status}")
    return "; ".join(lines) if lines else "no report"


def processes():
    text = run(["ps", "ax", "-o", "pid=,etime=,command="])
    hits = []
    for line in text.splitlines():
        if "watch_agents.py" in line:
            continue
        if ROOT in line and any(needle in line for needle in NEEDLES):
            hits.append(" ".join(line.split()[:2]) + " " + line.split(ROOT, 1)[0].split()[-1])
    return hits or ["none"]


def last_events(limit=8):
    if not os.path.isfile(EVENTS):
        return ["none"]
    rows = []
    with open(EVENTS, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(line)
    shown = []
    for line in rows[-limit:]:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        shown.append(
            "{at} {agent} {event} {task}".format(
                at=event.get("at", ""),
                agent=event.get("agent", ""),
                event=event.get("event", ""),
                task=event.get("task", ""),
            )
        )
    return shown or ["none"]


def frame():
    dirty = run(["git", "status", "--short"]) or "clean"
    parts = [
        time.strftime("%H:%M:%S"),
        ROOT,
        f"branch: {run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])}",
        f"reports: {report_status()}",
        "",
        "processes:",
        *[f"  {line}" for line in processes()],
        "",
        "recent events:",
        *[f"  {line}" for line in last_events()],
        "",
        "files:",
        dirty if dirty == "clean" else "\n".join(f"  {line}" for line in dirty.splitlines()[:12]),
        "",
        "Ctrl-C to quit.",
    ]
    return "\n".join(parts)


def main():
    while True:
        os.system("clear")
        print(frame(), flush=True)
        time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nstopped.")
