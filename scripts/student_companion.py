#!/usr/bin/env python3
"""Student Companion Agent CLI.

Small, dependency-free storage and analysis helper for an OpenClaw/Hermes
education skill. It stores parent-provided learning evidence locally as JSON
and turns it into weak-point analysis, teaching suggestions, and follow-up
actions.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


APP_NAME = "student-companion-agent"
VERSION = "0.1.0"

HOME_DATA_PATH = (
    Path.home() / ".local" / "share" / APP_NAME / "student-data.json"
)
DATA_PATH_OVERRIDE: Optional[Path] = None

VALID_HOMEWORK_STATUS = {"completed", "needs_review", "missing", "late"}
VALID_PROGRESS_STATUS = {"not_started", "learning", "blocked", "reviewing", "mastered"}
VALID_EVIDENCE_TYPE = {"image", "audio", "file", "text"}


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def today_iso() -> str:
    return date.today().isoformat()


def data_path() -> Path:
    return (DATA_PATH_OVERRIDE or HOME_DATA_PATH).expanduser()


def load_store() -> Dict[str, Any]:
    path = data_path()
    if not path.exists():
        return {"version": VERSION, "students": {}}
    try:
        with path.open("r", encoding="utf-8") as handle:
            store = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Data file is not valid JSON: {path}\n{exc}") from exc
    store.setdefault("version", VERSION)
    store.setdefault("students", {})
    return store


def save_store(store: Dict[str, Any]) -> None:
    path = data_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, ensure_ascii=False, indent=2, sort_keys=True)


def parse_knowledge(value: Optional[str]) -> List[str]:
    if not value:
        return []
    parts = re.split(r"[,;，；、\n]+", value)
    return [part.strip() for part in parts if part.strip()]


def ensure_student(store: Dict[str, Any], name: str) -> Dict[str, Any]:
    students = store.setdefault("students", {})
    if name not in students:
        students[name] = {
            "profile": {
                "name": name,
                "grade": "",
                "school": "",
                "goals": [],
                "created_at": now_iso(),
                "updated_at": now_iso(),
            },
            "records": [],
            "followups": [],
        }
    students[name].setdefault("records", [])
    students[name].setdefault("followups", [])
    students[name].setdefault("profile", {"name": name})
    return students[name]


def next_id(items: Iterable[Dict[str, Any]]) -> int:
    max_id = 0
    for item in items:
        try:
            max_id = max(max_id, int(item.get("id", 0)))
        except (TypeError, ValueError):
            continue
    return max_id + 1


def parse_date(value: Optional[str]) -> str:
    if not value:
        return today_iso()
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    raise SystemExit(f"Invalid date '{value}'. Use YYYY-MM-DD.")


def cutoff_date(days: Optional[int]) -> Optional[date]:
    if not days:
        return None
    ordinal = date.today().toordinal() - days
    return date.fromordinal(ordinal)


def in_window(record: Dict[str, Any], days: Optional[int]) -> bool:
    cutoff = cutoff_date(days)
    if cutoff is None:
        return True
    raw = record.get("date") or record.get("created_at", "")[:10]
    try:
        record_date = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return True
    return record_date >= cutoff


def print_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))


def write_or_print(content: str, output: Optional[str]) -> None:
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"Report written: {path}")
    else:
        print(content)


def normalize_import_record(raw: Dict[str, Any], default_student: Optional[str]) -> Dict[str, Any]:
    record_type = (raw.get("type") or raw.get("record_type") or "").strip().lower()
    if not record_type:
        raise ValueError("missing type")
    student = (raw.get("student") or default_student or "").strip()
    if not student:
        raise ValueError("missing student")

    normalized: Dict[str, Any] = {
        "student": student,
        "type": record_type,
        "subject": (raw.get("subject") or "").strip(),
        "title": (raw.get("title") or raw.get("name") or "").strip(),
        "date": parse_date(str(raw.get("date") or "")) if raw.get("date") else today_iso(),
        "knowledge_points": parse_knowledge(
            raw.get("knowledge")
            or raw.get("knowledge_points")
            or raw.get("weak_points")
            or ""
        ),
        "notes": (raw.get("notes") or raw.get("note") or "").strip(),
    }

    if record_type == "score":
        normalized["score"] = float(raw.get("score"))
        normalized["max_score"] = float(raw.get("max_score") or raw.get("max") or 100)
    elif record_type == "homework":
        status = (raw.get("status") or "needs_review").strip()
        if status not in VALID_HOMEWORK_STATUS:
            raise ValueError(f"invalid homework status: {status}")
        normalized["status"] = status
    elif record_type == "progress":
        status = (raw.get("status") or "learning").strip()
        if status not in VALID_PROGRESS_STATUS:
            raise ValueError(f"invalid progress status: {status}")
        normalized["status"] = status
        normalized["unit"] = (raw.get("unit") or raw.get("title") or "").strip()
    elif record_type == "evidence":
        source_type = (raw.get("source_type") or "file").strip()
        if source_type not in VALID_EVIDENCE_TYPE:
            raise ValueError(f"invalid evidence source_type: {source_type}")
        normalized["source_type"] = source_type
        normalized["source_path"] = (raw.get("source_path") or raw.get("path") or "").strip()
        normalized["extracted_text"] = (
            raw.get("extracted_text") or raw.get("text") or ""
        ).strip()
    else:
        raise ValueError(f"unsupported type: {record_type}")
    return normalized


def append_record(store: Dict[str, Any], student_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
    student = ensure_student(store, student_name)
    record = dict(record)
    record.pop("student", None)
    record["id"] = next_id(student["records"])
    record.setdefault("date", today_iso())
    record.setdefault("created_at", now_iso())
    student["records"].append(record)
    student["profile"]["updated_at"] = now_iso()
    return record


def cmd_init(args: argparse.Namespace) -> None:
    store = load_store()
    student = ensure_student(store, args.student)
    profile = student["profile"]
    if args.grade is not None:
        profile["grade"] = args.grade
    if args.school is not None:
        profile["school"] = args.school
    if args.goal:
        goals = profile.setdefault("goals", [])
        for goal in args.goal:
            if goal not in goals:
                goals.append(goal)
    profile["updated_at"] = now_iso()
    save_store(store)
    print(f"Student initialized: {args.student}")
    print(f"Data file: {data_path()}")


def cmd_record_score(args: argparse.Namespace) -> None:
    if args.max_score <= 0:
        raise SystemExit("--max-score must be greater than zero")
    store = load_store()
    record = append_record(
        store,
        args.student,
        {
            "type": "score",
            "subject": args.subject,
            "title": args.title,
            "date": parse_date(args.date),
            "score": args.score,
            "max_score": args.max_score,
            "knowledge_points": parse_knowledge(args.knowledge),
            "notes": args.notes or "",
        },
    )
    save_store(store)
    accuracy = record["score"] / record["max_score"] * 100
    print(f"Score recorded #{record['id']}: {args.subject} {accuracy:.1f}%")


def cmd_record_homework(args: argparse.Namespace) -> None:
    store = load_store()
    record = append_record(
        store,
        args.student,
        {
            "type": "homework",
            "subject": args.subject,
            "title": args.title,
            "date": parse_date(args.date),
            "status": args.status,
            "knowledge_points": parse_knowledge(args.knowledge),
            "notes": args.notes or "",
        },
    )
    save_store(store)
    print(f"Homework recorded #{record['id']}: {args.subject} {args.status}")


def cmd_record_progress(args: argparse.Namespace) -> None:
    store = load_store()
    record = append_record(
        store,
        args.student,
        {
            "type": "progress",
            "subject": args.subject,
            "unit": args.unit,
            "title": args.unit,
            "date": parse_date(args.date),
            "status": args.status,
            "knowledge_points": parse_knowledge(args.knowledge),
            "notes": args.notes or "",
        },
    )
    save_store(store)
    print(f"Progress recorded #{record['id']}: {args.subject} {args.status}")


def cmd_record_evidence(args: argparse.Namespace) -> None:
    store = load_store()
    record = append_record(
        store,
        args.student,
        {
            "type": "evidence",
            "subject": args.subject or "",
            "title": args.title or f"{args.source_type} evidence",
            "date": parse_date(args.date),
            "source_type": args.source_type,
            "source_path": args.source_path or "",
            "extracted_text": args.extracted_text or "",
            "knowledge_points": parse_knowledge(args.knowledge),
            "notes": args.notes or "",
        },
    )
    save_store(store)
    print(f"Evidence recorded #{record['id']}: {args.source_type}")


def cmd_import(args: argparse.Namespace) -> None:
    source = Path(args.file)
    if not source.exists():
        raise SystemExit(f"Import file not found: {source}")

    if source.suffix.lower() == ".json":
        raw = json.loads(source.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "records" in raw:
            rows = raw["records"]
        elif isinstance(raw, list):
            rows = raw
        else:
            raise SystemExit("JSON import must be a list or an object with records.")
    elif source.suffix.lower() in {".csv", ".tsv"}:
        delimiter = "\t" if source.suffix.lower() == ".tsv" else ","
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter=delimiter))
    else:
        text = source.read_text(encoding="utf-8")
        rows = [
            {
                "type": "evidence",
                "student": args.student,
                "title": source.name,
                "source_type": "file",
                "source_path": str(source),
                "extracted_text": text,
                "notes": "Imported unstructured text file",
            }
        ]

    store = load_store()
    imported = 0
    errors: List[str] = []
    for index, raw_row in enumerate(rows, start=1):
        try:
            normalized = normalize_import_record(raw_row, args.student)
            append_record(store, normalized["student"], normalized)
            imported += 1
        except Exception as exc:  # noqa: BLE001 - report all row issues to the parent/operator
            errors.append(f"row {index}: {exc}")
    save_store(store)

    print(f"Imported {imported} records from {source}")
    if errors:
        print("Import warnings:")
        for error in errors:
            print(f"- {error}")


def score_signal(record: Dict[str, Any]) -> Optional[float]:
    try:
        max_score = float(record.get("max_score", 0))
        if max_score <= 0:
            return None
        return max(0.0, min(1.0, float(record.get("score", 0)) / max_score))
    except (TypeError, ValueError):
        return None


def homework_signal(status: str) -> float:
    return {
        "completed": 0.92,
        "needs_review": 0.55,
        "late": 0.45,
        "missing": 0.2,
    }.get(status, 0.55)


def progress_signal(status: str) -> float:
    return {
        "mastered": 0.95,
        "reviewing": 0.72,
        "learning": 0.62,
        "blocked": 0.28,
        "not_started": 0.2,
    }.get(status, 0.6)


def record_evidence_summary(record: Dict[str, Any]) -> str:
    title = record.get("title") or record.get("unit") or record.get("source_path") or "record"
    record_type = record.get("type")
    if record_type == "score":
        signal = score_signal(record)
        pct = f"{signal * 100:.0f}%" if signal is not None else "unknown"
        return f"{record.get('date')}: {record.get('subject')} {title} {pct}"
    if record_type == "homework":
        return f"{record.get('date')}: {record.get('subject')} {title} homework {record.get('status')}"
    if record_type == "progress":
        return f"{record.get('date')}: {record.get('subject')} {title} progress {record.get('status')}"
    if record_type == "evidence":
        return f"{record.get('date')}: {record.get('source_type')} evidence {title}"
    return f"{record.get('date')}: {title}"


def analyze_student(store: Dict[str, Any], student_name: str, days: Optional[int]) -> Dict[str, Any]:
    students = store.get("students", {})
    if student_name not in students:
        raise SystemExit(f"No data for student: {student_name}")
    student = students[student_name]
    records = [r for r in student.get("records", []) if in_window(r, days)]

    buckets: Dict[tuple, Dict[str, Any]] = {}
    subject_totals: Dict[str, List[float]] = defaultdict(list)
    evidence_count_by_type: Dict[str, int] = defaultdict(int)

    for record in records:
        record_type = record.get("type", "")
        evidence_count_by_type[record_type] += 1
        subject = record.get("subject") or "未标注科目"
        points = record.get("knowledge_points") or []
        if not points:
            if record_type in {"score", "homework", "progress"}:
                points = ["未标注知识点"]
            else:
                continue

        signal: Optional[float] = None
        if record_type == "score":
            signal = score_signal(record)
        elif record_type == "homework":
            signal = homework_signal(record.get("status", "needs_review"))
        elif record_type == "progress":
            signal = progress_signal(record.get("status", "learning"))

        if signal is not None:
            subject_totals[subject].append(signal)

        for point in points:
            key = (subject, point)
            bucket = buckets.setdefault(
                key,
                {
                    "subject": subject,
                    "knowledge_point": point,
                    "signals": [],
                    "score_records": 0,
                    "homework_records": 0,
                    "progress_records": 0,
                    "evidence": [],
                    "notes": [],
                },
            )
            if signal is not None:
                bucket["signals"].append(signal)
            if record_type == "score":
                bucket["score_records"] += 1
            elif record_type == "homework":
                bucket["homework_records"] += 1
            elif record_type == "progress":
                bucket["progress_records"] += 1
            bucket["evidence"].append(record_evidence_summary(record))
            if record.get("notes"):
                bucket["notes"].append(record["notes"])

    weak_points = []
    for bucket in buckets.values():
        signals = bucket["signals"]
        if not signals:
            continue
        avg = sum(signals) / len(signals)
        repeated = len(signals)
        confidence = "high" if repeated >= 3 else "medium" if repeated == 2 else "low"
        severity_score = (1 - avg) * 100 + min(15, max(0, repeated - 1) * 5)
        severity = "high" if avg < 0.6 or severity_score >= 45 else "medium" if avg < 0.78 else "low"
        weak_points.append(
            {
                "subject": bucket["subject"],
                "knowledge_point": bucket["knowledge_point"],
                "performance": round(avg, 3),
                "severity": severity,
                "confidence": confidence,
                "signals": repeated,
                "score_records": bucket["score_records"],
                "homework_records": bucket["homework_records"],
                "progress_records": bucket["progress_records"],
                "evidence": bucket["evidence"][-4:],
                "notes": bucket["notes"][-3:],
            }
        )

    weak_points.sort(
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}[item["severity"]],
            item["performance"],
            -item["signals"],
        )
    )

    subject_summary = []
    for subject, signals in sorted(subject_totals.items()):
        avg = sum(signals) / len(signals)
        subject_summary.append(
            {
                "subject": subject,
                "performance": round(avg, 3),
                "records": len(signals),
                "status": "needs_attention" if avg < 0.7 else "stable" if avg < 0.85 else "strong",
            }
        )

    open_followups = [
        item
        for item in student.get("followups", [])
        if item.get("status", "open") != "completed"
    ]

    return {
        "student": student_name,
        "profile": student.get("profile", {}),
        "window_days": days,
        "record_count": len(records),
        "records_by_type": dict(sorted(evidence_count_by_type.items())),
        "subject_summary": subject_summary,
        "weak_points": weak_points,
        "open_followups": open_followups,
        "generated_at": now_iso(),
    }


def suggestion_for(point: Dict[str, Any]) -> Dict[str, str]:
    subject = point["subject"]
    knowledge = point["knowledge_point"]
    performance = point["performance"]
    if performance < 0.55:
        intensity = "先补概念，再做少量题"
        parent_action = f"本周安排 3 次 15 分钟复盘：让孩子口头讲清「{knowledge}」的解题步骤，再做 5 道基础题。"
    elif performance < 0.75:
        intensity = "用错题做针对训练"
        parent_action = f"从最近错题中挑 3 道「{knowledge}」题，让孩子写出错因和正确步骤，隔 2 天重做。"
    else:
        intensity = "保持复现，防止遗忘"
        parent_action = f"每周抽查 2 道「{knowledge}」变式题，确认不是靠记忆答案完成。"
    teacher_action = f"请老师或辅导老师确认 {subject} 的「{knowledge}」是否属于当前单元核心点，并补 1 次小测。"
    success_signal = f"下一次 {subject} 作业或小测中，{knowledge} 正确率达到 80% 以上。"
    return {
        "subject": subject,
        "knowledge_point": knowledge,
        "focus": intensity,
        "parent_action": parent_action,
        "teacher_action": teacher_action,
        "success_signal": success_signal,
    }


def build_markdown_analysis(analysis: Dict[str, Any]) -> str:
    lines = [
        f"# {analysis['student']} 学习分析",
        "",
        f"- 生成时间：{analysis['generated_at']}",
        f"- 数据窗口：{'全部记录' if not analysis['window_days'] else str(analysis['window_days']) + ' 天'}",
        f"- 记录数：{analysis['record_count']}",
        "",
        "## 分科概览",
        "",
    ]
    if analysis["subject_summary"]:
        for item in analysis["subject_summary"]:
            lines.append(
                f"- {item['subject']}：{item['performance'] * 100:.0f}%（{item['records']} 条信号，{item['status']}）"
            )
    else:
        lines.append("- 暂无足够的分科数据。")

    lines.extend(["", "## 薄弱知识点", ""])
    if analysis["weak_points"]:
        for index, point in enumerate(analysis["weak_points"][:8], start=1):
            lines.append(
                f"{index}. **{point['subject']} / {point['knowledge_point']}**："
                f"{point['severity']}，表现 {point['performance'] * 100:.0f}%，"
                f"证据强度 {point['confidence']}"
            )
            for evidence in point["evidence"][:3]:
                lines.append(f"   - 证据：{evidence}")
            for note in point["notes"][:2]:
                lines.append(f"   - 备注：{note}")
    else:
        lines.append("- 暂未识别出薄弱点。请补充成绩、作业或进度记录。")

    lines.extend(["", "## 建议", ""])
    if analysis["weak_points"]:
        for item in [suggestion_for(point) for point in analysis["weak_points"][:3]]:
            lines.append(f"- {item['subject']}「{item['knowledge_point']}」：{item['parent_action']}")
            lines.append(f"  验收信号：{item['success_signal']}")
    else:
        lines.append("- 先补充最近 2-3 次作业或测验，再生成稳定建议。")

    lines.extend(["", "## 待跟踪事项", ""])
    if analysis["open_followups"]:
        for item in analysis["open_followups"]:
            due = item.get("due") or "未设置"
            lines.append(
                f"- #{item['id']} {item.get('subject', '')}「{item.get('knowledge_point', '')}」"
                f"{item.get('action', '')}（截止：{due}）"
            )
    else:
        lines.append("- 暂无未完成跟踪事项。")
    return "\n".join(lines) + "\n"


def cmd_analyze(args: argparse.Namespace) -> None:
    store = load_store()
    analysis = analyze_student(store, args.student, args.days)
    if args.format == "json":
        print_json(analysis)
    else:
        print(build_markdown_analysis(analysis))


def cmd_report(args: argparse.Namespace) -> None:
    store = load_store()
    analysis = analyze_student(store, args.student, args.days)
    content = build_markdown_analysis(analysis)
    write_or_print(content, args.output)


def cmd_followup_add(args: argparse.Namespace) -> None:
    store = load_store()
    student = ensure_student(store, args.student)
    item = {
        "id": next_id(student["followups"]),
        "subject": args.subject,
        "knowledge_point": args.knowledge,
        "action": args.action,
        "due": args.due or "",
        "owner": args.owner or "parent",
        "status": "open",
        "created_at": now_iso(),
        "completed_at": "",
    }
    student["followups"].append(item)
    save_store(store)
    print(f"Follow-up added #{item['id']}: {item['action']}")


def cmd_followup_list(args: argparse.Namespace) -> None:
    store = load_store()
    student = ensure_student(store, args.student)
    items = student.get("followups", [])
    if args.open:
        items = [item for item in items if item.get("status") != "completed"]
    if args.format == "json":
        print_json(items)
        return
    if not items:
        print("No follow-ups.")
        return
    for item in items:
        due = item.get("due") or "no due date"
        print(
            f"#{item['id']} [{item.get('status', 'open')}] "
            f"{item.get('subject', '')}/{item.get('knowledge_point', '')}: "
            f"{item.get('action', '')} (due: {due})"
        )


def cmd_followup_complete(args: argparse.Namespace) -> None:
    store = load_store()
    student = ensure_student(store, args.student)
    for item in student.get("followups", []):
        if int(item.get("id", 0)) == args.id:
            item["status"] = "completed"
            item["completed_at"] = now_iso()
            save_store(store)
            print(f"Follow-up completed #{args.id}")
            return
    raise SystemExit(f"Follow-up not found: {args.id}")


def cmd_status(args: argparse.Namespace) -> None:
    store = load_store()
    student = ensure_student(store, args.student)
    profile = student.get("profile", {})
    records = student.get("records", [])
    followups = student.get("followups", [])
    subjects = sorted({r.get("subject") for r in records if r.get("subject")})
    print(f"Student: {args.student}")
    print(f"Grade: {profile.get('grade', '') or '-'}")
    print(f"Goals: {', '.join(profile.get('goals', [])) or '-'}")
    print(f"Subjects: {', '.join(subjects) or '-'}")
    print(f"Records: {len(records)}")
    print(f"Open follow-ups: {sum(1 for item in followups if item.get('status') != 'completed')}")
    print(f"Data file: {data_path()}")


def add_common_record_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--student", required=True, help="Student name")
    parser.add_argument("--subject", required=True, help="Subject name")
    parser.add_argument("--date", default=None, help="Record date, YYYY-MM-DD")
    parser.add_argument("--knowledge", default="", help="Comma-separated knowledge points")
    parser.add_argument("--notes", default="", help="Parent/teacher notes")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="student-companion",
        description="Parent-facing student companion agent data helper.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument(
        "--data",
        default=None,
        help="Path to the JSON data file. Defaults to ~/.local/share/student-companion-agent/student-data.json",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create or update a student profile")
    init.add_argument("--student", required=True)
    init.add_argument("--grade", default=None)
    init.add_argument("--school", default=None)
    init.add_argument("--goal", action="append", default=[])
    init.set_defaults(func=cmd_init)

    status = sub.add_parser("status", help="Show student data status")
    status.add_argument("--student", required=True)
    status.set_defaults(func=cmd_status)

    record = sub.add_parser("record", help="Record scores, homework, progress, or evidence")
    record_sub = record.add_subparsers(dest="record_type", required=True)

    score = record_sub.add_parser("score", help="Record an exam or quiz score")
    add_common_record_args(score)
    score.add_argument("--title", required=True)
    score.add_argument("--score", required=True, type=float)
    score.add_argument("--max-score", required=True, type=float)
    score.set_defaults(func=cmd_record_score)

    homework = record_sub.add_parser("homework", help="Record homework status")
    add_common_record_args(homework)
    homework.add_argument("--title", required=True)
    homework.add_argument("--status", required=True, choices=sorted(VALID_HOMEWORK_STATUS))
    homework.set_defaults(func=cmd_record_homework)

    progress = record_sub.add_parser("progress", help="Record teaching/curriculum progress")
    add_common_record_args(progress)
    progress.add_argument("--unit", required=True)
    progress.add_argument("--status", required=True, choices=sorted(VALID_PROGRESS_STATUS))
    progress.set_defaults(func=cmd_record_progress)

    evidence = record_sub.add_parser("evidence", help="Record image/audio/file/text evidence")
    evidence.add_argument("--student", required=True)
    evidence.add_argument("--subject", default="")
    evidence.add_argument("--title", default="")
    evidence.add_argument("--date", default=None)
    evidence.add_argument("--source-type", required=True, choices=sorted(VALID_EVIDENCE_TYPE))
    evidence.add_argument("--source-path", default="")
    evidence.add_argument("--extracted-text", default="")
    evidence.add_argument("--knowledge", default="")
    evidence.add_argument("--notes", default="")
    evidence.set_defaults(func=cmd_record_evidence)

    importer = sub.add_parser("import", help="Import CSV, TSV, JSON, Markdown, or TXT records")
    importer.add_argument("file")
    importer.add_argument("--student", default=None, help="Default student when file rows omit it")
    importer.set_defaults(func=cmd_import)

    analyze = sub.add_parser("analyze", help="Analyze weak knowledge points")
    analyze.add_argument("--student", required=True)
    analyze.add_argument("--days", type=int, default=None)
    analyze.add_argument("--format", choices=["markdown", "json"], default="markdown")
    analyze.set_defaults(func=cmd_analyze)

    report = sub.add_parser("report", help="Generate a parent-friendly Markdown report")
    report.add_argument("--student", required=True)
    report.add_argument("--days", type=int, default=None)
    report.add_argument("--output", default=None)
    report.set_defaults(func=cmd_report)

    followup = sub.add_parser("followup", help="Manage tracking actions")
    followup_sub = followup.add_subparsers(dest="followup_command", required=True)

    followup_add = followup_sub.add_parser("add", help="Add a follow-up action")
    followup_add.add_argument("--student", required=True)
    followup_add.add_argument("--subject", required=True)
    followup_add.add_argument("--knowledge", required=True)
    followup_add.add_argument("--action", required=True)
    followup_add.add_argument("--due", default="")
    followup_add.add_argument("--owner", default="parent")
    followup_add.set_defaults(func=cmd_followup_add)

    followup_list = followup_sub.add_parser("list", help="List follow-up actions")
    followup_list.add_argument("--student", required=True)
    followup_list.add_argument("--open", action="store_true")
    followup_list.add_argument("--format", choices=["text", "json"], default="text")
    followup_list.set_defaults(func=cmd_followup_list)

    followup_complete = followup_sub.add_parser("complete", help="Mark a follow-up as completed")
    followup_complete.add_argument("--student", required=True)
    followup_complete.add_argument("--id", required=True, type=int)
    followup_complete.set_defaults(func=cmd_followup_complete)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    global DATA_PATH_OVERRIDE
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.data:
        DATA_PATH_OVERRIDE = Path(args.data)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
