'use client';

import React, { useState } from 'react';
import { colors } from '@/lib/theme';
import {
  TrendingUp, TrendingDown, Euro, Target, Users, Calendar,
  Download, ChevronDown, BarChart3
} from 'lucide-react';

export default function ReportsPage() {
  const [period, setPeriod] = useState<'week' | 'month' | 'quarter' | 'year'>('month');

  // Sales Pipeline Data
  const pipelineData = [
    { stage: 'Lead', count: 12, value: 245000, color: colors.midGray },
    { stage: 'Qualifiziert', count: 8, value: 380000, color: colors.blue },
    { stage: 'Angebot', count: 5, value: 290000, color: colors.orange },
    { stage: 'Verhandlung', count: 4, value: 185000, color: '#9333ea' },
    { stage: 'Gewonnen', count: 6, value: 234000, color: colors.green },
  ];

  const totalPipeline = pipelineData.slice(0, 4).reduce((sum, s) => sum + s.value, 0);
  const wonValue = pipelineData[4].value;

  // Monthly Revenue
  const monthlyRevenue = [
    { month: 'Aug', value: 85000, target: 100000 },
    { month: 'Sep', value: 123000, target: 100000 },
    { month: 'Oct', value: 98000, target: 110000 },
    { month: 'Nov', value: 152000, target: 120000 },
    { month: 'Dec', value: 114000, target: 130000 },
    { month: 'Jan', value: 234000, target: 150000 },
  ];

  const maxRevenue = Math.max(...monthlyRevenue.map(m => Math.max(m.value, m.target)));

  // Team Performance
  const teamData = [
    { name: 'Max Kaufmann', won: 8, lost: 2, pipeline: 185000, revenue: 78000 },
    { name: 'Sarah Meyer', won: 6, lost: 3, pipeline: 245000, revenue: 92000 },
    { name: 'Tim Hoffmann', won: 5, lost: 1, pipeline: 156000, revenue: 45000 },
    { name: 'Julia Klein', won: 3, lost: 2, pipeline: 89000, revenue: 19000 },
  ];

  // Win/Loss by Source
  const sourceData = [
    { source: 'Website', won: 12, lost: 4 },
    { source: 'Empfehlung', won: 8, lost: 1 },
    { source: 'Messe', won: 4, lost: 3 },
    { source: 'Kaltakquise', won: 2, lost: 6 },
  ];

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
            Berichte
          </h1>
          <p style={{ fontSize: 14, color: colors.midGray, margin: 0 }}>
            Vertriebsanalysen und KPIs
          </p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <div style={{
            display: 'flex',
            backgroundColor: 'white',
            border: `1px solid ${colors.lightGray}`,
            borderRadius: 8,
            overflow: 'hidden',
          }}>
            {['week', 'month', 'quarter', 'year'].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p as any)}
                style={{
                  padding: '8px 14px',
                  backgroundColor: period === p ? colors.orange : 'transparent',
                  color: period === p ? 'white' : colors.midGray,
                  border: 'none',
                  fontSize: 13,
                  cursor: 'pointer',
                  textTransform: 'capitalize',
                }}
              >
                {p === 'week' ? 'Woche' : p === 'month' ? 'Monat' : p === 'quarter' ? 'Quartal' : 'Jahr'}
              </button>
            ))}
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
          }}>
            <Download size={18} />
            Export
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 20,
        marginBottom: 24,
      }}>
        <KPICard
          icon={<Euro size={24} />}
          label="Pipeline-Wert"
          value={`€${(totalPipeline / 1000).toFixed(0)}K`}
          change="+18%"
          positive
          color={colors.orange}
        />
        <KPICard
          icon={<Target size={24} />}
          label="Gewonnen"
          value={`€${(wonValue / 1000).toFixed(0)}K`}
          change="+23%"
          positive
          color={colors.green}
        />
        <KPICard
          icon={<TrendingUp size={24} />}
          label="Conversion Rate"
          value="32%"
          change="+5%"
          positive
          color={colors.blue}
        />
        <KPICard
          icon={<Calendar size={24} />}
          label="Avg. Sales Cycle"
          value="42 Tage"
          change="-8 Tage"
          positive
          color="#9333ea"
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
        {/* Revenue Chart */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 12,
          border: `1px solid ${colors.lightGray}`,
          padding: 24,
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: colors.dark, margin: '0 0 20px' }}>
            Umsatz vs. Ziel
          </h2>

          <div style={{
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-between',
            height: 200,
            gap: 8,
          }}>
            {monthlyRevenue.map((m) => (
              <div key={m.month} style={{ flex: 1, textAlign: 'center' }}>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 4,
                  marginBottom: 8,
                }}>
                  {/* Target line indicator */}
                  <div style={{
                    height: `${(m.target / maxRevenue) * 150}px`,
                    width: 2,
                    backgroundColor: colors.lightGray,
                    position: 'absolute',
                  }} />
                  {/* Actual bar */}
                  <div style={{
                    height: `${(m.value / maxRevenue) * 150}px`,
                    width: 32,
                    backgroundColor: m.value >= m.target ? colors.green : colors.orange,
                    borderRadius: '4px 4px 0 0',
                  }} />
                </div>
                <div style={{ fontSize: 12, color: colors.midGray }}>{m.month}</div>
                <div style={{ fontSize: 11, fontWeight: 600, color: colors.dark }}>
                  €{(m.value / 1000).toFixed(0)}K
                </div>
              </div>
            ))}
          </div>

          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: 24,
            marginTop: 16,
            fontSize: 12,
            color: colors.midGray,
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 12, height: 12, backgroundColor: colors.green, borderRadius: 2 }} />
              Über Ziel
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 12, height: 12, backgroundColor: colors.orange, borderRadius: 2 }} />
              Unter Ziel
            </span>
          </div>
        </div>

        {/* Pipeline Funnel */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 12,
          border: `1px solid ${colors.lightGray}`,
          padding: 24,
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: colors.dark, margin: '0 0 20px' }}>
            Sales Funnel
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {pipelineData.map((stage, i) => {
              const maxValue = pipelineData[0].value;
              const width = Math.max(30, (stage.value / maxValue) * 100);
              return (
                <div key={stage.stage}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: 4,
                    fontSize: 13,
                  }}>
                    <span style={{ color: colors.dark }}>{stage.stage}</span>
                    <span style={{ color: colors.midGray }}>{stage.count} Deals</span>
                  </div>
                  <div style={{
                    height: 28,
                    backgroundColor: colors.light,
                    borderRadius: 6,
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                  }}>
                    <div style={{
                      width: `${width}%`,
                      height: '100%',
                      backgroundColor: stage.color,
                      borderRadius: 6,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      paddingRight: 8,
                    }}>
                      <span style={{ fontSize: 11, fontWeight: 600, color: 'white' }}>
                        €{(stage.value / 1000).toFixed(0)}K
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Team & Sources */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 24,
        marginTop: 24,
      }}>
        {/* Team Performance */}
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
            <h2 style={{ fontSize: 16, fontWeight: 600, color: colors.dark, margin: 0 }}>
              Team Performance
            </h2>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: colors.light }}>
                <th style={thStyle}>Mitarbeiter</th>
                <th style={thStyle}>Gewonnen</th>
                <th style={thStyle}>Verloren</th>
                <th style={thStyle}>Win Rate</th>
                <th style={thStyle}>Pipeline</th>
              </tr>
            </thead>
            <tbody>
              {teamData.map((member) => {
                const winRate = Math.round((member.won / (member.won + member.lost)) * 100);
                return (
                  <tr key={member.name} style={{ borderBottom: `1px solid ${colors.lightGray}` }}>
                    <td style={tdStyle}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{
                          width: 32,
                          height: 32,
                          borderRadius: '50%',
                          backgroundColor: colors.blue + '20',
                          color: colors.blue,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: 11,
                          fontWeight: 600,
                        }}>
                          {member.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        {member.name}
                      </div>
                    </td>
                    <td style={{ ...tdStyle, color: colors.green, fontWeight: 600 }}>{member.won}</td>
                    <td style={{ ...tdStyle, color: colors.red }}>{member.lost}</td>
                    <td style={tdStyle}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{
                          width: 50,
                          height: 6,
                          backgroundColor: colors.lightGray,
                          borderRadius: 3,
                          overflow: 'hidden',
                        }}>
                          <div style={{
                            width: `${winRate}%`,
                            height: '100%',
                            backgroundColor: winRate >= 70 ? colors.green : winRate >= 50 ? colors.orange : colors.red,
                          }} />
                        </div>
                        <span style={{ fontSize: 12 }}>{winRate}%</span>
                      </div>
                    </td>
                    <td style={{ ...tdStyle, fontWeight: 600 }}>€{(member.pipeline / 1000).toFixed(0)}K</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Lead Sources */}
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
            <h2 style={{ fontSize: 16, fontWeight: 600, color: colors.dark, margin: 0 }}>
              Lead-Quellen
            </h2>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: colors.light }}>
                <th style={thStyle}>Quelle</th>
                <th style={thStyle}>Gewonnen</th>
                <th style={thStyle}>Verloren</th>
                <th style={thStyle}>Conversion</th>
              </tr>
            </thead>
            <tbody>
              {sourceData.map((source) => {
                const total = source.won + source.lost;
                const conversion = Math.round((source.won / total) * 100);
                return (
                  <tr key={source.source} style={{ borderBottom: `1px solid ${colors.lightGray}` }}>
                    <td style={tdStyle}>{source.source}</td>
                    <td style={{ ...tdStyle, color: colors.green, fontWeight: 600 }}>{source.won}</td>
                    <td style={{ ...tdStyle, color: colors.red }}>{source.lost}</td>
                    <td style={tdStyle}>
                      <div style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '4px 10px',
                        backgroundColor: conversion >= 70 ? colors.green + '15' : conversion >= 40 ? colors.orange + '15' : colors.red + '15',
                        color: conversion >= 70 ? colors.green : conversion >= 40 ? colors.orange : colors.red,
                        borderRadius: 6,
                        fontSize: 13,
                        fontWeight: 600,
                      }}>
                        {conversion >= 50 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                        {conversion}%
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function KPICard({ icon, label, value, change, positive, color }: any) {
  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: 12,
      border: `1px solid ${colors.lightGray}`,
      padding: 24,
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 16,
      }}>
        <div style={{
          width: 48,
          height: 48,
          borderRadius: 12,
          backgroundColor: color + '15',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: color,
        }}>
          {icon}
        </div>
        <span style={{
          fontSize: 13,
          fontWeight: 600,
          color: positive ? colors.green : colors.red,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
        }}>
          {positive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {change}
        </span>
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color: colors.dark, marginBottom: 4 }}>
        {value}
      </div>
      <div style={{ fontSize: 14, color: colors.midGray }}>
        {label}
      </div>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  padding: '12px 16px',
  textAlign: 'left',
  fontSize: 12,
  fontWeight: 500,
  color: colors.midGray,
  textTransform: 'uppercase',
};

const tdStyle: React.CSSProperties = {
  padding: '12px 16px',
  fontSize: 14,
  color: colors.dark,
};
