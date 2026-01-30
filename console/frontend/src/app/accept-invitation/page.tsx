'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle, AlertCircle, Eye, EyeOff } from 'lucide-react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  green: '#788c5d',
  red: '#d75757',
};

export default function AcceptInvitationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!token) {
      setError('Invalid or missing invitation token');
    }
  }, [token]);

  const validatePassword = () => {
    if (password.length < 8) {
      return 'Password must be at least 8 characters';
    }
    if (password !== passwordConfirm) {
      return 'Passwords do not match';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const validationError = validatePassword();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('http://localhost:4080/api/users/accept-invitation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          password,
          password_confirm: passwordConfirm,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to accept invitation');
      }

      setSuccess(true);

      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to accept invitation');
    } finally {
      setLoading(false);
    }
  };

  const getPasswordStrength = () => {
    if (password.length === 0) return null;
    if (password.length < 8) return { label: 'Too short', color: colors.red };
    if (password.length < 12) return { label: 'Good', color: colors.orange };
    return { label: 'Strong', color: colors.green };
  };

  const passwordStrength = getPasswordStrength();

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
            Account Activated!
          </h2>

          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: '0 0 24px',
            lineHeight: 1.6,
          }}>
            Your password has been set successfully. Redirecting to login...
          </p>

          <div style={{
            display: 'inline-block',
            padding: '8px 16px',
            backgroundColor: colors.lightGray,
            borderRadius: 8,
            fontSize: 13,
            color: colors.midGray,
          }}>
            Redirecting in 2 seconds...
          </div>
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
          Set Your Password
        </h2>

        <p style={{
          fontSize: 15,
          color: colors.midGray,
          margin: '0 0 32px',
          textAlign: 'center',
        }}>
          Complete your account setup by creating a password
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
          {/* Password */}
          <div style={{ marginBottom: 20 }}>
            <label style={{
              display: 'block',
              fontSize: 14,
              fontWeight: 500,
              marginBottom: 8,
              color: colors.dark,
            }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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
                  fontFamily: "'Lora', Georgia, serif",
                  outline: 'none',
                  transition: 'border 0.2s',
                }}
                onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
                onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: 12,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 4,
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {showPassword ? (
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
                    width: password.length < 8 ? '33%' : password.length < 12 ? '66%' : '100%',
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

          {/* Confirm Password */}
          <div style={{ marginBottom: 24 }}>
            <label style={{
              display: 'block',
              fontSize: 14,
              fontWeight: 500,
              marginBottom: 8,
              color: colors.dark,
            }}>
              Confirm Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPasswordConfirm ? 'text' : 'password'}
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                required
                placeholder="Re-enter your password"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  paddingRight: 48,
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
              <button
                type="button"
                onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                style={{
                  position: 'absolute',
                  right: 12,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 4,
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {showPasswordConfirm ? (
                  <EyeOff size={18} color={colors.midGray} />
                ) : (
                  <Eye size={18} color={colors.midGray} />
                )}
              </button>
            </div>

            {passwordConfirm && password !== passwordConfirm && (
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
            disabled={loading || !token}
            style={{
              width: '100%',
              padding: 14,
              backgroundColor: loading || !token ? colors.midGray : colors.orange,
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              fontSize: 16,
              fontFamily: "'Poppins', Arial, sans-serif",
              fontWeight: 600,
              cursor: loading || !token ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              opacity: loading || !token ? 0.7 : 1,
            }}
          >
            {loading ? 'Setting password...' : 'Complete Setup'}
          </button>
        </form>

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
