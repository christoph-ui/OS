'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { colors } from '@/lib/theme';
import {
  Plus, Search, Filter, MoreVertical, Mail, Phone, Building2,
  ChevronLeft, ChevronRight, Download, Upload
} from 'lucide-react';

interface Contact {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  company: string;
  position: string;
  tags: string[];
  lastContact: string;
  owner: string;
}

export default function ContactsPage() {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);
  const [showNewModal, setShowNewModal] = useState(false);

  const contacts: Contact[] = [
    { id: '1', firstName: 'Thomas', lastName: 'Müller', email: 'mueller@muellerundsoehne.de', phone: '+49 711 123456', company: 'Müller & Söhne GmbH', position: 'Geschäftsführer', tags: ['Bestandskunde', 'VIP'], lastContact: '2026-01-28', owner: 'Max Kaufmann' },
    { id: '2', firstName: 'Anna', lastName: 'Schmidt', email: 'a.schmidt@schmidt-ag.de', phone: '+49 89 987654', company: 'Schmidt AG', position: 'IT-Leiterin', tags: ['Neukunde'], lastContact: '2026-01-29', owner: 'Sarah Meyer' },
    { id: '3', firstName: 'Klaus', lastName: 'Bauer', email: 'k.bauer@bauer-kg.de', phone: '+49 30 456789', company: 'Bauer KG', position: 'Einkauf', tags: ['Lead'], lastContact: '2026-01-25', owner: 'Max Kaufmann' },
    { id: '4', firstName: 'Lisa', lastName: 'Weber', email: 'weber@webertechnik.de', phone: '+49 40 321654', company: 'Weber Technik', position: 'CEO', tags: ['Bestandskunde'], lastContact: '2026-01-30', owner: 'Tim Hoffmann' },
    { id: '5', firstName: 'Peter', lastName: 'Fischer', email: 'p.fischer@fischer-gmbh.de', phone: '+49 221 654321', company: 'Fischer GmbH', position: 'Vertriebsleiter', tags: ['Lead', 'Warm'], lastContact: '2026-01-27', owner: 'Julia Klein' },
    { id: '6', firstName: 'Maria', lastName: 'Hoffmann', email: 'm.hoffmann@hoffmann-industrie.de', phone: '+49 69 111222', company: 'Hoffmann Industrie', position: 'Prokuristin', tags: ['Neukunde'], lastContact: '2026-01-29', owner: 'Sarah Meyer' },
    { id: '7', firstName: 'Stefan', lastName: 'Klein', email: 's.klein@klein-solutions.de', phone: '+49 511 333444', company: 'Klein Solutions', position: 'Inhaber', tags: ['Bestandskunde', 'VIP'], lastContact: '2026-01-26', owner: 'Max Kaufmann' },
    { id: '8', firstName: 'Andrea', lastName: 'Wagner', email: 'a.wagner@wagner-tech.de', phone: '+49 351 555666', company: 'Wagner Tech', position: 'CTO', tags: ['Lead'], lastContact: '2026-01-24', owner: 'Tim Hoffmann' },
  ];

  const filteredContacts = contacts.filter(c => 
    `${c.firstName} ${c.lastName} ${c.company} ${c.email}`.toLowerCase().includes(search.toLowerCase())
  );

  const toggleSelect = (id: string) => {
    setSelectedContacts(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedContacts.length === filteredContacts.length) {
      setSelectedContacts([]);
    } else {
      setSelectedContacts(filteredContacts.map(c => c.id));
    }
  };

  const getTagColor = (tag: string) => {
    switch (tag) {
      case 'VIP': return colors.orange;
      case 'Bestandskunde': return colors.green;
      case 'Neukunde': return colors.blue;
      case 'Lead': return colors.midGray;
      case 'Warm': return colors.orange;
      default: return colors.midGray;
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 24,
      }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 600, color: colors.dark, margin: '0 0 4px' }}>
            Kontakte
          </h1>
          <p style={{ fontSize: 14, color: colors.midGray, margin: 0 }}>
            {contacts.length} Kontakte insgesamt
          </p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button style={{
            padding: '10px 16px',
            backgroundColor: 'white',
            border: `1px solid ${colors.lightGray}`,
            borderRadius: 8,
            fontSize: 14,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            color: colors.dark,
          }}>
            <Upload size={18} />
            Import
          </button>
          <button
            onClick={() => setShowNewModal(true)}
            style={{
              padding: '10px 20px',
              backgroundColor: colors.orange,
              color: 'white',
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <Plus size={18} />
            Neuer Kontakt
          </button>
        </div>
      </div>

      {/* Filters */}
      <div style={{
        display: 'flex',
        gap: 12,
        marginBottom: 20,
      }}>
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '10px 16px',
          backgroundColor: 'white',
          border: `1px solid ${colors.lightGray}`,
          borderRadius: 8,
        }}>
          <Search size={18} color={colors.midGray} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Suche nach Name, Firma, E-Mail..."
            style={{
              flex: 1,
              border: 'none',
              fontSize: 14,
              outline: 'none',
            }}
          />
        </div>
        <button style={{
          padding: '10px 16px',
          backgroundColor: 'white',
          border: `1px solid ${colors.lightGray}`,
          borderRadius: 8,
          fontSize: 14,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          color: colors.dark,
        }}>
          <Filter size={18} />
          Filter
        </button>
      </div>

      {/* Selection Actions */}
      {selectedContacts.length > 0 && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          padding: '12px 20px',
          backgroundColor: colors.orange + '10',
          borderRadius: 8,
          marginBottom: 16,
        }}>
          <span style={{ fontSize: 14, fontWeight: 500, color: colors.orange }}>
            {selectedContacts.length} ausgewählt
          </span>
          <button style={actionBtnStyle}>E-Mail senden</button>
          <button style={actionBtnStyle}>Tags hinzufügen</button>
          <button style={actionBtnStyle}>Zuweisen</button>
          <button style={{ ...actionBtnStyle, color: colors.red }}>Löschen</button>
        </div>
      )}

      {/* Table */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 12,
        border: `1px solid ${colors.lightGray}`,
        overflow: 'hidden',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: colors.light }}>
              <th style={{ ...thStyle, width: 40 }}>
                <input
                  type="checkbox"
                  checked={selectedContacts.length === filteredContacts.length && filteredContacts.length > 0}
                  onChange={toggleSelectAll}
                />
              </th>
              <th style={thStyle}>Name</th>
              <th style={thStyle}>Firma</th>
              <th style={thStyle}>Kontakt</th>
              <th style={thStyle}>Tags</th>
              <th style={thStyle}>Letzter Kontakt</th>
              <th style={thStyle}>Betreuer</th>
              <th style={{ ...thStyle, width: 50 }}></th>
            </tr>
          </thead>
          <tbody>
            {filteredContacts.map((contact) => (
              <tr
                key={contact.id}
                onClick={() => router.push(`/crm/contacts/${contact.id}`)}
                style={{
                  borderBottom: `1px solid ${colors.lightGray}`,
                  cursor: 'pointer',
                  backgroundColor: selectedContacts.includes(contact.id) ? colors.orange + '05' : 'white',
                }}
              >
                <td style={tdStyle} onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={selectedContacts.includes(contact.id)}
                    onChange={() => toggleSelect(contact.id)}
                  />
                </td>
                <td style={tdStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: 36,
                      height: 36,
                      borderRadius: '50%',
                      backgroundColor: colors.blue + '20',
                      color: colors.blue,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 13,
                      fontWeight: 600,
                    }}>
                      {contact.firstName[0]}{contact.lastName[0]}
                    </div>
                    <div>
                      <div style={{ fontWeight: 500, color: colors.dark }}>
                        {contact.firstName} {contact.lastName}
                      </div>
                      <div style={{ fontSize: 12, color: colors.midGray }}>
                        {contact.position}
                      </div>
                    </div>
                  </div>
                </td>
                <td style={tdStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Building2 size={14} color={colors.midGray} />
                    {contact.company}
                  </div>
                </td>
                <td style={tdStyle}>
                  <div style={{ fontSize: 13 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                      <Mail size={12} color={colors.midGray} />
                      {contact.email}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: colors.midGray }}>
                      <Phone size={12} />
                      {contact.phone}
                    </div>
                  </div>
                </td>
                <td style={tdStyle}>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    {contact.tags.map(tag => (
                      <span
                        key={tag}
                        style={{
                          fontSize: 11,
                          padding: '3px 8px',
                          borderRadius: 4,
                          backgroundColor: getTagColor(tag) + '15',
                          color: getTagColor(tag),
                          fontWeight: 500,
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </td>
                <td style={tdStyle}>
                  <span style={{ fontSize: 13, color: colors.midGray }}>
                    {new Date(contact.lastContact).toLocaleDateString('de-DE')}
                  </span>
                </td>
                <td style={tdStyle}>
                  <span style={{ fontSize: 13 }}>{contact.owner}</span>
                </td>
                <td style={tdStyle} onClick={(e) => e.stopPropagation()}>
                  <button style={{
                    backgroundColor: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    padding: 4,
                  }}>
                    <MoreVertical size={18} color={colors.midGray} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination */}
        <div style={{
          padding: '12px 20px',
          borderTop: `1px solid ${colors.lightGray}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span style={{ fontSize: 13, color: colors.midGray }}>
            Zeige 1-{filteredContacts.length} von {contacts.length}
          </span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button style={paginationBtn}><ChevronLeft size={18} /></button>
            <button style={{ ...paginationBtn, backgroundColor: colors.orange, color: 'white' }}>1</button>
            <button style={paginationBtn}>2</button>
            <button style={paginationBtn}>3</button>
            <button style={paginationBtn}><ChevronRight size={18} /></button>
          </div>
        </div>
      </div>

      {/* New Contact Modal */}
      {showNewModal && (
        <NewContactModal onClose={() => setShowNewModal(false)} />
      )}
    </div>
  );
}

function NewContactModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    company: '',
    position: '',
  });

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: 16,
        width: 500,
        maxHeight: '90vh',
        overflow: 'auto',
      }}>
        <div style={{
          padding: '20px 24px',
          borderBottom: `1px solid ${colors.lightGray}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>Neuer Kontakt</h2>
          <button onClick={onClose} style={{
            backgroundColor: 'transparent',
            border: 'none',
            fontSize: 20,
            cursor: 'pointer',
            color: colors.midGray,
          }}>×</button>
        </div>

        <div style={{ padding: 24 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div>
              <label style={labelStyle}>Vorname *</label>
              <input
                type="text"
                value={form.firstName}
                onChange={(e) => setForm({ ...form, firstName: e.target.value })}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Nachname *</label>
              <input
                type="text"
                value={form.lastName}
                onChange={(e) => setForm({ ...form, lastName: e.target.value })}
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>E-Mail *</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Telefon</label>
            <input
              type="tel"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Firma</label>
            <input
              type="text"
              value={form.company}
              onChange={(e) => setForm({ ...form, company: e.target.value })}
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={labelStyle}>Position</label>
            <input
              type="text"
              value={form.position}
              onChange={(e) => setForm({ ...form, position: e.target.value })}
              style={inputStyle}
            />
          </div>

          <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
            <button onClick={onClose} style={{
              padding: '12px 24px',
              backgroundColor: 'white',
              border: `1px solid ${colors.lightGray}`,
              borderRadius: 8,
              fontSize: 14,
              cursor: 'pointer',
            }}>
              Abbrechen
            </button>
            <button style={{
              padding: '12px 24px',
              backgroundColor: colors.orange,
              color: 'white',
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
            }}>
              Speichern
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  padding: '12px 16px',
  textAlign: 'left',
  fontSize: 13,
  fontWeight: 500,
  color: colors.midGray,
};

const tdStyle: React.CSSProperties = {
  padding: '12px 16px',
  fontSize: 14,
  color: colors.dark,
};

const actionBtnStyle: React.CSSProperties = {
  padding: '6px 12px',
  backgroundColor: 'white',
  border: `1px solid ${colors.lightGray}`,
  borderRadius: 6,
  fontSize: 13,
  cursor: 'pointer',
  color: colors.dark,
};

const paginationBtn: React.CSSProperties = {
  width: 32,
  height: 32,
  backgroundColor: 'white',
  border: `1px solid ${colors.lightGray}`,
  borderRadius: 6,
  fontSize: 13,
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: colors.dark,
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 14,
  fontWeight: 500,
  color: colors.dark,
  marginBottom: 6,
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px 14px',
  border: `1px solid ${colors.lightGray}`,
  borderRadius: 8,
  fontSize: 14,
  outline: 'none',
};
