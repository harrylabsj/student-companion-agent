import Foundation

public struct WeakPointAnalyzer {
    public init() {}

    public func analyze(
        profile: StudentProfile,
        scores: [ScoreRecord],
        wrongQuestions: [WrongQuestion],
        textbookUnits: [TextbookUnit],
        plans: [LearningPlan]
    ) -> [WeakPoint] {
        var buckets: [WeakPointKey: WeakPointAccumulator] = [:]

        for score in scores where score.maxScore > 0 {
            for point in score.knowledgePoints {
                let accuracy = score.accuracy
                guard accuracy < 0.8 else { continue }
                let weight = accuracy < 0.6 ? 4 : 2
                let percent = Int((accuracy * 100).rounded())
                buckets[WeakPointKey(score.subject, point), default: .init(subject: score.subject, knowledgePoint: point)]
                    .add(
                        weight: weight,
                        source: "score",
                        message: "\(score.title)正确率 \(percent)%"
                    )
            }
        }

        var wrongQuestionCounts: [WeakPointKey: Int] = [:]
        for question in wrongQuestions {
            for point in question.knowledgePoints {
                let key = WeakPointKey(question.subject, point)
                wrongQuestionCounts[key, default: 0] += 1
                let repeatBonus = wrongQuestionCounts[key, default: 0] > 1 ? 1 : 0
                buckets[key, default: .init(subject: question.subject, knowledgePoint: point)]
                    .add(
                        weight: 1 + repeatBonus,
                        source: "wrong-question",
                        message: "\(question.sourceTitle)\(question.questionLabel)错因：\(question.errorReason)",
                        abilityGaps: question.abilityTags
                    )
            }
        }

        for unit in textbookUnits {
            let weight: Int
            switch unit.progressStatus {
            case .blocked:
                weight = 2
            case .reviewing:
                weight = 1
            case .notStarted, .learning, .mastered:
                continue
            }
            for point in unit.knowledgePoints {
                buckets[WeakPointKey(unit.subject, point), default: .init(subject: unit.subject, knowledgePoint: point)]
                    .add(
                        weight: weight,
                        source: "textbook",
                        message: "\(unit.title)处于\(unit.progressStatus.label)"
                    )
            }
        }

        for plan in plans {
            let weight: Int
            switch plan.status {
            case .planned, .inProgress:
                weight = 1
            case .skipped:
                weight = 2
            case .completed:
                continue
            }
            buckets[WeakPointKey(plan.subject, plan.knowledgePoint), default: .init(subject: plan.subject, knowledgePoint: plan.knowledgePoint)]
                .add(
                    weight: weight,
                    source: "plan",
                    message: "计划「\(plan.action)」状态：\(plan.status.label)"
                )
        }

        return buckets.values
            .map { $0.makeWeakPoint() }
            .filter { $0.severity > 0 }
            .sorted {
                if $0.severity != $1.severity { return $0.severity > $1.severity }
                if $0.subject != $1.subject { return $0.subject < $1.subject }
                return $0.knowledgePoint < $1.knowledgePoint
            }
    }
}

private struct WeakPointKey: Hashable {
    var subject: String
    var knowledgePoint: KnowledgePoint

    init(_ subject: String, _ knowledgePoint: KnowledgePoint) {
        self.subject = subject
        self.knowledgePoint = knowledgePoint
    }
}

private struct WeakPointAccumulator {
    var subject: String
    var knowledgePoint: KnowledgePoint
    var severity = 0
    var evidence: [WeakPointEvidence] = []
    var abilityGaps: [String] = []

    mutating func add(
        weight: Int,
        source: String,
        message: String,
        abilityGaps newAbilityGaps: [String] = []
    ) {
        severity += weight
        evidence.append(.init(source: source, message: message, weight: weight))
        for gap in newAbilityGaps where !abilityGaps.contains(gap) {
            abilityGaps.append(gap)
        }
    }

    func makeWeakPoint() -> WeakPoint {
        WeakPoint(
            subject: subject,
            knowledgePoint: knowledgePoint,
            severity: severity,
            evidence: evidence,
            abilityGaps: abilityGaps,
            suggestion: suggestion()
        )
    }

    private func suggestion() -> String {
        if abilityGaps.contains(where: { $0.contains("审题") }) {
            return "先做审题口述：让孩子说出题意和已知条件，再动笔列式。"
        }
        if abilityGaps.contains(where: { $0.contains("等量") || $0.contains("关系") }) {
            return "每题先写出数量关系，再做 2 道同类变式题。"
        }
        return "本周安排 10-15 分钟短练，并记录下一次正确率变化。"
    }
}
