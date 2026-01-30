'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  orange: '#d97757',
};

export default function PartnerLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:4080/api/partners/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login fehlgeschlagen');
      }

      const data = await response.json();

      localStorage.setItem('0711_token', data.access_token);
      localStorage.setItem('0711_partner', JSON.stringify(data.partner));

      router.push('/partner');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login fehlgeschlagen');
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
    }}>
      <div style={{
        width: '100%',
        maxWidth: '420px',
        padding: '40px',
        backgroundColor: '#1a1a19',
        borderRadius: '16px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 32,
            fontWeight: 600,
            margin: 0,
            color: colors.light,
          }}>
            <span style={{ color: colors.orange }}>0711</span>
          </h1>
          <p style={{
            fontSize: 14,
            color: colors.midGray,
            margin: '8px 0 0',
          }}>
            Partner Portal
          </p>
        </div>

        <h2 style={{
          fontFamily: "'Poppins', Arial, sans-serif",
          fontSize: 24,
          fontWeight: 600,
          margin: '0 0 32px',
          color: colors.light,
          textAlign: 'center',
        }}>
          Anmeldung
        </h2>

        {error && (
          <div style={{
            padding: '12px 16px',
            backgroundColor: '#3d1f1f',
            border: `1px solid ${colors.orange}`,
            borderRadius: '8px',
            color: '#ff8a80',
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
              color: colors.midGray,
            }}>
              E-Mail
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="partner@firma.de"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid #333',
                borderRadius: '8px',
                fontSize: 15,
                backgroundColor: colors.dark,
                color: colors.light,
                outline: 'none',
              }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              fontSize: 14,
              fontWeight: 500,
              marginBottom: '8px',
              color: colors.midGray,
            }}>
              Passwort
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid #333',
                borderRadius: '8px',
                fontSize: 15,
                backgroundColor: colors.dark,
                color: colors.light,
                outline: 'none',
              }}
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
            }}
          >
            {loading ? 'Anmelden...' : 'Anmelden'}
          </button>
        </form>

        <div style={{
          marginTop: '24px',
          paddingTop: '24px',
          borderTop: '1px solid #333',
          textAlign: 'center',
          fontSize: 14,
          color: colors.midGray,
        }}>
          Noch kein Partner?{' '}
          <a href="/partner-signup" style={{ color: colors.orange, textDecoration: 'none' }}>
            Jetzt registrieren
          </a>
        </div>

        <div style={{
          marginTop: '24px',
          padding: '16px',
          backgroundColor: '#2a2a28',
          borderRadius: '8px',
          fontSize: '13px',
          color: colors.midGray,
        }}>
          <strong style={{ color: colors.light }}>Demo Account:</strong>
          <br />
          Email: sarah@success.de
          <br />
          Password: Success123
        </div>
      </div>
    </div>
  );
}
