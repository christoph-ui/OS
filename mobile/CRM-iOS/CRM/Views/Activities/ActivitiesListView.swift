import SwiftUI

struct ActivitiesListView: View {
    @EnvironmentObject var dataManager: DataManager
    @State private var filter: ActivityFilter = .today
    @State private var showingNewActivity = false
    
    enum ActivityFilter: String, CaseIterable {
        case today = "Heute"
        case upcoming = "Kommend"
        case overdue = "Überfällig"
        case completed = "Erledigt"
    }
    
    var filteredActivities: [Activity] {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())
        
        switch filter {
        case .today:
            return dataManager.activities.filter { 
                calendar.isDateInToday($0.dueDate) && !$0.completed 
            }
        case .upcoming:
            return dataManager.activities.filter { 
                $0.dueDate > today && !$0.completed 
            }
        case .overdue:
            return dataManager.activities.filter { 
                $0.dueDate < today && !$0.completed 
            }
        case .completed:
            return dataManager.activities.filter { $0.completed }
        }
    }
    
    var stats: [ActivityFilter: Int] {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())
        
        return [
            .today: dataManager.activities.filter { calendar.isDateInToday($0.dueDate) && !$0.completed }.count,
            .upcoming: dataManager.activities.filter { $0.dueDate > today && !$0.completed }.count,
            .overdue: dataManager.activities.filter { $0.dueDate < today && !$0.completed }.count,
            .completed: dataManager.activities.filter { $0.completed }.count
        ]
    }
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Stats Bar
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        ForEach(ActivityFilter.allCases, id: \.self) { filterOption in
                            FilterButton(
                                title: filterOption.rawValue,
                                count: stats[filterOption] ?? 0,
                                isSelected: filter == filterOption,
                                color: colorForFilter(filterOption)
                            ) {
                                filter = filterOption
                            }
                        }
                    }
                    .padding()
                }
                .background(Color.white)
                
                // Activities List
                List {
                    ForEach(filteredActivities) { activity in
                        ActivityListRow(activity: activity) {
                            dataManager.toggleActivityComplete(activity)
                        }
                    }
                }
                .listStyle(.plain)
            }
            .background(AppColors.light)
            .navigationTitle("Aktivitäten")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: { showingNewActivity = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingNewActivity) {
                NewActivityView()
            }
        }
    }
    
    func colorForFilter(_ filter: ActivityFilter) -> Color {
        switch filter {
        case .today: return AppColors.orange
        case .upcoming: return AppColors.blue
        case .overdue: return AppColors.red
        case .completed: return AppColors.green
        }
    }
}

struct FilterButton: View {
    let title: String
    let count: Int
    let isSelected: Bool
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Text("\(count)")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(color)
                Text(title)
                    .font(.caption)
                    .foregroundColor(isSelected ? color : AppColors.midGray)
            }
            .frame(width: 80)
            .padding(.vertical, 12)
            .background(isSelected ? color.opacity(0.1) : Color.clear)
            .cornerRadius(10)
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(isSelected ? color : AppColors.lightGray, lineWidth: 1)
            )
        }
    }
}

struct ActivityListRow: View {
    let activity: Activity
    let onToggle: () -> Void
    
    var body: some View {
        HStack(spacing: 12) {
            // Checkbox
            Button(action: onToggle) {
                Image(systemName: activity.completed ? "checkmark.circle.fill" : "circle")
                    .font(.title3)
                    .foregroundColor(activity.completed ? AppColors.green : AppColors.lightGray)
            }
            .buttonStyle(.plain)
            
            // Icon
            Image(systemName: activity.type.icon)
                .font(.subheadline)
                .foregroundColor(AppColors.blue)
                .frame(width: 32, height: 32)
                .background(AppColors.blue.opacity(0.15))
                .cornerRadius(8)
            
            // Content
            VStack(alignment: .leading, spacing: 4) {
                Text(activity.title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .strikethrough(activity.completed)
                    .foregroundColor(activity.completed ? AppColors.midGray : AppColors.dark)
                
                HStack(spacing: 8) {
                    Label(activity.contact, systemImage: "person")
                    Label(activity.company, systemImage: "building.2")
                }
                .font(.caption)
                .foregroundColor(AppColors.midGray)
            }
            
            Spacer()
            
            // Time & Priority
            VStack(alignment: .trailing, spacing: 4) {
                if let time = activity.dueTime {
                    Text(time)
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(AppColors.midGray)
                }
                
                Circle()
                    .fill(priorityColor(activity.priority))
                    .frame(width: 8, height: 8)
            }
        }
        .padding(.vertical, 4)
        .opacity(activity.completed ? 0.6 : 1)
    }
    
    func priorityColor(_ priority: Priority) -> Color {
        switch priority {
        case .high: return AppColors.red
        case .medium: return AppColors.orange
        case .low: return AppColors.midGray
        }
    }
}

struct NewActivityView: View {
    @Environment(\.dismiss) var dismiss
    @State private var type: ActivityType = .call
    @State private var title = ""
    @State private var description = ""
    @State private var contact = ""
    @State private var company = ""
    @State private var dueDate = Date()
    @State private var priority: Priority = .medium
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Typ") {
                    Picker("Typ", selection: $type) {
                        ForEach(ActivityType.allCases, id: \.self) { activityType in
                            Label(activityType.rawValue, systemImage: activityType.icon)
                                .tag(activityType)
                        }
                    }
                    .pickerStyle(.segmented)
                }
                
                Section("Details") {
                    TextField("Titel", text: $title)
                    TextField("Beschreibung", text: $description, axis: .vertical)
                        .lineLimit(3...6)
                }
                
                Section("Kontakt") {
                    TextField("Kontakt", text: $contact)
                    TextField("Firma", text: $company)
                }
                
                Section("Termin") {
                    DatePicker("Datum & Zeit", selection: $dueDate)
                    Picker("Priorität", selection: $priority) {
                        ForEach(Priority.allCases, id: \.self) { p in
                            Text(p.rawValue).tag(p)
                        }
                    }
                }
            }
            .navigationTitle("Neue Aktivität")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Abbrechen") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Erstellen") { dismiss() }
                        .disabled(title.isEmpty)
                }
            }
        }
    }
}

#Preview {
    ActivitiesListView()
        .environmentObject(DataManager())
}
