import SwiftUI

struct ContactsListView: View {
    @EnvironmentObject var dataManager: DataManager
    @State private var searchText = ""
    @State private var showingNewContact = false
    
    var filteredContacts: [Contact] {
        if searchText.isEmpty {
            return dataManager.contacts
        }
        return dataManager.contacts.filter {
            $0.fullName.localizedCaseInsensitiveContains(searchText) ||
            $0.company.localizedCaseInsensitiveContains(searchText) ||
            $0.email.localizedCaseInsensitiveContains(searchText)
        }
    }
    
    var body: some View {
        NavigationStack {
            List {
                ForEach(filteredContacts) { contact in
                    NavigationLink(destination: ContactDetailView(contact: contact)) {
                        ContactRow(contact: contact)
                    }
                }
            }
            .listStyle(.plain)
            .searchable(text: $searchText, prompt: "Suche nach Name, Firma...")
            .navigationTitle("Kontakte")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: { showingNewContact = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingNewContact) {
                NewContactView()
            }
        }
    }
}

struct ContactRow: View {
    let contact: Contact
    
    var body: some View {
        HStack(spacing: 12) {
            Text(contact.initials)
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(AppColors.blue)
                .frame(width: 40, height: 40)
                .background(AppColors.blue.opacity(0.2))
                .clipShape(Circle())
            
            VStack(alignment: .leading, spacing: 4) {
                Text(contact.fullName)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                HStack(spacing: 4) {
                    Image(systemName: "building.2")
                        .font(.caption2)
                    Text(contact.company)
                        .font(.caption)
                }
                .foregroundColor(AppColors.midGray)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text(contact.position)
                    .font(.caption)
                    .foregroundColor(AppColors.midGray)
                
                HStack(spacing: 4) {
                    ForEach(contact.tags.prefix(2), id: \.self) { tag in
                        Text(tag)
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(tagColor(for: tag).opacity(0.15))
                            .foregroundColor(tagColor(for: tag))
                            .cornerRadius(4)
                    }
                }
            }
        }
        .padding(.vertical, 4)
    }
    
    func tagColor(for tag: String) -> Color {
        switch tag {
        case "VIP": return AppColors.orange
        case "Bestandskunde": return AppColors.green
        case "Neukunde": return AppColors.blue
        case "Lead": return AppColors.midGray
        case "Warm": return AppColors.orange
        default: return AppColors.midGray
        }
    }
}

struct ContactDetailView: View {
    let contact: Contact
    
    var body: some View {
        List {
            Section {
                HStack {
                    Spacer()
                    VStack(spacing: 12) {
                        Text(contact.initials)
                            .font(.title)
                            .fontWeight(.bold)
                            .foregroundColor(AppColors.blue)
                            .frame(width: 80, height: 80)
                            .background(AppColors.blue.opacity(0.2))
                            .clipShape(Circle())
                        
                        Text(contact.fullName)
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text(contact.position)
                            .foregroundColor(AppColors.midGray)
                    }
                    Spacer()
                }
                .listRowBackground(Color.clear)
            }
            
            Section("Kontakt") {
                LabeledContent("E-Mail", value: contact.email)
                LabeledContent("Telefon", value: contact.phone)
            }
            
            Section("Firma") {
                LabeledContent("Firma", value: contact.company)
                LabeledContent("Betreuer", value: contact.owner)
            }
            
            Section("Tags") {
                HStack {
                    ForEach(contact.tags, id: \.self) { tag in
                        Text(tag)
                            .font(.subheadline)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(AppColors.orange.opacity(0.15))
                            .foregroundColor(AppColors.orange)
                            .cornerRadius(8)
                    }
                }
            }
            
            Section {
                Button(action: {}) {
                    Label("Anrufen", systemImage: "phone.fill")
                }
                Button(action: {}) {
                    Label("E-Mail senden", systemImage: "envelope.fill")
                }
            }
        }
        .navigationTitle("Kontakt")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct NewContactView: View {
    @Environment(\.dismiss) var dismiss
    @State private var firstName = ""
    @State private var lastName = ""
    @State private var email = ""
    @State private var phone = ""
    @State private var company = ""
    @State private var position = ""
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Name") {
                    TextField("Vorname", text: $firstName)
                    TextField("Nachname", text: $lastName)
                }
                
                Section("Kontakt") {
                    TextField("E-Mail", text: $email)
                        .keyboardType(.emailAddress)
                    TextField("Telefon", text: $phone)
                        .keyboardType(.phonePad)
                }
                
                Section("Firma") {
                    TextField("Firma", text: $company)
                    TextField("Position", text: $position)
                }
            }
            .navigationTitle("Neuer Kontakt")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Abbrechen") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Speichern") { dismiss() }
                        .disabled(firstName.isEmpty || lastName.isEmpty)
                }
            }
        }
    }
}

#Preview {
    ContactsListView()
        .environmentObject(DataManager())
}
