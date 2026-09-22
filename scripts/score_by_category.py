"""Summarize existing JSONL scores by evaluation category (stdlib only)."""

import argparse
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import sys


@dataclass
class Scores:
    values: list = field(default_factory=list)
    unscored: int = 0

    @property
    def n(self):
        return len(self.values)

    @property
    def average(self):
        return math.fsum(self.values) / self.n if self.n else None


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def summarize(scored_file, eval_file):
    """Return category totals, overall totals, and scored source records."""
    categories = {row["id"]: row["category"] for row in read_jsonl(eval_file)}
    groups = {}
    overall = Scores()
    scored_rows = []
    for row in read_jsonl(scored_file):
        category = categories.get(row["id"], "UNKNOWN")
        group = groups.setdefault(category, Scores())
        score = row.get("score")
        if score is None:
            group.unscored += 1
            overall.unscored += 1
            continue
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError(f"{row['id']}: non-numeric score {score!r}")
        score = float(score)
        if not math.isfinite(score):
            raise ValueError(f"{row['id']}: non-finite score {score!r}")
        group.values.append(score)
        overall.values.append(score)
        scored_rows.append(row)
    return groups, overall, scored_rows


def format_average(scores):
    return "N/A" if scores.average is None else f"{scores.average:.2f}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scored_file")
    parser.add_argument("--eval-file", required=True)
    args = parser.parse_args(argv)
    try:
        groups, overall, _ = summarize(args.scored_file, args.eval_file)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 2
    except (ValueError, KeyError, TypeError, OverflowError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print("category\tn\taverage\tunscored")
    for category, scores in sorted(groups.items()):
        print(f"{category}\t{scores.n}\t{format_average(scores)}\t{scores.unscored}")
    print(f"OVERALL\t{overall.n}\t{format_average(overall)}\t{overall.unscored}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
