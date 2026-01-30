'use client';

import { useState, useEffect } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import { Package, CheckCircle, XCircle, Clock, ExternalLink } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
  red: '#d75757',
};

interface MCP {
  id: string;
  name: string;
  display_name: string;
  description: string;
  developer_id: string | null;
  developer_name: string;
  category: string;
  pricing_model: string;
  status: 'pending' | 'approved' | 'rejected';
  submitted_at: string;
  api_docs_url: string;
}

export default function MCPApprovalPage() {
  const [mcps, setMcps] = useState<MCP[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMcp, setSelectedMcp] = useState<MCP | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadPendingMCPs();
  }, []);

  const loadPendingMCPs = async () => {
    try {
      const token = localStorage.getItem('0711_admin_token');

      const response = await fetch('http://localhost:4080/api/admin/mcps/pending', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setMcps(data.mcps || []);
      }
    } catch (error) {
      console.error('Error loading MCPs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (mcpId: string) => {
    setActionLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('0711_admin_token');

      const response = await fetch(`http://localhost:4080/api/admin/mcps/${mcpId}/approve`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to approve MCP');

      setSuccess('MCP approved successfully!');
      setShowDetailModal(false);
      loadPendingMCPs();

      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve MCP');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (mcpId: string, reason: string) => {
    setActionLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('0711_admin_token');

      const response = await fetch(`http://localhost:4080/api/admin/mcps/${mcpId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason }),
      });

      if (!response.ok) throw new Error('Failed to reject MCP');

      setSuccess('MCP rejected');
      setShowDetailModal(false);
      loadPendingMCPs();

      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject MCP');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
        }}>
          <div style={{ textAlign: 'center', color: colors.midGray }}>
            <div style={{ fontSize: 32, marginBottom: 16 }}>⟳</div>
            <div>Loading MCPs...</div>
          </div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div style={{ padding: 40 }}>
        {/* Header */}
        <header style={{ marginBottom: 32 }}>
          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 32,
            fontWeight: 600,
            margin: '0 0 8px',
            color: colors.dark,
          }}>
            MCP Approval Queue
          </h1>
          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: 0,
          }}>
            {mcps.length} pending MCP{mcps.length !== 1 ? 's' : ''} awaiting review
          </p>
        </header>

        {/* Alerts */}
        {error && (
          <div style={{
            padding: '12px 16px',
            marginBottom: 24,
            backgroundColor: '#fee',
            border: '1px solid #fcc',
            borderRadius: 8,
            color: '#c00',
            fontSize: 14,
          }}>
            {error}
          </div>
        )}

        {success && (
          <div style={{
            padding: '12px 16px',
            marginBottom: 24,
            backgroundColor: '#efe',
            border: `1px solid ${colors.green}`,
            borderRadius: 8,
            color: colors.green,
            fontSize: 14,
          }}>
            {success}
          </div>
        )}

        {/* MCPs List */}
        {mcps.length > 0 ? (
          <div style={{
            backgroundColor: '#fff',
            borderRadius: 16,
            border: `1.5px solid ${colors.lightGray}`,
            overflow: 'hidden',
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: colors.lightGray }}>
                  <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                    MCP
                  </th>
                  <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                    Developer
                  </th>
                  <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                    Category
                  </th>
                  <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                    Pricing
                  </th>
                  <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                    Submitted
                  </th>
                  <th style={{ padding: '16px 24px', textAlign: 'right', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {mcps.map((mcp, idx) => (
                  <tr
                    key={mcp.id}
                    style={{
                      borderBottom: idx < mcps.length - 1 ? `1px solid ${colors.lightGray}` : 'none',
                    }}
                  >
                    <td style={{ padding: '16px 24px' }}>
                      <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500, marginBottom: 4 }}>
                        {mcp.display_name}
                      </div>
                      <div style={{ fontSize: 12, color: colors.midGray }}>
                        {mcp.description.substring(0, 60)}...
                      </div>
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <div style={{ fontSize: 13, color: colors.midGray }}>
                        {mcp.developer_name || 'First-party'}
                      </div>
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <span style={{
                        padding: '4px 10px',
                        backgroundColor: `${colors.blue}15`,
                        color: colors.blue,
                        borderRadius: 6,
                        fontSize: 12,
                        fontWeight: 600,
                      }}>
                        {mcp.category}
                      </span>
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <div style={{ fontSize: 13, color: colors.midGray }}>
                        {mcp.pricing_model}
                      </div>
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <div style={{ fontSize: 13, color: colors.midGray }}>
                        {new Date(mcp.submitted_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td style={{ padding: '16px 24px', textAlign: 'right' }}>
                      <button
                        onClick={() => {
                          setSelectedMcp(mcp);
                          setShowDetailModal(true);
                        }}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: colors.orange,
                          color: '#fff',
                          border: 'none',
                          borderRadius: 6,
                          fontSize: 13,
                          fontWeight: 600,
                          cursor: 'pointer',
                          fontFamily: "'Poppins', Arial, sans-serif",
                        }}
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{
            padding: 60,
            textAlign: 'center',
            backgroundColor: '#fff',
            borderRadius: 16,
            border: `1.5px dashed ${colors.lightGray}`,
          }}>
            <Package size={48} color={colors.midGray} style={{ margin: '0 auto 16px' }} />
            <p style={{ fontSize: 15, color: colors.midGray, margin: 0 }}>
              No pending MCPs to review
            </p>
          </div>
        )}

        {/* Detail Modal */}
        {showDetailModal && selectedMcp && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(20, 20, 19, 0.8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
              padding: 20,
            }}
            onClick={() => setShowDetailModal(false)}
          >
            <div
              style={{
                backgroundColor: colors.light,
                borderRadius: 16,
                maxWidth: 700,
                width: '100%',
                padding: 40,
                maxHeight: '90vh',
                overflowY: 'auto',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <h2 style={{
                fontFamily: "'Poppins', Arial, sans-serif",
                fontSize: 28,
                fontWeight: 600,
                margin: '0 0 24px',
                color: colors.dark,
              }}>
                {selectedMcp.display_name}
              </h2>

              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 13, color: colors.midGray, marginBottom: 8 }}>
                  Description
                </div>
                <div style={{ fontSize: 15, color: colors.dark, lineHeight: 1.6 }}>
                  {selectedMcp.description}
                </div>
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 20,
                marginBottom: 24,
                padding: 20,
                backgroundColor: '#fff',
                borderRadius: 12,
              }}>
                <div>
                  <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                    Developer
                  </div>
                  <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                    {selectedMcp.developer_name || 'First-party'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                    Category
                  </div>
                  <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                    {selectedMcp.category}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                    Pricing Model
                  </div>
                  <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                    {selectedMcp.pricing_model}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                    Submitted
                  </div>
                  <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                    {new Date(selectedMcp.submitted_at).toLocaleDateString()}
                  </div>
                </div>
              </div>

              {selectedMcp.api_docs_url && (
                <a
                  href={selectedMcp.api_docs_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '10px 16px',
                    marginBottom: 32,
                    backgroundColor: colors.lightGray,
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 14,
                    color: colors.dark,
                    textDecoration: 'none',
                    cursor: 'pointer',
                  }}
                >
                  <ExternalLink size={16} />
                  View Documentation
                </a>
              )}

              {/* Actions */}
              <div style={{
                display: 'flex',
                gap: 12,
                justifyContent: 'flex-end',
                paddingTop: 24,
                borderTop: `1px solid ${colors.lightGray}`,
              }}>
                <button
                  onClick={() => setShowDetailModal(false)}
                  disabled={actionLoading}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: colors.lightGray,
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 15,
                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                    fontFamily: "'Poppins', Arial, sans-serif",
                  }}
                >
                  Cancel
                </button>

                <button
                  onClick={() => {
                    const reason = prompt('Reason for rejection (will be sent to developer):');
                    if (reason) handleReject(selectedMcp.id, reason);
                  }}
                  disabled={actionLoading}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: colors.red,
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 15,
                    fontWeight: 600,
                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                    fontFamily: "'Poppins', Arial, sans-serif",
                  }}
                >
                  Reject
                </button>

                <button
                  onClick={() => handleApprove(selectedMcp.id)}
                  disabled={actionLoading}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: colors.green,
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 15,
                    fontWeight: 600,
                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                    fontFamily: "'Poppins', Arial, sans-serif",
                  }}
                >
                  {actionLoading ? 'Processing...' : 'Approve'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
