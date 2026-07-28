# Data Schema

The CLI stores one JSON file. Use `--data /path/to/student-data.json` to override the path.

Writes are serialized with a cross-process lock file (`<data>.lock`) and the
store is written atomically (temp file + fsync + `os.replace`), so concurrent
CLI processes do not lose updates or leave a half-written file. The JSON is
always standards-compliant (`allow_nan=False`).

## Student

- `profile`: name, grade, school, goals, timestamps.
- `records`: facts and evidence.
- `followups`: tracking actions.

## Record Types

### score

Required: `subject`, `title`, `score`, `max_score`.

Optional: `date`, `knowledge_points`, `notes`.

Validation (CLI and import): `score` and `max_score` must be finite numbers
(no NaN/Infinity), `max_score > 0`, and `0 <= score <= max_score`.

### homework

Required: `subject`, `title`, `status`.

Allowed status: `completed`, `needs_review`, `missing`, `late`.

### progress

Required: `subject`, `unit`, `status`.

Allowed status: `not_started`, `learning`, `blocked`, `reviewing`, `mastered`.

`not_started` carries no capability signal and is excluded from weak-point
scoring; the other statuses feed the analysis.

### evidence

Required: `source_type`.

Allowed source type: `image`, `audio`, `file`, `text`.

Use `extracted_text` for OCR, transcription, or parent/teacher summary.

Evidence is qualitative and never scored. During analysis it either enriches
an existing structured weak point for the same `subject + knowledge_point`
(summary + truncated `extracted_text`), or it is reported as an
`evidence_candidates` entry (`status: pending_confirmation`) so the parent
can confirm and re-record it as a structured fact.

## Import

`import` is atomic: all rows are validated before anything is written. Any
row error aborts the whole import, prints the errors to stderr, and exits
non-zero — there is no silent partial import.
