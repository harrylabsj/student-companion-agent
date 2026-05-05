import StudentCompanionCore
import SwiftUI

struct PlanView: View {
    @Environment(StudentCompanionStore.self) private var store

    @State private var subject = "数学"
    @State private var knowledgePoint = "分数应用题"
    @State private var action = "做 6 道变式题，每题先口述题意"
    @State private var dueDate = Date().addingTimeInterval(3 * 24 * 60 * 60)
    @State private var reviewNote = "已完成，等待下次小测验证"

    var body: some View {
        Form {
            Section("添加学习计划") {
                TextField("科目", text: $subject)
                TextField("知识点", text: $knowledgePoint)
                TextField("行动", text: $action, axis: .vertical)
                DatePicker("截止日期", selection: $dueDate, displayedComponents: .date)
                Button("添加计划") {
                    store.addPlan(
                        LearningPlan(
                            subject: subject.trimmedNonEmpty(default: "数学"),
                            knowledgePoint: knowledgePoint.trimmedNonEmpty(default: "知识点"),
                            action: action.trimmedNonEmpty(default: "完成一项学习任务"),
                            dueDate: dueDate,
                            status: .planned,
                            reviewNote: ""
                        )
                    )
                    action = ""
                }
            }

            Section("计划跟踪") {
                TextField("完成备注", text: $reviewNote, axis: .vertical)
                ForEach(store.plans) { plan in
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(plan.action)
                                    .font(.headline)
                                Text("\(plan.subject) · \(plan.knowledgePoint)")
                                    .font(.caption)
                                    .foregroundStyle(CompanionPalette.muted)
                            }
                            Spacer()
                            TagView(text: plan.status.label, tint: statusTint(plan.status))
                        }
                        if !plan.reviewNote.isEmpty {
                            Text(plan.reviewNote)
                                .font(.caption)
                                .foregroundStyle(CompanionPalette.muted)
                        }
                        if plan.status != .completed {
                            Button("标记完成") {
                                store.completePlan(id: plan.id, reviewNote: reviewNote)
                            }
                            .buttonStyle(.borderedProminent)
                        }
                    }
                    .padding(.vertical, 6)
                }
            }
        }
        .navigationTitle("计划")
    }

    private func statusTint(_ status: PlanStatus) -> Color {
        switch status {
        case .planned:
            CompanionPalette.blue
        case .inProgress:
            CompanionPalette.amber
        case .completed:
            CompanionPalette.green
        case .skipped:
            CompanionPalette.red
        }
    }
}
