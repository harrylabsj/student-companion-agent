# Student Companion iOS

家长主导的学生学习陪伴官 iOS App。第一版是本地优先 SwiftUI App，覆盖学生信息、成绩、错题分析、教材进度和学习计划跟踪。

## Open In Xcode

1. Open `ios/StudentCompanion/StudentCompanion.xcodeproj`.
2. Select the `StudentCompanion` scheme.
3. Select an iPhone simulator.
4. Run the app.

The current shell cannot run `xcodebuild` because `xcode-select` points to `/Library/Developer/CommandLineTools`, not a full Xcode installation. Use Xcode.app locally for simulator verification.

## Command-Line Verification

The core logic and SwiftUI source syntax can be checked from this directory:

```bash
swift run StudentCompanionCoreChecks
swift build
```

`StudentCompanionCoreChecks` covers:

- Student profile fields.
- Exam score records and accuracy.
- Wrong-question records with ability tags.
- Textbook and unit progress records.
- Learning plan status and completion.
- Weak-point analysis across scores, wrong questions, textbook progress, and plans.
- JSON save/load round trip.

## App Structure

- `Sources/StudentCompanionCore`: models, weak-point analysis, local store, demo data.
- `App`: SwiftUI app shell and screens.
- `StudentCompanion.xcodeproj`: minimal iOS project wrapper for Xcode.
