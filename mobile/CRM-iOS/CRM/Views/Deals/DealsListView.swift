import SwiftUI

struct DealsListView: View {
    @EnvironmentObject var dataManager: DataManager
    @State private var viewMode: ViewMode = .kanban
    @State private var showingNewDeal = false
    
    enum ViewMode: String, CaseIterable {
        case kanban = "Kanban"
        case list = "Liste"
    }
    
    var pipelineValue: Int {
        dataManager.deals
            .filter { $0.stage != .won && $0.stage != .lost }
            .reduce(0) { $0 + $1.value }
    }
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Pipeline Summary
                HStack {
                    VStack(alignment: .leading) {
                        Text("Pipeline")
                            .font(.caption)
                            .foregroundColor(AppColors.midGray)
                        Text("€\(pipelineValue / 1000)K")
                            .font(.title2)
                            .fontWeight(.bold)
                    }
                    
                    Spacer()
                    
                    Picker("Ansicht", selection: $viewMode) {
                        ForEach(ViewMode.allCases, id: \.self) { mode in
                            Text(mode.rawValue).tag(mode)
                        }
                    }
                    .pickerStyle(.segmented)
                    .frame(width: 160)
                }
                .padding()
                .background(Color.white)
                
                if viewMode == .kanban {
                    KanbanView()
                } else {
                    DealsListContent()
                }
            }
            .background(AppColors.light)
            .navigationTitle("Deals")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: { showingNewDeal = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingNewDeal) {
                NewDealView()
            }
        }
    }
}

// MARK: - Kanban View
struct KanbanView: View {
    @EnvironmentObject var dataManager: DataManager
    
    let stages: [DealStage] = [.lead, .qualified, .proposal, .negotiation, .won]
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(alignment: .top, spacing: 12) {
                ForEach(stages, id: \.self) { stage in
                    KanbanColumn(stage: stage, deals: dataManager.deals.filter { $0.stage == stage })
                }
            }
            .padding()
        }
    }
}

struct KanbanColumn: View {
    let stage: DealStage
    let deals: [Deal]
    
    var totalValue: Int {
        deals.reduce(0) { $0 + $1.value }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                Circle()
                    .fill(Color(hex: stage.color))
                    .frame(width: 10, height: 10)
                
                Text(stage.rawValue)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                
                Text("\(deals.count)")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(Color.white)
                    .cornerRadius(10)
                
                Spacer()
                
                Text("€\(totalValue / 1000)K")
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(Color(hex: stage.color))
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            
            // Cards
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(deals) { deal in
                        DealCard(deal: deal)
                    }
                }
            }
        }
        .frame(width: 280)
        .background(AppColors.light)
        .cornerRadius(12)
    }
}

struct DealCard: View {
    let deal: Deal
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(deal.name)
                .font(.subheadline)
                .fontWeight(.medium)
                .lineLimit(2)
            
            HStack(spacing: 4) {
                Image(systemName: "building.2")
                    .font(.caption2)
                Text(deal.company)
                    .font(.caption)
            }
            .foregroundColor(AppColors.midGray)
            
            HStack {
                Text("€\(deal.value.formatted())")
                    .font(.headline)
                    .fontWeight(.bold)
                
                Spacer()
                
                Text("\(deal.probability)%")
                    .font(.caption)
                    .fontWeight(.medium)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(hex: deal.stage.color).opacity(0.15))
                    .foregroundColor(Color(hex: deal.stage.color))
                    .cornerRadius(6)
            }
            
            Divider()
            
            HStack {
                Image(systemName: "calendar")
                    .font(.caption2)
                Text(deal.expectedClose, style: .date)
                    .font(.caption)
                
                Spacer()
                
                Text(deal.owner.split(separator: " ").map { String($0.prefix(1)) }.joined())
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(AppColors.blue)
                    .frame(width: 24, height: 24)
                    .background(AppColors.blue.opacity(0.2))
                    .clipShape(Circle())
            }
            .foregroundColor(AppColors.midGray)
        }
        .padding()
        .background(Color.white)
        .cornerRadius(10)
        .shadow(color: .black.opacity(0.05), radius: 2, y: 1)
        .padding(.horizontal, 12)
    }
}

// MARK: - List View
struct DealsListContent: View {
    @EnvironmentObject var dataManager: DataManager
    
    var body: some View {
        List {
            ForEach(dataManager.deals) { deal in
                NavigationLink(destination: DealDetailView(deal: deal)) {
                    DealListRow(deal: deal)
                }
            }
        }
        .listStyle(.plain)
    }
}

struct DealListRow: View {
    let deal: Deal
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(deal.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text(deal.company)
                    .font(.caption)
                    .foregroundColor(AppColors.midGray)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text("€\(deal.value.formatted())")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                
                Text(deal.stage.rawValue)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(Color(hex: deal.stage.color).opacity(0.15))
                    .foregroundColor(Color(hex: deal.stage.color))
                    .cornerRadius(4)
            }
        }
        .padding(.vertical, 4)
    }
}

struct DealDetailView: View {
    let deal: Deal
    
    var body: some View {
        List {
            Section {
                HStack {
                    Spacer()
                    VStack(spacing: 8) {
                        Text("€\(deal.value.formatted())")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        Text(deal.stage.rawValue)
                            .font(.headline)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(Color(hex: deal.stage.color).opacity(0.15))
                            .foregroundColor(Color(hex: deal.stage.color))
                            .cornerRadius(8)
                    }
                    Spacer()
                }
                .listRowBackground(Color.clear)
            }
            
            Section("Details") {
                LabeledContent("Deal", value: deal.name)
                LabeledContent("Wahrscheinlichkeit", value: "\(deal.probability)%")
                LabeledContent("Erwarteter Abschluss", value: deal.expectedClose.formatted(date: .abbreviated, time: .omitted))
            }
            
            Section("Kontakt") {
                LabeledContent("Ansprechpartner", value: deal.contact)
                LabeledContent("Firma", value: deal.company)
            }
            
            Section("Zuweisung") {
                LabeledContent("Betreuer", value: deal.owner)
            }
        }
        .navigationTitle("Deal")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct NewDealView: View {
    @Environment(\.dismiss) var dismiss
    @State private var name = ""
    @State private var value = ""
    @State private var company = ""
    @State private var contact = ""
    @State private var stage: DealStage = .lead
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Deal") {
                    TextField("Name", text: $name)
                    TextField("Wert (€)", text: $value)
                        .keyboardType(.numberPad)
                }
                
                Section("Kontakt") {
                    TextField("Firma", text: $company)
                    TextField("Ansprechpartner", text: $contact)
                }
                
                Section("Status") {
                    Picker("Phase", selection: $stage) {
                        ForEach(DealStage.allCases, id: \.self) { stage in
                            Text(stage.rawValue).tag(stage)
                        }
                    }
                }
            }
            .navigationTitle("Neuer Deal")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Abbrechen") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Erstellen") { dismiss() }
                        .disabled(name.isEmpty)
                }
            }
        }
    }
}

#Preview {
    DealsListView()
        .environmentObject(DataManager())
}
