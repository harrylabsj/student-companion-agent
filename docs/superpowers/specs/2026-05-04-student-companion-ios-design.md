# Student Companion iOS App Design Draft

Status: Draft pending user review.
Date: 2026-05-04

## Objective

Build an easy-to-use, visually polished iOS app for a "student learning companion officer" experience. The first version is a parent-led, local-first SwiftUI app that helps a parent record learning data, understand weak points, and track improvement plans.

The explicit required capabilities are:

- Student basic information entry.
- Exam score entry.
- Wrong-question analysis that exposes weak knowledge points or ability gaps.
- Textbook information entry.
- Learning plan entry and tracking.
- A clean, elegant UI that is practical for repeated use.

## Product Direction

The first version should be parent-led. The parent is the primary operator who records scores, wrong questions, textbook progress, and learning plans. The student can be represented by tasks and progress records, but the first version does not need separate parent/student accounts.

The app should be local-first. Data is stored on the device using SwiftData or a simple local store. This keeps the first version private, reliable, and buildable without backend accounts. Cloud sync, OCR, voice input, and AI chat are intentionally deferred.

The existing `student-companion-agent` package should be treated as domain reference material, not as runtime code inside the iOS app. Its schema and analysis ideas map well to the mobile app, but a Python CLI is not an App Store-friendly runtime dependency.

## App Structure

Use a SwiftUI `TabView` with one `NavigationStack` per tab:

- Home: student summary, current weak points, today's plan, quick entry actions.
- Record: guided entry for student profile, exam scores, wrong questions, homework, and quick notes.
- Analysis: weak knowledge points, ability gaps, evidence, and suggested actions.
- Textbook: subjects, textbook metadata, units, lessons, knowledge points, and progress state.
- Plan: weekly plans, daily tasks, completion tracking, review checkpoints.

Student basic information should be collected in first-run onboarding and remain editable from Home or settings. This keeps the main navigation focused while still satisfying profile entry.

## Core Screens

### Onboarding And Student Profile

Collect only necessary fields:

- Student name.
- Grade.
- School, optional.
- Learning goals.
- Active subjects.

Avoid collecting sensitive data such as ID number, detailed home address, school account credentials, or medical/psychological information.

### Home

Home answers: "What should I pay attention to this week?"

It should show:

- Current student and grade.
- Highest-priority weak point, with evidence count.
- Plan completion rate.
- Pending wrong questions.
- Today's learning action.
- Quick buttons for score entry and wrong-question entry.

### Record

Record is a guided input surface with segmented modes:

- Score: subject, exam title, date, score, max score, knowledge points, notes.
- Wrong question: subject, source, question title or number, knowledge points, error reason, correction status, notes.
- Student profile: basic profile edits.
- Homework or evidence notes can be included as optional first-version extensions if they support analysis.

Inputs should use pickers and chips for common subjects, knowledge points, and error reasons. The parent should not need to type everything repeatedly.

### Analysis

Analysis explains weak points with evidence. Each weak point should include:

- Subject.
- Knowledge point.
- Severity.
- Evidence count.
- Recent score accuracy where available.
- Repeated wrong-question count.
- Related ability gaps.
- Suggested parent action.

Ability gaps should be concrete and parent-readable, for example:

- Reading and extracting key information.
- Building an equation or quantity relationship.
- Calculation accuracy.
- Concept recall.
- Multi-step reasoning.
- Time management or careless checking.

The analysis must be explainable. Avoid opaque "AI says so" conclusions in the first version.

### Textbook

Textbook entry should support:

- Subject.
- Publisher or textbook name.
- Grade/semester.
- Units.
- Lessons.
- Knowledge points.
- Progress state: not started, learning, blocked, reviewing, mastered.

Textbook progress should feed analysis. A weak point becomes more important when the related textbook unit is blocked or reviewing.

### Plan

Learning plan tracking should support:

- Plan title.
- Subject.
- Linked knowledge point.
- Action.
- Due date.
- Status: planned, in progress, completed, skipped.
- Completion evidence or review note.

Plans should be created manually and also suggested from analysis. For example, a weak point in "fraction word problems" can create a plan item: "Do six variation problems this week; before solving, say the quantity relationship out loud."

## Data Model

Recommended first-version entities:

- `StudentProfile`: name, grade, school, goals, active subjects, timestamps.
- `ScoreRecord`: subject, title, date, score, maxScore, knowledgePoints, notes.
- `WrongQuestion`: subject, sourceTitle, date, knowledgePoints, abilityTags, errorReason, correctionStatus, notes.
- `Textbook`: subject, name, publisher, grade, semester.
- `TextbookUnit`: textbook, title, sequence, knowledgePoints, progressStatus.
- `LearningPlan`: subject, knowledgePoint, action, dueDate, status, linkedWeakPoint, reviewNote.
- `WeakPoint`: derived analysis result, not necessarily persisted unless caching is useful.

Use stable identifiers and timestamps for all persisted records.

## Analysis Rules

The first version should use deterministic, explainable rules:

- Score accuracy below a threshold increases severity for linked knowledge points.
- Repeated wrong questions on the same knowledge point increase severity.
- Ability tags attached to wrong questions reveal ability gaps.
- Textbook units marked blocked or reviewing increase priority for related weak points.
- Unfinished or skipped plans keep a weak point active.
- Completed plans reduce priority only when followed by improved evidence.

Each result should show evidence rather than only a score. The parent should see why a knowledge point was flagged.

## UI Direction

The UI should feel calm, modern, and work-focused:

- Native SwiftUI with `TabView`, `NavigationStack`, sheets, forms, and list/detail flows.
- Soft neutral backgrounds with restrained blue, teal, green, amber, and red accents for meaning.
- Compact cards for individual insights and tasks.
- Clear typography, strong hierarchy, and short Chinese labels.
- Quick actions near the top of Home.
- No decorative landing page; the app opens directly into the learning dashboard after onboarding.

The app should optimize for repeated parent use: fast entry, low typing, clear evidence, and visible follow-up.

## Deferred Scope

The first version should not include:

- User accounts.
- Cloud sync.
- Multi-device collaboration.
- OCR photo recognition.
- Voice transcription.
- AI chat coach.
- Teacher or school integrations.
- Payment, subscriptions, or social sharing.

These can be added after the core local workflow proves useful.

## Success Criteria

The first version is successful when a parent can:

- Create or edit a student profile.
- Enter an exam score in under a minute.
- Enter wrong-question details and tag knowledge points or ability gaps.
- Enter textbook units and progress.
- Create a learning plan linked to a weak point.
- Mark plan tasks complete and review whether the weak point improves.
- Open the Analysis tab and understand what is weak, why it is weak, and what to do next.

## Open Review Items

The current draft assumes:

- Parent-led first version.
- Local-first data storage.
- Rule-based analysis before AI/OCR.
- Five-tab navigation.

These assumptions need user confirmation before implementation planning.
