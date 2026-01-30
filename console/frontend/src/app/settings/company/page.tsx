'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Building2, Save } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  green: '#788c5d',
};

interface CustomerData {
  id: string;
  company_name: string;
  company_type: string;
  vat_id: string;
  street: string;
  city: string;
  postal_code: string;
  country: string;
  contact_phone: string;
  tier: string;
  created_at: string;
}

export default function CompanySettingsPage() {
  const router = useRouter();
  const [customer, setCustomer] = useState<CustomerData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);

  const [form, setForm] = useState({
    company_name: '',
    company_type: '',
    vat_id: '',
    street: '',
    city: '',
    postal_code: '',
    country: 'DE',
    contact_phone: '',
  });

  useEffect(() => {
    loadCompanyData();
  }, []);

  const loadCompanyData = async () => {
    try {
      const token = localStorage.getItem('0711_token');
      if (!token) {
        router.push('/login');
        return;
      }

      // Check if user is admin
      const userStr = localStorage.getItem('0711_user');
      if (userStr) {
        const user = JSON.parse(userStr);
        setIsAdmin(user.role === 'customer_admin');
      }

      const payload = JSON.parse(atob(token.split('.')[1]));
      const customerId = payload.customer_id;

      const response = await fetch(`http://localhost:4080/api/customers/${customerId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to load company data');

      const customerData = await response.json();
      setCustomer(customerData);
      setForm({
        company_name: customerData.company_name || '',
        company_type: customerData.company_type || '',
        vat_id: customerData.vat_id || '',
        street: customerData.street || '',
        city: customerData.city || '',
        postal_code: customerData.postal_code || '',
        country: customerData.country || 'DE',
        contact_phone: customerData.contact_phone || '',
      });
    } catch (error) {
      console.error('Error loading company data:', error);
      setError('Failed to load company details');
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

      const response = await fetch(`http://localhost:4080/api/customers/${payload.customer_id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(form),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update company');
      }

      setSuccess('Company details updated successfully!');
      loadCompanyData();

      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update company');
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
          <div>Loading company details...</div>
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
            Company Settings
          </h1>

          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: 0,
          }}>
            {isAdmin ? 'Manage your organization details' : 'View your organization details'}
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
            {/* Company Information */}
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 18,
              fontWeight: 600,
              margin: '0 0 24px',
              color: colors.dark,
            }}>
              Company Information
            </h3>

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
                disabled={!isAdmin}
                required
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 15,
                  outline: 'none',
                  backgroundColor: isAdmin ? '#fff' : colors.lightGray,
                  cursor: isAdmin ? 'text' : 'not-allowed',
                  color: isAdmin ? colors.dark : colors.midGray,
                }}
                onFocus={(e) => isAdmin && (e.currentTarget.style.borderColor = colors.orange)}
                onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
              <div>
                <label style={{
                  display: 'block',
                  fontSize: 14,
                  fontWeight: 500,
                  marginBottom: 8,
                  color: colors.dark,
                }}>
                  Company Type
                </label>
                <select
                  value={form.company_type}
                  onChange={(e) => setForm({ ...form, company_type: e.target.value })}
                  disabled={!isAdmin}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 15,
                    outline: 'none',
                    backgroundColor: isAdmin ? '#fff' : colors.lightGray,
                    cursor: isAdmin ? 'pointer' : 'not-allowed',
                  }}
                >
                  <option value="">Select type</option>
                  <option value="GmbH">GmbH</option>
                  <option value="AG">AG</option>
                  <option value="UG">UG</option>
                  <option value="KG">KG</option>
                  <option value="OHG">OHG</option>
                  <option value="Einzelunternehmen">Einzelunternehmen</option>
                </select>
              </div>

              <div>
                <label style={{
                  display: 'block',
                  fontSize: 14,
                  fontWeight: 500,
                  marginBottom: 8,
                  color: colors.dark,
                }}>
                  USt-IdNr.
                </label>
                <input
                  type="text"
                  value={form.vat_id}
                  onChange={(e) => setForm({ ...form, vat_id: e.target.value })}
                  disabled={!isAdmin}
                  placeholder="DE123456789"
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 15,
                    outline: 'none',
                    backgroundColor: isAdmin ? '#fff' : colors.lightGray,
                    cursor: isAdmin ? 'text' : 'not-allowed',
                    color: isAdmin ? colors.dark : colors.midGray,
                  }}
                  onFocus={(e) => isAdmin && (e.currentTarget.style.borderColor = colors.orange)}
                  onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
                />
              </div>
            </div>

            {/* Address */}
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 18,
              fontWeight: 600,
              margin: '32px 0 24px',
              paddingTop: 32,
              borderTop: `1px solid ${colors.lightGray}`,
              color: colors.dark,
            }}>
              Address
            </h3>

            <div style={{ marginBottom: 20 }}>
              <label style={{
                display: 'block',
                fontSize: 14,
                fontWeight: 500,
                marginBottom: 8,
                color: colors.dark,
              }}>
                Street
              </label>
              <input
                type="text"
                value={form.street}
                onChange={(e) => setForm({ ...form, street: e.target.value })}
                disabled={!isAdmin}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 15,
                  outline: 'none',
                  backgroundColor: isAdmin ? '#fff' : colors.lightGray,
                  cursor: isAdmin ? 'text' : 'not-allowed',
                  color: isAdmin ? colors.dark : colors.midGray,
                }}
                onFocus={(e) => isAdmin && (e.currentTarget.style.borderColor = colors.orange)}
                onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 1fr', gap: 20, marginBottom: 20 }}>
              <div>
                <label style={{
                  display: 'block',
                  fontSize: 14,
                  fontWeight: 500,
                  marginBottom: 8,
                  color: colors.dark,
                }}>
                  Postal Code
                </label>
                <input
                  type="text"
                  value={form.postal_code}
                  onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
                  disabled={!isAdmin}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 15,
                    outline: 'none',
                    backgroundColor: isAdmin ? '#fff' : colors.lightGray,
                    cursor: isAdmin ? 'text' : 'not-allowed',
                    color: isAdmin ? colors.dark : colors.midGray,
                  }}
                  onFocus={(e) => isAdmin && (e.currentTarget.style.borderColor = colors.orange)}
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
                  City
                </label>
                <input
                  type="text"
                  value={form.city}
                  onChange={(e) => setForm({ ...form, city: e.target.value })}
                  disabled={!isAdmin}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 15,
                    outline: 'none',
                    backgroundColor: isAdmin ? '#fff' : colors.lightGray,
                    cursor: isAdmin ? 'text' : 'not-allowed',
                    color: isAdmin ? colors.dark : colors.midGray,
                  }}
                  onFocus={(e) => isAdmin && (e.currentTarget.style.borderColor = colors.orange)}
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
                  Country
                </label>
                <select
                  value={form.country}
                  onChange={(e) => setForm({ ...form, country: e.target.value })}
                  disabled={!isAdmin}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 15,
                    outline: 'none',
                    backgroundColor: isAdmin ? '#fff' : colors.lightGray,
                    cursor: isAdmin ? 'pointer' : 'not-allowed',
                  }}
                >
                  <option value="DE">Deutschland</option>
                  <option value="AT">Österreich</option>
                  <option value="CH">Schweiz</option>
                </select>
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
                Phone
              </label>
              <input
                type="tel"
                value={form.contact_phone}
                onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                disabled={!isAdmin}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 15,
                  outline: 'none',
                  backgroundColor: isAdmin ? '#fff' : colors.lightGray,
                  cursor: isAdmin ? 'text' : 'not-allowed',
                  color: isAdmin ? colors.dark : colors.midGray,
                }}
                onFocus={(e) => isAdmin && (e.currentTarget.style.borderColor = colors.orange)}
                onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
              />
            </div>

            {/* Account Info (Read-only) */}
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
                  Plan
                </div>
                <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                  {customer?.tier.replace(/\b\w/g, l => l.toUpperCase()) || 'Starter'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                  Member Since
                </div>
                <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                  {customer?.created_at ? new Date(customer.created_at).toLocaleDateString() : '-'}
                </div>
              </div>
            </div>

            {!isAdmin && (
              <div style={{
                marginTop: 24,
                padding: 16,
                backgroundColor: `${colors.orange}10`,
                border: `1px solid ${colors.orange}30`,
                borderRadius: 8,
                fontSize: 14,
                color: colors.dark,
              }}>
                <strong>Note:</strong> Only admins can edit company details. Contact your admin to make changes.
              </div>
            )}

            {/* Actions */}
            {isAdmin && (
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
            )}
          </form>
        </div>
      </main>
    </div>
  );
}
