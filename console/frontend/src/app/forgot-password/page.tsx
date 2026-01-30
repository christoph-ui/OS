'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Mail, CheckCircle, AlertCircle } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  green: '#788c5d',
};

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:4080/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send reset email');
      }

      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
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
          maxWidth: 420,
          padding: 40,
          backgroundColor: '#fff',
          borderRadius: 16,
          border: `1.5px solid ${colors.lightGray}`,
          boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
          textAlign: 'center',
        }}>
          <div style={{
            width: 64,
            height: 64,
            margin: '0 auto 24px',
            borderRadius: '50%',
            backgroundColor: `${colors.green}15`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <CheckCircle size={32} color={colors.green} />
          </div>

          <h2 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 24,
            fontWeight: 600,
            margin: '0 0 12px',
            color: colors.dark,
          }}>
            Check Your Email
          </h2>

          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: '0 0 24px',
            lineHeight: 1.6,
          }}>
            If an account exists with <strong>{email}</strong>, we've sent you a password reset link.
          </p>

          <div style={{
            padding: 16,
            backgroundColor: colors.light,
            borderRadius: 8,
            marginBottom: 24,
          }}>
            <p style={{
              fontSize: 13,
              color: colors.midGray,
              margin: 0,
              lineHeight: 1.5,
            }}>
              Didn't receive an email? Check your spam folder or try again in a few minutes.
            </p>
          </div>

          <button
            onClick={() => router.push('/login')}
            style={{
              width: '100%',
              padding: 14,
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
            Back to Login
          </button>
        </div>
      </div>
    );
  }

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
        maxWidth: 420,
        padding: 40,
        backgroundColor: '#fff',
        borderRadius: 16,
        border: `1.5px solid ${colors.lightGray}`,
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
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
          Reset Password
        </h2>

        <p style={{
          fontSize: 15,
          color: colors.midGray,
          margin: '0 0 32px',
          textAlign: 'center',
        }}>
          Enter your email and we'll send you a reset link
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
          <div style={{ marginBottom: 24 }}>
            <label style={{
              display: 'block',
              fontSize: 14,
              fontWeight: 500,
              marginBottom: 8,
              color: colors.dark,
            }}>
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="your@email.com"
                autoComplete="email"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  paddingLeft: 48,
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 15,
                  fontFamily: "'Lora', Georgia, serif",
                  outline: 'none',
                  transition: 'border 0.2s',
                }}
                onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
                onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
              />
              <div style={{
                position: 'absolute',
                left: 16,
                top: '50%',
                transform: 'translateY(-50%)',
              }}>
                <Mail size={18} color={colors.midGray} />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: 14,
              backgroundColor: loading ? colors.midGray : colors.orange,
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              fontSize: 16,
              fontFamily: "'Poppins', Arial, sans-serif",
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              opacity: loading ? 0.7 : 1,
              boxShadow: loading ? 'none' : `0 4px 12px ${colors.orange}40`,
            }}
          >
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>

        <div style={{
          marginTop: 24,
          textAlign: 'center',
        }}>
          <button
            onClick={() => router.push('/login')}
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
            Back to Login
          </button>
        </div>

        <p style={{
          marginTop: 24,
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
