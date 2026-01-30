'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Users, UserPlus, Edit2, Trash2, Mail, CheckCircle, XCircle, Clock, Shield } from 'lucide-react';

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

interface TeamMember {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  status: string;
  permissions: Record<string, boolean>;
  last_login_at: string | null;
  created_at: string;
  invited_by_id: string | null;
  invited_at: string | null;
}

export default function TeamManagementPage() {
  const router = useRouter();
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Invite form state
  const [inviteForm, setInviteForm] = useState({
    email: '',
    first_name: '',
    last_name: '',
    role: 'customer_user',
    permissions: {
      'data.view': true,
      'data.edit': false,
      'billing.view': false,
      'users.invite': false,
    },
  });

  useEffect(() => {
    loadTeamMembers();
  }, []);

  const loadTeamMembers = async () => {
    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4080/api/users/?page=1&page_size=50', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to load team members');

      const data = await response.json();
      setMembers(data.users || []);
    } catch (error) {
      console.error('Error loading team members:', error);
      setError('Failed to load team members');
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4080/api/users/invite', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(inviteForm),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send invitation');
      }

      setSuccess(`Invitation sent to ${inviteForm.email}`);
      setShowInviteModal(false);
      setInviteForm({
        email: '',
        first_name: '',
        last_name: '',
        role: 'customer_user',
        permissions: {
          'data.view': true,
          'data.edit': false,
          'billing.view': false,
          'users.invite': false,
        },
      });
      loadTeamMembers();

      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to send invitation');
    }
  };

  const handleUpdateMember = async () => {
    if (!selectedMember) return;

    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch(`http://localhost:4080/api/users/${selectedMember.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          role: selectedMember.role,
          permissions: selectedMember.permissions,
        }),
      });

      if (!response.ok) throw new Error('Failed to update member');

      setSuccess(`Updated ${selectedMember.first_name} ${selectedMember.last_name}`);
      setShowEditModal(false);
      setSelectedMember(null);
      loadTeamMembers();

      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update member');
    }
  };

  const handleDeleteMember = async () => {
    if (!selectedMember) return;

    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch(`http://localhost:4080/api/users/${selectedMember.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to remove member');

      setSuccess(`Removed ${selectedMember.first_name} ${selectedMember.last_name}`);
      setShowDeleteModal(false);
      setSelectedMember(null);
      loadTeamMembers();

      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to remove member');
    }
  };

  const getRoleBadge = (role: string) => {
    const roleConfig = {
      platform_admin: { label: 'Platform Admin', color: colors.red },
      partner_admin: { label: 'Partner Admin', color: colors.blue },
      customer_admin: { label: 'Admin', color: colors.orange },
      customer_user: { label: 'User', color: colors.green },
    }[role] || { label: role, color: colors.midGray };

    return (
      <span style={{
        padding: '4px 12px',
        backgroundColor: `${roleConfig.color}15`,
        color: roleConfig.color,
        borderRadius: 6,
        fontSize: 12,
        fontWeight: 600,
      }}>
        {roleConfig.label}
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: { icon: CheckCircle, label: 'Active', color: colors.green },
      invited: { icon: Clock, label: 'Invited', color: colors.orange },
      suspended: { icon: XCircle, label: 'Suspended', color: colors.red },
      inactive: { icon: XCircle, label: 'Inactive', color: colors.midGray },
    }[status] || { icon: Clock, label: status, color: colors.midGray };

    const Icon = statusConfig.icon;

    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <Icon size={14} color={statusConfig.color} />
        <span style={{ fontSize: 13, color: statusConfig.color }}>
          {statusConfig.label}
        </span>
      </div>
    );
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: colors.light,
      }}>
        <div style={{ textAlign: 'center', color: colors.midGray }}>
          <div style={{ fontSize: 32, marginBottom: 16 }}>⟳</div>
          <div>Loading team members...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: colors.light,
      fontFamily: "'Lora', Georgia, serif",
    }}>
      {/* Header */}
      <header style={{
        backgroundColor: '#fff',
        borderBottom: `1.5px solid ${colors.lightGray}`,
        padding: '24px 40px',
      }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          <button
            onClick={() => router.push('/settings')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 16px',
              marginBottom: 16,
              backgroundColor: colors.lightGray,
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              color: colors.dark,
              cursor: 'pointer',
              fontFamily: "'Lora', Georgia, serif",
            }}
          >
            ← Back to Settings
          </button>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 style={{
                fontFamily: "'Poppins', Arial, sans-serif",
                fontSize: 32,
                fontWeight: 600,
                margin: '0 0 8px',
                color: colors.dark,
              }}>
                Team Management
              </h1>
              <p style={{
                fontSize: 15,
                color: colors.midGray,
                margin: 0,
              }}>
                {members.length} team {members.length === 1 ? 'member' : 'members'}
              </p>
            </div>

            <button
              onClick={() => setShowInviteModal(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '12px 24px',
                backgroundColor: colors.orange,
                color: '#fff',
                border: 'none',
                borderRadius: 10,
                fontSize: 15,
                fontWeight: 600,
                cursor: 'pointer',
                fontFamily: "'Poppins', Arial, sans-serif",
                boxShadow: `0 4px 12px ${colors.orange}40`,
              }}
            >
              <UserPlus size={18} />
              Invite Member
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main style={{ maxWidth: 1400, margin: '0 auto', padding: 40 }}>
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

        {/* Team Members Table */}
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
                  Name
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Email
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Role
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Status
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Last Login
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'right', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {members.map((member, idx) => (
                <tr
                  key={member.id}
                  style={{
                    borderBottom: idx < members.length - 1 ? `1px solid ${colors.lightGray}` : 'none',
                  }}
                >
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                      {member.first_name} {member.last_name}
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ fontSize: 13, color: colors.midGray }}>
                      {member.email}
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    {getRoleBadge(member.role)}
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    {getStatusBadge(member.status)}
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ fontSize: 13, color: colors.midGray }}>
                      {member.last_login_at
                        ? new Date(member.last_login_at).toLocaleDateString()
                        : 'Never'}
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px', textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                      <button
                        onClick={() => {
                          setSelectedMember(member);
                          setShowEditModal(true);
                        }}
                        style={{
                          padding: '8px 12px',
                          backgroundColor: colors.lightGray,
                          border: 'none',
                          borderRadius: 6,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                        title="Edit member"
                      >
                        <Edit2 size={14} color={colors.dark} />
                      </button>

                      {member.status !== 'invited' && (
                        <button
                          onClick={() => {
                            setSelectedMember(member);
                            setShowDeleteModal(true);
                          }}
                          style={{
                            padding: '8px 12px',
                            backgroundColor: `${colors.red}15`,
                            border: 'none',
                            borderRadius: 6,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                          }}
                          title="Remove member"
                        >
                          <Trash2 size={14} color={colors.red} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>

      {/* Invite Modal */}
      {showInviteModal && (
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
          onClick={() => setShowInviteModal(false)}
        >
          <div
            style={{
              backgroundColor: colors.light,
              borderRadius: 16,
              maxWidth: 500,
              width: '100%',
              padding: 32,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 24,
              fontWeight: 600,
              margin: '0 0 24px',
              color: colors.dark,
            }}>
              Invite Team Member
            </h2>

            <form onSubmit={handleInvite}>
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 8, color: colors.dark }}>
                  Email
                </label>
                <input
                  type="email"
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 15,
                    outline: 'none',
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 8, color: colors.dark }}>
                    First Name
                  </label>
                  <input
                    type="text"
                    value={inviteForm.first_name}
                    onChange={(e) => setInviteForm({ ...inviteForm, first_name: e.target.value })}
                    required
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      border: `1.5px solid ${colors.lightGray}`,
                      borderRadius: 8,
                      fontSize: 15,
                      outline: 'none',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 8, color: colors.dark }}>
                    Last Name
                  </label>
                  <input
                    type="text"
                    value={inviteForm.last_name}
                    onChange={(e) => setInviteForm({ ...inviteForm, last_name: e.target.value })}
                    required
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      border: `1.5px solid ${colors.lightGray}`,
                      borderRadius: 8,
                      fontSize: 15,
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 8, color: colors.dark }}>
                  Role
                </label>
                <select
                  value={inviteForm.role}
                  onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 15,
                    outline: 'none',
                    backgroundColor: '#fff',
                  }}
                >
                  <option value="customer_user">User</option>
                  <option value="customer_admin">Admin</option>
                </select>
              </div>

              <div style={{ marginBottom: 24 }}>
                <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 12, color: colors.dark }}>
                  Permissions
                </label>
                {Object.entries(inviteForm.permissions).map(([key, value]) => (
                  <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={(e) => setInviteForm({
                        ...inviteForm,
                        permissions: { ...inviteForm.permissions, [key]: e.target.checked }
                      })}
                      style={{ cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: 14, color: colors.dark }}>
                      {key.replace('.', ' ').replace(/_/g, ' ')}
                    </span>
                  </label>
                ))}
              </div>

              <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: colors.lightGray,
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 15,
                    cursor: 'pointer',
                    fontFamily: "'Poppins', Arial, sans-serif",
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{
                    padding: '12px 24px',
                    backgroundColor: colors.orange,
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 15,
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontFamily: "'Poppins', Arial, sans-serif",
                  }}
                >
                  Send Invitation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedMember && (
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
          onClick={() => {
            setShowEditModal(false);
            setSelectedMember(null);
          }}
        >
          <div
            style={{
              backgroundColor: colors.light,
              borderRadius: 16,
              maxWidth: 500,
              width: '100%',
              padding: 32,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 24,
              fontWeight: 600,
              margin: '0 0 24px',
              color: colors.dark,
            }}>
              Edit {selectedMember.first_name} {selectedMember.last_name}
            </h2>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 8, color: colors.dark }}>
                Role
              </label>
              <select
                value={selectedMember.role}
                onChange={(e) => setSelectedMember({ ...selectedMember, role: e.target.value })}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 15,
                  outline: 'none',
                  backgroundColor: '#fff',
                }}
              >
                <option value="customer_user">User</option>
                <option value="customer_admin">Admin</option>
              </select>
            </div>

            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setSelectedMember(null);
                }}
                style={{
                  padding: '12px 24px',
                  backgroundColor: colors.lightGray,
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 15,
                  cursor: 'pointer',
                  fontFamily: "'Poppins', Arial, sans-serif",
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateMember}
                style={{
                  padding: '12px 24px',
                  backgroundColor: colors.orange,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontFamily: "'Poppins', Arial, sans-serif",
                }}
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && selectedMember && (
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
          onClick={() => {
            setShowDeleteModal(false);
            setSelectedMember(null);
          }}
        >
          <div
            style={{
              backgroundColor: colors.light,
              borderRadius: 16,
              maxWidth: 500,
              width: '100%',
              padding: 32,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 24,
              fontWeight: 600,
              margin: '0 0 16px',
              color: colors.dark,
            }}>
              Remove Team Member?
            </h2>

            <p style={{
              fontSize: 15,
              color: colors.midGray,
              margin: '0 0 24px',
              lineHeight: 1.6,
            }}>
              Are you sure you want to remove <strong>{selectedMember.first_name} {selectedMember.last_name}</strong>? They will lose access to the platform.
            </p>

            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setSelectedMember(null);
                }}
                style={{
                  padding: '12px 24px',
                  backgroundColor: colors.lightGray,
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 15,
                  cursor: 'pointer',
                  fontFamily: "'Poppins', Arial, sans-serif",
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteMember}
                style={{
                  padding: '12px 24px',
                  backgroundColor: colors.red,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontFamily: "'Poppins', Arial, sans-serif",
                }}
              >
                Remove Member
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
