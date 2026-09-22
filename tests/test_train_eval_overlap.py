"""Overlap checker must fail on a copied eval prompt and pass on unrelated text."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_train_eval_overlap.py"
PREFIX = "Translate into Marathi: The monsoon usually arrives"


def write_jsonl(folder, name, rows):
    path = Path(folder) / name
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


class OverlapTests(unittest.TestCase):
    def run_check(self, eval_rows, dpo_rows):
        with tempfile.TemporaryDirectory() as directory:
            eval_path = write_jsonl(directory, "eval.jsonl", eval_rows)
            sft_path = write_jsonl(directory, "sft.jsonl", [{
                "id": "SFT-1",
                "messages": [{"role": "user", "content": "unrelated question"}],
            }])
            dpo_path = write_jsonl(directory, "dpo.jsonl", dpo_rows)
            return subprocess.run(
                [sys.executable, str(SCRIPT),
                 "--eval", str(eval_path), "--sft", str(sft_path), "--dpo", str(dpo_path)],
                capture_output=True, text=True, check=False,
            )

    def test_equal_prompt_fails(self):
        prompt = "Translate into Marathi: Could you please repeat what the doctor said about the medicine dosage?"
        result = self.run_check(
            [{"id": "MBL-0010", "prompt": prompt}],
            [{"id": "DPO-0011", "prompt": prompt}],
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("DPO-0011", result.stdout)
        self.assertIn("equal", result.stdout)

    def test_shared_prefix_fails(self):
        result = self.run_check(
            [{"id": "MBL-0009", "prompt": PREFIX + " in Maharashtra by the first week of June."}],
            [{"id": "DPO-0013", "prompt": PREFIX + " by the first week of June."}],
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("prefix", result.stdout)

    def test_unrelated_prompts_pass(self):
        result = self.run_check(
            [{"id": "MBL-0009", "prompt": PREFIX + " in Maharashtra by the first week of June."}],
            [{"id": "DPO-0013", "prompt": "Translate into Marathi: The winter exam timetable will be put up next week."}],
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("status: OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
