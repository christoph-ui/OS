'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { colors } from '@/lib/theme';
import {
  TrendingUp, TrendingDown, Users, Building2, Target, Euro,
  Phone, Mail, Calendar, Clock, ChevronRight, ArrowUpRight
} from 'lucide-react';

export default function CRMDashboard() {
  const router = useRouter();

  const stats = [
    { 
      label: 'Offene Deals', 
      value: '€847K', 
      change: '+12%', 
      positive: true,
      icon: Target,
      color: colors.orange 
    },
    { 
      label: 'Neue Kontakte', 
      value: '34', 
      change: '+8', 
      positive: true,
      subtext: 'diesen Monat',
      icon: Users,
      color: colors.blue 
    },
    { 
      label: 'Gewonnene Deals', 
      value: '€234K', 
      change: '+23%', 
      positive: true,
      subtext: 'vs. Vormonat',
      icon: Euro,
      color: colors.green 
    },
    { 
      label: 'Conversion Rate', 
      value: '32%', 
      change: '-2%', 
      positive: false,
      icon: TrendingUp,
      color: colors.midGray 
    },
  ];

  const recentDeals = [
    { id: '1', name: 'ERP-Integration Müller GmbH', value: 45000, stage: 'Verhandlung', probability: 80, contact: 'Thomas Müller' },
    { id: '2', name: 'Cloud Migration Schmidt AG', value: 128000, stage: 'Angebot', probability: 60, contact: 'Anna Schmidt' },
    { id: '3', name: 'IT-Wartung Bauer KG', value: 24000, stage: 'Qualifizierung', probability: 40, contact: 'Klaus Bauer' },
    { id: '4', name: 'Netzwerk-Upgrade Weber', value: 67000, stage: 'Verhandlung', probability: 75, contact: 'Lisa Weber' },
  ];

  const upcomingActivities = [
    { id: '1', type: 'call', title: 'Folgeanruf Müller GmbH', time: '10:00', contact: 'Thomas Müller' },
    { id: '2', type: 'meeting', title: 'Demo Schmidt AG', time: '14:00', contact: 'Anna Schmidt' },
    { id: '3', type: 'email', title: 'Angebot nachfassen', time: '16:00', contact: 'Klaus Bauer' },
    { id: '4', type: 'call', title: 'Erstgespräch Fischer', time: 'Morgen 09:00', contact: 'Peter Fischer' },
  ];

  const teamPerformance = [
    { name: 'Max Kaufmann', deals: 12, value: 234000, avatar: 'MK' },
    { name: 'Sarah Meyer', deals: 9, value: 187000, avatar: 'SM' },
    { name: 'Tim Hoffmann', deals: 8, value: 156000, avatar: 'TH' },
    { name: 'Julia Klein', deals: 6, value: 142000, avatar: 'JK' },
  ];

  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'Verhandlung': return colors.orange;
      case 'Angebot': return colors.blue;
      case 'Qualifizierung': return colors.midGray;
      case 'Gewonnen': return colors.green;
      default: return colors.midGray;
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'call': return <Phone size={16} />;
      case 'meeting': return <Calendar size={16} />;
      case 'email': return <Mail size={16} />;
      default: return <Clock size={16} />;
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 600, color: colors.dark, margin: '0 0 4px' }}>
          Dashboard
        </h1>
        <p style={{ fontSize: 14, color: colors.midGray, margin: 0 }}>
          Willkommen zurück, Max. Hier ist dein Überblick.
        </p>
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 20,
        marginBottom: 24,
      }}>
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div
              key={i}
              style={{
                backgroundColor: 'white',
                borderRadius: 12,
                border: `1px solid ${colors.lightGray}`,
                padding: 24,
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: 16,
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
                <span style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: stat.positive ? colors.green : colors.red,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                }}>
                  {stat.positive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  {stat.change}
                </span>
              </div>
              <div style={{ fontSize: 28, fontWeight: 700, color: colors.dark, marginBottom: 4 }}>
                {stat.value}
              </div>
              <div style={{ fontSize: 14, color: colors.midGray }}>
                {stat.label}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
        {/* Recent Deals */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 12,
          border: `1px solid ${colors.lightGray}`,
          overflow: 'hidden',
        }}>
          <div style={{
            padding: '20px 24px',
            borderBottom: `1px solid ${colors.lightGray}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: colors.dark, margin: 0 }}>
              Aktuelle Deals
            </h2>
            <button
              onClick={() => router.push('/crm/deals')}
              style={{
                fontSize: 13,
                color: colors.orange,
                backgroundColor: 'transparent',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              Alle anzeigen <ChevronRight size={16} />
            </button>
          </div>

          <div>
            {recentDeals.map((deal, i) => (
              <div
                key={deal.id}
                onClick={() => router.push(`/crm/deals/${deal.id}`)}
                style={{
                  padding: '16px 24px',
                  borderBottom: i < recentDeals.length - 1 ? `1px solid ${colors.lightGray}` : 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 500, color: colors.dark, marginBottom: 4 }}>
                    {deal.name}
                  </div>
                  <div style={{ fontSize: 13, color: colors.midGray }}>
                    {deal.contact}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 15, fontWeight: 600, color: colors.dark, marginBottom: 4 }}>
                    €{deal.value.toLocaleString('de-DE')}
                  </div>
                  <span style={{
                    fontSize: 12,
                    fontWeight: 500,
                    padding: '4px 10px',
                    borderRadius: 6,
                    backgroundColor: getStageColor(deal.stage) + '15',
                    color: getStageColor(deal.stage),
                  }}>
                    {deal.stage} · {deal.probability}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Upcoming Activities */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: 12,
            border: `1px solid ${colors.lightGray}`,
            overflow: 'hidden',
          }}>
            <div style={{
              padding: '16px 20px',
              borderBottom: `1px solid ${colors.lightGray}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <h2 style={{ fontSize: 15, fontWeight: 600, color: colors.dark, margin: 0 }}>
                Heute
              </h2>
              <span style={{
                fontSize: 12,
                color: colors.midGray,
                padding: '4px 8px',
                backgroundColor: colors.light,
                borderRadius: 4,
              }}>
                {new Date().toLocaleDateString('de-DE', { weekday: 'short', day: 'numeric', month: 'short' })}
              </span>
            </div>

            <div>
              {upcomingActivities.map((activity, i) => (
                <div
                  key={activity.id}
                  style={{
                    padding: '12px 20px',
                    borderBottom: i < upcomingActivities.length - 1 ? `1px solid ${colors.lightGray}` : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: 8,
                    backgroundColor: colors.blue + '15',
                    color: colors.blue,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    {getActivityIcon(activity.type)}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: colors.dark }}>
                      {activity.title}
                    </div>
                    <div style={{ fontSize: 12, color: colors.midGray }}>
                      {activity.contact}
                    </div>
                  </div>
                  <div style={{ fontSize: 12, color: colors.midGray, fontWeight: 500 }}>
                    {activity.time}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Team Leaderboard */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: 12,
            border: `1px solid ${colors.lightGray}`,
            overflow: 'hidden',
          }}>
            <div style={{
              padding: '16px 20px',
              borderBottom: `1px solid ${colors.lightGray}`,
            }}>
              <h2 style={{ fontSize: 15, fontWeight: 600, color: colors.dark, margin: 0 }}>
                Team Ranking
              </h2>
            </div>

            <div>
              {teamPerformance.map((member, i) => (
                <div
                  key={member.name}
                  style={{
                    padding: '12px 20px',
                    borderBottom: i < teamPerformance.length - 1 ? `1px solid ${colors.lightGray}` : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <span style={{
                    width: 20,
                    fontSize: 13,
                    fontWeight: 600,
                    color: i < 3 ? colors.orange : colors.midGray,
                  }}>
                    #{i + 1}
                  </span>
                  <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    backgroundColor: colors.blue + '20',
                    color: colors.blue,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 12,
                    fontWeight: 600,
                  }}>
                    {member.avatar}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: colors.dark }}>
                      {member.name}
                    </div>
                    <div style={{ fontSize: 12, color: colors.midGray }}>
                      {member.deals} Deals
                    </div>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: colors.green }}>
                    €{(member.value / 1000).toFixed(0)}K
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
