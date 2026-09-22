"""Render existing baseline scores as a Markdown report."""

import argparse
from pathlib import Path
import sys

try:
    from .score_by_category import format_average, summarize
except ImportError:
    from score_by_category import format_average, summarize


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def render(scored_file, eval_file):
    groups, overall, rows = summarize(scored_file, eval_file)
    lines = [
        "# Baseline score summary",
        "",
        "These are the existing lab scores copied from the JSONL, not a new "
        "judgment, and they are not native-speaker gold. Model answers are "
        "machine-written, non-gold Marathi; this report does not rescore them.",
        "",
        f"Source: `{scored_file}`. Evaluation categories: `{eval_file}`.",
        "",
        "## Category scores",
        "",
        "n counts scored items only. Null or missing scores are counted as "
        "unscored and excluded from averages. N/A means no scored items.",
        "",
        "| category | n | avg | unscored |",
        "|---|---:|---:|---:|",
    ]
    for category, scores in [*sorted(groups.items()), ("OVERALL", overall)]:
        lines.append(f"| {cell(category)} | {scores.n} | {format_average(scores)} | {scores.unscored} |")
    lines.extend([
        "", "## Worst 10 scored items", "",
        "Sorted by ascending score, then id to break ties. Failure tags are "
        "copied from the source; an em dash means no recorded tags.", "",
        "| id | score | failure tags |", "|---|---:|---|",
    ])
    for row in sorted(rows, key=lambda row: (float(row["score"]), row["id"]))[:10]:
        tags = ", ".join(row.get("failure_tags") or []) or "—"
        lines.append(f"| {cell(row['id'])} | {float(row['score']):g} | {cell(tags)} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scored_file")
    parser.add_argument("--eval-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        markdown = render(args.scored_file, args.eval_file)
        Path(args.out).write_text(markdown, encoding="utf-8")
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 2
    except (ValueError, KeyError, TypeError, OverflowError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
