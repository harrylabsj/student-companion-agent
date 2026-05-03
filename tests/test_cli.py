import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import student_companion  # noqa: E402


class StudentCompanionCliTest(unittest.TestCase):
    def run_cli(self, data_file, *args):
        output = StringIO()
        with redirect_stdout(output):
            student_companion.main(["--data", str(data_file), *args])
        return output.getvalue()

    def test_full_parent_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_file = Path(tmp) / "student-data.json"
            report_file = Path(tmp) / "weekly.md"

            self.run_cli(data_file, "init", "--student", "小明", "--grade", "五年级")
            self.run_cli(data_file, "import", "examples/sample_records.csv", "--student", "小明")
            self.run_cli(
                data_file,
                "record",
                "evidence",
                "--student",
                "小明",
                "--subject",
                "数学",
                "--source-type",
                "audio",
                "--source-path",
                "teacher-feedback.ogg",
                "--extracted-text",
                "老师反馈：分数应用题审题不稳定，单位换算要复查。",
                "--knowledge",
                "分数应用题,单位换算",
            )
            self.run_cli(
                data_file,
                "followup",
                "add",
                "--student",
                "小明",
                "--subject",
                "数学",
                "--knowledge",
                "分数应用题",
                "--action",
                "复盘 5 道分数应用题",
            )

            analysis_result = self.run_cli(
                data_file, "analyze", "--student", "小明", "--format", "json"
            )
            analysis = json.loads(analysis_result)

            self.assertEqual(analysis["student"], "小明")
            self.assertGreaterEqual(analysis["record_count"], 6)
            self.assertIn("score", analysis["records_by_type"])
            self.assertIn("homework", analysis["records_by_type"])
            self.assertIn("progress", analysis["records_by_type"])
            self.assertIn("evidence", analysis["records_by_type"])
            self.assertTrue(
                any(point["knowledge_point"] == "分数应用题" for point in analysis["weak_points"])
            )
            self.assertTrue(analysis["open_followups"])

            self.run_cli(data_file, "report", "--student", "小明", "--output", str(report_file))
            report = report_file.read_text(encoding="utf-8")
            self.assertIn("薄弱知识点", report)
            self.assertIn("建议", report)
            self.assertIn("待跟踪事项", report)


if __name__ == "__main__":
    unittest.main()
