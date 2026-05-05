import StudentCompanionCore
import SwiftUI

struct HomeView: View {
    @Environment(StudentCompanionStore.self) private var store

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                header
                focusCard
                metrics
                todayPlan
                recentScores
            }
            .padding(16)
        }
        .appBackground()
        .navigationTitle("学习看板")
    }

    private var header: some View {
        HStack(spacing: 14) {
            VStack(alignment: .leading, spacing: 4) {
                Text("\(store.profile.name) / \(store.profile.grade)")
                    .font(.subheadline)
                    .foregroundStyle(CompanionPalette.muted)
                Text("本周学习重点")
                    .font(.largeTitle.weight(.bold))
                    .foregroundStyle(CompanionPalette.ink)
            }
            Spacer()
            Text(String(store.profile.name.prefix(1)))
                .font(.title2.weight(.bold))
                .foregroundStyle(CompanionPalette.blue)
                .frame(width: 48, height: 48)
                .background(CompanionPalette.blue.opacity(0.12))
                .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
        }
    }

    private var focusCard: some View {
        let top = store.weakPoints().first
        return CompanionCard(title: "最需要关注", systemImage: "target") {
            if let top {
                VStack(alignment: .leading, spacing: 10) {
                    Text("\(top.subject) · \(top.knowledgePoint)")
                        .font(.title3.weight(.bold))
                    Text("\(top.evidence.count) 条证据，严重度 \(top.severity)")
                        .font(.subheadline)
                        .foregroundStyle(CompanionPalette.muted)
                    Text(top.suggestion)
                        .font(.callout)
                        .foregroundStyle(CompanionPalette.teal)
                }
            } else {
                Text("暂无薄弱点。录入成绩或错题后会自动生成分析。")
                    .foregroundStyle(CompanionPalette.muted)
            }
        }
    }

    private var metrics: some View {
        HStack(spacing: 12) {
            MetricTile(
                title: "计划完成",
                value: "\(Int((store.planCompletionRate * 100).rounded()))%",
                tint: CompanionPalette.green
            )
            MetricTile(
                title: "待复盘错题",
                value: "\(store.pendingWrongQuestionCount)",
                tint: CompanionPalette.red
            )
        }
    }

    private var todayPlan: some View {
        CompanionCard(title: "今日行动", systemImage: "calendar") {
            if let plan = store.plans.first(where: { $0.status == .planned || $0.status == .inProgress }) {
                VStack(alignment: .leading, spacing: 8) {
                    Text(plan.action)
                        .font(.headline)
                    HStack {
                        TagView(text: plan.subject, tint: CompanionPalette.blue)
                        TagView(text: plan.knowledgePoint, tint: CompanionPalette.teal)
                        TagView(text: plan.status.label, tint: CompanionPalette.amber)
                    }
                }
            } else {
                Text("没有待执行计划。可以从“计划”页添加下一步行动。")
                    .foregroundStyle(CompanionPalette.muted)
            }
        }
    }

    private var recentScores: some View {
        CompanionCard(title: "最近成绩", systemImage: "doc.text.magnifyingglass") {
            ForEach(store.scores.prefix(3)) { score in
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(score.title)
                            .font(.subheadline.weight(.semibold))
                        Text(score.subject)
                            .font(.caption)
                            .foregroundStyle(CompanionPalette.muted)
                    }
                    Spacer()
                    Text("\(Int(score.score))/\(Int(score.maxScore))")
                        .font(.headline)
                        .foregroundStyle(score.accuracy < 0.8 ? CompanionPalette.red : CompanionPalette.green)
                }
                if score.id != store.scores.prefix(3).last?.id {
                    Divider()
                }
            }
        }
    }
}
