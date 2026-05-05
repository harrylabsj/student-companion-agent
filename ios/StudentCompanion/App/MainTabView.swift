import SwiftUI

struct MainTabView: View {
    var body: some View {
        TabView {
            NavigationStack {
                HomeView()
            }
            .tabItem { Label("首页", systemImage: "house.fill") }

            NavigationStack {
                RecordView()
            }
            .tabItem { Label("录入", systemImage: "square.and.pencil") }

            NavigationStack {
                AnalysisView()
            }
            .tabItem { Label("分析", systemImage: "chart.bar.xaxis") }

            NavigationStack {
                TextbookView()
            }
            .tabItem { Label("教材", systemImage: "books.vertical.fill") }

            NavigationStack {
                PlanView()
            }
            .tabItem { Label("计划", systemImage: "checklist") }
        }
    }
}
