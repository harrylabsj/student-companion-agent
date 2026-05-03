# Student Companion Agent

面向家长的学生陪伴 agent，可作为 OpenClaw/Hermes skill 使用。它把成绩、作业、教学进度、图片/语音/文件提取内容统一记录下来，生成多科薄弱点分析、教学建议和跟踪事项。

## Install Locally

OpenClaw:

```bash
mkdir -p ~/.openclaw/workspace/skills
ln -s "$PWD/student-companion-agent" ~/.openclaw/workspace/skills/student-companion-agent
```

Hermes:

```bash
hermes skills publish ./student-companion-agent --to github --repo <owner>/<repo>
```

For local Hermes development, place or symlink this directory under `~/.hermes/skills/education/student-companion-agent`.

## Verify

```bash
cd student-companion-agent
bash scripts/verify.sh
```

## Use

```bash
python3 scripts/student_companion.py init --student 小明 --grade 五年级 --goal "数学稳定 90+"
python3 scripts/student_companion.py import examples/sample_records.csv --student 小明
python3 scripts/student_companion.py analyze --student 小明
python3 scripts/student_companion.py report --student 小明 --output reports/xiaoming-weekly.md
```

The default database is `~/.local/share/student-companion-agent/student-data.json`.
Use `--data /path/to/student-data.json` for a different location.

## Multimodal Inputs

Images, audio, PDFs, and office files should be handled by the host agent or model first:

1. Extract text, scores, teacher marks, wrong questions, or spoken feedback.
2. Record the original source path and extracted text with `record evidence`.
3. Record reliable structured facts separately with `record score`, `record homework`, or `record progress`.

This keeps the agent portable across OpenClaw and Hermes without depending on one OCR/STT provider.
