#!/usr/bin/env python3
"""JSONL validator for Marathi Mini Lab datasets.

Usage:
    python3 scripts/validate_jsonl.py <file.jsonl>
    python3 scripts/validate_jsonl.py <file.jsonl> --eval
    python3 scripts/validate_jsonl.py <file.jsonl> --fields id,category,prompt

Stdlib only. Exit codes:
    0  file is valid JSONL (and fields present, if --eval / --fields given)
    1  at least one line failed validation
    2  usage error or file unreadable
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_EVAL_FIELDS = ("id", "category", "prompt", "expected_behavior")


def read_lines(file_path: Path):
    """Yield (line_no, line) for non-empty (after strip) lines.

    Blank trailing lines are tolerated (common with editors), but a blank
    line in the middle of the file is reported as a violation since JSONL
    sets are line-delimited records.
    """
    with file_path.open("r", encoding="utf-8") as fh:
        for i, raw in enumerate(fh, start=1):
            if raw.strip() == "":
                # Tolerate only a final trailing newline by checking if
                # this is the last line we are likely to see. We still
                # surface mid-file blanks by reporting them below.
                continue
            yield i, raw.rstrip("\n")


def validate_json(line_no: int, line: str):
    """Return (obj, None) on success or (None, error_message)."""
    try:
        return json.loads(line), None
    except json.JSONDecodeError as e:
        return None, f"line {line_no}: invalid JSON: {e.msg} (col {e.colno})"


def validate_fields(line_no: int, obj, required):
    """Return list of error messages for missing fields."""
    if not isinstance(obj, dict):
        return [f"line {line_no}: expected JSON object, got {type(obj).__name__}"]
    msgs = []
    for field in required:
        if field not in obj:
            msgs.append(f"line {line_no}: missing required field '{field}'")
        elif obj[field] is None or (isinstance(obj[field], str) and obj[field].strip() == ""):
            msgs.append(f"line {line_no}: field '{field}' is empty")
    return msgs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="JSONL file path")
    parser.add_argument(
        "--eval",
        action="store_true",
        help=f"check required eval fields: {', '.join(DEFAULT_EVAL_FIELDS)}",
    )
    parser.add_argument(
        "--fields",
        help="comma-separated list of required fields (overrides --eval)",
    )
    parser.add_argument(
        "--require-ids-unique",
        action="store_true",
        help="fail if the 'id' field is duplicated across records",
    )
    args = parser.parse_args(argv)

    file_path = Path(args.file)
    if not file_path.is_file():
        print(f"error: file not found: {file_path}", file=sys.stderr)
        return 2

    required = None
    if args.fields:
        required = tuple(f.strip() for f in args.fields.split(",") if f.strip())
    elif args.eval:
        required = DEFAULT_EVAL_FIELDS

    errors = []
    total = 0
    seen_ids = {}
    bad_lines = 0
    field_errors = 0
    blank_lines_midfile = 0
    dup_id_errors = 0

    last_nonblank = 0
    with file_path.open("r", encoding="utf-8") as fh:
        for i, raw in enumerate(fh, start=1):
            if raw.strip() == "":
                if last_nonblank and i != last_nonblank + 1:
                    blank_lines_midfile += 1
                    errors.append(f"line {i}: blank line inside file")
                continue
            last_nonblank = i

    # Re-iterate via read_lines for actual validation.
    for line_no, raw in read_lines(file_path):
        total += 1
        obj, err = validate_json(line_no, raw)
        if err is not None:
            bad_lines += 1
            errors.append(err)
            continue
        if required:
            msgs = validate_fields(line_no, obj, required)
            for m in msgs:
                field_errors += 1
                errors.append(m)
        if args.require_ids_unique and isinstance(obj, dict) and "id" in obj:
            id_val = obj["id"]
            if id_val in seen_ids:
                dup_id_errors += 1
                errors.append(
                    f"line {line_no}: duplicate id '{id_val}' first seen at line {seen_ids[id_val]}"
                )
            else:
                seen_ids[id_val] = line_no

    print(f"\n[{file_path}]")
    print(f"  records:      {total}")
    print(f"  bad_json:      {bad_lines}")
    print(f"  field_errors:  {field_errors}")
    print(f"  blank_midfile: {blank_lines_midfile}")
    print(f"  dup_ids:       {dup_id_errors}")
    if args.require_ids_unique:
        print(f"  unique_ids:    {len(seen_ids)}")

    no_errors = not errors
    if no_errors:
        print("  status:        OK")
        return 0
    print("  status:        FAILED")
    print("--- errors ---")
    for e in errors:
        print(e)
    return 1


if __name__ == "__main__":
    sys.exit(main())
