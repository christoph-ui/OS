'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { colors } from '@/lib/theme';
import {
  Plus, Search, Filter, MoreVertical, Euro, Calendar,
  User, Building2, ChevronDown, LayoutGrid, List
} from 'lucide-react';

interface Deal {
  id: string;
  name: string;
  value: number;
  stage: string;
  probability: number;
  contact: string;
  company: string;
  owner: string;
  expectedClose: string;
  createdAt: string;
}

const stages = [
  { id: 'lead', name: 'Lead', color: colors.midGray },
  { id: 'qualified', name: 'Qualifiziert', color: colors.blue },
  { id: 'proposal', name: 'Angebot', color: colors.orange },
  { id: 'negotiation', name: 'Verhandlung', color: '#9333ea' },
  { id: 'won', name: 'Gewonnen', color: colors.green },
];

export default function DealsPage() {
  const router = useRouter();
  const [view, setView] = useState<'kanban' | 'list'>('kanban');
  const [search, setSearch] = useState('');
  const [showNewModal, setShowNewModal] = useState(false);
  const [draggedDeal, setDraggedDeal] = useState<string | null>(null);

  const [deals, setDeals] = useState<Deal[]>([
    { id: '1', name: 'ERP-Integration Müller GmbH', value: 45000, stage: 'negotiation', probability: 80, contact: 'Thomas Müller', company: 'Müller & Söhne GmbH', owner: 'Max Kaufmann', expectedClose: '2026-02-15', createdAt: '2026-01-10' },
    { id: '2', name: 'Cloud Migration Schmidt AG', value: 128000, stage: 'proposal', probability: 60, contact: 'Anna Schmidt', company: 'Schmidt AG', owner: 'Sarah Meyer', expectedClose: '2026-03-01', createdAt: '2026-01-05' },
    { id: '3', name: 'IT-Wartung Bauer KG', value: 24000, stage: 'qualified', probability: 40, contact: 'Klaus Bauer', company: 'Bauer KG', owner: 'Max Kaufmann', expectedClose: '2026-02-28', createdAt: '2026-01-15' },
    { id: '4', name: 'Netzwerk-Upgrade Weber', value: 67000, stage: 'negotiation', probability: 75, contact: 'Lisa Weber', company: 'Weber Technik', owner: 'Tim Hoffmann', expectedClose: '2026-02-10', createdAt: '2026-01-08' },
    { id: '5', name: 'Software-Lizenzierung Fischer', value: 35000, stage: 'lead', probability: 20, contact: 'Peter Fischer', company: 'Fischer GmbH', owner: 'Julia Klein', expectedClose: '2026-04-01', createdAt: '2026-01-20' },
    { id: '6', name: 'Datacenter Hoffmann Industrie', value: 250000, stage: 'qualified', probability: 50, contact: 'Maria Hoffmann', company: 'Hoffmann Industrie', owner: 'Sarah Meyer', expectedClose: '2026-05-01', createdAt: '2026-01-12' },
    { id: '7', name: 'Security Audit Klein Solutions', value: 18000, stage: 'proposal', probability: 70, contact: 'Stefan Klein', company: 'Klein Solutions', owner: 'Max Kaufmann', expectedClose: '2026-02-05', createdAt: '2026-01-18' },
    { id: '8', name: 'VoIP System Wagner Tech', value: 42000, stage: 'won', probability: 100, contact: 'Andrea Wagner', company: 'Wagner Tech', owner: 'Tim Hoffmann', expectedClose: '2026-01-25', createdAt: '2026-01-02' },
    { id: '9', name: 'Backup-Lösung Meier AG', value: 28000, stage: 'lead', probability: 15, contact: 'Hans Meier', company: 'Meier AG', owner: 'Julia Klein', expectedClose: '2026-04-15', createdAt: '2026-01-22' },
  ]);

  const getDealsForStage = (stageId: string) => 
    deals.filter(d => d.stage === stageId);

  const getStageValue = (stageId: string) =>
    getDealsForStage(stageId).reduce((sum, d) => sum + d.value, 0);

  const handleDragStart = (dealId: string) => {
    setDraggedDeal(dealId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (stageId: string) => {
    if (draggedDeal) {
      setDeals(prev => prev.map(d => 
        d.id === draggedDeal ? { ...d, stage: stageId } : d
      ));
      setDraggedDeal(null);
    }
  };

  const totalPipeline = deals.filter(d => d.stage !== 'won').reduce((sum, d) => sum + d.value, 0);
  const weightedPipeline = deals.filter(d => d.stage !== 'won').reduce((sum, d) => sum + (d.value * d.probability / 100), 0);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
      }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 600, color: colors.dark, margin: '0 0 4px' }}>
            Deals
          </h1>
          <p style={{ fontSize: 14, color: colors.midGray, margin: 0 }}>
            Pipeline: €{(totalPipeline / 1000).toFixed(0)}K · Gewichtet: €{(weightedPipeline / 1000).toFixed(0)}K
          </p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          {/* View Toggle */}
          <div style={{
            display: 'flex',
            backgroundColor: 'white',
            border: `1px solid ${colors.lightGray}`,
            borderRadius: 8,
            overflow: 'hidden',
          }}>
            <button
              onClick={() => setView('kanban')}
              style={{
                padding: '8px 12px',
                backgroundColor: view === 'kanban' ? colors.orange : 'transparent',
                color: view === 'kanban' ? 'white' : colors.midGray,
                border: 'none',
                cursor: 'pointer',
              }}
            >
              <LayoutGrid size={18} />
            </button>
            <button
              onClick={() => setView('list')}
              style={{
                padding: '8px 12px',
                backgroundColor: view === 'list' ? colors.orange : 'transparent',
                color: view === 'list' ? 'white' : colors.midGray,
                border: 'none',
                cursor: 'pointer',
              }}
            >
              <List size={18} />
            </button>
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
            Neuer Deal
          </button>
        </div>
      </div>

      {/* Search */}
      <div style={{
        display: 'flex',
        gap: 12,
        marginBottom: 20,
      }}>
        <div style={{
          flex: 1,
          maxWidth: 400,
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
            placeholder="Suche nach Deal, Firma..."
            style={{
              flex: 1,
              border: 'none',
              fontSize: 14,
              outline: 'none',
            }}
          />
        </div>
      </div>

      {/* Kanban Board */}
      {view === 'kanban' && (
        <div style={{
          flex: 1,
          display: 'flex',
          gap: 16,
          overflow: 'auto',
          paddingBottom: 20,
        }}>
          {stages.map((stage) => (
            <div
              key={stage.id}
              onDragOver={handleDragOver}
              onDrop={() => handleDrop(stage.id)}
              style={{
                flex: 1,
                minWidth: 280,
                backgroundColor: colors.light,
                borderRadius: 12,
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              {/* Stage Header */}
              <div style={{
                padding: '16px 16px 12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: stage.color,
                  }} />
                  <span style={{ fontSize: 14, fontWeight: 600, color: colors.dark }}>
                    {stage.name}
                  </span>
                  <span style={{
                    fontSize: 12,
                    color: colors.midGray,
                    backgroundColor: 'white',
                    padding: '2px 8px',
                    borderRadius: 10,
                  }}>
                    {getDealsForStage(stage.id).length}
                  </span>
                </div>
                <span style={{ fontSize: 13, fontWeight: 600, color: stage.color }}>
                  €{(getStageValue(stage.id) / 1000).toFixed(0)}K
                </span>
              </div>

              {/* Cards */}
              <div style={{
                flex: 1,
                padding: '0 12px 12px',
                overflow: 'auto',
              }}>
                {getDealsForStage(stage.id).map((deal) => (
                  <div
                    key={deal.id}
                    draggable
                    onDragStart={() => handleDragStart(deal.id)}
                    onClick={() => router.push(`/crm/deals/${deal.id}`)}
                    style={{
                      backgroundColor: 'white',
                      borderRadius: 10,
                      padding: 16,
                      marginBottom: 10,
                      cursor: 'pointer',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
                      border: draggedDeal === deal.id ? `2px solid ${colors.orange}` : '1px solid transparent',
                    }}
                  >
                    <div style={{
                      fontSize: 14,
                      fontWeight: 500,
                      color: colors.dark,
                      marginBottom: 8,
                    }}>
                      {deal.name}
                    </div>

                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      fontSize: 13,
                      color: colors.midGray,
                      marginBottom: 12,
                    }}>
                      <Building2 size={14} />
                      {deal.company}
                    </div>

                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}>
                      <span style={{
                        fontSize: 16,
                        fontWeight: 700,
                        color: colors.dark,
                      }}>
                        €{deal.value.toLocaleString('de-DE')}
                      </span>
                      <span style={{
                        fontSize: 12,
                        padding: '4px 8px',
                        borderRadius: 4,
                        backgroundColor: stage.color + '15',
                        color: stage.color,
                        fontWeight: 500,
                      }}>
                        {deal.probability}%
                      </span>
                    </div>

                    <div style={{
                      marginTop: 12,
                      paddingTop: 12,
                      borderTop: `1px solid ${colors.lightGray}`,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        fontSize: 12,
                        color: colors.midGray,
                      }}>
                        <Calendar size={12} />
                        {new Date(deal.expectedClose).toLocaleDateString('de-DE', { day: 'numeric', month: 'short' })}
                      </div>
                      <div style={{
                        width: 24,
                        height: 24,
                        borderRadius: '50%',
                        backgroundColor: colors.blue + '20',
                        color: colors.blue,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 10,
                        fontWeight: 600,
                      }}>
                        {deal.owner.split(' ').map(n => n[0]).join('')}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Add Deal Button */}
                <button
                  onClick={() => setShowNewModal(true)}
                  style={{
                    width: '100%',
                    padding: 12,
                    backgroundColor: 'transparent',
                    border: `2px dashed ${colors.lightGray}`,
                    borderRadius: 10,
                    fontSize: 13,
                    color: colors.midGray,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 6,
                  }}
                >
                  <Plus size={16} />
                  Deal hinzufügen
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* List View */}
      {view === 'list' && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: 12,
          border: `1px solid ${colors.lightGray}`,
          overflow: 'hidden',
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: colors.light }}>
                <th style={thStyle}>Deal</th>
                <th style={thStyle}>Wert</th>
                <th style={thStyle}>Phase</th>
                <th style={thStyle}>Wahrscheinlichkeit</th>
                <th style={thStyle}>Abschluss</th>
                <th style={thStyle}>Betreuer</th>
              </tr>
            </thead>
            <tbody>
              {deals.map((deal) => {
                const stage = stages.find(s => s.id === deal.stage);
                return (
                  <tr
                    key={deal.id}
                    onClick={() => router.push(`/crm/deals/${deal.id}`)}
                    style={{
                      borderBottom: `1px solid ${colors.lightGray}`,
                      cursor: 'pointer',
                    }}
                  >
                    <td style={tdStyle}>
                      <div style={{ fontWeight: 500 }}>{deal.name}</div>
                      <div style={{ fontSize: 12, color: colors.midGray }}>{deal.company}</div>
                    </td>
                    <td style={tdStyle}>
                      <span style={{ fontWeight: 600 }}>€{deal.value.toLocaleString('de-DE')}</span>
                    </td>
                    <td style={tdStyle}>
                      <span style={{
                        padding: '4px 10px',
                        borderRadius: 6,
                        backgroundColor: (stage?.color || colors.midGray) + '15',
                        color: stage?.color,
                        fontSize: 12,
                        fontWeight: 500,
                      }}>
                        {stage?.name}
                      </span>
                    </td>
                    <td style={tdStyle}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{
                          width: 60,
                          height: 6,
                          backgroundColor: colors.lightGray,
                          borderRadius: 3,
                          overflow: 'hidden',
                        }}>
                          <div style={{
                            width: `${deal.probability}%`,
                            height: '100%',
                            backgroundColor: stage?.color,
                          }} />
                        </div>
                        <span style={{ fontSize: 13 }}>{deal.probability}%</span>
                      </div>
                    </td>
                    <td style={tdStyle}>
                      {new Date(deal.expectedClose).toLocaleDateString('de-DE')}
                    </td>
                    <td style={tdStyle}>{deal.owner}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* New Deal Modal */}
      {showNewModal && (
        <NewDealModal onClose={() => setShowNewModal(false)} />
      )}
    </div>
  );
}

function NewDealModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({
    name: '',
    value: '',
    company: '',
    contact: '',
    stage: 'lead',
    probability: 20,
    expectedClose: '',
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
          <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>Neuer Deal</h2>
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
            <label style={labelStyle}>Deal-Name *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="z.B. ERP-Integration Müller GmbH"
              style={inputStyle}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div>
              <label style={labelStyle}>Wert (€) *</label>
              <input
                type="number"
                value={form.value}
                onChange={(e) => setForm({ ...form, value: e.target.value })}
                placeholder="45000"
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Phase</label>
              <select
                value={form.stage}
                onChange={(e) => setForm({ ...form, stage: e.target.value })}
                style={inputStyle}
              >
                {stages.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
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

          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Kontakt</label>
            <input
              type="text"
              value={form.contact}
              onChange={(e) => setForm({ ...form, contact: e.target.value })}
              style={inputStyle}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
            <div>
              <label style={labelStyle}>Wahrscheinlichkeit (%)</label>
              <input
                type="number"
                value={form.probability}
                onChange={(e) => setForm({ ...form, probability: parseInt(e.target.value) })}
                min="0"
                max="100"
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Erwarteter Abschluss</label>
              <input
                type="date"
                value={form.expectedClose}
                onChange={(e) => setForm({ ...form, expectedClose: e.target.value })}
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
              Deal erstellen
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
  padding: '16px',
  fontSize: 14,
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
