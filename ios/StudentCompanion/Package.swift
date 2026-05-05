// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "StudentCompanion",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    products: [
        .library(name: "StudentCompanionCore", targets: ["StudentCompanionCore"]),
        .executable(name: "StudentCompanionApp", targets: ["StudentCompanionApp"]),
        .executable(name: "StudentCompanionCoreChecks", targets: ["StudentCompanionCoreChecks"])
    ],
    targets: [
        .target(name: "StudentCompanionCore"),
        .executableTarget(
            name: "StudentCompanionApp",
            dependencies: ["StudentCompanionCore"],
            path: "App"
        ),
        .executableTarget(
            name: "StudentCompanionCoreChecks",
            dependencies: ["StudentCompanionCore"],
            path: "Checks"
        )
    ]
)
