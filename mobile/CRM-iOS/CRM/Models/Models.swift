import Foundation

// MARK: - Contact
struct Contact: Identifiable, Codable {
    let id: String
    var firstName: String
    var lastName: String
    var email: String
    var phone: String
    var company: String
    var position: String
    var tags: [String]
    var lastContact: Date
    var owner: String
    
    var fullName: String { "\(firstName) \(lastName)" }
    var initials: String { "\(firstName.prefix(1))\(lastName.prefix(1))" }
}

// MARK: - Company
struct Company: Identifiable, Codable {
    let id: String
    var name: String
    var industry: String
    var size: String
    var website: String
    var city: String
    var country: String
    var contacts: Int
    var deals: Int
    var totalValue: Int
    var owner: String
    var status: CompanyStatus
}

enum CompanyStatus: String, Codable, CaseIterable {
    case customer = "Kunde"
    case prospect = "Interessent"
    case partner = "Partner"
    case inactive = "Inaktiv"
}

// MARK: - Deal
struct Deal: Identifiable, Codable {
    let id: String
    var name: String
    var value: Int
    var stage: DealStage
    var probability: Int
    var contact: String
    var company: String
    var owner: String
    var expectedClose: Date
    var createdAt: Date
}

enum DealStage: String, Codable, CaseIterable {
    case lead = "Lead"
    case qualified = "Qualifiziert"
    case proposal = "Angebot"
    case negotiation = "Verhandlung"
    case won = "Gewonnen"
    case lost = "Verloren"
    
    var color: String {
        switch self {
        case .lead: return "94a3b8"
        case .qualified: return "6a9bcc"
        case .proposal: return "d97757"
        case .negotiation: return "9333ea"
        case .won: return "57d797"
        case .lost: return "d75757"
        }
    }
}

// MARK: - Activity
struct Activity: Identifiable, Codable {
    let id: String
    var type: ActivityType
    var title: String
    var description: String?
    var contact: String
    var company: String
    var dueDate: Date
    var dueTime: String?
    var completed: Bool
    var owner: String
    var priority: Priority
}

enum ActivityType: String, Codable, CaseIterable {
    case call = "Anruf"
    case email = "E-Mail"
    case meeting = "Meeting"
    case task = "Aufgabe"
    
    var icon: String {
        switch self {
        case .call: return "phone.fill"
        case .email: return "envelope.fill"
        case .meeting: return "calendar"
        case .task: return "checkmark.square.fill"
        }
    }
}

enum Priority: String, Codable, CaseIterable {
    case low = "Niedrig"
    case medium = "Mittel"
    case high = "Hoch"
}

// MARK: - Dashboard Stats
struct DashboardStats {
    var openDeals: Int
    var openDealsValue: Int
    var newContacts: Int
    var wonDealsValue: Int
    var conversionRate: Double
}

// MARK: - Team Member
struct TeamMember: Identifiable {
    let id: String
    var name: String
    var deals: Int
    var revenue: Int
    
    var initials: String {
        name.split(separator: " ").map { String($0.prefix(1)) }.joined()
    }
}
