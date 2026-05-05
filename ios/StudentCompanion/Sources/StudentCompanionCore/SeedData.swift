import Foundation

public extension StudentCompanionSnapshot {
    static var demo: StudentCompanionSnapshot {
        let textbookID = UUID(uuidString: "11111111-1111-1111-1111-111111111111")!
        let profile = StudentProfile(
            id: UUID(uuidString: "22222222-2222-2222-2222-222222222222")!,
            name: "小明",
            grade: "五年级",
            school: "实验小学",
            goals: ["数学稳定 90+", "减少应用题失分"],
            activeSubjects: ["数学", "语文", "英语"]
        )
        return StudentCompanionSnapshot(
            profile: profile,
            scores: [
                ScoreRecord(
                    id: UUID(uuidString: "33333333-3333-3333-3333-333333333333")!,
                    subject: "数学",
                    title: "期中考试",
                    date: Date(timeIntervalSince1970: 1_777_824_000),
                    score: 78,
                    maxScore: 100,
                    knowledgePoints: ["分数应用题", "单位换算"],
                    notes: "应用题扣分集中"
                )
            ],
            wrongQuestions: [
                WrongQuestion(
                    id: UUID(uuidString: "44444444-4444-4444-4444-444444444444")!,
                    subject: "数学",
                    sourceTitle: "周练",
                    date: Date(timeIntervalSince1970: 1_778_428_800),
                    questionLabel: "第 4 题",
                    knowledgePoints: ["分数应用题"],
                    abilityTags: ["审题提取信息"],
                    errorReason: "漏读关键条件",
                    correctionStatus: .reviewing,
                    notes: "需要先圈出单位和数量关系"
                )
            ],
            textbooks: [
                Textbook(
                    id: textbookID,
                    subject: "数学",
                    name: "数学五年级上册",
                    publisher: "人教版",
                    grade: "五年级",
                    semester: "上"
                )
            ],
            textbookUnits: [
                TextbookUnit(
                    id: UUID(uuidString: "55555555-5555-5555-5555-555555555555")!,
                    textbookID: textbookID,
                    subject: "数学",
                    title: "第 3 单元 分数应用题",
                    sequence: 3,
                    knowledgePoints: ["分数应用题"],
                    progressStatus: .reviewing
                )
            ],
            plans: [
                LearningPlan(
                    id: UUID(uuidString: "66666666-6666-6666-6666-666666666666")!,
                    subject: "数学",
                    knowledgePoint: "分数应用题",
                    action: "本周做 6 道变式题，每题先口述题意",
                    dueDate: Date(timeIntervalSince1970: 1_779_292_800),
                    status: .inProgress,
                    reviewNote: ""
                )
            ]
        )
    }
}
