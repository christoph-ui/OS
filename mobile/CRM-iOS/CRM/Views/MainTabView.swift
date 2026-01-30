import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            DashboardView()
                .tabItem {
                    Image(systemName: "square.grid.2x2.fill")
                    Text("Dashboard")
                }
                .tag(0)
            
            ContactsListView()
                .tabItem {
                    Image(systemName: "person.2.fill")
                    Text("Kontakte")
                }
                .tag(1)
            
            CompaniesListView()
                .tabItem {
                    Image(systemName: "building.2.fill")
                    Text("Firmen")
                }
                .tag(2)
            
            DealsListView()
                .tabItem {
                    Image(systemName: "target")
                    Text("Deals")
                }
                .tag(3)
            
            ActivitiesListView()
                .tabItem {
                    Image(systemName: "checkmark.square.fill")
                    Text("Aktivitäten")
                }
                .tag(4)
        }
        .tint(AppColors.orange)
    }
}

#Preview {
    MainTabView()
        .environmentObject(DataManager())
}
