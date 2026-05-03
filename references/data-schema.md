# Data Schema

The CLI stores one JSON file. Use `--data /path/to/student-data.json` to override the path.

## Student

- `profile`: name, grade, school, goals, timestamps.
- `records`: facts and evidence.
- `followups`: tracking actions.

## Record Types

### score

Required: `subject`, `title`, `score`, `max_score`.

Optional: `date`, `knowledge_points`, `notes`.

### homework

Required: `subject`, `title`, `status`.

Allowed status: `completed`, `needs_review`, `missing`, `late`.

### progress

Required: `subject`, `unit`, `status`.

Allowed status: `not_started`, `learning`, `blocked`, `reviewing`, `mastered`.

### evidence

Required: `source_type`.

Allowed source type: `image`, `audio`, `file`, `text`.

Use `extracted_text` for OCR, transcription, or parent/teacher summary.
