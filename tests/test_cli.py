import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, timedelta
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import student_companion  # noqa: E402

SCRIPT = ROOT / "scripts" / "student_companion.py"
TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()


class StudentCompanionCliTest(unittest.TestCase):
    def run_cli(self, data_file, *args):
        output = StringIO()
        with redirect_stdout(output):
            student_companion.main(["--data", str(data_file), *args])
        return output.getvalue()

    def run_cli_error(self, data_file, *args):
        """Run the CLI expecting a SystemExit; return (exit_code, stderr)."""
        stderr = StringIO()
        with redirect_stdout(StringIO()), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                student_companion.main(["--data", str(data_file), *args])
        return ctx.exception.code, stderr.getvalue()

    def read_store(self, data_file):
        return json.loads(Path(data_file).read_text(encoding="utf-8"))

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


class ConcurrencyAndAtomicWriteTest(unittest.TestCase):
    """Issue 1: concurrent read-modify-write must not lose updates."""

    def run_cli(self, data_file, *args):
        with redirect_stdout(StringIO()):
            student_companion.main(["--data", str(data_file), *args])

    def test_concurrent_writes_no_lost_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_file = Path(tmp) / "student-data.json"
            self.run_cli(data_file, "init", "--student", "小明")

            worker_count = 8
            processes = []
            for index in range(worker_count):
                processes.append(
                    subprocess.Popen(
                        [
                            sys.executable,
                            str(SCRIPT),
                            "--data",
                            str(data_file),
                            "record",
                            "score",
                            "--student",
                            "小明",
                            "--subject",
                            "数学",
                            "--title",
                            f"测验{index}",
                            "--score",
                            "80",
                            "--max-score",
                            "100",
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                )
            for process in processes:
                self.assertEqual(process.wait(), 0)

            store = json.loads(data_file.read_text(encoding="utf-8"))
            records = store["students"]["小明"]["records"]
            self.assertEqual(
                len(records),
                worker_count,
                f"lost updates: expected {worker_count} records, got {len(records)}",
            )
            ids = [record["id"] for record in records]
            self.assertEqual(len(set(ids)), worker_count, "duplicate ids under concurrency")
            self.assertTrue(
                (Path(str(data_file) + ".lock")).exists(),
                "expected a sibling lock file",
            )
            leftovers = list(Path(tmp).glob("*.tmp"))
            self.assertEqual(leftovers, [], "atomic write left temp files behind")

    def test_save_store_rejects_nan(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_file = Path(tmp) / "student-data.json"
            student_companion.DATA_PATH_OVERRIDE = data_file
            try:
                with self.assertRaises(ValueError):
                    student_companion.save_store({"students": {}, "bad": float("nan")})
            finally:
                student_companion.DATA_PATH_OVERRIDE = None


class ScoreValidationTest(unittest.TestCase):
    """Issue 2: NaN/Infinity/negative/out-of-range scores rejected everywhere."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_file = Path(self.tmp.name) / "student-data.json"
        with redirect_stdout(StringIO()):
            student_companion.main(
                ["--data", str(self.data_file), "init", "--student", "小明"]
            )

    def run_cli_error(self, *args):
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                student_companion.main(["--data", str(self.data_file), *args])

    def record_count(self):
        store = json.loads(self.data_file.read_text(encoding="utf-8"))
        return len(store["students"]["小明"]["records"])

    def assert_score_rejected(self, score, max_score):
        self.run_cli_error(
            "record",
            "score",
            "--student",
            "小明",
            "--subject",
            "数学",
            "--title",
            "测验",
            "--score",
            score,
            "--max-score",
            max_score,
        )
        self.assertEqual(self.record_count(), 0, "invalid score must not be stored")

    def test_nan_rejected(self):
        self.assert_score_rejected("nan", "100")

    def test_infinity_rejected(self):
        self.assert_score_rejected("inf", "100")
        self.assert_score_rejected("80", "inf")

    def test_negative_rejected(self):
        self.assert_score_rejected("-5", "100")

    def test_score_above_max_rejected(self):
        self.assert_score_rejected("120", "100")

    def test_zero_or_negative_max_rejected(self):
        self.assert_score_rejected("80", "0")
        self.assert_score_rejected("80", "-100")

    def test_boundary_values_accepted(self):
        with redirect_stdout(StringIO()):
            student_companion.main(
                [
                    "--data",
                    str(self.data_file),
                    "record",
                    "score",
                    "--student",
                    "小明",
                    "--subject",
                    "数学",
                    "--title",
                    "满分",
                    "--score",
                    "100",
                    "--max-score",
                    "100",
                ]
            )
        self.assertEqual(self.record_count(), 1)
        store = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.assertEqual(store["students"]["小明"]["records"][0]["score"], 100.0)

    def test_score_signal_ignores_non_finite_legacy_data(self):
        self.assertIsNone(student_companion.score_signal({"score": float("nan"), "max_score": 100}))
        self.assertIsNone(student_companion.score_signal({"score": 80, "max_score": float("inf")}))


class AtomicImportTest(unittest.TestCase):
    """Issue 3: import validates all rows first; any error aborts with no writes."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_file = Path(self.tmp.name) / "student-data.json"
        with redirect_stdout(StringIO()):
            student_companion.main(
                ["--data", str(self.data_file), "init", "--student", "小明"]
            )

    def test_partial_failure_aborts_entire_import(self):
        bad_json = Path(self.tmp.name) / "bad.json"
        bad_json.write_text(
            json.dumps(
                [
                    {"type": "score", "subject": "数学", "title": "好", "score": 80, "max_score": 100},
                    {"type": "score", "subject": "数学", "title": "坏", "score": 150, "max_score": 100},
                    {"type": "homework", "subject": "语文", "title": "作业", "status": "bogus"},
                ]
            ),
            encoding="utf-8",
        )
        stderr = StringIO()
        with redirect_stdout(StringIO()), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                student_companion.main(
                    ["--data", str(self.data_file), "import", str(bad_json), "--student", "小明"]
                )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIn("row 2", stderr.getvalue())
        self.assertIn("row 3", stderr.getvalue())
        store = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.assertEqual(
            store["students"]["小明"]["records"],
            [],
            "failed import must not write partial data",
        )

    def test_import_rejects_nan_score(self):
        nan_json = Path(self.tmp.name) / "nan.json"
        # json.loads accepts NaN by default; validation must still reject it.
        nan_json.write_text(
            '[{"type": "score", "subject": "数学", "title": "坏", "score": NaN, "max_score": 100}]',
            encoding="utf-8",
        )
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                student_companion.main(
                    ["--data", str(self.data_file), "import", str(nan_json), "--student", "小明"]
                )
        store = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.assertEqual(store["students"]["小明"]["records"], [])

    def test_valid_import_still_works(self):
        output = StringIO()
        with redirect_stdout(output):
            student_companion.main(
                [
                    "--data",
                    str(self.data_file),
                    "import",
                    str(ROOT / "examples" / "sample_records.csv"),
                    "--student",
                    "小明",
                ]
            )
        self.assertIn("Imported 5 records", output.getvalue())
        store = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.assertEqual(len(store["students"]["小明"]["records"]), 5)


class EvidenceAnalysisTest(unittest.TestCase):
    """Issue 4: evidence is qualitative — candidates or enrichment, never scored."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_file = Path(self.tmp.name) / "student-data.json"
        with redirect_stdout(StringIO()):
            student_companion.main(
                ["--data", str(self.data_file), "init", "--student", "小明"]
            )

    def run_cli(self, *args):
        output = StringIO()
        with redirect_stdout(output):
            student_companion.main(["--data", str(self.data_file), *args])
        return output.getvalue()

    def analyze(self):
        return json.loads(self.run_cli("analyze", "--student", "小明", "--format", "json"))

    def test_evidence_only_yields_candidates_not_weak_points(self):
        self.run_cli(
            "record",
            "evidence",
            "--student",
            "小明",
            "--subject",
            "数学",
            "--source-type",
            "image",
            "--source-path",
            "paper.jpg",
            "--extracted-text",
            "试卷显示分数应用题错了两道，" + "细节很多。" * 100,
            "--knowledge",
            "分数应用题",
        )
        analysis = self.analyze()
        self.assertEqual(analysis["weak_points"], [], "evidence must not fabricate weak points")
        self.assertEqual(analysis["subject_summary"], [])
        candidates = analysis["evidence_candidates"]
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["status"], "pending_confirmation")
        self.assertEqual(candidates[0]["knowledge_points"], ["分数应用题"])
        self.assertLessEqual(len(candidates[0]["extracted_text"]), 160, "text must be truncated")

        markdown = self.run_cli("analyze", "--student", "小明")
        self.assertIn("待确认证据", markdown)
        self.assertIn("待确认", markdown)

    def test_evidence_enriches_matching_weak_point(self):
        self.run_cli(
            "record", "score", "--student", "小明", "--subject", "数学",
            "--title", "期中", "--score", "55", "--max-score", "100",
            "--knowledge", "分数应用题",
        )
        self.run_cli(
            "record", "evidence", "--student", "小明", "--subject", "数学",
            "--source-type", "image", "--source-path", "paper.jpg",
            "--extracted-text", "第 4 题审题错误，单位漏写。",
            "--knowledge", "分数应用题",
        )
        analysis = self.analyze()
        self.assertEqual(analysis["evidence_candidates"], [])
        weak = analysis["weak_points"][0]
        self.assertEqual(weak["knowledge_point"], "分数应用题")
        self.assertTrue(
            any("第 4 题审题错误" in entry for entry in weak["evidence"]),
            f"extracted text should enrich the weak point: {weak['evidence']}",
        )


class ProgressSignalTest(unittest.TestCase):
    """Issue 5: not_started carries no capability signal."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_file = Path(self.tmp.name) / "student-data.json"

    def run_cli(self, *args):
        output = StringIO()
        with redirect_stdout(output):
            student_companion.main(["--data", str(self.data_file), *args])
        return output.getvalue()

    def test_not_started_generates_no_weak_point(self):
        self.run_cli("init", "--student", "小明")
        self.run_cli(
            "record", "progress", "--student", "小明", "--subject", "数学",
            "--unit", "圆柱体积", "--status", "not_started", "--knowledge", "圆柱体积",
        )
        analysis = json.loads(self.run_cli("analyze", "--student", "小明", "--format", "json"))
        self.assertEqual(analysis["weak_points"], [])
        self.assertEqual(analysis["subject_summary"], [])

    def test_blocked_still_generates_weak_point(self):
        self.run_cli("init", "--student", "小明")
        self.run_cli(
            "record", "progress", "--student", "小明", "--subject", "数学",
            "--unit", "分数应用题单元", "--status", "blocked", "--knowledge", "分数应用题",
        )
        analysis = json.loads(self.run_cli("analyze", "--student", "小明", "--format", "json"))
        self.assertEqual(len(analysis["weak_points"]), 1)
        self.assertEqual(analysis["weak_points"][0]["severity"], "high")


class DaysWindowTest(unittest.TestCase):
    """Issue 7: --days N covers exactly N calendar dates; non-positive rejected."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_file = Path(self.tmp.name) / "student-data.json"

    def run_cli(self, *args):
        output = StringIO()
        with redirect_stdout(output):
            student_companion.main(["--data", str(self.data_file), *args])
        return output.getvalue()

    def record_on(self, day, title):
        self.run_cli(
            "record", "score", "--student", "小明", "--subject", "数学",
            "--title", title, "--score", "80", "--max-score", "100", "--date", day,
        )

    def test_days_one_covers_only_today(self):
        self.run_cli("init", "--student", "小明")
        self.record_on(TODAY, "今天")
        self.record_on(YESTERDAY, "昨天")
        analysis = json.loads(
            self.run_cli("analyze", "--student", "小明", "--days", "1", "--format", "json")
        )
        self.assertEqual(analysis["record_count"], 1, "--days 1 must cover exactly today")

    def test_days_two_covers_today_and_yesterday(self):
        self.run_cli("init", "--student", "小明")
        self.record_on(TODAY, "今天")
        self.record_on(YESTERDAY, "昨天")
        analysis = json.loads(
            self.run_cli("analyze", "--student", "小明", "--days", "2", "--format", "json")
        )
        self.assertEqual(analysis["record_count"], 2)

    def test_non_positive_days_rejected(self):
        self.run_cli("init", "--student", "小明")
        for command in ("analyze", "report"):
            for bad in ("0", "-3"):
                with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                    with self.assertRaises(SystemExit):
                        student_companion.main(
                            [
                                "--data", str(self.data_file),
                                command, "--student", "小明", "--days", bad,
                            ]
                        )


class UnknownStudentTest(unittest.TestCase):
    """Issue 8: read-only commands must not create students on typos."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_file = Path(self.tmp.name) / "student-data.json"

    def run_cli(self, *args):
        output = StringIO()
        with redirect_stdout(output):
            student_companion.main(["--data", str(self.data_file), *args])
        return output.getvalue()

    def assert_unknown_student_fails(self, *args):
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                student_companion.main(["--data", str(self.data_file), *args])
        self.assertIn("No data for student: 小名", str(ctx.exception))

    def test_status_unknown_student(self):
        self.assert_unknown_student_fails("status", "--student", "小名")
        self.assertFalse(
            self.data_file.exists(),
            "status on an unknown student must not create the store",
        )

    def test_followup_list_unknown_student(self):
        self.run_cli("init", "--student", "小明")
        self.assert_unknown_student_fails("followup", "list", "--student", "小名")
        store = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.assertNotIn("小名", store["students"], "typo must not create a student")

    def test_status_and_list_work_for_existing_student(self):
        self.run_cli("init", "--student", "小明")
        status = self.run_cli("status", "--student", "小明")
        self.assertIn("Student: 小明", status)
        followups = self.run_cli("followup", "list", "--student", "小明")
        self.assertIn("No follow-ups", followups)


class MarkdownReportTest(unittest.TestCase):
    """Extra: suggestion_for teacher_action must appear in the Markdown report."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_file = Path(self.tmp.name) / "student-data.json"

    def run_cli(self, *args):
        output = StringIO()
        with redirect_stdout(output):
            student_companion.main(["--data", str(self.data_file), *args])
        return output.getvalue()

    def test_report_includes_teacher_action(self):
        self.run_cli("init", "--student", "小明")
        self.run_cli(
            "record", "score", "--student", "小明", "--subject", "数学",
            "--title", "期中", "--score", "55", "--max-score", "100",
            "--knowledge", "分数应用题",
        )
        report = self.run_cli("report", "--student", "小明")
        self.assertIn("老师/辅导建议", report)
        self.assertIn("请老师或辅导老师确认", report)


if __name__ == "__main__":
    unittest.main()
