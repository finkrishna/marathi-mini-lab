#!/usr/bin/env python3
"""Interactive scorer for Marathi Mini Lab outputs.

Reads an unscored (or partially scored) outputs JSONL, shows each prompt +
answer, and prompts you to enter score, failure tags, and notes. Writes valid
JSONL to the same file in place (preserving any already-scored records).

Usage:
    python3 scripts/interactive_score.py outputs/baseline_<model>_RUN-004.jsonl
    python3 scripts/interactive_score.py <file.jsonl> --start 6   # resume from record 6
    python3 scripts/interactive_score.py <file.jsonl> --skip-scored

You enter:
    score (1-5)         : a number, or empty to keep existing score
    failure tags         : comma-separated, e.g. "too_verbose,poor_marathi"
                           or empty for none. Canonical tags listed.
    notes                : any free text, or empty
    q                    : (at any prompt) save & quit
    s                    : (at any prompt) skip this record without scoring

Stdlib only.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TAGS_FILE = REPO_ROOT / "evals" / "failure_tags.md"

# Canonical tags parsed from evals/failure_tags.md on first run.
CANONICAL_TAGS = []


def load_canonical_tags():
    """Parse the tag names out of evals/failure_tags.md table."""
    if not TAGS_FILE.is_file():
        return []
    tags = []
    pattern = re.compile(r"^\|\s*`([a-z_]+)`\s*\|")
    with TAGS_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            m = pattern.match(line)
            if m:
                tags.append(m.group(1))
    return tags


def _closest(tag, canonical):
    """Return the closest canonical tag by edit distance (heuristic)."""
    import difflib
    matches = difflib.get_close_matches(tag, canonical, n=1, cutoff=0.6)
    return matches[0] if matches else None


ALIASES = {
    "success": None,
    "failed": "failed_instruction",
    "translitonese": "translationese",
    "over_confident": "overconfident",
    "tooo_verbose": "too_verbose",
    "missed_context": "missed_context",
}


def parse_tags_input(raw):
    """Turn a typed tag string into a list of canonical, validated tags.

    Accepts commas, semicolons, spaces, quotes, brackets — whatever you
    type, we extract the tag tokens, fix common typos, and map unknowns
    to their closest canonical neighbour (with a confirmation prompt).
    """
    raw_tags = [t.strip().strip("`").strip('"').strip("'")
                for t in re.split(r"[,;\s\[\]]+", raw) if t.strip().strip("`").strip('"').strip("'")]
    out = []
    for t in raw_tags:
        if t in CANONICAL_TAGS:
            out.append(t)
            continue
        if t in ALIASES:
            mapped = ALIASES[t]
            if mapped is None:
                print(f"  tag '{t}': not a failure tag (success-like) — skipping.")
            else:
                print(f"  tag '{t}': mapped to '{mapped}' (alias).")
                out.append(mapped)
            continue
        # Try fuzzy match against the canonical list.
        guess = _closest(t, CANONICAL_TAGS)
        if guess:
            ans = input(f"  tag '{t}' not canonical. Use '{guess}' instead? [Y/n] ").strip().lower()
            if ans in ("", "y", "yes"):
                out.append(guess)
            else:
                print(f"  tag '{t}': dropped (not in canonical list, see evals/failure_tags.md).")
        else:
            print(f"  tag '{t}': skipped — no close match in canonical list.")
    return out


def load_records(file_path):
    """Yield (line_no, obj_or_None, raw_line) per non-empty line."""
    with file_path.open("r", encoding="utf-8") as fh:
        for i, raw in enumerate(fh, start=1):
            if raw.strip() == "":
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                obj = None
            yield i, obj, raw.rstrip("\n")


def prompt_user(obj, idx, total):
    """Show the record and prompt for score/tags/notes. Return updated obj or None to skip."""
    print()
    print("=" * 72)
    print(f"Record {idx}/{total}  id={obj.get('id','?')}  model={obj.get('model','?')}")
    print("-" * 72)
    print("PROMPT:")
    print(obj.get("prompt", "").strip())
    print("-" * 72)
    print("ANSWER:")
    ans = obj.get("answer", "").strip()
    print(ans if ans else "(empty answer)")
    print("-" * 72)
    if obj.get("score") is not None:
        print(f"  existing score: {obj['score']}  tags: {obj.get('failure_tags', [])}")
        print("  (press Enter on any field to keep existing value)")

    score_in = input("score (1-5, or q=quit/s=skip): ").strip()
    if score_in.lower() == "q":
        return "QUIT"
    if score_in.lower() == "s":
        return None
    if score_in == "":
        if obj.get("score") is None:
            print("  no existing score; skipping.")
            return None
        score = obj["score"]
        try:
            score = float(score)
        except (TypeError, ValueError):
            print(f"  existing score not a number: {score}; skipping.")
            return None
    else:
        try:
            score = float(score_in)
        except ValueError:
            print("  invalid score; record skipped.")
            return None
    if score < 0 or score > 5:
        print("  score out of 0-5 range; record skipped.")
        return None

    tags_in = input(f"failure tags (comma-sep, e.g. 'too_verbose,poor_marathi'): ").strip()
    if tags_in == "":
        tags = list(obj.get("failure_tags") or [])
    else:
        tags = parse_tags_input(tags_in)

    notes_in = input("notes: ").strip()
    if notes_in == "":
        notes = obj.get("notes", "")
    else:
        notes = notes_in

    new_obj = dict(obj)
    new_obj["score"] = score
    new_obj["failure_tags"] = tags
    new_obj["notes"] = notes
    return new_obj


def main(argv=None):
    global CANONICAL_TAGS

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="path to outputs JSONL")
    parser.add_argument("--start", type=int, default=1,
                        help="record number to start at (1-indexed)")
    parser.add_argument("--skip-scored", action="store_true",
                        help="skip records that already have a numeric score")
    args = parser.parse_args(argv)

    file_path = Path(args.file)
    if not file_path.is_file():
        print(f"error: file not found: {file_path}", file=sys.stderr)
        return 2

    CANONICAL_TAGS = load_canonical_tags()
    print(f"Canonical tags loaded ({len(CANONICAL_TAGS)}):")
    print("  " + ", ".join(CANONICAL_TAGS))
    print()
    print(f"Scoring: {file_path}")
    print("Type 'q' at the score prompt to save and quit, 's' to skip a record.")

    records = list(load_records(file_path))
    total = len(records)
    # Pre-fill out_lines with the original raw lines so that if we quit
    # early, the unprocessed records are preserved unchanged.
    out_lines = [raw for (_, _, raw) in records]
    quit_after = False

    for idx, (line_no, obj, raw) in enumerate(records, start=1):
        if idx < args.start:
            continue
        if quit_after:
            break
        if obj is None:
            print(f"Record {idx}/{total}: line {line_no} is invalid JSON — kept as-is.")
            continue
        if args.skip_scored and obj.get("score") is not None:
            try:
                _ = float(obj["score"])
                continue
            except (TypeError, ValueError):
                pass

        result = prompt_user(obj, idx, total)
        if result == "QUIT":
            quit_after = True
            break
        if result is None:
            continue
        out_lines[idx - 1] = json.dumps(result, ensure_ascii=False)

    with file_path.open("w", encoding="utf-8") as fh:
        for line in out_lines:
            fh.write(line + "\n")

    print()
    print(f"Saved: {file_path}")
    if quit_after:
        print(f"Quit at record {idx}/{total}.")
    print(f"Next: python3 scripts/score_outputs.py {file_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
