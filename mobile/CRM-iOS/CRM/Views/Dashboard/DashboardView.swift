import SwiftUI

struct DashboardView: View {
    @EnvironmentObject var dataManager: DataManager
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // Welcome Header
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Dashboard")
                                .font(.largeTitle)
                                .fontWeight(.bold)
                            Text("Willkommen zurück, Max")
                                .foregroundColor(AppColors.midGray)
                        }
                        Spacer()
                        
                        Button(action: {}) {
                            Image(systemName: "plus")
                                .font(.title2)
                                .foregroundColor(.white)
                                .frame(width: 44, height: 44)
                                .background(AppColors.orange)
                                .clipShape(Circle())
                        }
                    }
                    .padding(.horizontal)
                    
                    // KPI Cards
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                        KPICard(
                            title: "Offene Deals",
                            value: "€\(dataManager.dashboardStats.openDealsValue / 1000)K",
                            change: "+12%",
                            positive: true,
                            icon: "target",
                            color: AppColors.orange
                        )
                        
                        KPICard(
                            title: "Neue Kontakte",
                            value: "\(dataManager.dashboardStats.newContacts)",
                            change: "+8",
                            positive: true,
                            icon: "person.2.fill",
                            color: AppColors.blue
                        )
                        
                        KPICard(
                            title: "Gewonnen",
                            value: "€\(dataManager.dashboardStats.wonDealsValue / 1000)K",
                            change: "+23%",
                            positive: true,
                            icon: "eurosign",
                            color: AppColors.green
                        )
                        
                        KPICard(
                            title: "Conversion",
                            value: "\(Int(dataManager.dashboardStats.conversionRate))%",
                            change: "-2%",
                            positive: false,
                            icon: "chart.line.uptrend.xyaxis",
                            color: AppColors.midGray
                        )
                    }
                    .padding(.horizontal)
                    
                    // Recent Deals
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("Aktuelle Deals")
                                .font(.headline)
                            Spacer()
                            NavigationLink(destination: DealsListView()) {
                                Text("Alle anzeigen")
                                    .font(.subheadline)
                                    .foregroundColor(AppColors.orange)
                            }
                        }
                        
                        VStack(spacing: 0) {
                            ForEach(dataManager.recentDeals) { deal in
                                DealRow(deal: deal)
                                if deal.id != dataManager.recentDeals.last?.id {
                                    Divider()
                                }
                            }
                        }
                        .background(Color.white)
                        .cornerRadius(12)
                    }
                    .padding(.horizontal)
                    
                    // Today's Activities
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("Heute")
                                .font(.headline)
                            Spacer()
                            Text(Date(), style: .date)
                                .font(.caption)
                                .foregroundColor(AppColors.midGray)
                        }
                        
                        VStack(spacing: 0) {
                            ForEach(dataManager.todayActivities) { activity in
                                ActivityRow(activity: activity)
                                if activity.id != dataManager.todayActivities.last?.id {
                                    Divider()
                                }
                            }
                        }
                        .background(Color.white)
                        .cornerRadius(12)
                    }
                    .padding(.horizontal)
                    
                    // Team Ranking
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Team Ranking")
                            .font(.headline)
                        
                        VStack(spacing: 0) {
                            ForEach(Array(dataManager.teamMembers.enumerated()), id: \.element.id) { index, member in
                                TeamMemberRow(member: member, rank: index + 1)
                                if index < dataManager.teamMembers.count - 1 {
                                    Divider()
                                }
                            }
                        }
                        .background(Color.white)
                        .cornerRadius(12)
                    }
                    .padding(.horizontal)
                }
                .padding(.vertical)
            }
            .background(AppColors.light)
        }
    }
}

// MARK: - KPI Card
struct KPICard: View {
    let title: String
    let value: String
    let change: String
    let positive: Bool
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)
                    .frame(width: 40, height: 40)
                    .background(color.opacity(0.15))
                    .cornerRadius(10)
                
                Spacer()
                
                HStack(spacing: 2) {
                    Image(systemName: positive ? "arrow.up.right" : "arrow.down.right")
                        .font(.caption2)
                    Text(change)
                        .font(.caption)
                        .fontWeight(.semibold)
                }
                .foregroundColor(positive ? AppColors.green : AppColors.red)
            }
            
            Text(value)
                .font(.title)
                .fontWeight(.bold)
            
            Text(title)
                .font(.subheadline)
                .foregroundColor(AppColors.midGray)
        }
        .padding()
        .background(Color.white)
        .cornerRadius(12)
    }
}

// MARK: - Deal Row
struct DealRow: View {
    let deal: Deal
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(deal.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text(deal.contact)
                    .font(.caption)
                    .foregroundColor(AppColors.midGray)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text("€\(deal.value.formatted())")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                
                Text("\(deal.stage.rawValue) · \(deal.probability)%")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(hex: deal.stage.color).opacity(0.15))
                    .foregroundColor(Color(hex: deal.stage.color))
                    .cornerRadius(6)
            }
        }
        .padding()
    }
}

// MARK: - Activity Row
struct ActivityRow: View {
    let activity: Activity
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: activity.type.icon)
                .font(.subheadline)
                .foregroundColor(AppColors.blue)
                .frame(width: 32, height: 32)
                .background(AppColors.blue.opacity(0.15))
                .cornerRadius(8)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(activity.title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text(activity.contact)
                    .font(.caption)
                    .foregroundColor(AppColors.midGray)
            }
            
            Spacer()
            
            if let time = activity.dueTime {
                Text(time)
                    .font(.caption)
                    .foregroundColor(AppColors.midGray)
            }
        }
        .padding()
    }
}

// MARK: - Team Member Row
struct TeamMemberRow: View {
    let member: TeamMember
    let rank: Int
    
    var body: some View {
        HStack(spacing: 12) {
            Text("#\(rank)")
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(rank <= 3 ? AppColors.orange : AppColors.midGray)
                .frame(width: 24)
            
            Text(member.initials)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(AppColors.blue)
                .frame(width: 32, height: 32)
                .background(AppColors.blue.opacity(0.2))
                .clipShape(Circle())
            
            VStack(alignment: .leading, spacing: 2) {
                Text(member.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text("\(member.deals) Deals")
                    .font(.caption)
                    .foregroundColor(AppColors.midGray)
            }
            
            Spacer()
            
            Text("€\(member.revenue / 1000)K")
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(AppColors.green)
        }
        .padding()
    }
}

#Preview {
    DashboardView()
        .environmentObject(DataManager())
}
