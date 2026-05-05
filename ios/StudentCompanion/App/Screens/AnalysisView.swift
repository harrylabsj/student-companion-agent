import StudentCompanionCore
import SwiftUI

struct AnalysisView: View {
    @Environment(StudentCompanionStore.self) private var store

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                summary
                ForEach(store.weakPoints()) { weakPoint in
                    weakPointCard(weakPoint)
                }
            }
            .padding(16)
        }
        .appBackground()
        .navigationTitle("薄弱点分析")
    }

    private var summary: some View {
        CompanionCard(title: "分析说明", systemImage: "lightbulb") {
            Text("根据成绩正确率、重复错题、教材进度和计划执行生成。每个结论都保留证据，便于家长判断下一步。")
                .font(.callout)
                .foregroundStyle(CompanionPalette.muted)
        }
    }

    private func weakPointCard(_ weakPoint: WeakPoint) -> some View {
        CompanionCard(title: "\(weakPoint.subject) · \(weakPoint.knowledgePoint)", systemImage: "exclamationmark.triangle") {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    MetricTile(title: "严重度", value: "\(weakPoint.severity)", tint: CompanionPalette.red)
                    MetricTile(title: "证据", value: "\(weakPoint.evidence.count)", tint: CompanionPalette.amber)
                }

                if !weakPoint.abilityGaps.isEmpty {
                    WrapTags(items: weakPoint.abilityGaps, tint: CompanionPalette.blue)
                }

                Text(weakPoint.suggestion)
                    .font(.headline)
                    .foregroundStyle(CompanionPalette.teal)

                VStack(alignment: .leading, spacing: 8) {
                    ForEach(weakPoint.evidence) { evidence in
                        HStack(alignment: .top, spacing: 8) {
                            Image(systemName: "checkmark.seal")
                                .foregroundStyle(CompanionPalette.green)
                            Text(evidence.message)
                                .font(.subheadline)
                                .foregroundStyle(CompanionPalette.ink)
                        }
                    }
                }
            }
        }
    }
}

struct WrapTags: View {
    var items: [String]
    var tint: Color

    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 96), spacing: 8)], alignment: .leading, spacing: 8) {
            ForEach(items, id: \.self) { item in
                TagView(text: item, tint: tint)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }
}
