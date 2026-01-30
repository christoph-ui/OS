'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { colors } from '@/lib/theme';
import {
  Plus, Search, Filter, Building2, MapPin, Globe, Users,
  Euro, MoreVertical, ChevronRight
} from 'lucide-react';

interface Company {
  id: string;
  name: string;
  industry: string;
  size: string;
  website: string;
  city: string;
  country: string;
  contacts: number;
  deals: number;
  totalValue: number;
  owner: string;
  status: 'customer' | 'prospect' | 'partner' | 'inactive';
}

export default function CompaniesPage() {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [showNewModal, setShowNewModal] = useState(false);

  const companies: Company[] = [
    { id: '1', name: 'Müller & Söhne GmbH', industry: 'Maschinenbau', size: '50-200', website: 'muellerundsoehne.de', city: 'Stuttgart', country: 'Deutschland', contacts: 4, deals: 2, totalValue: 78000, owner: 'Max Kaufmann', status: 'customer' },
    { id: '2', name: 'Schmidt AG', industry: 'IT-Services', size: '200-500', website: 'schmidt-ag.de', city: 'München', country: 'Deutschland', contacts: 6, deals: 3, totalValue: 185000, owner: 'Sarah Meyer', status: 'customer' },
    { id: '3', name: 'Bauer KG', industry: 'Handel', size: '10-50', website: 'bauer-kg.de', city: 'Berlin', country: 'Deutschland', contacts: 2, deals: 1, totalValue: 24000, owner: 'Max Kaufmann', status: 'prospect' },
    { id: '4', name: 'Weber Technik', industry: 'Elektrotechnik', size: '50-200', website: 'webertechnik.de', city: 'Hamburg', country: 'Deutschland', contacts: 3, deals: 1, totalValue: 67000, owner: 'Tim Hoffmann', status: 'customer' },
    { id: '5', name: 'Fischer GmbH', industry: 'Logistik', size: '200-500', website: 'fischer-gmbh.de', city: 'Köln', country: 'Deutschland', contacts: 5, deals: 2, totalValue: 52000, owner: 'Julia Klein', status: 'prospect' },
    { id: '6', name: 'Hoffmann Industrie', industry: 'Fertigung', size: '500+', website: 'hoffmann-industrie.de', city: 'Frankfurt', country: 'Deutschland', contacts: 8, deals: 4, totalValue: 320000, owner: 'Sarah Meyer', status: 'customer' },
    { id: '7', name: 'Klein Solutions', industry: 'Software', size: '10-50', website: 'klein-solutions.de', city: 'Hannover', country: 'Deutschland', contacts: 2, deals: 1, totalValue: 18000, owner: 'Max Kaufmann', status: 'customer' },
    { id: '8', name: 'Wagner Tech', industry: 'Telekommunikation', size: '50-200', website: 'wagner-tech.de', city: 'Dresden', country: 'Deutschland', contacts: 3, deals: 2, totalValue: 84000, owner: 'Tim Hoffmann', status: 'customer' },
  ];

  const filteredCompanies = companies.filter(c =>
    `${c.name} ${c.industry} ${c.city}`.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'customer': return colors.green;
      case 'prospect': return colors.orange;
      case 'partner': return colors.blue;
      case 'inactive': return colors.midGray;
      default: return colors.midGray;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'customer': return 'Kunde';
      case 'prospect': return 'Interessent';
      case 'partner': return 'Partner';
      case 'inactive': return 'Inaktiv';
      default: return status;
    }
  };

  const stats = {
    total: companies.length,
    customers: companies.filter(c => c.status === 'customer').length,
    prospects: companies.filter(c => c.status === 'prospect').length,
    totalValue: companies.reduce((sum, c) => sum + c.totalValue, 0),
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
            Firmen
          </h1>
          <p style={{ fontSize: 14, color: colors.midGray, margin: 0 }}>
            {stats.total} Firmen · {stats.customers} Kunden · €{(stats.totalValue / 1000).toFixed(0)}K Gesamtwert
          </p>
        </div>
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
          Neue Firma
        </button>
      </div>

      {/* Stats Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 16,
        marginBottom: 24,
      }}>
        {[
          { label: 'Gesamt', value: stats.total, icon: Building2, color: colors.dark },
          { label: 'Kunden', value: stats.customers, icon: Users, color: colors.green },
          { label: 'Interessenten', value: stats.prospects, icon: Users, color: colors.orange },
          { label: 'Gesamtwert', value: `€${(stats.totalValue / 1000).toFixed(0)}K`, icon: Euro, color: colors.blue },
        ].map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div key={i} style={{
              backgroundColor: 'white',
              borderRadius: 12,
              border: `1px solid ${colors.lightGray}`,
              padding: 20,
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}>
              <div style={{
                width: 44,
                height: 44,
                borderRadius: 10,
                backgroundColor: stat.color + '15',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: stat.color,
              }}>
                <Icon size={22} />
              </div>
              <div>
                <div style={{ fontSize: 22, fontWeight: 700, color: colors.dark }}>{stat.value}</div>
                <div style={{ fontSize: 13, color: colors.midGray }}>{stat.label}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Search */}
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
            placeholder="Suche nach Firma, Branche, Stadt..."
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

      {/* Companies Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: 16,
      }}>
        {filteredCompanies.map((company) => (
          <div
            key={company.id}
            onClick={() => router.push(`/crm/companies/${company.id}`)}
            style={{
              backgroundColor: 'white',
              borderRadius: 12,
              border: `1px solid ${colors.lightGray}`,
              padding: 20,
              cursor: 'pointer',
              transition: 'box-shadow 0.2s',
            }}
          >
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: 16,
            }}>
              <div style={{ display: 'flex', gap: 14 }}>
                <div style={{
                  width: 48,
                  height: 48,
                  borderRadius: 10,
                  backgroundColor: colors.blue + '15',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: colors.blue,
                }}>
                  <Building2 size={24} />
                </div>
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 600, color: colors.dark, margin: '0 0 4px' }}>
                    {company.name}
                  </h3>
                  <div style={{ fontSize: 13, color: colors.midGray }}>
                    {company.industry} · {company.size} Mitarbeiter
                  </div>
                </div>
              </div>
              <span style={{
                fontSize: 11,
                fontWeight: 500,
                padding: '4px 10px',
                borderRadius: 6,
                backgroundColor: getStatusColor(company.status) + '15',
                color: getStatusColor(company.status),
              }}>
                {getStatusLabel(company.status)}
              </span>
            </div>

            <div style={{
              display: 'flex',
              gap: 20,
              marginBottom: 16,
              fontSize: 13,
              color: colors.midGray,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <MapPin size={14} />
                {company.city}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Globe size={14} />
                {company.website}
              </div>
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              paddingTop: 16,
              borderTop: `1px solid ${colors.lightGray}`,
            }}>
              <div style={{ display: 'flex', gap: 20 }}>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: colors.dark }}>
                    {company.contacts}
                  </div>
                  <div style={{ fontSize: 12, color: colors.midGray }}>Kontakte</div>
                </div>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: colors.dark }}>
                    {company.deals}
                  </div>
                  <div style={{ fontSize: 12, color: colors.midGray }}>Deals</div>
                </div>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: colors.green }}>
                    €{(company.totalValue / 1000).toFixed(0)}K
                  </div>
                  <div style={{ fontSize: 12, color: colors.midGray }}>Wert</div>
                </div>
              </div>
              <ChevronRight size={20} color={colors.midGray} />
            </div>
          </div>
        ))}
      </div>

      {/* New Company Modal */}
      {showNewModal && (
        <NewCompanyModal onClose={() => setShowNewModal(false)} />
      )}
    </div>
  );
}

function NewCompanyModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({
    name: '',
    industry: '',
    size: '',
    website: '',
    city: '',
    country: 'Deutschland',
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
          <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>Neue Firma</h2>
          <button onClick={onClose} style={{
            backgroundColor: 'transparent',
            border: 'none',
            fontSize: 20,
            cursor: 'pointer',
            color: colors.midGray,
          }}>×</button>
        </div>

        <div style={{ padding: 24 }}>
          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Firmenname *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              style={inputStyle}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div>
              <label style={labelStyle}>Branche</label>
              <select
                value={form.industry}
                onChange={(e) => setForm({ ...form, industry: e.target.value })}
                style={inputStyle}
              >
                <option value="">Auswählen...</option>
                <option value="IT-Services">IT-Services</option>
                <option value="Maschinenbau">Maschinenbau</option>
                <option value="Handel">Handel</option>
                <option value="Fertigung">Fertigung</option>
                <option value="Logistik">Logistik</option>
                <option value="Software">Software</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Größe</label>
              <select
                value={form.size}
                onChange={(e) => setForm({ ...form, size: e.target.value })}
                style={inputStyle}
              >
                <option value="">Auswählen...</option>
                <option value="1-10">1-10 Mitarbeiter</option>
                <option value="10-50">10-50 Mitarbeiter</option>
                <option value="50-200">50-200 Mitarbeiter</option>
                <option value="200-500">200-500 Mitarbeiter</option>
                <option value="500+">500+ Mitarbeiter</option>
              </select>
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Website</label>
            <input
              type="text"
              value={form.website}
              onChange={(e) => setForm({ ...form, website: e.target.value })}
              placeholder="beispiel.de"
              style={inputStyle}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
            <div>
              <label style={labelStyle}>Stadt</label>
              <input
                type="text"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Land</label>
              <input
                type="text"
                value={form.country}
                onChange={(e) => setForm({ ...form, country: e.target.value })}
                style={inputStyle}
              />
            </div>
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
