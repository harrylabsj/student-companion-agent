# Student Companion iOS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a parent-led SwiftUI iOS app for student profile entry, exam score entry, wrong-question analysis, textbook entry, and learning plan tracking.

**Architecture:** Create a new `ios/StudentCompanion` Swift package with a testable `StudentCompanionCore` library and a SwiftUI app target. The core library owns value models, JSON persistence, seed data, and deterministic weak-point analysis; the app target owns navigation, forms, and visual presentation. A minimal Xcode project wraps the same app/core files for iOS use, while `swift test` and `swift build` verify what this environment can build without full Xcode.

**Tech Stack:** Swift 6, SwiftUI, Observation, Foundation JSON persistence, Swift Testing/XCTest, local-first data storage.

---

## File Structure

- Create `ios/StudentCompanion/Package.swift`: package manifest for core, app executable, and tests.
- Create `ios/StudentCompanion/Sources/StudentCompanionCore/Models.swift`: student, score, wrong question, textbook, plan, and weak point value types.
- Create `ios/StudentCompanion/Sources/StudentCompanionCore/WeakPointAnalyzer.swift`: deterministic analysis rules.
- Create `ios/StudentCompanion/Sources/StudentCompanionCore/StudentCompanionStore.swift`: app state mutations plus JSON load/save.
- Create `ios/StudentCompanion/Sources/StudentCompanionCore/SeedData.swift`: realistic demo data.
- Create `ios/StudentCompanion/Tests/StudentCompanionCoreTests/WeakPointAnalyzerTests.swift`: analyzer behavior tests.
- Create `ios/StudentCompanion/Tests/StudentCompanionCoreTests/StudentCompanionStoreTests.swift`: store mutation and persistence tests.
- Create `ios/StudentCompanion/App/StudentCompanionApp.swift`: SwiftUI app entry.
- Create `ios/StudentCompanion/App/MainTabView.swift`: five-tab shell.
- Create `ios/StudentCompanion/App/DesignSystem.swift`: colors, card styles, field helpers.
- Create `ios/StudentCompanion/App/Screens/HomeView.swift`: student summary and quick actions.
- Create `ios/StudentCompanion/App/Screens/RecordView.swift`: profile, score, and wrong-question entry.
- Create `ios/StudentCompanion/App/Screens/AnalysisView.swift`: weak points, evidence, ability gaps.
- Create `ios/StudentCompanion/App/Screens/TextbookView.swift`: textbook and unit entry/progress.
- Create `ios/StudentCompanion/App/Screens/PlanView.swift`: learning plan list, entry, completion tracking.
- Create `ios/StudentCompanion/StudentCompanion.xcodeproj/project.pbxproj`: minimal iOS app project referencing app and core files.
- Create `ios/StudentCompanion/README.md`: run, verify, and Xcode notes.

## Task 1: Swift Package Scaffold

**Files:**
- Create: `ios/StudentCompanion/Package.swift`
- Create: `ios/StudentCompanion/Sources/StudentCompanionCore/Models.swift`
- Create: `ios/StudentCompanion/Tests/StudentCompanionCoreTests/ModelSmokeTests.swift`

- [ ] **Step 1: Write a failing model smoke test**

```swift
import XCTest
@testable import StudentCompanionCore

final class ModelSmokeTests: XCTestCase {
    func testStudentProfileStoresBasicLearningContext() {
        let profile = StudentProfile(
            name: "小明",
            grade: "五年级",
            school: "实验小学",
            goals: ["数学稳定 90+"],
            activeSubjects: ["数学", "语文"]
        )

        XCTAssertEqual(profile.name, "小明")
        XCTAssertEqual(profile.grade, "五年级")
        XCTAssertEqual(profile.goals, ["数学稳定 90+"])
    }
}
```

- [ ] **Step 2: Run the test and verify RED**

Run: `cd ios/StudentCompanion && swift test --filter ModelSmokeTests`

Expected: FAIL because `Package.swift` or `StudentProfile` does not exist yet.

- [ ] **Step 3: Add the package manifest and minimal model**

`Package.swift` should define:

```swift
// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "StudentCompanion",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "StudentCompanionCore", targets: ["StudentCompanionCore"]),
        .executable(name: "StudentCompanionApp", targets: ["StudentCompanionApp"])
    ],
    targets: [
        .target(name: "StudentCompanionCore"),
        .executableTarget(
            name: "StudentCompanionApp",
            dependencies: ["StudentCompanionCore"],
            path: "App"
        ),
        .testTarget(
            name: "StudentCompanionCoreTests",
            dependencies: ["StudentCompanionCore"]
        )
    ]
)
```

`Models.swift` starts with `StudentProfile` plus shared type aliases:

```swift
import Foundation

public typealias KnowledgePoint = String

public struct StudentProfile: Codable, Equatable, Identifiable {
    public var id: UUID
    public var name: String
    public var grade: String
    public var school: String
    public var goals: [String]
    public var activeSubjects: [String]
    public var createdAt: Date
    public var updatedAt: Date

    public init(
        id: UUID = UUID(),
        name: String,
        grade: String,
        school: String = "",
        goals: [String] = [],
        activeSubjects: [String] = [],
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.grade = grade
        self.school = school
        self.goals = goals
        self.activeSubjects = activeSubjects
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}
```

- [ ] **Step 4: Run the test and verify GREEN**

Run: `cd ios/StudentCompanion && swift test --filter ModelSmokeTests`

Expected: PASS.

## Task 2: Complete Domain Models

**Files:**
- Modify: `ios/StudentCompanion/Sources/StudentCompanionCore/Models.swift`
- Create: `ios/StudentCompanion/Tests/StudentCompanionCoreTests/DomainModelTests.swift`

- [ ] **Step 1: Write failing tests for required record types**

Test that `ScoreRecord`, `WrongQuestion`, `Textbook`, `TextbookUnit`, and `LearningPlan` capture the required fields and statuses.

- [ ] **Step 2: Verify RED**

Run: `cd ios/StudentCompanion && swift test --filter DomainModelTests`

Expected: FAIL because those model types do not exist.

- [ ] **Step 3: Implement the models**

Add codable/equatable structs and enums:

- `ScoreRecord`: subject, title, date, score, maxScore, knowledgePoints, notes.
- `WrongQuestion`: subject, sourceTitle, date, knowledgePoints, abilityTags, errorReason, correctionStatus, notes.
- `Textbook`: subject, name, publisher, grade, semester.
- `TextbookUnit`: textbookID, title, sequence, knowledgePoints, progressStatus.
- `LearningPlan`: subject, knowledgePoint, action, dueDate, status, reviewNote.
- `WeakPoint`: subject, knowledgePoint, severity, evidence, abilityGaps, suggestion.

- [ ] **Step 4: Verify GREEN**

Run: `cd ios/StudentCompanion && swift test --filter DomainModelTests`

Expected: PASS.

## Task 3: Weak-Point Analyzer

**Files:**
- Create: `ios/StudentCompanion/Sources/StudentCompanionCore/WeakPointAnalyzer.swift`
- Create: `ios/StudentCompanion/Tests/StudentCompanionCoreTests/WeakPointAnalyzerTests.swift`

- [ ] **Step 1: Write failing analyzer tests**

Cover these behaviors:

- A score below 80% creates a weak point for each linked knowledge point.
- Repeated wrong questions on the same knowledge point raise severity.
- Ability tags from wrong questions are surfaced as ability gaps.
- Blocked textbook units add evidence to the same knowledge point.
- Completed plans do not clear a weak point unless improved evidence exists.

- [ ] **Step 2: Verify RED**

Run: `cd ios/StudentCompanion && swift test --filter WeakPointAnalyzerTests`

Expected: FAIL because `WeakPointAnalyzer` does not exist.

- [ ] **Step 3: Implement deterministic analysis**

Create:

```swift
public struct WeakPointAnalyzer {
    public init() {}

    public func analyze(
        profile: StudentProfile,
        scores: [ScoreRecord],
        wrongQuestions: [WrongQuestion],
        textbookUnits: [TextbookUnit],
        plans: [LearningPlan]
    ) -> [WeakPoint] {
        // Aggregate by subject + knowledgePoint.
        // Add evidence for low scores, repeated wrong questions, blocked/reviewing units,
        // and unfinished plans. Sort by severity descending.
    }
}
```

Severity scoring should be simple and explainable:

- Low score below 80%: +2.
- Low score below 60%: additional +2.
- Each wrong question: +1.
- Repeated wrong questions after the first: additional +1 each.
- Blocked textbook unit: +2.
- Reviewing textbook unit: +1.
- Planned or in-progress plan: +1.
- Skipped plan: +2.

- [ ] **Step 4: Verify GREEN**

Run: `cd ios/StudentCompanion && swift test --filter WeakPointAnalyzerTests`

Expected: PASS.

## Task 4: Store And Persistence

**Files:**
- Create: `ios/StudentCompanion/Sources/StudentCompanionCore/StudentCompanionStore.swift`
- Create: `ios/StudentCompanion/Tests/StudentCompanionCoreTests/StudentCompanionStoreTests.swift`

- [ ] **Step 1: Write failing store tests**

Cover profile update, score entry, wrong-question entry, textbook unit entry, plan entry, plan completion, and JSON save/load round trip.

- [ ] **Step 2: Verify RED**

Run: `cd ios/StudentCompanion && swift test --filter StudentCompanionStoreTests`

Expected: FAIL because `StudentCompanionStore` does not exist.

- [ ] **Step 3: Implement store**

Use a codable `StudentCompanionSnapshot` and a `@MainActor @Observable final class StudentCompanionStore` with mutation methods:

- `updateProfile(_:)`
- `addScore(_:)`
- `addWrongQuestion(_:)`
- `addTextbook(_:)`
- `addTextbookUnit(_:)`
- `addPlan(_:)`
- `completePlan(id:reviewNote:)`
- `weakPoints()`
- `save(to:)`
- `load(from:)`

- [ ] **Step 4: Verify GREEN**

Run: `cd ios/StudentCompanion && swift test --filter StudentCompanionStoreTests`

Expected: PASS.

## Task 5: Seed Data And App Shell

**Files:**
- Create: `ios/StudentCompanion/Sources/StudentCompanionCore/SeedData.swift`
- Create: `ios/StudentCompanion/App/StudentCompanionApp.swift`
- Create: `ios/StudentCompanion/App/MainTabView.swift`
- Create: `ios/StudentCompanion/App/DesignSystem.swift`

- [ ] **Step 1: Add app shell files**

Use `@State private var store = StudentCompanionStore(seed: .demo)` in the app entry. Use a five-tab `TabView`: Home, Record, Analysis, Textbook, Plan.

- [ ] **Step 2: Build app target**

Run: `cd ios/StudentCompanion && swift build`

Expected: PASS in this environment for macOS-compatible SwiftUI syntax. iOS simulator build still requires full Xcode.

## Task 6: Home And Record Screens

**Files:**
- Create: `ios/StudentCompanion/App/Screens/HomeView.swift`
- Create: `ios/StudentCompanion/App/Screens/RecordView.swift`

- [ ] **Step 1: Implement Home**

Home must show profile, top weak point, evidence count, plan completion rate, pending wrong-question count, today's plan, and quick links.

- [ ] **Step 2: Implement Record**

Record must provide profile editing, score entry, and wrong-question entry with segmented controls and compact forms.

- [ ] **Step 3: Build app target**

Run: `cd ios/StudentCompanion && swift build`

Expected: PASS.

## Task 7: Analysis, Textbook, And Plan Screens

**Files:**
- Create: `ios/StudentCompanion/App/Screens/AnalysisView.swift`
- Create: `ios/StudentCompanion/App/Screens/TextbookView.swift`
- Create: `ios/StudentCompanion/App/Screens/PlanView.swift`

- [ ] **Step 1: Implement Analysis**

Show weak points grouped by severity with evidence, ability gaps, and recommended actions.

- [ ] **Step 2: Implement Textbook**

Allow adding textbook units and changing progress status.

- [ ] **Step 3: Implement Plan**

Allow adding plans, viewing statuses, and marking plans complete with review notes.

- [ ] **Step 4: Build app target**

Run: `cd ios/StudentCompanion && swift build`

Expected: PASS.

## Task 8: iOS Project And Documentation

**Files:**
- Create: `ios/StudentCompanion/StudentCompanion.xcodeproj/project.pbxproj`
- Create: `ios/StudentCompanion/README.md`

- [ ] **Step 1: Add minimal Xcode project**

Create an iOS app target named `StudentCompanion` that references the app files and `StudentCompanionCore` source files.

- [ ] **Step 2: Document run and verification**

README must state:

- Open `ios/StudentCompanion/StudentCompanion.xcodeproj` in Xcode.
- Select an iPhone simulator.
- Run the `StudentCompanion` scheme.
- In this environment, `xcodebuild` is unavailable because `xcode-select` points to Command Line Tools.
- Core verification command is `swift test`.
- Source syntax verification command is `swift build`.

- [ ] **Step 3: Final verification**

Run:

```bash
cd ios/StudentCompanion && swift test
cd ios/StudentCompanion && swift build
```

Expected: both commands PASS.

## Coverage Check

- Student basic information entry: Task 2 model, Task 4 store, Task 6 Record screen.
- Exam score entry: Task 2 model, Task 4 store, Task 6 Record screen.
- Wrong-question analysis: Task 3 analyzer, Task 7 Analysis screen.
- Knowledge/ability gaps: Task 2 wrong-question ability tags, Task 3 analyzer evidence, Task 7 Analysis screen.
- Textbook information entry: Task 2 model, Task 4 store, Task 7 Textbook screen.
- Learning plan entry and tracking: Task 2 model, Task 4 store, Task 7 Plan screen.
- Easy and elegant UI: Task 5 design system, Task 6/7 SwiftUI screens.
- iOS deliverable: Task 5 SwiftUI app source, Task 8 Xcode project.

## Known Environment Constraint

`xcodebuild` cannot run in the current shell because the active developer directory is `/Library/Developer/CommandLineTools`, not a full Xcode installation. Implementation must still include the Xcode project, but final verification in this environment is limited to `swift test`, `swift build`, file inspection, and clear documentation of the Xcode requirement.
