import SwiftUI

enum CompanionPalette {
    static let background = Color(red: 0.96, green: 0.98, blue: 0.99)
    static let ink = Color(red: 0.06, green: 0.09, blue: 0.16)
    static let muted = Color(red: 0.39, green: 0.45, blue: 0.55)
    static let teal = Color(red: 0.04, green: 0.47, blue: 0.43)
    static let blue = Color(red: 0.15, green: 0.38, blue: 0.92)
    static let green = Color(red: 0.09, green: 0.64, blue: 0.29)
    static let amber = Color(red: 0.85, green: 0.42, blue: 0.03)
    static let red = Color(red: 0.86, green: 0.15, blue: 0.15)
}

struct CompanionCard<Content: View>: View {
    var title: String?
    var systemImage: String?
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            if let title {
                HStack(spacing: 8) {
                    if let systemImage {
                        Image(systemName: systemImage)
                            .foregroundStyle(CompanionPalette.teal)
                    }
                    Text(title)
                        .font(.headline)
                        .foregroundStyle(CompanionPalette.ink)
                }
            }
            content
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
        .shadow(color: .black.opacity(0.06), radius: 12, x: 0, y: 6)
    }
}

struct MetricTile: View {
    var title: String
    var value: String
    var tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption)
                .foregroundStyle(CompanionPalette.muted)
            Text(value)
                .font(.title2.weight(.bold))
                .foregroundStyle(tint)
        }
        .frame(maxWidth: .infinity, minHeight: 72, alignment: .leading)
        .padding(14)
        .background(tint.opacity(0.09))
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}

struct TagView: View {
    var text: String
    var tint: Color = CompanionPalette.teal

    var body: some View {
        Text(text)
            .font(.caption.weight(.semibold))
            .foregroundStyle(tint)
            .padding(.horizontal, 9)
            .padding(.vertical, 6)
            .background(tint.opacity(0.12))
            .clipShape(Capsule())
    }
}

extension View {
    func appBackground() -> some View {
        background(CompanionPalette.background.ignoresSafeArea())
    }
}
