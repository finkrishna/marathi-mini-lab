#!/usr/bin/env python3
"""Summarise scored model outputs for Marathi Mini Lab.

Reads a JSONL file where each record has:
    id, prompt, model, answer, score, failure_tags, notes

and prints:
    - average score per model
    - count of each failure tag (per model + overall)
    - worst 10 examples by overall score

Usage:
    python3 scripts/score_outputs.py <scored.jsonl>

Stdlib only. Exit codes:
    0  summary printed
    1  at least one record failed to parse
    2  usage error or file unreadable
"""

import argparse
import json
import sys
from pathlib import Path

REQUIRED_FIELDS = ("id", "prompt", "model", "answer", "score", "failure_tags", "notes")
WORST_N = 10


def read_records(file_path: Path):
    """Yield (line_no, obj) for non-empty lines."""
    with file_path.open("r", encoding="utf-8") as fh:
        for i, raw in enumerate(fh, start=1):
            if raw.strip() == "":
                continue
            yield i, raw.rstrip("\n")


# Known canonical failure tags. Used to salvage hand-edited records where
# `failure_tags` was written without JSON string quoting (e.g.
# `[too_verbose, poor_marathi]` instead of `["too_verbose", "poor_marathi"]`).
CANONICAL_TAGS = {
    "poor_marathi", "too_hindi_like", "too_english", "translationese",
    "wrong_register", "missed_context", "hallucinated_fact", "unsafe_advice",
    "overconfident", "too_verbose", "too_generic", "bad_format",
    "failed_instruction", "weak_reasoning", "refused_unnecessarily",
}
ALIASES = {
    "success": None,
    "failed": "failed_instruction",
    "translitonese": "translationese",
    "over_confident": "overconfident",
    "tooo_verbose": "too_verbose",
}


def _salvage_tags(line):
    """Try to extract and quote a broken failure_tags list from a JSON line.

    Returns (rewritten_line, list_of_tags) or (original_line, None) if we
    couldn't find a salvageable pattern.
    """
    import re
    m = re.search(r'"failure_tags":\s*\[([^\]]*)\]', line)
    if not m:
        return line, None
    inner = m.group(1).strip()
    if inner == "":
        # Empty list — already valid JSON if it parsed. Should not reach here.
        return line, []
    # Split on anything that looks like a delimiter, drop quotes/brackets.
    raw_tokens = re.split(r"[,;]+", inner)
    tags = []
    for tok in raw_tokens:
        t = tok.strip().strip("`").strip('"').strip("'").strip()
        if not t:
            continue
        if t in CANONICAL_TAGS:
            tags.append(t)
        elif t in ALIASES:
            mapped = ALIASES[t]
            if mapped is not None:
                tags.append(mapped)
    new_json_list = json.dumps(tags, ensure_ascii=False)
    new_line = line[:m.start()] + '"failure_tags": ' + new_json_list + line[m.end():]
    return new_line, tags


def parse_record(line_no, line):
    """Return (obj, None) on success or (None, error_message).

    On JSON failures we attempt one repair: re-quoting a likely-broken
    `failure_tags` list and re-parsing. This makes the scorer tolerant of
    hand-edited records where tags were written without JSON string quotes.
    """
    try:
        obj = json.loads(line)
    except json.JSONDecodeError as e:
        # Try the salvage path before giving up.
        salvaged, tags = _salvage_tags(line)
        if tags is None:
            return None, f"line {line_no}: invalid JSON: {e.msg} (col {e.colno})"
        try:
            obj = json.loads(salvaged)
            obj["_salvaged_tags"] = True
            return obj, f"line {line_no}: repaired failure_tags -> {tags}"
        except json.JSONDecodeError as e2:
            return None, f"line {line_no}: invalid JSON (salvage failed): {e2.msg} (col {e2.colno})"
    if not isinstance(obj, dict):
        return None, f"line {line_no}: expected JSON object, got {type(obj).__name__}"
    for field in REQUIRED_FIELDS:
        if field not in obj:
            return None, f"line {line_no}: missing required field '{field}'"
    return obj, None


def coerce_score(raw):
    """Return float score or None if invalid."""
    try:
        s = float(raw)
    except (TypeError, ValueError):
        return None
    if s < 0 or s > 5:
        return None
    return s


def coerce_tags(raw):
    """Return list of str tags from raw (list or comma string)."""
    if isinstance(raw, list):
        return [str(t).strip() for t in raw if str(t).strip()]
    if isinstance(raw, str):
        return [t.strip() for t in raw.split(",") if t.strip()]
    return []


def summarise(records):
    """Build aggregates from parsed records."""
    by_model = {}
    tag_counts = {}
    total_per_model = {}

    for obj in records:
        model = str(obj.get("model", ""))
        score = coerce_score(obj.get("score"))
        tags = coerce_tags(obj.get("failure_tags"))
        rec_id = str(obj.get("id", ""))
        prompt = str(obj.get("prompt", ""))
        notes = str(obj.get("notes", ""))

        if score is None:
            obj["_score_invalid"] = True
            continue

        by_model.setdefault(model, []).append(score)
        total_per_model.setdefault(model, 0)
        total_per_model[model] += 1
        for tag in tags:
            key = (model, tag)
            tag_counts[key] = tag_counts.get(key, 0) + 1
            tag_counts[("ALL", tag)] = tag_counts.get(("ALL", tag), 0) + 1

        obj["_score_float"] = score
        obj["_tags_list"] = tags
        obj["_model_str"] = model
        obj["_id_str"] = rec_id
        obj["_prompt_str"] = prompt
        obj["_notes_str"] = notes
    return by_model, tag_counts, total_per_model


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="path to scored JSONL file")
    parser.add_argument("--worst", type=int, default=WORST_N,
                        help=f"number of worst examples to list (default {WORST_N})")
    args = parser.parse_args(argv)

    file_path = Path(args.file)
    if not file_path.is_file():
        print(f"error: file not found: {file_path}", file=sys.stderr)
        return 2

    records = []
    errors = []
    total = 0
    valid = 0
    invalid_score = 0

    for line_no, raw in read_records(file_path):
        total += 1
        obj, err = parse_record(line_no, raw)
        if obj is None:
            # Hard failure — could not parse even after salvage.
            if err is not None:
                errors.append(err)
            continue
        if err is not None:
            # Salvage succeeded — record warning but keep the obj.
            errors.append(err)
        score = coerce_score(obj.get("score"))
        if score is None:
            invalid_score += 1
            errors.append(f"line {line_no}: invalid score '{obj.get('score')}' (must be 0-5)")
            continue
        valid += 1
        records.append(obj)

    if total == 0:
        print(f"[{file_path}] no records found.", file=sys.stderr)
        return 2

    print(f"\n[{file_path}]")
    print(f"  total lines:   {total}")
    print(f"  valid records: {valid}")
    print(f"  salvaged:      {sum(1 for e in errors if 'repaired failure_tags' in e)}")
    print(f"  bad records:   {len(errors) - sum(1 for e in errors if 'repaired failure_tags' in e) - invalid_score}")
    print(f"  invalid_score: {invalid_score}")

    if not records:
        if errors:
            print("\n--- errors ---")
            for e in errors:
                print(e)
        return 1

    by_model, tag_counts, total_per_model = summarise(records)

    # Average score per model
    print("\n--- average score per model ---")
    print(f"{'model':<30} {'n':>5} {'avg':>7} {'min':>5} {'max':>5}")
    for model in sorted(by_model):
        scores = by_model[model]
        if not scores:
            continue
        avg = sum(scores) / len(scores)
        print(f"{model:<30} {len(scores):>5} {avg:>7.2f} {min(scores):>5.1f} {max(scores):>5.1f}")

    # Failure tag counts
    print("\n--- failure tags ---")
    models = sorted({m for (m, _) in tag_counts if m != "ALL"})
    tags = sorted({t for (_, t) in tag_counts if t != "ALL"})
    if not tags:
        print("  (no failure tags recorded)")
    else:
        header = f"{'tag':<25}" + f"{'ALL':>6}" + "".join(f"{m[:10]:>12}" for m in models)
        print(header)
        for tag in tags:
            row = f"{tag:<25}"
            row += f"{tag_counts.get(('ALL', tag), 0):>6}"
            for m in models:
                row += f"{tag_counts.get((m, tag), 0):>12}"
            print(row)

    # Worst N across all models
    worst_n = max(1, args.worst)
    scored = [r for r in records if "_score_float" in r]
    scored.sort(key=lambda r: (r["_score_float"], r["_model_str"], r["_id_str"]))
    worst = scored[:worst_n]

    print(f"\n--- worst {len(worst)} examples ---")
    print(f"{'id':<12} {'model':<26} {'score':>5}  {'tags':<25} {'prompt':<40}")
    for r in worst:
        tags_str = ",".join(r.get("_tags_list", [])) or "-"
        prompt_preview = r["_prompt_str"].replace("\n", " ")[:40]
        print(f"{r['_id_str']:<12} {r['_model_str']:<26} {r['_score_float']:>5.1f}  {tags_str:<25} {prompt_preview:<40}")

    if errors:
        print("\n--- errors / warnings ---")
        for e in errors:
            print(e)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
