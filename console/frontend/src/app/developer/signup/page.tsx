'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Code, AlertCircle, CheckCircle } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
};

export default function DeveloperSignupPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const [form, setForm] = useState({
    company_name: '',
    contact_name: '',
    contact_email: '',
    website: '',
    description: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:4080/api/mcp-developers/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
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
          maxWidth: 500,
          padding: 40,
          backgroundColor: '#fff',
          borderRadius: 16,
          border: `1.5px solid ${colors.lightGray}`,
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
            Application Submitted!
          </h2>

          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: '0 0 24px',
            lineHeight: 1.6,
          }}>
            Your developer application has been submitted. Our team will review it and notify you within 1-2 business days.
          </p>

          <button
            onClick={() => router.push('/')}
            style={{
              padding: '12px 32px',
              backgroundColor: colors.orange,
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              fontSize: 15,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: "'Poppins', Arial, sans-serif",
            }}
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: colors.light,
      fontFamily: "'Lora', Georgia, serif",
      padding: '40px 20px',
    }}>
      <div style={{ maxWidth: 600, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{
            width: 64,
            height: 64,
            margin: '0 auto 24px',
            borderRadius: 12,
            backgroundColor: `${colors.blue}15`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Code size={32} color={colors.blue} />
          </div>

          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 32,
            fontWeight: 600,
            margin: '0 0 12px',
            color: colors.dark,
          }}>
            Become an MCP Developer
          </h1>

          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: 0,
            lineHeight: 1.6,
          }}>
            Join our marketplace and earn 70% revenue share on your MCPs
          </p>
        </div>

        {/* Form */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          padding: 32,
          border: `1.5px solid ${colors.lightGray}`,
        }}>
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

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 20 }}>
              <label style={{
                display: 'block',
                fontSize: 14,
                fontWeight: 500,
                marginBottom: 8,
                color: colors.dark,
              }}>
                Company Name
              </label>
              <input
                type="text"
                value={form.company_name}
                onChange={(e) => setForm({ ...form, company_name: e.target.value })}
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

            <div style={{ marginBottom: 20 }}>
              <label style={{
                display: 'block',
                fontSize: 14,
                fontWeight: 500,
                marginBottom: 8,
                color: colors.dark,
              }}>
                Contact Name
              </label>
              <input
                type="text"
                value={form.contact_name}
                onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
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
                value={form.contact_email}
                onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
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

            <div style={{ marginBottom: 20 }}>
              <label style={{
                display: 'block',
                fontSize: 14,
                fontWeight: 500,
                marginBottom: 8,
                color: colors.dark,
              }}>
                Website
              </label>
              <input
                type="url"
                value={form.website}
                onChange={(e) => setForm({ ...form, website: e.target.value })}
                placeholder="https://..."
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

            <div style={{ marginBottom: 32 }}>
              <label style={{
                display: 'block',
                fontSize: 14,
                fontWeight: 500,
                marginBottom: 8,
                color: colors.dark,
              }}>
                Company Description
              </label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                required
                rows={4}
                placeholder="Tell us about your company and what MCPs you plan to build..."
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 15,
                  outline: 'none',
                  fontFamily: "'Lora', Georgia, serif",
                  resize: 'vertical',
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
                padding: 14,
                backgroundColor: loading ? colors.midGray : colors.orange,
                color: '#fff',
                border: 'none',
                borderRadius: 10,
                fontSize: 16,
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                fontFamily: "'Poppins', Arial, sans-serif",
                boxShadow: loading ? 'none' : `0 4px 12px ${colors.orange}40`,
              }}
            >
              {loading ? 'Submitting...' : 'Submit Application'}
            </button>
          </form>

          <div style={{
            marginTop: 24,
            padding: 16,
            backgroundColor: colors.light,
            borderRadius: 8,
            fontSize: 13,
            color: colors.midGray,
            lineHeight: 1.6,
          }}>
            <strong style={{ color: colors.dark }}>What happens next?</strong><br />
            Our team will review your application within 1-2 business days. Once approved, you'll receive access to submit MCPs and earn 70% revenue share.
          </div>
        </div>
      </div>
    </div>
  );
}
