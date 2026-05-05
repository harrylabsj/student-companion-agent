import Foundation

public typealias KnowledgePoint = String

public struct StudentProfile: Codable, Equatable, Identifiable, Sendable {
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

public enum CorrectionStatus: String, Codable, CaseIterable, Sendable {
    case unresolved
    case reviewing
    case corrected

    public var label: String {
        switch self {
        case .unresolved: "未订正"
        case .reviewing: "复盘中"
        case .corrected: "已掌握"
        }
    }
}

public enum ProgressStatus: String, Codable, CaseIterable, Sendable {
    case notStarted
    case learning
    case blocked
    case reviewing
    case mastered

    public var label: String {
        switch self {
        case .notStarted: "未开始"
        case .learning: "学习中"
        case .blocked: "卡住"
        case .reviewing: "复习中"
        case .mastered: "已掌握"
        }
    }
}

public enum PlanStatus: String, Codable, CaseIterable, Sendable {
    case planned
    case inProgress
    case completed
    case skipped

    public var label: String {
        switch self {
        case .planned: "待开始"
        case .inProgress: "进行中"
        case .completed: "已完成"
        case .skipped: "已跳过"
        }
    }
}

public struct ScoreRecord: Codable, Equatable, Identifiable, Sendable {
    public var id: UUID
    public var subject: String
    public var title: String
    public var date: Date
    public var score: Double
    public var maxScore: Double
    public var knowledgePoints: [KnowledgePoint]
    public var notes: String

    public var accuracy: Double {
        guard maxScore > 0 else { return 0 }
        return score / maxScore
    }

    public init(
        id: UUID = UUID(),
        subject: String,
        title: String,
        date: Date = Date(),
        score: Double,
        maxScore: Double,
        knowledgePoints: [KnowledgePoint] = [],
        notes: String = ""
    ) {
        self.id = id
        self.subject = subject
        self.title = title
        self.date = date
        self.score = score
        self.maxScore = maxScore
        self.knowledgePoints = knowledgePoints
        self.notes = notes
    }
}

public struct WrongQuestion: Codable, Equatable, Identifiable, Sendable {
    public var id: UUID
    public var subject: String
    public var sourceTitle: String
    public var date: Date
    public var questionLabel: String
    public var knowledgePoints: [KnowledgePoint]
    public var abilityTags: [String]
    public var errorReason: String
    public var correctionStatus: CorrectionStatus
    public var notes: String

    public init(
        id: UUID = UUID(),
        subject: String,
        sourceTitle: String,
        date: Date = Date(),
        questionLabel: String,
        knowledgePoints: [KnowledgePoint] = [],
        abilityTags: [String] = [],
        errorReason: String,
        correctionStatus: CorrectionStatus = .unresolved,
        notes: String = ""
    ) {
        self.id = id
        self.subject = subject
        self.sourceTitle = sourceTitle
        self.date = date
        self.questionLabel = questionLabel
        self.knowledgePoints = knowledgePoints
        self.abilityTags = abilityTags
        self.errorReason = errorReason
        self.correctionStatus = correctionStatus
        self.notes = notes
    }
}

public struct Textbook: Codable, Equatable, Identifiable, Sendable {
    public var id: UUID
    public var subject: String
    public var name: String
    public var publisher: String
    public var grade: String
    public var semester: String

    public init(
        id: UUID = UUID(),
        subject: String,
        name: String,
        publisher: String,
        grade: String,
        semester: String
    ) {
        self.id = id
        self.subject = subject
        self.name = name
        self.publisher = publisher
        self.grade = grade
        self.semester = semester
    }
}

public struct TextbookUnit: Codable, Equatable, Identifiable, Sendable {
    public var id: UUID
    public var textbookID: UUID
    public var subject: String
    public var title: String
    public var sequence: Int
    public var knowledgePoints: [KnowledgePoint]
    public var progressStatus: ProgressStatus

    public init(
        id: UUID = UUID(),
        textbookID: UUID,
        subject: String,
        title: String,
        sequence: Int,
        knowledgePoints: [KnowledgePoint] = [],
        progressStatus: ProgressStatus = .notStarted
    ) {
        self.id = id
        self.textbookID = textbookID
        self.subject = subject
        self.title = title
        self.sequence = sequence
        self.knowledgePoints = knowledgePoints
        self.progressStatus = progressStatus
    }
}

public struct LearningPlan: Codable, Equatable, Identifiable, Sendable {
    public var id: UUID
    public var subject: String
    public var knowledgePoint: KnowledgePoint
    public var action: String
    public var dueDate: Date
    public var status: PlanStatus
    public var reviewNote: String

    public init(
        id: UUID = UUID(),
        subject: String,
        knowledgePoint: KnowledgePoint,
        action: String,
        dueDate: Date,
        status: PlanStatus = .planned,
        reviewNote: String = ""
    ) {
        self.id = id
        self.subject = subject
        self.knowledgePoint = knowledgePoint
        self.action = action
        self.dueDate = dueDate
        self.status = status
        self.reviewNote = reviewNote
    }
}

public struct WeakPointEvidence: Codable, Equatable, Identifiable, Sendable {
    public var id: UUID
    public var source: String
    public var message: String
    public var weight: Int

    public init(id: UUID = UUID(), source: String, message: String, weight: Int) {
        self.id = id
        self.source = source
        self.message = message
        self.weight = weight
    }
}

public struct WeakPoint: Codable, Equatable, Identifiable, Sendable {
    public var id: String { "\(subject)-\(knowledgePoint)" }
    public var subject: String
    public var knowledgePoint: KnowledgePoint
    public var severity: Int
    public var evidence: [WeakPointEvidence]
    public var abilityGaps: [String]
    public var suggestion: String

    public init(
        subject: String,
        knowledgePoint: KnowledgePoint,
        severity: Int,
        evidence: [WeakPointEvidence],
        abilityGaps: [String],
        suggestion: String
    ) {
        self.subject = subject
        self.knowledgePoint = knowledgePoint
        self.severity = severity
        self.evidence = evidence
        self.abilityGaps = abilityGaps
        self.suggestion = suggestion
    }
}
