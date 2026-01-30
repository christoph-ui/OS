'use client';

import React, { useState, useEffect } from 'react';

// ============================================================================
// ADMIN - EXPERT APPLICATION REVIEW INTERFACE
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
  CTAX: { name: 'German Tax', icon: '📊', color: theme.colors.orange },
  FPA: { name: 'FP&A', icon: '📈', color: theme.colors.blue },
  LEGAL: { name: 'Legal', icon: '⚖️', color: theme.colors.dark },
  ETIM: { name: 'Product Class', icon: '🏷️', color: '#5ab5b5' },
};

interface Application {
  id: string;
  email: string;
  name: string;
  headline: string;
  mcps: string[];
  years_experience: number;
  status: 'submitted' | 'under_review' | 'approved' | 'rejected';
  submitted_at: string;
  reviewed_at?: string;
  application_data: any;
}

const MOCK_APPLICATIONS: Application[] = [
  {
    id: 'app_1',
    email: 'sarah.mueller@example.com',
    name: 'Sarah Müller',
    headline: 'Senior Tax Specialist | 12+ years',
    mcps: ['CTAX', 'FPA', 'LEGAL'],
    years_experience: 12,
    status: 'submitted',
    submitted_at: '2025-11-29T10:30:00Z',
    application_data: {
      first_name: 'Sarah',
      last_name: 'Müller',
      languages: ['German', 'English'],
      industries: ['Tech/SaaS', 'Manufacturing'],
      tools_proficiency: ['DATEV', 'SAP', 'Excel'],
      max_clients: 10,
      weekly_availability: 20,
    },
  },
  {
    id: 'app_2',
    email: 'michael.koch@example.com',
    name: 'Michael Koch',
    headline: 'FP&A Expert | Ex-McKinsey',
    mcps: ['FPA', 'CTAX'],
    years_experience: 10,
    status: 'under_review',
    submitted_at: '2025-11-28T14:20:00Z',
    application_data: {
      first_name: 'Michael',
      last_name: 'Koch',
      languages: ['German', 'English', 'French'],
      industries: ['Tech/SaaS', 'Finance'],
      tools_proficiency: ['Excel', 'Power BI', 'SQL'],
      max_clients: 8,
      weekly_availability: 25,
    },
  },
];

const ExpertApplicationReview: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>(MOCK_APPLICATIONS);
  const [selectedApp, setSelectedApp] = useState<Application | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const filteredApps = applications.filter(app =>
    filterStatus === 'all' || app.status === filterStatus
  );

  const handleApprove = async (appId: string) => {
    if (!confirm('Approve this expert application?')) return;

    // TODO: Call API
    const response = await fetch(`/api/experts/admin/applications/${appId}/approve`, {
      method: 'PUT',
    });

    if (response.ok) {
      setApplications(apps =>
        apps.map(app => app.id === appId ? { ...app, status: 'approved' as const, reviewed_at: new Date().toISOString() } : app)
      );
      setSelectedApp(null);
      alert('Expert approved! Welcome email sent.');
    }
  };

  const handleReject = async (appId: string) => {
    const reason = prompt('Rejection reason (will be sent to applicant):');
    if (!reason) return;

    // TODO: Call API
    const response = await fetch(`/api/experts/admin/applications/${appId}/reject`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason })
    });

    if (response.ok) {
      setApplications(apps =>
        apps.map(app => app.id === appId ? { ...app, status: 'rejected' as const, reviewed_at: new Date().toISOString() } : app)
      );
      setSelectedApp(null);
      alert('Application rejected.');
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: theme.colors.light, padding: '40px' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '32px', fontWeight: 600, marginBottom: '8px' }}>
            Expert Applications
          </h1>
          <p style={{ color: theme.colors.midGray }}>
            {applications.filter(a => a.status === 'submitted').length} pending review
          </p>
        </div>

        {/* Filter Tabs */}
        <div style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '24px',
          padding: '8px',
          background: 'white',
          borderRadius: '12px',
          width: 'fit-content',
        }}>
          {[
            { id: 'all', label: 'All' },
            { id: 'submitted', label: 'Pending' },
            { id: 'under_review', label: 'Under Review' },
            { id: 'approved', label: 'Approved' },
            { id: 'rejected', label: 'Rejected' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setFilterStatus(tab.id)}
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                background: filterStatus === tab.id ? theme.colors.orange : 'transparent',
                color: filterStatus === tab.id ? 'white' : theme.colors.dark,
                fontFamily: "'Poppins', sans-serif",
                fontSize: '13px',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              {tab.label}
              <span style={{
                marginLeft: '8px',
                padding: '2px 8px',
                borderRadius: '100px',
                background: filterStatus === tab.id ? 'rgba(255,255,255,0.2)' : theme.colors.lightGray,
                fontSize: '11px',
              }}>
                {applications.filter(a => tab.id === 'all' || a.status === tab.id).length}
              </span>
            </button>
          ))}
        </div>

        {/* Applications Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: selectedApp ? '400px 1fr' : '1fr', gap: '24px' }}>
          {/* List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filteredApps.map(app => (
              <div
                key={app.id}
                onClick={() => setSelectedApp(app)}
                style={{
                  background: 'white',
                  padding: '20px',
                  borderRadius: '16px',
                  border: selectedApp?.id === app.id ? `2px solid ${theme.colors.orange}` : `1px solid ${theme.colors.lightGray}`,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '4px' }}>
                      {app.name}
                    </h3>
                    <p style={{ fontSize: '13px', color: theme.colors.midGray }}>
                      {app.headline}
                    </p>
                  </div>
                  <span style={{
                    padding: '4px 10px',
                    borderRadius: '100px',
                    background: app.status === 'submitted' ? `${theme.colors.orange}20` :
                                app.status === 'approved' ? `${theme.colors.green}20` :
                                app.status === 'rejected' ? `${theme.colors.red}20` :
                                `${theme.colors.blue}20`,
                    color: app.status === 'submitted' ? theme.colors.orange :
                           app.status === 'approved' ? theme.colors.green :
                           app.status === 'rejected' ? theme.colors.red :
                           theme.colors.blue,
                    fontSize: '11px',
                    fontWeight: 600,
                    textTransform: 'capitalize',
                  }}>
                    {app.status.replace('_', ' ')}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '6px', marginBottom: '12px', flexWrap: 'wrap' }}>
                  {app.mcps.map(mcp => {
                    const mcpInfo = MCP_CATALOG[mcp];
                    return mcpInfo ? (
                      <span key={mcp} style={{
                        padding: '4px 8px',
                        borderRadius: '6px',
                        background: `${mcpInfo.color}15`,
                        color: mcpInfo.color,
                        fontSize: '11px',
                        fontFamily: "'Poppins', sans-serif",
                        fontWeight: 500,
                      }}>
                        {mcpInfo.icon} {mcpInfo.name}
                      </span>
                    ) : null;
                  })}
                </div>

                <div style={{ fontSize: '12px', color: theme.colors.midGray }}>
                  <span>{app.years_experience} years exp</span>
                  <span style={{ margin: '0 8px' }}>·</span>
                  <span>Submitted {new Date(app.submitted_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}

            {filteredApps.length === 0 && (
              <div style={{
                background: 'white',
                padding: '60px',
                borderRadius: '16px',
                textAlign: 'center',
              }}>
                <p style={{ fontSize: '48px', marginBottom: '12px' }}>✓</p>
                <p style={{ color: theme.colors.midGray }}>No applications in this category</p>
              </div>
            )}
          </div>

          {/* Detail View */}
          {selectedApp && (
            <div style={{
              background: 'white',
              borderRadius: '20px',
              padding: '32px',
              border: `1px solid ${theme.colors.lightGray}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
                <div>
                  <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, marginBottom: '4px' }}>
                    {selectedApp.name}
                  </h2>
                  <p style={{ color: theme.colors.midGray }}>
                    {selectedApp.email}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedApp(null)}
                  style={{
                    background: 'none',
                    border: 'none',
                    fontSize: '24px',
                    cursor: 'pointer',
                    color: theme.colors.midGray,
                  }}
                >
                  ×
                </button>
              </div>

              {/* Application Details */}
              <div style={{ marginBottom: '24px' }}>
                <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: theme.colors.midGray }}>
                  BASIC INFORMATION
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '12px', fontSize: '14px' }}>
                  <span style={{ color: theme.colors.midGray }}>Headline:</span>
                  <span>{selectedApp.headline}</span>

                  <span style={{ color: theme.colors.midGray }}>Experience:</span>
                  <span>{selectedApp.years_experience} years</span>

                  <span style={{ color: theme.colors.midGray }}>Languages:</span>
                  <span>{selectedApp.application_data.languages?.join(', ')}</span>

                  <span style={{ color: theme.colors.midGray }}>Industries:</span>
                  <span>{selectedApp.application_data.industries?.join(', ')}</span>

                  <span style={{ color: theme.colors.midGray }}>Tools:</span>
                  <span>{selectedApp.application_data.tools_proficiency?.join(', ')}</span>
                </div>
              </div>

              <div style={{ marginBottom: '24px' }}>
                <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: theme.colors.midGray }}>
                  MCP EXPERTISE
                </h3>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {selectedApp.mcps.map(mcp => {
                    const mcpInfo = MCP_CATALOG[mcp];
                    return mcpInfo ? (
                      <span key={mcp} style={{
                        padding: '8px 14px',
                        borderRadius: '8px',
                        background: `${mcpInfo.color}15`,
                        color: mcpInfo.color,
                        fontSize: '13px',
                        fontFamily: "'Poppins', sans-serif",
                        fontWeight: 500,
                      }}>
                        {mcpInfo.icon} {mcpInfo.name}
                      </span>
                    ) : null;
                  })}
                </div>
              </div>

              <div style={{ marginBottom: '24px' }}>
                <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: theme.colors.midGray }}>
                  AVAILABILITY
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '12px', fontSize: '14px' }}>
                  <span style={{ color: theme.colors.midGray }}>Max Clients:</span>
                  <span>{selectedApp.application_data.max_clients}</span>

                  <span style={{ color: theme.colors.midGray }}>Weekly Hours:</span>
                  <span>{selectedApp.application_data.weekly_availability} hours/week</span>
                </div>
              </div>

              <div style={{ marginBottom: '32px' }}>
                <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: theme.colors.midGray }}>
                  VERIFICATION CHECKLIST
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input type="checkbox" defaultChecked />
                    <span style={{ fontSize: '14px' }}>Email verified</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input type="checkbox" />
                    <span style={{ fontSize: '14px' }}>ID document verified</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input type="checkbox" />
                    <span style={{ fontSize: '14px' }}>Certifications verified</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input type="checkbox" />
                    <span style={{ fontSize: '14px' }}>Background check (optional)</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input type="checkbox" />
                    <span style={{ fontSize: '14px' }}>Banking details valid</span>
                  </label>
                </div>
              </div>

              {/* Actions */}
              {selectedApp.status === 'submitted' || selectedApp.status === 'under_review' ? (
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button
                    onClick={() => handleApprove(selectedApp.id)}
                    style={{
                      flex: 1,
                      padding: '14px',
                      borderRadius: '100px',
                      border: 'none',
                      background: theme.colors.green,
                      color: 'white',
                      fontFamily: "'Poppins', sans-serif",
                      fontSize: '14px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    ✓ Approve Expert
                  </button>
                  <button
                    onClick={() => handleReject(selectedApp.id)}
                    style={{
                      flex: 1,
                      padding: '14px',
                      borderRadius: '100px',
                      border: `1.5px solid ${theme.colors.red}`,
                      background: 'transparent',
                      color: theme.colors.red,
                      fontFamily: "'Poppins', sans-serif",
                      fontSize: '14px',
                      fontWeight: 500,
                      cursor: 'pointer',
                    }}
                  >
                    × Reject
                  </button>
                </div>
              ) : (
                <div style={{
                  padding: '16px',
                  borderRadius: '12px',
                  background: theme.colors.lightGray,
                  textAlign: 'center',
                  fontSize: '14px',
                  color: theme.colors.midGray,
                }}>
                  Application {selectedApp.status}
                  {selectedApp.reviewed_at && ` on ${new Date(selectedApp.reviewed_at).toLocaleDateString()}`}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExpertApplicationReview;
