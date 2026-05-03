---
name: student-companion-agent
slug: student-companion-agent
version: 0.1.0
author: harrylabsj
license: MIT
description: "Parent-facing student companion agent for OpenClaw and Hermes. Use when parents want to collect exam scores, homework, curriculum progress, images, voice notes, or files; analyze weak knowledge points across multiple subjects; generate teaching suggestions; and track follow-up actions over time. 适用场景：家长记录孩子成绩、作业、教学进度、试卷图片、语音反馈或文件，分析多科薄弱知识点，生成教学建议并持续跟踪。"
platforms: [macos, linux, windows]
metadata:
  hermes:
    category: education
    tags: [education, parent, student, homework, exams, tracking, multimodal, 学习, 家长, 成绩, 作业]
    related_skills: [learning-planner]
  clawdbot:
    emoji: "🎓"
    requires:
      bins: [python3]
    os: [linux, darwin, win32]
---

# Student Companion Agent

家长使用的学生陪伴 agent。目标不是替代老师，而是把零散的成绩、作业、课堂进度、语音、图片和文件变成可跟踪的学习画像。

## When To Use

Use this skill when a parent asks to:
- 记录考试成绩、测验、小题得分、作业完成情况、错题、课堂或补习进度。
- 上传试卷图片、作业照片、老师语音反馈、成绩单文件、Excel/CSV/JSON/Markdown/TXT。
- 识别多科目薄弱知识点，并希望获得家庭辅导建议。
- 持续跟踪补救行动、复盘结果和下一次检查日期。

## Operating Principles

- 面向家长：先给一句结论，再给可执行动作；避免教育术语堆叠。
- 证据优先：所有判断都要能追溯到成绩、作业、进度或附件提取内容。
- 多科统一：按 `subject + knowledge_point` 聚合，避免只按总分判断。
- 小步跟踪：每次建议都转成 1-3 个 follow-up 动作，带截止日期或检查点。
- 风险边界：不要做医学、心理诊断；发现明显焦虑、厌学、霸凌、睡眠严重不足等信号时，建议家长联系老师或专业人士。
- 隐私最小化：不要要求身份证号、详细住址、学校账号密码等不必要信息。

## Quick Start

The deterministic helper lives at `scripts/student_companion.py`.

```bash
python3 scripts/student_companion.py init --student 小明 --grade 五年级 --goal "数学稳定 90+"
python3 scripts/student_companion.py record score --student 小明 --subject 数学 --title "期中考试" --score 78 --max-score 100 --knowledge "分数应用题,单位换算"
python3 scripts/student_companion.py record homework --student 小明 --subject 数学 --title "周三作业" --status needs_review --knowledge "分数应用题" --notes "应用题第 4、6 题错"
python3 scripts/student_companion.py analyze --student 小明
python3 scripts/student_companion.py report --student 小明 --output reports/xiaoming-weekly.md
```

By default data is stored in `~/.local/share/student-companion-agent/student-data.json`.
Use `--data /path/to/student-data.json` when you need a project-local or test database.

## Parent Workflow

1. **收集输入**
   - Ask for the student's name/grade if unknown.
   - Accept text, voice, image, spreadsheet, PDF, CSV, JSON, Markdown, or TXT.
   - For image or voice input, extract the visible/spoken facts first, then record both the extracted text and source path with `record evidence`.
   - For structured files, prefer `import` over manually rewriting rows.

2. **标准化记录**
   - Scores: subject, title, date, score, max score, knowledge points.
   - Homework: subject, title, date, status, knowledge points, notes.
   - Teaching progress: subject, unit, status, knowledge points, notes.
   - Evidence: source type, source path, extracted text, related subject.

3. **分析薄弱点**
   - Run `analyze` after new data is recorded.
   - Focus on high-severity knowledge points with repeated evidence, not one isolated low score.
   - Explain whether the weakness comes from scores, homework errors, unfinished progress, or teacher notes.

4. **给教学建议**
   - Separate parent actions from teacher/tutor suggestions.
   - Keep suggestions specific: what to practice, how long, what evidence proves improvement.
   - Prefer short routines parents can run at home: 10-20 minutes, 2-4 times per week.

5. **跟踪**
   - Convert advice into follow-up actions with `followup add`.
   - At the next check-in, compare new records against the old weak points.
   - Mark completed actions with `followup complete` only after evidence is collected.

## Multimodal Handling

OpenClaw/Hermes may receive attachments through chat gateways, browser tools, or local files. Use this rule:

| Input | Agent action | CLI action |
| --- | --- | --- |
| Voice note | Transcribe or summarize spoken facts. Include uncertainty. | `record evidence --source-type audio --extracted-text ...` |
| Test paper image | Extract subject, score, question errors, and visible knowledge points. | `record evidence --source-type image ...`, then `record score` if score is reliable |
| Homework photo | Extract completion status, wrong questions, teacher marks. | `record homework` plus optional `record evidence` |
| CSV/JSON | Use structured import. | `import <file> --student ...` |
| PDF/DOC/XLSX | Extract or convert relevant tables/text first. | `record evidence` or generated CSV/JSON import |

Do not pretend OCR/STT is exact. If text is unclear, say what is uncertain and ask for confirmation before recording a score.

## CLI Reference

```bash
# profile
python3 scripts/student_companion.py init --student NAME [--grade GRADE] [--school SCHOOL] [--goal GOAL]
python3 scripts/student_companion.py --data ./student-data.json init --student NAME
python3 scripts/student_companion.py status --student NAME

# record facts
python3 scripts/student_companion.py record score --student NAME --subject SUBJECT --title TITLE --score N --max-score N --knowledge "A,B"
python3 scripts/student_companion.py record homework --student NAME --subject SUBJECT --title TITLE --status completed|needs_review|missing|late --knowledge "A,B"
python3 scripts/student_companion.py record progress --student NAME --subject SUBJECT --unit UNIT --status not_started|learning|blocked|reviewing|mastered --knowledge "A,B"
python3 scripts/student_companion.py record evidence --student NAME --source-type image|audio|file|text --source-path PATH --extracted-text TEXT

# bulk import
python3 scripts/student_companion.py import examples/sample_records.csv --student NAME
python3 scripts/student_companion.py import examples/sample_records.json --student NAME

# analysis and reporting
python3 scripts/student_companion.py analyze --student NAME [--days 30] [--format markdown|json]
python3 scripts/student_companion.py report --student NAME --output weekly.md

# tracking
python3 scripts/student_companion.py followup add --student NAME --subject SUBJECT --knowledge "知识点" --action "本周练 10 道分数应用题" --due 2026-05-09
python3 scripts/student_companion.py followup list --student NAME
python3 scripts/student_companion.py followup complete --student NAME --id 1
```

## Output Expectations

A useful answer to the parent should include:
- **当前判断**：1-2 句说明最需要关注的科目/知识点。
- **证据**：引用最近成绩、作业或进度记录。
- **家庭动作**：1-3 条可执行建议。
- **跟踪点**：下次看什么数据，什么时候检查。
- **需要补充**：只问最关键的缺口，例如“这张试卷满分是多少？”

## Verification

Before claiming the agent package is ready:
- `python3 scripts/student_companion.py --help`
- `python3 -m unittest discover -s tests`
- `bash scripts/verify.sh`
- Confirm `SKILL.md` frontmatter has `name` and `description`.
- Confirm `clawhub.json`, `package.json`, and `README.md` point to the same package name and version.
