import SwiftUI

@main
struct CRMApp: App {
    @StateObject private var dataManager = DataManager()
    
    var body: some Scene {
        WindowGroup {
            MainTabView()
                .environmentObject(dataManager)
        }
    }
}

// MARK: - Theme Colors
struct AppColors {
    static let dark = Color(hex: "1e293b")
    static let light = Color(hex: "faf9f5")
    static let midGray = Color(hex: "94a3b8")
    static let lightGray = Color(hex: "e8e6dc")
    static let orange = Color(hex: "d97757")
    static let red = Color(hex: "d75757")
    static let blue = Color(hex: "6a9bcc")
    static let green = Color(hex: "57d797")
}

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 6:
            (a, r, g, b) = (255, (int >> 16) & 0xFF, (int >> 8) & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
