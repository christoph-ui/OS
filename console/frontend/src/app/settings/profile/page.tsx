'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { User, Save } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  green: '#788c5d',
};

interface UserData {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  status: string;
  email_verified: boolean;
}

export default function ProfileSettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
  });

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const token = localStorage.getItem('0711_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const payload = JSON.parse(atob(token.split('.')[1]));

      const response = await fetch(`http://localhost:4080/api/users/${payload.user_id}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to load user');

      const userData = await response.json();
      setUser(userData);
      setForm({
        first_name: userData.first_name || '',
        last_name: userData.last_name || '',
        email: userData.email || '',
      });
    } catch (error) {
      console.error('Error loading user data:', error);
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('0711_token');
      const payload = JSON.parse(atob(token!.split('.')[1]));

      const response = await fetch(`http://localhost:4080/api/users/${payload.user_id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          first_name: form.first_name,
          last_name: form.last_name,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update profile');
      }

      setSuccess('Profile updated successfully!');
      loadUserData();

      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setSaving(false);
    }
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
          <div>Loading profile...</div>
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
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
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

          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 32,
            fontWeight: 600,
            margin: '0 0 8px',
            color: colors.dark,
          }}>
            Profile Settings
          </h1>

          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: 0,
          }}>
            Manage your personal information
          </p>
        </div>
      </header>

      {/* Content */}
      <main style={{ maxWidth: 800, margin: '0 auto', padding: 40 }}>
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

        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          padding: 32,
          border: `1.5px solid ${colors.lightGray}`,
        }}>
          <form onSubmit={handleSubmit}>
            {/* Profile Picture Placeholder */}
            <div style={{ marginBottom: 32, display: 'flex', alignItems: 'center', gap: 20 }}>
              <div style={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                backgroundColor: `${colors.orange}15`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}>
                <User size={36} color={colors.orange} />
              </div>
              <div>
                <h3 style={{
                  fontFamily: "'Poppins', Arial, sans-serif",
                  fontSize: 18,
                  fontWeight: 600,
                  margin: '0 0 4px',
                  color: colors.dark,
                }}>
                  {form.first_name} {form.last_name}
                </h3>
                <p style={{
                  fontSize: 14,
                  color: colors.midGray,
                  margin: 0,
                }}>
                  {user?.role.replace('_', ' ')} • {user?.email_verified ? '✓ Verified' : 'Not verified'}
                </p>
              </div>
            </div>

            {/* Personal Information */}
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 18,
              fontWeight: 600,
              margin: '0 0 24px',
              color: colors.dark,
            }}>
              Personal Information
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
              <div>
                <label style={{
                  display: 'block',
                  fontSize: 14,
                  fontWeight: 500,
                  marginBottom: 8,
                  color: colors.dark,
                }}>
                  First Name
                </label>
                <input
                  type="text"
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 15,
                    outline: 'none',
                  }}
                  onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
                  onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
                />
              </div>

              <div>
                <label style={{
                  display: 'block',
                  fontSize: 14,
                  fontWeight: 500,
                  marginBottom: 8,
                  color: colors.dark,
                }}>
                  Last Name
                </label>
                <input
                  type="text"
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 15,
                    outline: 'none',
                  }}
                  onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
                  onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
                />
              </div>
            </div>

            <div style={{ marginBottom: 32 }}>
              <label style={{
                display: 'block',
                fontSize: 14,
                fontWeight: 500,
                marginBottom: 8,
                color: colors.dark,
              }}>
                Email Address
              </label>
              <input
                type="email"
                value={form.email}
                disabled
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 15,
                  outline: 'none',
                  backgroundColor: colors.lightGray,
                  cursor: 'not-allowed',
                  color: colors.midGray,
                }}
              />
              <p style={{
                fontSize: 12,
                color: colors.midGray,
                margin: '8px 0 0',
                fontStyle: 'italic',
              }}>
                Email cannot be changed. Contact support if you need to update it.
              </p>
            </div>

            {/* Account Information */}
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 18,
              fontWeight: 600,
              margin: '32px 0 24px',
              paddingTop: 32,
              borderTop: `1px solid ${colors.lightGray}`,
              color: colors.dark,
            }}>
              Account Information
            </h3>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 24,
              padding: 24,
              backgroundColor: colors.light,
              borderRadius: 12,
            }}>
              <div>
                <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                  Role
                </div>
                <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                  {user?.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </div>
              </div>

              <div>
                <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                  Status
                </div>
                <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                  {user?.status.replace(/\b\w/g, l => l.toUpperCase())}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              paddingTop: 32,
              marginTop: 32,
              borderTop: `1px solid ${colors.lightGray}`,
            }}>
              <button
                type="submit"
                disabled={saving}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '12px 32px',
                  backgroundColor: saving ? colors.midGray : colors.orange,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 10,
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: saving ? 'not-allowed' : 'pointer',
                  fontFamily: "'Poppins', Arial, sans-serif",
                  boxShadow: saving ? 'none' : `0 4px 12px ${colors.orange}40`,
                  transition: 'all 0.2s',
                }}
              >
                <Save size={18} />
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
