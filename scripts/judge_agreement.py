#!/usr/bin/env python3
"""Compare human and judge JSONL records by id, score, and failure_tags.

Tags are sets per item; omitted failure_tags means no tags. Metrics cover
human IDs only (additional judge IDs are validated but not compared).
Empty human input has n=0 and mae=n/a. No answers are judged here.
"""

import argparse
import json
import math
import sys


def read_records(path, side):
    records = {}
    with open(path, encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            location = f"{side} {path}:{line_number}"
            try:
                record = json.loads(line)
            except ValueError as error:
                raise ValueError(f"{location}: invalid JSON: {error}") from error
            if not isinstance(record, dict):
                raise ValueError(f"{location}: expected an object")
            record_id = record.get("id")
            if isinstance(record_id, bool) or not isinstance(record_id, (str, int)):
                raise ValueError(f"{location}: id must be a string or integer")
            if record_id in records:
                raise ValueError(f"{location}: duplicate {side} id {record_id!r}")
            score = record.get("score")
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise ValueError(f"{location}: id {record_id!r}: score must be numeric")
            if isinstance(score, float) and not math.isfinite(score):
                raise ValueError(f"{location}: id {record_id!r}: score must be finite")
            tags = record.get("failure_tags", [])
            if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
                raise ValueError(f"{location}: id {record_id!r}: failure_tags must be a list of strings")
            records[record_id] = (score, set(tags))
    return records


def ratio(numerator, denominator):
    return f"{numerator / denominator:.3f}" if denominator else "n/a"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("human")
    parser.add_argument("judge")
    args = parser.parse_args(argv)
    try:
        human = read_records(args.human, "human")
        judge = read_records(args.judge, "judge")
        missing = human.keys() - judge.keys()
        if missing:
            for record_id in sorted(missing, key=repr):
                print(f"missing judge id {record_id!r}", file=sys.stderr)
            return 1
        gaps = []
        intersection = human_count = judge_count = 0
        for record_id, (human_score, human_tags) in human.items():
            judge_score, judge_tags = judge[record_id]
            gap = abs(human_score - judge_score)
            if isinstance(gap, float) and not math.isfinite(gap):
                raise ValueError(f"id {record_id!r}: score difference is not finite")
            gaps.append(gap)
            intersection += len(human_tags & judge_tags)
            human_count += len(human_tags)
            judge_count += len(judge_tags)
        mae = ratio(sum(gaps), len(gaps))
    except (OSError, UnicodeError, ValueError, OverflowError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"n: {len(gaps)}")
    print(f"mae: {mae}")
    print(f"exact: {sum(gap == 0 for gap in gaps)}")
    print(f"within_half: {sum(gap <= 0.5 for gap in gaps)}")
    print(f"precision: {ratio(intersection, judge_count)}")
    print(f"recall: {ratio(intersection, human_count)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
