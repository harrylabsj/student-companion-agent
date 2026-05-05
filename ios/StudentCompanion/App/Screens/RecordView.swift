import StudentCompanionCore
import SwiftUI

struct RecordView: View {
    @Environment(StudentCompanionStore.self) private var store
    @State private var mode: RecordMode = .score

    @State private var profileName = ""
    @State private var profileGrade = ""
    @State private var profileSchool = ""
    @State private var profileGoal = ""

    @State private var scoreSubject = "数学"
    @State private var scoreTitle = "单元测验"
    @State private var scoreValue = "80"
    @State private var scoreMax = "100"
    @State private var scoreKnowledge = "分数应用题"
    @State private var scoreNotes = ""

    @State private var wrongSubject = "数学"
    @State private var wrongSource = "周练"
    @State private var wrongLabel = "第 1 题"
    @State private var wrongKnowledge = "分数应用题"
    @State private var wrongAbilities = "审题提取信息"
    @State private var wrongReason = "漏读条件"
    @State private var wrongStatus: CorrectionStatus = .unresolved
    @State private var wrongNotes = ""

    var body: some View {
        Form {
            Picker("录入类型", selection: $mode) {
                ForEach(RecordMode.allCases) { mode in
                    Text(mode.title).tag(mode)
                }
            }
            .pickerStyle(.segmented)

            switch mode {
            case .profile:
                profileSection
            case .score:
                scoreSection
            case .wrongQuestion:
                wrongQuestionSection
            }
        }
        .navigationTitle("录入")
        .onAppear(perform: fillProfileIfNeeded)
    }

    private var profileSection: some View {
        Section("学生基本信息") {
            TextField("姓名", text: $profileName)
            TextField("年级", text: $profileGrade)
            TextField("学校（可选）", text: $profileSchool)
            TextField("学习目标", text: $profileGoal)
            Button("保存学生信息") {
                let goals = profileGoal.isEmpty ? store.profile.goals : [profileGoal]
                store.updateProfile(
                    StudentProfile(
                        id: store.profile.id,
                        name: profileName.trimmedNonEmpty(default: store.profile.name),
                        grade: profileGrade.trimmedNonEmpty(default: store.profile.grade),
                        school: profileSchool,
                        goals: goals,
                        activeSubjects: store.profile.activeSubjects,
                        createdAt: store.profile.createdAt
                    )
                )
            }
        }
    }

    private var scoreSection: some View {
        Section("考试成绩") {
            TextField("科目", text: $scoreSubject)
            TextField("考试名称", text: $scoreTitle)
            HStack {
                TextField("得分", text: $scoreValue)
                TextField("满分", text: $scoreMax)
            }
            TextField("关联知识点，用逗号分隔", text: $scoreKnowledge)
            TextField("备注", text: $scoreNotes, axis: .vertical)
            Button("保存成绩并更新分析") {
                let score = ScoreRecord(
                    subject: scoreSubject.trimmedNonEmpty(default: "数学"),
                    title: scoreTitle.trimmedNonEmpty(default: "考试"),
                    score: Double(scoreValue) ?? 0,
                    maxScore: max(Double(scoreMax) ?? 100, 1),
                    knowledgePoints: scoreKnowledge.knowledgeList,
                    notes: scoreNotes
                )
                store.addScore(score)
                scoreTitle = ""
                scoreNotes = ""
            }
        }
    }

    private var wrongQuestionSection: some View {
        Section("错题记录") {
            TextField("科目", text: $wrongSubject)
            TextField("来源，如期中考试/周练", text: $wrongSource)
            TextField("题号", text: $wrongLabel)
            TextField("知识点，用逗号分隔", text: $wrongKnowledge)
            TextField("能力标签，用逗号分隔", text: $wrongAbilities)
            TextField("错因", text: $wrongReason)
            Picker("订正状态", selection: $wrongStatus) {
                ForEach(CorrectionStatus.allCases, id: \.self) { status in
                    Text(status.label).tag(status)
                }
            }
            TextField("复盘备注", text: $wrongNotes, axis: .vertical)
            Button("保存错题") {
                let question = WrongQuestion(
                    subject: wrongSubject.trimmedNonEmpty(default: "数学"),
                    sourceTitle: wrongSource.trimmedNonEmpty(default: "练习"),
                    questionLabel: wrongLabel.trimmedNonEmpty(default: "题目"),
                    knowledgePoints: wrongKnowledge.knowledgeList,
                    abilityTags: wrongAbilities.knowledgeList,
                    errorReason: wrongReason.trimmedNonEmpty(default: "未填写"),
                    correctionStatus: wrongStatus,
                    notes: wrongNotes
                )
                store.addWrongQuestion(question)
                wrongLabel = ""
                wrongNotes = ""
            }
        }
    }

    private func fillProfileIfNeeded() {
        guard profileName.isEmpty else { return }
        profileName = store.profile.name
        profileGrade = store.profile.grade
        profileSchool = store.profile.school
        profileGoal = store.profile.goals.first ?? ""
    }
}

private enum RecordMode: String, CaseIterable, Identifiable {
    case score
    case wrongQuestion
    case profile

    var id: String { rawValue }

    var title: String {
        switch self {
        case .score: "成绩"
        case .wrongQuestion: "错题"
        case .profile: "学生"
        }
    }
}

extension String {
    var knowledgeList: [String] {
        split { ",，、;；\n".contains($0) }
            .map { String($0).trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }

    func trimmedNonEmpty(default fallback: String) -> String {
        let value = trimmingCharacters(in: .whitespacesAndNewlines)
        return value.isEmpty ? fallback : value
    }
}
