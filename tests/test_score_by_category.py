import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.score_by_category import summarize


ROOT = Path(__file__).resolve().parents[1]


class ScoreByCategoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.evals = self.write("eval.jsonl", [
            {"id": "a", "category": "alpha"},
            {"id": "b", "category": "alpha"},
            {"id": "c", "category": "alpha"},
            {"id": "d", "category": "empty"},
        ])
        self.scored = self.write("scored.jsonl", [
            {"id": "a", "score": 3.5, "failure_tags": ["too_verbose"]},
            {"id": "b", "score": 4},
            {"id": "c", "score": None},
            {"id": "d"},
            {"id": "unknown", "score": 1, "failure_tags": ["bad_format"]},
        ])

    def write(self, name, rows):
        path = self.folder / name
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return path

    def run_script(self, script="score_by_category.py", scored=None, evals=None, extra=()):
        return subprocess.run([
            sys.executable, str(ROOT / "scripts" / script),
            str(scored or self.scored), "--eval-file", str(evals or self.evals), *extra,
        ], capture_output=True, text=True)

    def test_null_missing_half_scores_and_unknown(self):
        groups, overall, rows = summarize(self.scored, self.evals)
        self.assertEqual((groups["alpha"].n, groups["alpha"].average, groups["alpha"].unscored), (2, 3.75, 1))
        self.assertEqual((groups["UNKNOWN"].n, groups["UNKNOWN"].average), (1, 1.0))
        self.assertEqual((groups["empty"].n, groups["empty"].average, groups["empty"].unscored), (0, None, 1))
        self.assertEqual((overall.n, overall.unscored), (3, 2))
        self.assertAlmostEqual(overall.average, 2.833333333333333)
        self.assertEqual(len(rows), 3)

    def test_cli_table(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "category\tn\taverage\tunscored\nUNKNOWN\t1\t1.00\t0\nalpha\t2\t3.75\t1\nempty\t0\tN/A\t1\nOVERALL\t3\t2.83\t2\n")

    def test_missing_files_exit_two(self):
        for keyword in ("scored", "evals"):
            with self.subTest(keyword=keyword):
                result = self.run_script(**{keyword: self.folder / "missing.jsonl"})
                self.assertEqual(result.returncode, 2)

    def test_invalid_scores_exit_one(self):
        for score in ("bad", "3.5", True, [], {}, float("nan"), float("inf")):
            with self.subTest(score=score):
                path = self.write("invalid.jsonl", [{"id": "a", "score": score}])
                result = self.run_script(scored=path)
                self.assertEqual(result.returncode, 1)
                self.assertIn("score", result.stderr)

    def test_no_scored_items(self):
        path = self.write("unscored.jsonl", [{"id": "a", "score": None}])
        result = self.run_script(scored=path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OVERALL\t0\tN/A\t1", result.stdout)

    def test_renderer(self):
        out = self.folder / "summary.md"
        result = self.run_script("render_baseline_report.py", extra=("--out", str(out)))
        self.assertEqual(result.returncode, 0, result.stderr)
        markdown = out.read_text(encoding="utf-8")
        first_paragraph = markdown.split("\n\n")[1]
        for phrase in ("existing lab scores copied from the JSONL", "not a new judgment", "not native-speaker gold"):
            self.assertIn(phrase, first_paragraph)
        self.assertIn("| alpha | 2 | 3.75 | 1 |", markdown)
        self.assertIn("| UNKNOWN | 1 | 1.00 | 0 |", markdown)
        self.assertIn("| OVERALL | 3 | 2.83 | 2 |", markdown)
        self.assertIn("| unknown | 1 | bad_format |", markdown)
        self.assertIn("| a | 3.5 | too_verbose |", markdown)
        self.assertLess(markdown.index("| unknown |"), markdown.index("| a |"))


if __name__ == "__main__":
    unittest.main()
