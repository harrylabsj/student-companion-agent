import StudentCompanionCore
import SwiftUI

@main
struct StudentCompanionApp: App {
    @State private var store = StudentCompanionStore(snapshot: .demo)

    var body: some Scene {
        WindowGroup {
            MainTabView()
                .environment(store)
        }
    }
}
