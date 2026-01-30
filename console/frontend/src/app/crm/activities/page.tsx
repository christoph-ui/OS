'use client';

import React, { useState } from 'react';
import { colors } from '@/lib/theme';
import {
  Plus, Search, Filter, Phone, Mail, Calendar, CheckSquare,
  Clock, User, Building2, Check, MoreVertical
} from 'lucide-react';

type ActivityType = 'call' | 'email' | 'meeting' | 'task';

interface Activity {
  id: string;
  type: ActivityType;
  title: string;
  description?: string;
  contact: string;
  company: string;
  dueDate: string;
  dueTime?: string;
  completed: boolean;
  owner: string;
  priority: 'low' | 'medium' | 'high';
}

export default function ActivitiesPage() {
  const [filter, setFilter] = useState<'all' | 'today' | 'upcoming' | 'overdue' | 'completed'>('today');
  const [search, setSearch] = useState('');
  const [showNewModal, setShowNewModal] = useState(false);

  const [activities, setActivities] = useState<Activity[]>([
    { id: '1', type: 'call', title: 'Folgeanruf Müller GmbH', description: 'Nachfassen zum Angebot', contact: 'Thomas Müller', company: 'Müller & Söhne GmbH', dueDate: '2026-01-30', dueTime: '10:00', completed: false, owner: 'Max Kaufmann', priority: 'high' },
    { id: '2', type: 'meeting', title: 'Demo Schmidt AG', description: 'Produktvorstellung Cloud-Lösung', contact: 'Anna Schmidt', company: 'Schmidt AG', dueDate: '2026-01-30', dueTime: '14:00', completed: false, owner: 'Sarah Meyer', priority: 'high' },
    { id: '3', type: 'email', title: 'Angebot nachfassen', contact: 'Klaus Bauer', company: 'Bauer KG', dueDate: '2026-01-30', dueTime: '16:00', completed: false, owner: 'Max Kaufmann', priority: 'medium' },
    { id: '4', type: 'call', title: 'Erstgespräch Fischer', description: 'Bedarfsanalyse', contact: 'Peter Fischer', company: 'Fischer GmbH', dueDate: '2026-01-31', dueTime: '09:00', completed: false, owner: 'Julia Klein', priority: 'medium' },
    { id: '5', type: 'task', title: 'Präsentation vorbereiten', description: 'Für Meeting mit Hoffmann Industrie', contact: 'Maria Hoffmann', company: 'Hoffmann Industrie', dueDate: '2026-01-31', completed: false, owner: 'Sarah Meyer', priority: 'high' },
    { id: '6', type: 'meeting', title: 'Vertragsverhandlung Weber', contact: 'Lisa Weber', company: 'Weber Technik', dueDate: '2026-02-01', dueTime: '11:00', completed: false, owner: 'Tim Hoffmann', priority: 'high' },
    { id: '7', type: 'call', title: 'Support-Rückruf Klein', contact: 'Stefan Klein', company: 'Klein Solutions', dueDate: '2026-01-29', dueTime: '15:00', completed: true, owner: 'Max Kaufmann', priority: 'low' },
    { id: '8', type: 'email', title: 'Rechnung senden Wagner', contact: 'Andrea Wagner', company: 'Wagner Tech', dueDate: '2026-01-28', completed: true, owner: 'Tim Hoffmann', priority: 'medium' },
  ]);

  const today = new Date().toISOString().split('T')[0];

  const getFilteredActivities = () => {
    let filtered = activities;

    switch (filter) {
      case 'today':
        filtered = activities.filter(a => a.dueDate === today && !a.completed);
        break;
      case 'upcoming':
        filtered = activities.filter(a => a.dueDate > today && !a.completed);
        break;
      case 'overdue':
        filtered = activities.filter(a => a.dueDate < today && !a.completed);
        break;
      case 'completed':
        filtered = activities.filter(a => a.completed);
        break;
    }

    if (search) {
      filtered = filtered.filter(a =>
        `${a.title} ${a.contact} ${a.company}`.toLowerCase().includes(search.toLowerCase())
      );
    }

    return filtered.sort((a, b) => {
      if (a.dueDate !== b.dueDate) return a.dueDate.localeCompare(b.dueDate);
      if (a.dueTime && b.dueTime) return a.dueTime.localeCompare(b.dueTime);
      return 0;
    });
  };

  const toggleComplete = (id: string) => {
    setActivities(prev =>
      prev.map(a => a.id === id ? { ...a, completed: !a.completed } : a)
    );
  };

  const getTypeIcon = (type: ActivityType) => {
    switch (type) {
      case 'call': return <Phone size={16} />;
      case 'email': return <Mail size={16} />;
      case 'meeting': return <Calendar size={16} />;
      case 'task': return <CheckSquare size={16} />;
    }
  };

  const getTypeColor = (type: ActivityType) => {
    switch (type) {
      case 'call': return colors.green;
      case 'email': return colors.blue;
      case 'meeting': return colors.orange;
      case 'task': return '#9333ea';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return colors.red;
      case 'medium': return colors.orange;
      case 'low': return colors.midGray;
      default: return colors.midGray;
    }
  };

  const stats = {
    today: activities.filter(a => a.dueDate === today && !a.completed).length,
    overdue: activities.filter(a => a.dueDate < today && !a.completed).length,
    upcoming: activities.filter(a => a.dueDate > today && !a.completed).length,
    completed: activities.filter(a => a.completed).length,
  };

  const filteredActivities = getFilteredActivities();

  // Group by date
  const groupedByDate = filteredActivities.reduce((acc, activity) => {
    const date = activity.dueDate;
    if (!acc[date]) acc[date] = [];
    acc[date].push(activity);
    return acc;
  }, {} as Record<string, Activity[]>);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    if (dateStr === today) return 'Heute';
    if (dateStr === new Date(Date.now() + 86400000).toISOString().split('T')[0]) return 'Morgen';
    return date.toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long' });
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
            Aktivitäten
          </h1>
          <p style={{ fontSize: 14, color: colors.midGray, margin: 0 }}>
            Verwalte Anrufe, E-Mails, Meetings und Aufgaben
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
          Neue Aktivität
        </button>
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 12,
        marginBottom: 24,
      }}>
        {[
          { key: 'today', label: 'Heute', count: stats.today, color: colors.orange },
          { key: 'overdue', label: 'Überfällig', count: stats.overdue, color: colors.red },
          { key: 'upcoming', label: 'Kommend', count: stats.upcoming, color: colors.blue },
          { key: 'completed', label: 'Erledigt', count: stats.completed, color: colors.green },
        ].map((stat) => (
          <button
            key={stat.key}
            onClick={() => setFilter(stat.key as any)}
            style={{
              padding: '16px 20px',
              backgroundColor: filter === stat.key ? stat.color + '10' : 'white',
              border: `1px solid ${filter === stat.key ? stat.color : colors.lightGray}`,
              borderRadius: 10,
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
            <div style={{
              fontSize: 24,
              fontWeight: 700,
              color: stat.color,
              marginBottom: 4,
            }}>
              {stat.count}
            </div>
            <div style={{ fontSize: 13, color: colors.midGray }}>{stat.label}</div>
          </button>
        ))}
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
            placeholder="Suche nach Aktivität, Kontakt..."
            style={{
              flex: 1,
              border: 'none',
              fontSize: 14,
              outline: 'none',
            }}
          />
        </div>
      </div>

      {/* Activity List */}
      <div>
        {Object.entries(groupedByDate).map(([date, dayActivities]) => (
          <div key={date} style={{ marginBottom: 24 }}>
            <h3 style={{
              fontSize: 14,
              fontWeight: 600,
              color: colors.midGray,
              marginBottom: 12,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}>
              {formatDate(date)}
            </h3>

            <div style={{
              backgroundColor: 'white',
              borderRadius: 12,
              border: `1px solid ${colors.lightGray}`,
              overflow: 'hidden',
            }}>
              {dayActivities.map((activity, i) => (
                <div
                  key={activity.id}
                  style={{
                    padding: '16px 20px',
                    borderBottom: i < dayActivities.length - 1 ? `1px solid ${colors.lightGray}` : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 16,
                    opacity: activity.completed ? 0.6 : 1,
                  }}
                >
                  {/* Checkbox */}
                  <button
                    onClick={() => toggleComplete(activity.id)}
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: 6,
                      border: `2px solid ${activity.completed ? colors.green : colors.lightGray}`,
                      backgroundColor: activity.completed ? colors.green : 'transparent',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      flexShrink: 0,
                    }}
                  >
                    {activity.completed && <Check size={14} />}
                  </button>

                  {/* Type Icon */}
                  <div style={{
                    width: 36,
                    height: 36,
                    borderRadius: 8,
                    backgroundColor: getTypeColor(activity.type) + '15',
                    color: getTypeColor(activity.type),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    {getTypeIcon(activity.type)}
                  </div>

                  {/* Content */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: 14,
                      fontWeight: 500,
                      color: colors.dark,
                      marginBottom: 4,
                      textDecoration: activity.completed ? 'line-through' : 'none',
                    }}>
                      {activity.title}
                    </div>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      fontSize: 13,
                      color: colors.midGray,
                    }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <User size={12} />
                        {activity.contact}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Building2 size={12} />
                        {activity.company}
                      </span>
                    </div>
                  </div>

                  {/* Time */}
                  {activity.dueTime && (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      fontSize: 13,
                      color: colors.midGray,
                      flexShrink: 0,
                    }}>
                      <Clock size={14} />
                      {activity.dueTime}
                    </div>
                  )}

                  {/* Priority */}
                  <div style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: getPriorityColor(activity.priority),
                    flexShrink: 0,
                  }} />

                  {/* Owner Avatar */}
                  <div style={{
                    width: 28,
                    height: 28,
                    borderRadius: '50%',
                    backgroundColor: colors.blue + '20',
                    color: colors.blue,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 10,
                    fontWeight: 600,
                    flexShrink: 0,
                  }}>
                    {activity.owner.split(' ').map(n => n[0]).join('')}
                  </div>

                  {/* Actions */}
                  <button style={{
                    backgroundColor: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    padding: 4,
                    flexShrink: 0,
                  }}>
                    <MoreVertical size={18} color={colors.midGray} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}

        {filteredActivities.length === 0 && (
          <div style={{
            textAlign: 'center',
            padding: 60,
            color: colors.midGray,
          }}>
            <CheckSquare size={48} strokeWidth={1} style={{ marginBottom: 16, opacity: 0.5 }} />
            <div style={{ fontSize: 16, fontWeight: 500, marginBottom: 8 }}>
              Keine Aktivitäten
            </div>
            <div style={{ fontSize: 14 }}>
              {filter === 'completed' ? 'Noch keine erledigten Aktivitäten' : 'Alle Aktivitäten erledigt!'}
            </div>
          </div>
        )}
      </div>

      {/* New Activity Modal */}
      {showNewModal && (
        <NewActivityModal onClose={() => setShowNewModal(false)} />
      )}
    </div>
  );
}

function NewActivityModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({
    type: 'call' as ActivityType,
    title: '',
    description: '',
    contact: '',
    company: '',
    dueDate: '',
    dueTime: '',
    priority: 'medium',
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
          <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>Neue Aktivität</h2>
          <button onClick={onClose} style={{
            backgroundColor: 'transparent',
            border: 'none',
            fontSize: 20,
            cursor: 'pointer',
            color: colors.midGray,
          }}>×</button>
        </div>

        <div style={{ padding: 24 }}>
          {/* Type Selection */}
          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Typ</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {[
                { type: 'call', label: 'Anruf', icon: Phone },
                { type: 'email', label: 'E-Mail', icon: Mail },
                { type: 'meeting', label: 'Meeting', icon: Calendar },
                { type: 'task', label: 'Aufgabe', icon: CheckSquare },
              ].map((t) => {
                const Icon = t.icon;
                return (
                  <button
                    key={t.type}
                    onClick={() => setForm({ ...form, type: t.type as ActivityType })}
                    style={{
                      flex: 1,
                      padding: '10px',
                      backgroundColor: form.type === t.type ? colors.orange + '15' : colors.light,
                      border: `1px solid ${form.type === t.type ? colors.orange : colors.lightGray}`,
                      borderRadius: 8,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 6,
                      fontSize: 13,
                      color: form.type === t.type ? colors.orange : colors.dark,
                    }}
                  >
                    <Icon size={16} />
                    {t.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Titel *</label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="z.B. Folgeanruf Müller GmbH"
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Beschreibung</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
              style={{ ...inputStyle, resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div>
              <label style={labelStyle}>Kontakt</label>
              <input
                type="text"
                value={form.contact}
                onChange={(e) => setForm({ ...form, contact: e.target.value })}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Firma</label>
              <input
                type="text"
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 24 }}>
            <div>
              <label style={labelStyle}>Datum *</label>
              <input
                type="date"
                value={form.dueDate}
                onChange={(e) => setForm({ ...form, dueDate: e.target.value })}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Uhrzeit</label>
              <input
                type="time"
                value={form.dueTime}
                onChange={(e) => setForm({ ...form, dueTime: e.target.value })}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Priorität</label>
              <select
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: e.target.value })}
                style={inputStyle}
              >
                <option value="low">Niedrig</option>
                <option value="medium">Mittel</option>
                <option value="high">Hoch</option>
              </select>
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
              Erstellen
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
