import SwiftUI

struct CompaniesListView: View {
    @EnvironmentObject var dataManager: DataManager
    @State private var searchText = ""
    
    var filteredCompanies: [Company] {
        if searchText.isEmpty {
            return dataManager.companies
        }
        return dataManager.companies.filter {
            $0.name.localizedCaseInsensitiveContains(searchText) ||
            $0.industry.localizedCaseInsensitiveContains(searchText) ||
            $0.city.localizedCaseInsensitiveContains(searchText)
        }
    }
    
    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(spacing: 12) {
                    ForEach(filteredCompanies) { company in
                        NavigationLink(destination: CompanyDetailView(company: company)) {
                            CompanyCard(company: company)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding()
            }
            .background(AppColors.light)
            .searchable(text: $searchText, prompt: "Suche nach Firma, Branche...")
            .navigationTitle("Firmen")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: {}) {
                        Image(systemName: "plus")
                    }
                }
            }
        }
    }
}

struct CompanyCard: View {
    let company: Company
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(alignment: .top) {
                Image(systemName: "building.2.fill")
                    .font(.title2)
                    .foregroundColor(AppColors.blue)
                    .frame(width: 48, height: 48)
                    .background(AppColors.blue.opacity(0.15))
                    .cornerRadius(12)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(company.name)
                        .font(.headline)
                        .foregroundColor(AppColors.dark)
                    
                    Text("\(company.industry) · \(company.size) Mitarbeiter")
                        .font(.caption)
                        .foregroundColor(AppColors.midGray)
                }
                
                Spacer()
                
                Text(company.status.rawValue)
                    .font(.caption)
                    .fontWeight(.medium)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(statusColor(company.status).opacity(0.15))
                    .foregroundColor(statusColor(company.status))
                    .cornerRadius(6)
            }
            
            HStack(spacing: 16) {
                Label(company.city, systemImage: "mappin")
                Label(company.website, systemImage: "globe")
            }
            .font(.caption)
            .foregroundColor(AppColors.midGray)
            
            Divider()
            
            HStack(spacing: 24) {
                VStack(alignment: .leading) {
                    Text("\(company.contacts)")
                        .font(.title3)
                        .fontWeight(.bold)
                    Text("Kontakte")
                        .font(.caption)
                        .foregroundColor(AppColors.midGray)
                }
                
                VStack(alignment: .leading) {
                    Text("\(company.deals)")
                        .font(.title3)
                        .fontWeight(.bold)
                    Text("Deals")
                        .font(.caption)
                        .foregroundColor(AppColors.midGray)
                }
                
                VStack(alignment: .leading) {
                    Text("€\(company.totalValue / 1000)K")
                        .font(.title3)
                        .fontWeight(.bold)
                        .foregroundColor(AppColors.green)
                    Text("Wert")
                        .font(.caption)
                        .foregroundColor(AppColors.midGray)
                }
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .foregroundColor(AppColors.midGray)
            }
        }
        .padding()
        .background(Color.white)
        .cornerRadius(16)
    }
    
    func statusColor(_ status: CompanyStatus) -> Color {
        switch status {
        case .customer: return AppColors.green
        case .prospect: return AppColors.orange
        case .partner: return AppColors.blue
        case .inactive: return AppColors.midGray
        }
    }
}

struct CompanyDetailView: View {
    let company: Company
    
    var body: some View {
        List {
            Section {
                HStack {
                    Spacer()
                    VStack(spacing: 12) {
                        Image(systemName: "building.2.fill")
                            .font(.largeTitle)
                            .foregroundColor(AppColors.blue)
                            .frame(width: 80, height: 80)
                            .background(AppColors.blue.opacity(0.15))
                            .cornerRadius(20)
                        
                        Text(company.name)
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text(company.industry)
                            .foregroundColor(AppColors.midGray)
                    }
                    Spacer()
                }
                .listRowBackground(Color.clear)
            }
            
            Section("Details") {
                LabeledContent("Branche", value: company.industry)
                LabeledContent("Größe", value: company.size)
                LabeledContent("Stadt", value: company.city)
                LabeledContent("Website", value: company.website)
            }
            
            Section("Statistiken") {
                LabeledContent("Kontakte", value: "\(company.contacts)")
                LabeledContent("Deals", value: "\(company.deals)")
                LabeledContent("Gesamtwert", value: "€\(company.totalValue.formatted())")
            }
            
            Section("Betreuer") {
                LabeledContent("Zuständig", value: company.owner)
            }
        }
        .navigationTitle("Firma")
        .navigationBarTitleDisplayMode(.inline)
    }
}

#Preview {
    CompaniesListView()
        .environmentObject(DataManager())
}
