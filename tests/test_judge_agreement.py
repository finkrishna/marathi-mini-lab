"""CLI tests using synthetic temporary fixtures only."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "judge_agreement.py"


def item(record_id, score, tags=()):
    return {"id": record_id, "score": score, "failure_tags": list(tags)}


class JudgeAgreementTests(unittest.TestCase):
    def run_cli(self, human, judge):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ("human.jsonl", "judge.jsonl")]
            for path, records in zip(paths, (human, judge)):
                path.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
            return subprocess.run([sys.executable, str(SCRIPT), *map(str, paths)],
                                  capture_output=True, text=True, check=False)

    def metrics(self, human, judge):
        result = self.run_cli(human, judge)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return dict(line.split(": ", 1) for line in result.stdout.splitlines())

    def test_known_scores_joined_by_id(self):
        metrics = self.metrics([item("one", 5), item("two", 3)],
                               [item("two", 3), item("one", 4)])
        self.assertEqual(int(metrics["n"]), 2)
        self.assertEqual(float(metrics["mae"]), 0.5)
        self.assertEqual(int(metrics["exact"]), 1)
        self.assertEqual(int(metrics["within_half"]), 1)
        self.assertEqual(metrics["mae"], "0.500")

    def test_missing_judge_id(self):
        result = self.run_cli([item("missing", 5)], [])
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing", result.stderr)
        self.assertNotIn("mae", result.stdout)

    def test_tag_overlap(self):
        metrics = self.metrics([item("one", 3, ["a", "b"])],
                               [item("one", 3, ["b", "c"])])
        self.assertEqual(float(metrics["precision"]), 0.5)
        self.assertEqual(float(metrics["recall"]), 0.5)
        self.assertEqual(metrics["precision"], "0.500")
        self.assertEqual(metrics["recall"], "0.500")

    def test_no_tags(self):
        metrics = self.metrics([item("one", 3)], [item("one", 3)])
        self.assertEqual(metrics["precision"], "n/a")
        self.assertEqual(metrics["recall"], "n/a")

    def test_duplicate_judge_id(self):
        result = self.run_cli([item("one", 3)], [item("one", 3), item("one", 4)])
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate judge id 'one'", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_invalid_scores_on_either_side(self):
        for score in (True, False, "3", None, [], {}, float("nan"), float("inf")):
            for side in (0, 1):
                with self.subTest(score=score, side=side):
                    records = [[item("one", 3)], [item("one", 3)]]
                    records[side][0]["score"] = score
                    result = self.run_cli(*records)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("score", result.stderr)
                    self.assertEqual(result.stdout, "")

    def test_half_point_boundary(self):
        metrics = self.metrics([item("one", 3), item("two", 3)],
                               [item("one", 3.5), item("two", 3.501)])
        self.assertEqual(int(metrics["within_half"]), 1)

    def test_pooled_tag_sets(self):
        metrics = self.metrics([item("one", 3, ["a", "a", "b"]), item("two", 3, ["c"])],
                               [item("one", 3, ["a", "a"]), item("two", 3, ["d", "e", "f"])])
        self.assertEqual(metrics["precision"], "0.250")
        self.assertEqual(metrics["recall"], "0.333")

    def test_one_empty_tag_denominator(self):
        for human_tags, judge_tags, precision, recall in (([], ["a"], "0.000", "n/a"),
                                                         (["a"], [], "n/a", "0.000")):
            with self.subTest(human_tags=human_tags):
                metrics = self.metrics([item("one", 3, human_tags)], [item("one", 3, judge_tags)])
                self.assertEqual(metrics["precision"], precision)
                self.assertEqual(metrics["recall"], recall)


if __name__ == "__main__":
    unittest.main()
