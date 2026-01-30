'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, Eye, EyeOff, Lock, AlertCircle } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  green: '#788c5d',
  red: '#d75757',
};

export default function SecuritySettingsPage() {
  const router = useRouter();
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [form, setForm] = useState({
    current_password: '',
    new_password: '',
    new_password_confirm: '',
  });

  const validatePassword = () => {
    if (form.new_password.length < 8) {
      return 'New password must be at least 8 characters';
    }
    if (form.new_password !== form.new_password_confirm) {
      return 'Passwords do not match';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const validationError = validatePassword();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSaving(true);

    try {
      const token = localStorage.getItem('0711_token');

      const response = await fetch('http://localhost:4080/api/users/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: form.current_password,
          new_password: form.new_password,
          new_password_confirm: form.new_password_confirm,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to change password');
      }

      setSuccess('Password changed successfully!');
      setForm({
        current_password: '',
        new_password: '',
        new_password_confirm: '',
      });

      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change password');
    } finally {
      setSaving(false);
    }
  };

  const getPasswordStrength = () => {
    if (form.new_password.length === 0) return null;
    if (form.new_password.length < 8) return { label: 'Too short', color: colors.red, width: '33%' };
    if (form.new_password.length < 12) return { label: 'Good', color: colors.orange, width: '66%' };
    return { label: 'Strong', color: colors.green, width: '100%' };
  };

  const passwordStrength = getPasswordStrength();

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
            Security Settings
          </h1>

          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: 0,
          }}>
            Manage your password and authentication settings
          </p>
        </div>
      </header>

      {/* Content */}
      <main style={{ maxWidth: 800, margin: '0 auto', padding: 40 }}>
        {/* Alerts */}
        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 16px',
            marginBottom: 24,
            backgroundColor: '#fee',
            border: '1px solid #fcc',
            borderRadius: 8,
          }}>
            <AlertCircle size={18} color="#c00" />
            <span style={{ fontSize: 14, color: '#c00' }}>
              {error}
            </span>
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

        {/* Change Password */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          padding: 32,
          border: `1.5px solid ${colors.lightGray}`,
          marginBottom: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
            <div style={{
              width: 48,
              height: 48,
              borderRadius: 12,
              backgroundColor: `${colors.orange}15`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Lock size={24} color={colors.orange} />
            </div>
            <div>
              <h3 style={{
                fontFamily: "'Poppins', Arial, sans-serif",
                fontSize: 18,
                fontWeight: 600,
                margin: 0,
                color: colors.dark,
              }}>
                Change Password
              </h3>
              <p style={{
                fontSize: 14,
                color: colors.midGray,
                margin: '4px 0 0',
              }}>
                Update your password to keep your account secure
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            {/* Current Password */}
            <div style={{ marginBottom: 20 }}>
              <label style={{
                display: 'block',
                fontSize: 14,
                fontWeight: 500,
                marginBottom: 8,
                color: colors.dark,
              }}>
                Current Password
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showCurrentPassword ? 'text' : 'password'}
                  value={form.current_password}
                  onChange={(e) => setForm({ ...form, current_password: e.target.value })}
                  required
                  placeholder="Enter your current password"
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    paddingRight: 48,
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 15,
                    outline: 'none',
                  }}
                  onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
                  onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  style={{
                    position: 'absolute',
                    right: 12,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: 4,
                  }}
                >
                  {showCurrentPassword ? (
                    <EyeOff size={18} color={colors.midGray} />
                  ) : (
                    <Eye size={18} color={colors.midGray} />
                  )}
                </button>
              </div>
            </div>

            {/* New Password */}
            <div style={{ marginBottom: 20 }}>
              <label style={{
                display: 'block',
                fontSize: 14,
                fontWeight: 500,
                marginBottom: 8,
                color: colors.dark,
              }}>
                New Password
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showNewPassword ? 'text' : 'password'}
                  value={form.new_password}
                  onChange={(e) => setForm({ ...form, new_password: e.target.value })}
                  required
                  minLength={8}
                  placeholder="At least 8 characters"
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    paddingRight: 48,
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 15,
                    outline: 'none',
                  }}
                  onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
                  onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  style={{
                    position: 'absolute',
                    right: 12,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: 4,
                  }}
                >
                  {showNewPassword ? (
                    <EyeOff size={18} color={colors.midGray} />
                  ) : (
                    <Eye size={18} color={colors.midGray} />
                  )}
                </button>
              </div>

              {passwordStrength && (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginTop: 8,
                }}>
                  <div style={{
                    flex: 1,
                    height: 4,
                    backgroundColor: colors.lightGray,
                    borderRadius: 2,
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      width: passwordStrength.width,
                      height: '100%',
                      backgroundColor: passwordStrength.color,
                      transition: 'all 0.3s',
                    }} />
                  </div>
                  <span style={{
                    fontSize: 12,
                    color: passwordStrength.color,
                    fontWeight: 500,
                    minWidth: 60,
                  }}>
                    {passwordStrength.label}
                  </span>
                </div>
              )}
            </div>

            {/* Confirm New Password */}
            <div style={{ marginBottom: 24 }}>
              <label style={{
                display: 'block',
                fontSize: 14,
                fontWeight: 500,
                marginBottom: 8,
                color: colors.dark,
              }}>
                Confirm New Password
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={form.new_password_confirm}
                  onChange={(e) => setForm({ ...form, new_password_confirm: e.target.value })}
                  required
                  placeholder="Re-enter your new password"
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    paddingRight: 48,
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 15,
                    outline: 'none',
                  }}
                  onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
                  onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  style={{
                    position: 'absolute',
                    right: 12,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: 4,
                  }}
                >
                  {showConfirmPassword ? (
                    <EyeOff size={18} color={colors.midGray} />
                  ) : (
                    <Eye size={18} color={colors.midGray} />
                  )}
                </button>
              </div>

              {form.new_password_confirm && form.new_password !== form.new_password_confirm && (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  marginTop: 8,
                  fontSize: 12,
                  color: colors.red,
                }}>
                  <AlertCircle size={14} />
                  Passwords do not match
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={saving}
              style={{
                width: '100%',
                padding: 14,
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
              {saving ? 'Changing password...' : 'Change Password'}
            </button>
          </form>
        </div>

        {/* Future: Two-Factor Authentication */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          padding: 32,
          border: `1.5px solid ${colors.lightGray}`,
          opacity: 0.6,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
            <div style={{
              width: 48,
              height: 48,
              borderRadius: 12,
              backgroundColor: `${colors.midGray}15`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Shield size={24} color={colors.midGray} />
            </div>
            <div>
              <h3 style={{
                fontFamily: "'Poppins', Arial, sans-serif",
                fontSize: 18,
                fontWeight: 600,
                margin: 0,
                color: colors.dark,
              }}>
                Two-Factor Authentication
              </h3>
              <p style={{
                fontSize: 14,
                color: colors.midGray,
                margin: '4px 0 0',
              }}>
                Add an extra layer of security to your account
              </p>
            </div>
          </div>

          <div style={{
            padding: 16,
            backgroundColor: colors.light,
            borderRadius: 8,
            fontSize: 14,
            color: colors.midGray,
            fontStyle: 'italic',
          }}>
            Coming soon! Two-factor authentication will be available in a future update.
          </div>
        </div>
      </main>
    </div>
  );
}
