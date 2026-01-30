'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, AlertCircle } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  red: '#d75757',
};

export default function AdminLoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:4080/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();

      // Verify platform_admin role
      if (data.user.role !== 'platform_admin') {
        throw new Error('Access denied. Platform admin role required.');
      }

      localStorage.setItem('0711_admin_token', data.access_token);
      localStorage.setItem('0711_admin_user', JSON.stringify(data.user));

      router.push('/admin');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: colors.dark,
      fontFamily: "'Lora', Georgia, serif",
    }}>
      <div style={{
        width: '100%',
        maxWidth: 420,
        padding: 40,
        backgroundColor: colors.light,
        borderRadius: 16,
        border: `1.5px solid ${colors.lightGray}`,
        boxShadow: '0 8px 40px rgba(0,0,0,0.4)',
      }}>
        {/* Shield Icon */}
        <div style={{
          width: 64,
          height: 64,
          margin: '0 auto 24px',
          borderRadius: '50%',
          backgroundColor: `${colors.red}15`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <Shield size={32} color={colors.red} />
        </div>

        <h1 style={{
          fontFamily: "'Poppins', Arial, sans-serif",
          fontSize: 28,
          fontWeight: 600,
          margin: '0 0 8px',
          color: colors.dark,
          textAlign: 'center',
        }}>
          Platform Admin
        </h1>

        <p style={{
          fontSize: 14,
          color: colors.midGray,
          margin: '0 0 32px',
          textAlign: 'center',
        }}>
          0711 Staff Only
        </p>

        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 16px',
            backgroundColor: '#fee',
            border: '1px solid #fcc',
            borderRadius: 8,
            marginBottom: 24,
          }}>
            <AlertCircle size={18} color="#c00" />
            <span style={{ fontSize: 14, color: '#c00' }}>
              {error}
            </span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 20 }}>
            <label style={{
              display: 'block',
              fontSize: 14,
              fontWeight: 500,
              marginBottom: 8,
              color: colors.dark,
            }}>
              Email
            </label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
              placeholder="admin@0711.io"
              autoComplete="email"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: `1.5px solid ${colors.lightGray}`,
                borderRadius: 8,
                fontSize: 15,
                outline: 'none',
              }}
              onFocus={(e) => e.currentTarget.style.borderColor = colors.red}
              onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{
              display: 'block',
              fontSize: 14,
              fontWeight: 500,
              marginBottom: 8,
              color: colors.dark,
            }}>
              Password
            </label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
              placeholder="••••••••"
              autoComplete="current-password"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: `1.5px solid ${colors.lightGray}`,
                borderRadius: 8,
                fontSize: 15,
                outline: 'none',
              }}
              onFocus={(e) => e.currentTarget.style.borderColor = colors.red}
              onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: 14,
              backgroundColor: loading ? colors.midGray : colors.red,
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              fontSize: 16,
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              fontFamily: "'Poppins', Arial, sans-serif",
              opacity: loading ? 0.7 : 1,
              boxShadow: loading ? 'none' : `0 4px 12px ${colors.red}40`,
            }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={{
          marginTop: 32,
          padding: 16,
          backgroundColor: `${colors.red}10`,
          border: `1px solid ${colors.red}30`,
          borderRadius: 8,
          fontSize: 13,
          color: colors.dark,
          textAlign: 'center',
        }}>
          ⚠️ This area is restricted to 0711 platform administrators only
        </div>
      </div>
    </div>
  );
}
