import Foundation
import SwiftUI

@MainActor
class DataManager: ObservableObject {
    @Published var contacts: [Contact] = []
    @Published var companies: [Company] = []
    @Published var deals: [Deal] = []
    @Published var activities: [Activity] = []
    @Published var teamMembers: [TeamMember] = []
    
    init() {
        loadSampleData()
    }
    
    var dashboardStats: DashboardStats {
        let openDeals = deals.filter { $0.stage != .won && $0.stage != .lost }
        let wonDeals = deals.filter { $0.stage == .won }
        
        return DashboardStats(
            openDeals: openDeals.count,
            openDealsValue: openDeals.reduce(0) { $0 + $1.value },
            newContacts: 34,
            wonDealsValue: wonDeals.reduce(0) { $0 + $1.value },
            conversionRate: 32.0
        )
    }
    
    var todayActivities: [Activity] {
        let calendar = Calendar.current
        return activities.filter { 
            calendar.isDateInToday($0.dueDate) && !$0.completed 
        }.sorted { ($0.dueTime ?? "") < ($1.dueTime ?? "") }
    }
    
    var recentDeals: [Deal] {
        deals.filter { $0.stage != .won && $0.stage != .lost }
            .sorted { $0.value > $1.value }
            .prefix(4)
            .map { $0 }
    }
    
    func toggleActivityComplete(_ activity: Activity) {
        if let index = activities.firstIndex(where: { $0.id == activity.id }) {
            activities[index].completed.toggle()
        }
    }
    
    func moveDeal(_ deal: Deal, to stage: DealStage) {
        if let index = deals.firstIndex(where: { $0.id == deal.id }) {
            deals[index].stage = stage
        }
    }
    
    // MARK: - Sample Data
    private func loadSampleData() {
        let dateFormatter = ISO8601DateFormatter()
        
        contacts = [
            Contact(id: "1", firstName: "Thomas", lastName: "Müller", email: "mueller@muellerundsoehne.de", phone: "+49 711 123456", company: "Müller & Söhne GmbH", position: "Geschäftsführer", tags: ["Bestandskunde", "VIP"], lastContact: Date(), owner: "Max Kaufmann"),
            Contact(id: "2", firstName: "Anna", lastName: "Schmidt", email: "a.schmidt@schmidt-ag.de", phone: "+49 89 987654", company: "Schmidt AG", position: "IT-Leiterin", tags: ["Neukunde"], lastContact: Date(), owner: "Sarah Meyer"),
            Contact(id: "3", firstName: "Klaus", lastName: "Bauer", email: "k.bauer@bauer-kg.de", phone: "+49 30 456789", company: "Bauer KG", position: "Einkauf", tags: ["Lead"], lastContact: Date(), owner: "Max Kaufmann"),
            Contact(id: "4", firstName: "Lisa", lastName: "Weber", email: "weber@webertechnik.de", phone: "+49 40 321654", company: "Weber Technik", position: "CEO", tags: ["Bestandskunde"], lastContact: Date(), owner: "Tim Hoffmann"),
            Contact(id: "5", firstName: "Peter", lastName: "Fischer", email: "p.fischer@fischer-gmbh.de", phone: "+49 221 654321", company: "Fischer GmbH", position: "Vertriebsleiter", tags: ["Lead", "Warm"], lastContact: Date(), owner: "Julia Klein"),
        ]
        
        companies = [
            Company(id: "1", name: "Müller & Söhne GmbH", industry: "Maschinenbau", size: "50-200", website: "muellerundsoehne.de", city: "Stuttgart", country: "Deutschland", contacts: 4, deals: 2, totalValue: 78000, owner: "Max Kaufmann", status: .customer),
            Company(id: "2", name: "Schmidt AG", industry: "IT-Services", size: "200-500", website: "schmidt-ag.de", city: "München", country: "Deutschland", contacts: 6, deals: 3, totalValue: 185000, owner: "Sarah Meyer", status: .customer),
            Company(id: "3", name: "Bauer KG", industry: "Handel", size: "10-50", website: "bauer-kg.de", city: "Berlin", country: "Deutschland", contacts: 2, deals: 1, totalValue: 24000, owner: "Max Kaufmann", status: .prospect),
            Company(id: "4", name: "Weber Technik", industry: "Elektrotechnik", size: "50-200", website: "webertechnik.de", city: "Hamburg", country: "Deutschland", contacts: 3, deals: 1, totalValue: 67000, owner: "Tim Hoffmann", status: .customer),
        ]
        
        deals = [
            Deal(id: "1", name: "ERP-Integration Müller GmbH", value: 45000, stage: .negotiation, probability: 80, contact: "Thomas Müller", company: "Müller & Söhne GmbH", owner: "Max Kaufmann", expectedClose: Date().addingTimeInterval(86400 * 15), createdAt: Date()),
            Deal(id: "2", name: "Cloud Migration Schmidt AG", value: 128000, stage: .proposal, probability: 60, contact: "Anna Schmidt", company: "Schmidt AG", owner: "Sarah Meyer", expectedClose: Date().addingTimeInterval(86400 * 30), createdAt: Date()),
            Deal(id: "3", name: "IT-Wartung Bauer KG", value: 24000, stage: .qualified, probability: 40, contact: "Klaus Bauer", company: "Bauer KG", owner: "Max Kaufmann", expectedClose: Date().addingTimeInterval(86400 * 28), createdAt: Date()),
            Deal(id: "4", name: "Netzwerk-Upgrade Weber", value: 67000, stage: .negotiation, probability: 75, contact: "Lisa Weber", company: "Weber Technik", owner: "Tim Hoffmann", expectedClose: Date().addingTimeInterval(86400 * 10), createdAt: Date()),
            Deal(id: "5", name: "Software-Lizenzierung Fischer", value: 35000, stage: .lead, probability: 20, contact: "Peter Fischer", company: "Fischer GmbH", owner: "Julia Klein", expectedClose: Date().addingTimeInterval(86400 * 60), createdAt: Date()),
            Deal(id: "6", name: "VoIP System Wagner", value: 42000, stage: .won, probability: 100, contact: "Andrea Wagner", company: "Wagner Tech", owner: "Tim Hoffmann", expectedClose: Date(), createdAt: Date()),
        ]
        
        activities = [
            Activity(id: "1", type: .call, title: "Folgeanruf Müller GmbH", description: "Nachfassen zum Angebot", contact: "Thomas Müller", company: "Müller & Söhne GmbH", dueDate: Date(), dueTime: "10:00", completed: false, owner: "Max Kaufmann", priority: .high),
            Activity(id: "2", type: .meeting, title: "Demo Schmidt AG", description: "Produktvorstellung", contact: "Anna Schmidt", company: "Schmidt AG", dueDate: Date(), dueTime: "14:00", completed: false, owner: "Sarah Meyer", priority: .high),
            Activity(id: "3", type: .email, title: "Angebot nachfassen", contact: "Klaus Bauer", company: "Bauer KG", dueDate: Date(), dueTime: "16:00", completed: false, owner: "Max Kaufmann", priority: .medium),
            Activity(id: "4", type: .call, title: "Erstgespräch Fischer", description: "Bedarfsanalyse", contact: "Peter Fischer", company: "Fischer GmbH", dueDate: Date().addingTimeInterval(86400), dueTime: "09:00", completed: false, owner: "Julia Klein", priority: .medium),
        ]
        
        teamMembers = [
            TeamMember(id: "1", name: "Max Kaufmann", deals: 12, revenue: 234000),
            TeamMember(id: "2", name: "Sarah Meyer", deals: 9, revenue: 187000),
            TeamMember(id: "3", name: "Tim Hoffmann", deals: 8, revenue: 156000),
            TeamMember(id: "4", name: "Julia Klein", deals: 6, revenue: 142000),
        ]
    }
}
