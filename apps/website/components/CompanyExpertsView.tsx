'use client';

import React, { useState } from 'react';

// ============================================================================
// COMPANY DASHBOARD - MY EXPERTS SECTION
// ============================================================================

const theme = {
  colors: {
    dark: '#141413',
    light: '#faf9f5',
    midGray: '#b0aea5',
    lightGray: '#e8e6dc',
    orange: '#d97757',
    blue: '#6a9bcc',
    green: '#788c5d',
    red: '#c75a5a',
  }
};

const MCP_CATALOG: Record<string, any> = {
  CTAX: { name: 'Tax', icon: '📊', color: theme.colors.orange },
  FPA: { name: 'FP&A', icon: '📈', color: theme.colors.blue },
  LEGAL: { name: 'Legal', icon: '⚖️', color: theme.colors.dark },
  ETIM: { name: 'Products', icon: '🏷️', color: '#5ab5b5' },
};

interface ExpertEngagement {
  id: string;
  expert: {
    id: string;
    name: string;
    avatar: string;
    headline: string;
    rating: number;
    total_reviews: number;
  };
  mcps: string[];
  monthly_rate: number;
  status: 'active' | 'paused' | 'ended';
  health_score: number;
  ai_automation_rate: number;
  tasks_completed: number;
  tasks_this_month: number;
  start_date: string;
  last_activity: string;
  avg_response_time: string;
}

const MOCK_EXPERT_ENGAGEMENTS: ExpertEngagement[] = [
  {
    id: 'eng_1',
    expert: {
      id: 'exp_1',
      name: 'Sarah Müller',
      avatar: 'SM',
      headline: 'Senior Tax Specialist',
      rating: 4.9,
      total_reviews: 47,
    },
    mcps: ['CTAX', 'FPA'],
    monthly_rate: 4200,
    status: 'active',
    health_score: 95,
    ai_automation_rate: 92,
    tasks_completed: 156,
    tasks_this_month: 23,
    start_date: '2024-10-01',
    last_activity: '5 min ago',
    avg_response_time: '< 2 hours',
  },
  {
    id: 'eng_2',
    expert: {
      id: 'exp_2',
      name: 'Anna Lehmann',
      avatar: 'AL',
      headline: 'Corporate Lawyer',
      rating: 4.7,
      total_reviews: 28,
    },
    mcps: ['LEGAL'],
    monthly_rate: 4500,
    status: 'active',
    health_score: 88,
    ai_automation_rate: 85,
    tasks_completed: 87,
    tasks_this_month: 12,
    start_date: '2024-11-01',
    last_activity: '1 hour ago',
    avg_response_time: '< 4 hours',
  },
];

const CompanyExpertsView: React.FC = () => {
  const [engagements, setEngagements] = useState<ExpertEngagement[]>(MOCK_EXPERT_ENGAGEMENTS);
  const [selectedEngagement, setSelectedEngagement] = useState<ExpertEngagement | null>(null);

  const totalMonthlySpend = engagements.reduce((sum, eng) => sum + eng.monthly_rate, 0);
  const avgHealthScore = Math.round(engagements.reduce((sum, eng) => sum + eng.health_score, 0) / engagements.length);
  const avgAutomationRate = Math.round(engagements.reduce((sum, eng) => sum + eng.ai_automation_rate, 0) / engagements.length);
  const totalTasksThisMonth = engagements.reduce((sum, eng) => sum + eng.tasks_this_month, 0);

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '28px', fontWeight: 600, marginBottom: '8px' }}>
            My Experts
          </h1>
          <p style={{ color: theme.colors.midGray }}>
            {engagements.filter(e => e.status === 'active').length} active engagements
          </p>
        </div>
        <button
          onClick={() => window.location.href = '/marketplace'}
          style={{
            padding: '12px 24px',
            borderRadius: '100px',
            border: 'none',
            background: theme.colors.orange,
            color: 'white',
            fontFamily: "'Poppins', sans-serif",
            fontSize: '14px',
            fontWeight: 500,
            cursor: 'pointer',
          }}
        >
          + Find More Experts
        </button>
      </div>

      {/* Summary Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' }}>
        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '16px',
          border: `1px solid ${theme.colors.lightGray}`,
        }}>
          <p style={{ fontSize: '12px', color: theme.colors.midGray, marginBottom: '4px' }}>
            Total Monthly Spend
          </p>
          <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, color: theme.colors.green }}>
            €{totalMonthlySpend.toLocaleString()}
          </p>
          <p style={{ fontSize: '11px', color: theme.colors.midGray, marginTop: '4px' }}>
            vs. €{Math.round(totalMonthlySpend * 3.3).toLocaleString()} traditional
          </p>
        </div>

        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '16px',
          border: `1px solid ${theme.colors.lightGray}`,
        }}>
          <p style={{ fontSize: '12px', color: theme.colors.midGray, marginBottom: '4px' }}>
            Avg Health Score
          </p>
          <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, color: avgHealthScore >= 90 ? theme.colors.green : theme.colors.orange }}>
            {avgHealthScore}%
          </p>
          <p style={{ fontSize: '11px', color: theme.colors.midGray, marginTop: '4px' }}>
            All experts performing well
          </p>
        </div>

        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '16px',
          border: `1px solid ${theme.colors.lightGray}`,
        }}>
          <p style={{ fontSize: '12px', color: theme.colors.midGray, marginBottom: '4px' }}>
            AI Automation
          </p>
          <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, color: theme.colors.blue }}>
            {avgAutomationRate}%
          </p>
          <p style={{ fontSize: '11px', color: theme.colors.midGray, marginTop: '4px' }}>
            Platform average
          </p>
        </div>

        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '16px',
          border: `1px solid ${theme.colors.lightGray}`,
        }}>
          <p style={{ fontSize: '12px', color: theme.colors.midGray, marginBottom: '4px' }}>
            Tasks This Month
          </p>
          <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600 }}>
            {totalTasksThisMonth}
          </p>
          <p style={{ fontSize: '11px', color: theme.colors.midGray, marginTop: '4px' }}>
            Across all experts
          </p>
        </div>
      </div>

      {/* Expert Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        {engagements.map(eng => {
          const healthColor = eng.health_score >= 90 ? theme.colors.green :
                             eng.health_score >= 70 ? theme.colors.orange : theme.colors.red;

          return (
            <div
              key={eng.id}
              style={{
                background: 'white',
                borderRadius: '20px',
                padding: '24px',
                border: `1px solid ${theme.colors.lightGray}`,
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 20px 40px rgba(20,20,19,0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
              onClick={() => setSelectedEngagement(eng)}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '12px',
                    background: `linear-gradient(135deg, ${theme.colors.orange}, ${theme.colors.blue})`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '18px',
                    fontFamily: "'Poppins', sans-serif",
                    fontWeight: 600,
                    color: 'white',
                  }}>
                    {eng.expert.avatar}
                  </div>
                  <div>
                    <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '2px' }}>
                      {eng.expert.name}
                    </h3>
                    <p style={{ fontSize: '12px', color: theme.colors.midGray }}>
                      {eng.expert.headline}
                    </p>
                  </div>
                </div>
                <span style={{
                  padding: '4px 10px',
                  borderRadius: '100px',
                  background: `${theme.colors.green}20`,
                  color: theme.colors.green,
                  fontSize: '11px',
                  fontWeight: 600,
                }}>
                  ● Active
                </span>
              </div>

              {/* MCPs */}
              <div style={{ display: 'flex', gap: '6px', marginBottom: '16px', flexWrap: 'wrap' }}>
                {eng.mcps.map(mcpId => {
                  const mcp = MCP_CATALOG[mcpId];
                  return mcp ? (
                    <span key={mcpId} style={{
                      padding: '4px 8px',
                      borderRadius: '6px',
                      background: `${mcp.color}15`,
                      color: mcp.color,
                      fontSize: '11px',
                      fontFamily: "'Poppins', sans-serif",
                      fontWeight: 500,
                    }}>
                      {mcp.icon} {mcp.name}
                    </span>
                  ) : null;
                })}
              </div>

              {/* Stats Grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '12px',
                padding: '16px',
                background: theme.colors.light,
                borderRadius: '12px',
                marginBottom: '16px',
              }}>
                <div>
                  <p style={{ fontSize: '11px', color: theme.colors.midGray, marginBottom: '2px' }}>Health</p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, color: healthColor }}>
                    {eng.health_score}%
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: '11px', color: theme.colors.midGray, marginBottom: '2px' }}>AI Rate</p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, color: theme.colors.blue }}>
                    {eng.ai_automation_rate}%
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: '11px', color: theme.colors.midGray, marginBottom: '2px' }}>Tasks</p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600 }}>
                    {eng.tasks_this_month}
                  </p>
                </div>
              </div>

              {/* Footer */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <p style={{ fontSize: '12px', color: theme.colors.midGray }}>Monthly Rate</p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '18px', fontWeight: 600, color: theme.colors.green }}>
                    €{eng.monthly_rate.toLocaleString()}
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      alert('Message feature coming soon');
                    }}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '100px',
                      border: `1px solid ${theme.colors.lightGray}`,
                      background: 'white',
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    💬
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      window.location.href = `/experts/${eng.expert.id}`;
                    }}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '100px',
                      border: 'none',
                      background: theme.colors.dark,
                      color: 'white',
                      fontSize: '12px',
                      fontWeight: 500,
                      cursor: 'pointer',
                    }}
                  >
                    View Profile
                  </button>
                </div>
              </div>
            </div>
          );
        })}

        {/* Add Expert Card */}
        <div
          onClick={() => window.location.href = '/marketplace'}
          style={{
            background: 'white',
            borderRadius: '20px',
            padding: '24px',
            border: `2px dashed ${theme.colors.lightGray}`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '280px',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = theme.colors.orange;
            e.currentTarget.style.background = `${theme.colors.orange}05`;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = theme.colors.lightGray;
            e.currentTarget.style.background = 'white';
          }}
        >
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '16px',
            background: theme.colors.lightGray,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '32px',
            marginBottom: '16px',
          }}>
            +
          </div>
          <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '4px' }}>
            Find New Expert
          </p>
          <p style={{ fontSize: '13px', color: theme.colors.midGray }}>
            Browse marketplace
          </p>
        </div>
      </div>

      {/* Cost Breakdown */}
      <div style={{
        background: 'white',
        borderRadius: '20px',
        padding: '32px',
        border: `1px solid ${theme.colors.lightGray}`,
        marginBottom: '32px',
      }}>
        <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '20px', fontWeight: 600, marginBottom: '24px' }}>
          Cost Analytics
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '32px' }}>
          {/* By Expert */}
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: theme.colors.midGray, marginBottom: '16px' }}>
              BY EXPERT
            </h3>
            {engagements.map(eng => (
              <div key={eng.id} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px 0',
                borderBottom: `1px solid ${theme.colors.lightGray}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    background: `linear-gradient(135deg, ${theme.colors.orange}, ${theme.colors.blue})`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px',
                    fontFamily: "'Poppins', sans-serif",
                    fontWeight: 600,
                    color: 'white',
                  }}>
                    {eng.expert.avatar}
                  </div>
                  <div>
                    <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '14px', fontWeight: 500 }}>
                      {eng.expert.name}
                    </p>
                    <p style={{ fontSize: '12px', color: theme.colors.midGray }}>
                      {eng.mcps.map(m => MCP_CATALOG[m]?.name).join(' + ')}
                    </p>
                  </div>
                </div>
                <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, color: theme.colors.green }}>
                  €{eng.monthly_rate.toLocaleString()}
                </p>
              </div>
            ))}
          </div>

          {/* By MCP */}
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: theme.colors.midGray, marginBottom: '16px' }}>
              BY MCP
            </h3>
            {Object.entries(
              engagements.reduce((acc, eng) => {
                eng.mcps.forEach(mcp => {
                  acc[mcp] = (acc[mcp] || 0) + eng.monthly_rate / eng.mcps.length;
                });
                return acc;
              }, {} as Record<string, number>)
            ).map(([mcpId, cost]) => {
              const mcp = MCP_CATALOG[mcpId];
              return mcp ? (
                <div key={mcpId} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px',
                  marginBottom: '8px',
                  background: `${mcp.color}05`,
                  borderRadius: '12px',
                }}>
                  <span style={{ fontSize: '14px', fontFamily: "'Poppins', sans-serif", fontWeight: 500 }}>
                    {mcp.icon} {mcp.name}
                  </span>
                  <span style={{ fontSize: '14px', fontWeight: 600 }}>
                    €{Math.round(cost).toLocaleString()}
                  </span>
                </div>
              ) : null;
            })}

            <div style={{
              padding: '16px',
              marginTop: '16px',
              background: `${theme.colors.green}10`,
              borderRadius: '12px',
            }}>
              <p style={{ fontSize: '11px', color: theme.colors.midGray, marginBottom: '4px' }}>
                💰 Cost Savings
              </p>
              <p style={{ fontSize: '18px', fontWeight: 600, color: theme.colors.green }}>
                €{Math.round(totalMonthlySpend * 2.3).toLocaleString()}/month
              </p>
              <p style={{ fontSize: '11px', color: theme.colors.midGray }}>
                vs. traditional consultants (70% savings)
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ROI Insights */}
      <div style={{
        background: theme.colors.dark,
        color: theme.colors.light,
        borderRadius: '20px',
        padding: '32px',
      }}>
        <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '20px', fontWeight: 600, marginBottom: '24px' }}>
          AI Insights
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{
            padding: '16px',
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '12px',
            borderLeft: `4px solid ${theme.colors.green}`,
          }}>
            <p style={{ fontSize: '14px', marginBottom: '4px' }}>
              💡 <strong>Optimization Opportunity</strong>
            </p>
            <p style={{ fontSize: '13px', color: theme.colors.midGray }}>
              Sarah's automation rate is 92% on CTAX. Consider expanding her scope to include tax optimization tasks.
            </p>
          </div>

          <div style={{
            padding: '16px',
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '12px',
            borderLeft: `4px solid ${theme.colors.blue}`,
          }}>
            <p style={{ fontSize: '14px', marginBottom: '4px' }}>
              📊 <strong>Performance Insight</strong>
            </p>
            <p style={{ fontSize: '13px', color: theme.colors.midGray }}>
              Your team completed {totalTasksThisMonth} tasks this month, saving approximately 420 hours compared to traditional processes.
            </p>
          </div>

          <div style={{
            padding: '16px',
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '12px',
            borderLeft: `4px solid ${theme.colors.orange}`,
          }}>
            <p style={{ fontSize: '14px', marginBottom: '4px' }}>
              ⚡ <strong>Capacity Recommendation</strong>
            </p>
            <p style={{ fontSize: '13px', color: theme.colors.midGray }}>
              Based on your growth trajectory, consider adding an FPA expert in Q1 2026 to handle increased forecasting needs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyExpertsView;
