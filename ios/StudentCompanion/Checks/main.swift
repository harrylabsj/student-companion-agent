import Foundation
import StudentCompanionCore

func check(_ condition: @autoclosure () -> Bool, _ message: String) {
    if !condition() {
        fputs("Check failed: \(message)\n", stderr)
        exit(1)
    }
}

func checkStudentProfileStoresBasicLearningContext() {
    let profile = StudentProfile(
        name: "小明",
        grade: "五年级",
        school: "实验小学",
        goals: ["数学稳定 90+"],
        activeSubjects: ["数学", "语文"]
    )

    check(profile.name == "小明", "profile name")
    check(profile.grade == "五年级", "profile grade")
    check(profile.school == "实验小学", "profile school")
    check(profile.goals == ["数学稳定 90+"], "profile goals")
    check(profile.activeSubjects == ["数学", "语文"], "profile active subjects")
}

func checkDomainModelsCaptureRequiredRecords() {
    let textbookID = UUID()
    let score = ScoreRecord(
        subject: "数学",
        title: "期中考试",
        score: 78,
        maxScore: 100,
        knowledgePoints: ["分数应用题", "单位换算"],
        notes: "应用题扣分多"
    )
    let wrongQuestion = WrongQuestion(
        subject: "数学",
        sourceTitle: "期中考试",
        questionLabel: "第 8 题",
        knowledgePoints: ["分数应用题"],
        abilityTags: ["审题提取信息", "建立等量关系"],
        errorReason: "等量关系不清",
        correctionStatus: .reviewing,
        notes: "能列式但条件找不全"
    )
    let textbook = Textbook(
        id: textbookID,
        subject: "数学",
        name: "数学五年级上册",
        publisher: "人教版",
        grade: "五年级",
        semester: "上"
    )
    let unit = TextbookUnit(
        textbookID: textbookID,
        subject: "数学",
        title: "第 3 单元 分数应用题",
        sequence: 3,
        knowledgePoints: ["分数应用题"],
        progressStatus: .blocked
    )
    let plan = LearningPlan(
        subject: "数学",
        knowledgePoint: "分数应用题",
        action: "本周做 6 道变式题",
        dueDate: Date(timeIntervalSince1970: 1_779_292_800),
        status: .inProgress,
        reviewNote: ""
    )

    check(score.accuracy == 0.78, "score accuracy")
    check(wrongQuestion.abilityTags.count == 2, "wrong question ability tags")
    check(textbook.publisher == "人教版", "textbook publisher")
    check(unit.progressStatus == .blocked, "textbook progress")
    check(plan.status == .inProgress, "plan status")
}

func checkWeakPointAnalyzerExposesKnowledgeAndAbilityGaps() {
    let profile = StudentProfile(name: "小明", grade: "五年级", activeSubjects: ["数学"])
    let textbookID = UUID()
    let weakPoints = WeakPointAnalyzer().analyze(
        profile: profile,
        scores: [
            ScoreRecord(
                subject: "数学",
                title: "期中考试",
                score: 58,
                maxScore: 100,
                knowledgePoints: ["分数应用题"],
                notes: ""
            )
        ],
        wrongQuestions: [
            WrongQuestion(
                subject: "数学",
                sourceTitle: "周练",
                questionLabel: "第 4 题",
                knowledgePoints: ["分数应用题"],
                abilityTags: ["审题提取信息"],
                errorReason: "条件漏读",
                correctionStatus: .unresolved,
                notes: ""
            ),
            WrongQuestion(
                subject: "数学",
                sourceTitle: "作业",
                questionLabel: "第 6 题",
                knowledgePoints: ["分数应用题"],
                abilityTags: ["建立等量关系"],
                errorReason: "关系式错误",
                correctionStatus: .reviewing,
                notes: ""
            )
        ],
        textbookUnits: [
            TextbookUnit(
                textbookID: textbookID,
                subject: "数学",
                title: "第 3 单元 分数应用题",
                sequence: 3,
                knowledgePoints: ["分数应用题"],
                progressStatus: .blocked
            )
        ],
        plans: [
            LearningPlan(
                subject: "数学",
                knowledgePoint: "分数应用题",
                action: "本周做 6 道变式题",
                dueDate: Date(),
                status: .inProgress,
                reviewNote: ""
            )
        ]
    )

    let top = weakPoints.first
    check(top?.subject == "数学", "weak point subject")
    check(top?.knowledgePoint == "分数应用题", "weak point knowledge point")
    check((top?.severity ?? 0) >= 10, "weak point severity")
    check(top?.abilityGaps.contains("审题提取信息") == true, "ability gap from wrong question")
    check(top?.evidence.contains { $0.message.contains("期中考试") } == true, "score evidence")
    check(top?.suggestion.contains("审题") == true, "parent-readable suggestion")
}

func checkStoreMutatesAndPersistsLearningData() throws {
    let store = StudentCompanionStore(snapshot: .demo)
    let plan = LearningPlan(
        subject: "数学",
        knowledgePoint: "分数应用题",
        action: "口述 2 道错题",
        dueDate: Date(timeIntervalSince1970: 1_779_292_800),
        status: .planned,
        reviewNote: ""
    )
    store.addPlan(plan)
    store.completePlan(id: plan.id, reviewNote: "已完成，仍需检查等量关系")

    let savedPlan = store.plans.first { $0.id == plan.id }
    check(savedPlan?.status == .completed, "completed plan status")
    check(savedPlan?.reviewNote == "已完成，仍需检查等量关系", "completed plan review note")

    let url = URL(fileURLWithPath: NSTemporaryDirectory())
        .appendingPathComponent("student-companion-check-\(UUID().uuidString).json")
    try store.save(to: url)
    let loaded = try StudentCompanionStore.load(from: url)
    try? FileManager.default.removeItem(at: url)

    check(loaded.profile.name == store.profile.name, "loaded profile")
    check(loaded.plans.contains { $0.id == plan.id && $0.status == .completed }, "loaded completed plan")
}

checkStudentProfileStoresBasicLearningContext()
checkDomainModelsCaptureRequiredRecords()
checkWeakPointAnalyzerExposesKnowledgeAndAbilityGaps()
try checkStoreMutatesAndPersistsLearningData()
print("StudentCompanionCoreChecks ok")
