#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
DATA_FILE="$TMP_DIR/student-data.json"

python3 "$ROOT_DIR/scripts/student_companion.py" --help >/dev/null
python3 "$ROOT_DIR/scripts/student_companion.py" --data "$DATA_FILE" init --student 小明 --grade 五年级 --goal "数学稳定 90+"
python3 "$ROOT_DIR/scripts/student_companion.py" --data "$DATA_FILE" import "$ROOT_DIR/examples/sample_records.csv" --student 小明
python3 "$ROOT_DIR/scripts/student_companion.py" --data "$DATA_FILE" record evidence \
  --student 小明 \
  --subject 数学 \
  --source-type image \
  --source-path examples/math-paper.jpg \
  --extracted-text "试卷图片显示：分数应用题第 4 题和第 6 题错误，单位换算漏写单位。" \
  --knowledge "分数应用题,单位换算"
python3 "$ROOT_DIR/scripts/student_companion.py" --data "$DATA_FILE" followup add \
  --student 小明 \
  --subject 数学 \
  --knowledge 分数应用题 \
  --action "本周三前复盘 5 道分数应用题并记录错因" \
  --due 2026-05-09

python3 "$ROOT_DIR/scripts/student_companion.py" --data "$DATA_FILE" analyze --student 小明 --format json >"$TMP_DIR/analysis.json"
python3 "$ROOT_DIR/scripts/student_companion.py" --data "$DATA_FILE" report --student 小明 --output "$TMP_DIR/report.md"

python3 - "$TMP_DIR/analysis.json" "$TMP_DIR/report.md" <<'PY'
import json
import sys
from pathlib import Path

analysis = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
report = Path(sys.argv[2]).read_text(encoding="utf-8")

assert analysis["student"] == "小明"
assert analysis["record_count"] >= 5
assert any(item["subject"] == "数学" for item in analysis["subject_summary"])
assert any(item["knowledge_point"] == "分数应用题" for item in analysis["weak_points"])
assert analysis["open_followups"], "expected open follow-up"
assert "薄弱知识点" in report
assert "建议" in report
print("verification ok")
PY

echo "Data file: $DATA_FILE"
