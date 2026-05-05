import Foundation
import Observation

public struct StudentCompanionSnapshot: Codable, Equatable, Sendable {
    public var profile: StudentProfile
    public var scores: [ScoreRecord]
    public var wrongQuestions: [WrongQuestion]
    public var textbooks: [Textbook]
    public var textbookUnits: [TextbookUnit]
    public var plans: [LearningPlan]

    public init(
        profile: StudentProfile,
        scores: [ScoreRecord] = [],
        wrongQuestions: [WrongQuestion] = [],
        textbooks: [Textbook] = [],
        textbookUnits: [TextbookUnit] = [],
        plans: [LearningPlan] = []
    ) {
        self.profile = profile
        self.scores = scores
        self.wrongQuestions = wrongQuestions
        self.textbooks = textbooks
        self.textbookUnits = textbookUnits
        self.plans = plans
    }
}

@Observable
public final class StudentCompanionStore {
    public var profile: StudentProfile
    public var scores: [ScoreRecord]
    public var wrongQuestions: [WrongQuestion]
    public var textbooks: [Textbook]
    public var textbookUnits: [TextbookUnit]
    public var plans: [LearningPlan]

    private let analyzer: WeakPointAnalyzer

    public init(snapshot: StudentCompanionSnapshot, analyzer: WeakPointAnalyzer = WeakPointAnalyzer()) {
        self.profile = snapshot.profile
        self.scores = snapshot.scores
        self.wrongQuestions = snapshot.wrongQuestions
        self.textbooks = snapshot.textbooks
        self.textbookUnits = snapshot.textbookUnits
        self.plans = snapshot.plans
        self.analyzer = analyzer
    }

    public var snapshot: StudentCompanionSnapshot {
        StudentCompanionSnapshot(
            profile: profile,
            scores: scores,
            wrongQuestions: wrongQuestions,
            textbooks: textbooks,
            textbookUnits: textbookUnits,
            plans: plans
        )
    }

    public var pendingWrongQuestionCount: Int {
        wrongQuestions.filter { $0.correctionStatus != .corrected }.count
    }

    public var planCompletionRate: Double {
        guard !plans.isEmpty else { return 0 }
        let completed = plans.filter { $0.status == .completed }.count
        return Double(completed) / Double(plans.count)
    }

    public func weakPoints() -> [WeakPoint] {
        analyzer.analyze(
            profile: profile,
            scores: scores,
            wrongQuestions: wrongQuestions,
            textbookUnits: textbookUnits,
            plans: plans
        )
    }

    public func updateProfile(_ newProfile: StudentProfile) {
        profile = newProfile
        profile.updatedAt = Date()
    }

    public func addScore(_ score: ScoreRecord) {
        scores.insert(score, at: 0)
    }

    public func addWrongQuestion(_ wrongQuestion: WrongQuestion) {
        wrongQuestions.insert(wrongQuestion, at: 0)
    }

    public func addTextbook(_ textbook: Textbook) {
        textbooks.append(textbook)
    }

    public func addTextbookUnit(_ unit: TextbookUnit) {
        textbookUnits.append(unit)
    }

    public func updateTextbookUnit(id: UUID, progressStatus: ProgressStatus) {
        guard let index = textbookUnits.firstIndex(where: { $0.id == id }) else { return }
        textbookUnits[index].progressStatus = progressStatus
    }

    public func addPlan(_ plan: LearningPlan) {
        plans.insert(plan, at: 0)
    }

    public func completePlan(id: UUID, reviewNote: String) {
        guard let index = plans.firstIndex(where: { $0.id == id }) else { return }
        plans[index].status = .completed
        plans[index].reviewNote = reviewNote
    }

    public func save(to url: URL) throws {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(snapshot)
        try data.write(to: url, options: .atomic)
    }

    public static func load(from url: URL) throws -> StudentCompanionStore {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let data = try Data(contentsOf: url)
        let snapshot = try decoder.decode(StudentCompanionSnapshot.self, from: data)
        return StudentCompanionStore(snapshot: snapshot)
    }
}
