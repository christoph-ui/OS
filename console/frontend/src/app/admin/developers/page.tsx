'use client';

import { useState, useEffect } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import { UserCheck, CheckCircle, XCircle, Mail, Package } from 'lucide-react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
  red: '#d75757',
};

interface Developer {
  id: string;
  company_name: string;
  contact_name: string;
  contact_email: string;
  website: string;
  status: 'pending' | 'verified' | 'rejected';
  created_at: string;
  total_mcps: number;
}

export default function DeveloperVerificationPage() {
  const [developers, setDevelopers] = useState<Developer[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDev, setSelectedDev] = useState<Developer | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadPendingDevelopers();
  }, []);

  const loadPendingDevelopers = async () => {
    try {
      const token = localStorage.getItem('0711_admin_token');

      const response = await fetch('http://localhost:4080/api/admin/mcp-developers/pending', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setDevelopers(data.developers || []);
      }
    } catch (error) {
      console.error('Error loading developers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (devId: string) => {
    setActionLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('0711_admin_token');

      const response = await fetch(`http://localhost:4080/api/admin/mcp-developers/${devId}/verify`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to verify developer');

      setSuccess('Developer verified successfully!');
      setShowDetailModal(false);
      loadPendingDevelopers();

      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to verify developer');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (devId: string, reason: string) => {
    setActionLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('0711_admin_token');

      const response = await fetch(`http://localhost:4080/api/admin/mcp-developers/${devId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason }),
      });

      if (!response.ok) throw new Error('Failed to reject developer');

      setSuccess('Developer application rejected');
      setShowDetailModal(false);
      loadPendingDevelopers();

      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject developer');
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
            <div>Loading developers...</div>
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
            Developer Verification
          </h1>
          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: 0,
          }}>
            {developers.length} pending developer{developers.length !== 1 ? 's' : ''} awaiting verification
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

        {/* Developers List */}
        {developers.length > 0 ? (
          <div style={{
            display: 'grid',
            gap: 20,
          }}>
            {developers.map((dev) => (
              <div
                key={dev.id}
                style={{
                  padding: 24,
                  backgroundColor: '#fff',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 16,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <h3 style={{
                      fontFamily: "'Poppins', Arial, sans-serif",
                      fontSize: 20,
                      fontWeight: 600,
                      margin: '0 0 8px',
                      color: colors.dark,
                    }}>
                      {dev.company_name}
                    </h3>

                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      marginBottom: 16,
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 14, color: colors.midGray }}>
                        <Mail size={14} />
                        {dev.contact_email}
                      </div>

                      {dev.website && (
                        <a
                          href={dev.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ fontSize: 14, color: colors.blue, textDecoration: 'none' }}
                        >
                          {dev.website}
                        </a>
                      )}
                    </div>

                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      fontSize: 13,
                      color: colors.midGray,
                    }}>
                      <div>
                        Contact: {dev.contact_name}
                      </div>
                      <div>•</div>
                      <div>
                        Registered: {new Date(dev.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 12 }}>
                    <button
                      onClick={() => {
                        const reason = prompt('Reason for rejection (will be sent to developer):');
                        if (reason) handleReject(dev.id, reason);
                      }}
                      disabled={actionLoading}
                      style={{
                        padding: '10px 20px',
                        backgroundColor: `${colors.red}15`,
                        color: colors.red,
                        border: 'none',
                        borderRadius: 8,
                        fontSize: 14,
                        fontWeight: 600,
                        cursor: actionLoading ? 'not-allowed' : 'pointer',
                        fontFamily: "'Poppins', Arial, sans-serif",
                      }}
                    >
                      Reject
                    </button>

                    <button
                      onClick={() => handleVerify(dev.id)}
                      disabled={actionLoading}
                      style={{
                        padding: '10px 20px',
                        backgroundColor: colors.green,
                        color: '#fff',
                        border: 'none',
                        borderRadius: 8,
                        fontSize: 14,
                        fontWeight: 600,
                        cursor: actionLoading ? 'not-allowed' : 'pointer',
                        fontFamily: "'Poppins', Arial, sans-serif",
                      }}
                    >
                      {actionLoading ? 'Processing...' : 'Verify'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{
            padding: 60,
            textAlign: 'center',
            backgroundColor: '#fff',
            borderRadius: 16,
            border: `1.5px dashed ${colors.lightGray}`,
          }}>
            <UserCheck size={48} color={colors.midGray} style={{ margin: '0 auto 16px' }} />
            <p style={{ fontSize: 15, color: colors.midGray, margin: 0 }}>
              No pending developers to verify
            </p>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
