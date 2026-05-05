import StudentCompanionCore
import SwiftUI

struct TextbookView: View {
    @Environment(StudentCompanionStore.self) private var store

    @State private var subject = "数学"
    @State private var name = "数学五年级上册"
    @State private var publisher = "人教版"
    @State private var grade = "五年级"
    @State private var semester = "上"

    @State private var unitTitle = "第 3 单元 分数应用题"
    @State private var unitSequence = "3"
    @State private var unitKnowledge = "分数应用题"
    @State private var progress: ProgressStatus = .learning

    var body: some View {
        Form {
            Section("教材信息") {
                TextField("科目", text: $subject)
                TextField("教材名称", text: $name)
                TextField("出版社", text: $publisher)
                HStack {
                    TextField("年级", text: $grade)
                    TextField("学期", text: $semester)
                }
                Button("添加教材") {
                    store.addTextbook(
                        Textbook(
                            subject: subject.trimmedNonEmpty(default: "数学"),
                            name: name.trimmedNonEmpty(default: "教材"),
                            publisher: publisher,
                            grade: grade,
                            semester: semester
                        )
                    )
                }
            }

            Section("单元进度") {
                TextField("单元/课时", text: $unitTitle)
                TextField("顺序", text: $unitSequence)
                TextField("知识点，用逗号分隔", text: $unitKnowledge)
                Picker("状态", selection: $progress) {
                    ForEach(ProgressStatus.allCases, id: \.self) { status in
                        Text(status.label).tag(status)
                    }
                }
                Button("添加单元进度") {
                    let textbook = ensureTextbook()
                    store.addTextbookUnit(
                        TextbookUnit(
                            textbookID: textbook.id,
                            subject: textbook.subject,
                            title: unitTitle.trimmedNonEmpty(default: "单元"),
                            sequence: Int(unitSequence) ?? store.textbookUnits.count + 1,
                            knowledgePoints: unitKnowledge.knowledgeList,
                            progressStatus: progress
                        )
                    )
                }
            }

            Section("已录入教材") {
                ForEach(store.textbooks) { textbook in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(textbook.name)
                            .font(.headline)
                        Text("\(textbook.subject) · \(textbook.publisher) · \(textbook.grade)\(textbook.semester)")
                            .font(.caption)
                            .foregroundStyle(CompanionPalette.muted)
                    }
                }
            }

            Section("单元状态") {
                ForEach(store.textbookUnits) { unit in
                    VStack(alignment: .leading, spacing: 6) {
                        Text(unit.title)
                            .font(.headline)
                        HStack {
                            TagView(text: unit.subject, tint: CompanionPalette.blue)
                            TagView(text: unit.progressStatus.label, tint: unit.progressStatus == .blocked ? CompanionPalette.red : CompanionPalette.teal)
                        }
                    }
                }
            }
        }
        .navigationTitle("教材")
    }

    private func ensureTextbook() -> Textbook {
        if let existing = store.textbooks.first(where: { $0.subject == subject && $0.name == name }) {
            return existing
        }
        let textbook = Textbook(
            subject: subject.trimmedNonEmpty(default: "数学"),
            name: name.trimmedNonEmpty(default: "教材"),
            publisher: publisher,
            grade: grade,
            semester: semester
        )
        store.addTextbook(textbook)
        return textbook
    }
}
