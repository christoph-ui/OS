'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
};

export default function ConsoleLoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const apiUrl = 'http://localhost:4080';  // Control Plane API (User auth)
      const response = await fetch(`${apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Login failed');
      }

      const data = await response.json();

      // Store token and user data
      localStorage.setItem('0711_token', data.access_token);
      localStorage.setItem('0711_user', JSON.stringify(data.user));
      if (data.customer) {
        localStorage.setItem('0711_customer', JSON.stringify(data.customer));
      }

      // Redirect to console
      router.push('/');
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
      backgroundColor: colors.light,
      fontFamily: "'Lora', Georgia, serif",
    }}>
      <div style={{
        width: '100%',
        maxWidth: '420px',
        padding: '40px',
        backgroundColor: '#fff',
        borderRadius: '16px',
        border: `1.5px solid ${colors.lightGray}`,
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 32,
            fontWeight: 600,
            margin: 0,
          }}>
            <span style={{ color: colors.orange }}>0711</span>
          </h1>
          <p style={{
            fontSize: 14,
            color: colors.midGray,
            margin: '8px 0 0',
            letterSpacing: '0.5px',
          }}>
            Intelligence Platform
          </p>
        </div>

        <h2 style={{
          fontFamily: "'Poppins', Arial, sans-serif",
          fontSize: 24,
          fontWeight: 600,
          margin: '0 0 8px',
          color: colors.dark,
          textAlign: 'center',
        }}>
          Console Login
        </h2>

        <p style={{
          fontSize: 15,
          color: colors.midGray,
          margin: '0 0 32px',
          textAlign: 'center',
        }}>
          Sign in to access your data
        </p>

        {error && (
          <div style={{
            padding: '12px 16px',
            backgroundColor: '#fee',
            border: '1px solid #fcc',
            borderRadius: '8px',
            color: '#c00',
            fontSize: '14px',
            marginBottom: '24px',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              fontSize: 14,
              fontWeight: 500,
              marginBottom: '8px',
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
                borderRadius: '8px',
                fontSize: 15,
                fontFamily: "'Lora', Georgia, serif",
                outline: 'none',
                transition: 'border 0.2s',
              }}
              onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
              onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              fontSize: 14,
              fontWeight: 500,
              marginBottom: '8px',
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
                borderRadius: '8px',
                fontSize: 15,
                fontFamily: "'Lora', Georgia, serif",
                outline: 'none',
                transition: 'border 0.2s',
              }}
              onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
              onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '14px',
              backgroundColor: loading ? colors.midGray : colors.orange,
              color: '#fff',
              border: 'none',
              borderRadius: '10px',
              fontSize: 16,
              fontFamily: "'Poppins', Arial, sans-serif",
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={{
          marginTop: '32px',
          padding: '20px',
          backgroundColor: colors.light,
          borderRadius: '8px',
          fontSize: '13px',
          color: colors.midGray,
        }}>
          <strong style={{ color: colors.dark }}>Demo Credentials:</strong>
          <br />
          Email: admin@0711.io
          <br />
          Password: admin123
        </div>

        <div style={{
          marginTop: '20px',
          textAlign: 'center',
        }}>
          <button
            onClick={() => router.push('/forgot-password')}
            style={{
              background: 'none',
              border: 'none',
              color: colors.orange,
              fontSize: 14,
              cursor: 'pointer',
              textDecoration: 'underline',
              fontFamily: "'Lora', Georgia, serif",
            }}
          >
            Forgot password?
          </button>
        </div>

        <p style={{
          marginTop: '24px',
          textAlign: 'center',
          fontSize: 14,
          color: colors.midGray,
        }}>
          Need help? Contact{' '}
          <a href="mailto:support@0711.io" style={{ color: colors.orange, textDecoration: 'none' }}>
            support@0711.io
          </a>
        </p>
      </div>
    </div>
  );
}
