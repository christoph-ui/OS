'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import DeveloperLayout from '@/components/developer/DeveloperLayout';
import { Package, AlertCircle } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  green: '#788c5d',
};

export default function SubmitMCPPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    name: '',
    display_name: '',
    description: '',
    category: '',
    subcategory: '',
    connection_type: 'api_key',
    pricing_model: 'free',
    api_docs_url: '',
    setup_instructions: '',
    icon: '',
    icon_color: colors.blue,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('0711_developer_token');

      const response = await fetch('http://localhost:4080/api/mcp-developers/mcps', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(form),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit MCP');
      }

      router.push('/developer?success=mcp_submitted');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit MCP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DeveloperLayout>
      <div style={{ padding: 40 }}>
        <header style={{ marginBottom: 32 }}>
          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 32,
            fontWeight: 600,
            margin: '0 0 8px',
            color: colors.dark,
          }}>
            Submit New MCP
          </h1>
          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: 0,
          }}>
            Your MCP will be reviewed by our team before going live
          </p>
        </header>

        <div style={{
          maxWidth: 800,
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
              <span style={{ fontSize: 14, color: '#c00' }}>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 18,
              fontWeight: 600,
              margin: '0 0 24px',
              color: colors.dark,
            }}>
              Basic Information
            </h3>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 8, color: colors.dark }}>
                MCP Name (technical)
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                placeholder="my-awesome-mcp"
                pattern="[a-z0-9-]+"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 15,
                  outline: 'none',
                  fontFamily: "'SF Mono', monospace",
                }}
                onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
                onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
              />
              <p style={{ fontSize: 12, color: colors.midGray, margin: '6px 0 0' }}>
                Lowercase, numbers, and hyphens only
              </p>
            </div>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 8, color: colors.dark }}>
                Display Name
              </label>
              <input
                type="text"
                value={form.display_name}
                onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                required
                placeholder="My Awesome MCP"
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
              <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 8, color: colors.dark }}>
                Description
              </label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                required
                rows={4}
                placeholder="Describe what your MCP does..."
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

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 32 }}>
              <div>
                <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 8, color: colors.dark }}>
                  Category
                </label>
                <select
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  required
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
                  <option value="">Select category</option>
                  <option value="crm">CRM</option>
                  <option value="finance">Finance</option>
                  <option value="communication">Communication</option>
                  <option value="devops">DevOps</option>
                  <option value="ecommerce">E-commerce</option>
                  <option value="database">Database</option>
                  <option value="ai">AI</option>
                  <option value="data">Data</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 8, color: colors.dark }}>
                  Connection Type
                </label>
                <select
                  value={form.connection_type}
                  onChange={(e) => setForm({ ...form, connection_type: e.target.value })}
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
                  <option value="api_key">API Key</option>
                  <option value="oauth2">OAuth 2.0</option>
                  <option value="database">Database</option>
                  <option value="service_account">Service Account</option>
                </select>
              </div>
            </div>

            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 18,
              fontWeight: 600,
              margin: '32px 0 24px',
              paddingTop: 32,
              borderTop: `1px solid ${colors.lightGray}`,
              color: colors.dark,
            }}>
              Documentation
            </h3>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 8, color: colors.dark }}>
                API Documentation URL
              </label>
              <input
                type="url"
                value={form.api_docs_url}
                onChange={(e) => setForm({ ...form, api_docs_url: e.target.value })}
                required
                placeholder="https://docs.example.com/api"
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
              <label style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 8, color: colors.dark }}>
                Setup Instructions
              </label>
              <textarea
                value={form.setup_instructions}
                onChange={(e) => setForm({ ...form, setup_instructions: e.target.value })}
                required
                rows={6}
                placeholder="Step-by-step instructions for customers to connect..."
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

            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={() => router.push('/developer')}
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
                disabled={loading}
                style={{
                  padding: '12px 24px',
                  backgroundColor: loading ? colors.midGray : colors.orange,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontFamily: "'Poppins', Arial, sans-serif",
                  boxShadow: loading ? 'none' : `0 4px 12px ${colors.orange}40`,
                }}
              >
                {loading ? 'Submitting...' : 'Submit for Approval'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </DeveloperLayout>
  );
}
