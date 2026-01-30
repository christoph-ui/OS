'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import PartnerHeader from '@/components/PartnerHeader';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
};

interface CustomerForm {
  companyName: string;
  contactName: string;
  contactEmail: string;
  contactPhone: string;
  companyType: string;
  vatId: string;
  street: string;
  city: string;
  postalCode: string;
}

export default function EditCustomerPage() {
  const router = useRouter();
  const params = useParams();
  const customerId = params?.id as string;

  const [form, setForm] = useState<CustomerForm>({
    companyName: '',
    contactName: '',
    contactEmail: '',
    contactPhone: '',
    companyType: 'GmbH',
    vatId: '',
    street: '',
    city: '',
    postalCode: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadCustomer();
  }, [customerId]);

  const loadCustomer = async () => {
    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch(`http://localhost:4080/api/partners/customers/${customerId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to load customer');

      const customer = await response.json();
      setForm({
        companyName: customer.company_name || '',
        contactName: customer.contact_name || '',
        contactEmail: customer.contact_email || '',
        contactPhone: customer.contact_phone || '',
        companyType: customer.company_type || 'GmbH',
        vatId: customer.vat_id || '',
        street: customer.street || '',
        city: customer.city || '',
        postalCode: customer.postal_code || '',
      });
    } catch (error) {
      console.error('Error loading customer:', error);
      setError('Kunde konnte nicht geladen werden');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch(`http://localhost:4080/api/partners/customers/${customerId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          company_name: form.companyName,
          contact_name: form.contactName,
          contact_email: form.contactEmail,
          contact_phone: form.contactPhone,
          company_type: form.companyType,
          vat_id: form.vatId,
          street: form.street,
          city: form.city,
          postal_code: form.postalCode,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Kunde konnte nicht aktualisiert werden');
      }

      // Success - redirect back to detail page
      router.push(`/partner/customers/${customerId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Speichern');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div>
        <PartnerHeader title="Kunde bearbeiten" />
        <div style={{ padding: 40, textAlign: 'center', color: colors.midGray }}>
          Lädt...
        </div>
      </div>
    );
  }

  return (
    <div>
      <PartnerHeader title="Kunde bearbeiten" />

      <div style={{ padding: 40, maxWidth: 800 }}>
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

        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          padding: 32,
          border: `1.5px solid ${colors.lightGray}`,
        }}>
          <form onSubmit={handleSubmit}>
            {/* Company Info */}
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 16,
              fontWeight: 600,
              margin: '0 0 20px',
              color: colors.dark,
            }}>
              Firmendaten
            </h3>

            <div style={{ marginBottom: 20 }}>
              <label style={{
                display: 'block',
                fontSize: 14,
                fontWeight: 500,
                marginBottom: 8,
                color: colors.dark,
              }}>
                Firmenname
              </label>
              <input
                type="text"
                value={form.companyName}
                onChange={(e) => setForm({ ...form, companyName: e.target.value })}
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

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
              <div>
                <label style={{
                  display: 'block',
                  fontSize: 14,
                  fontWeight: 500,
                  marginBottom: 8,
                  color: colors.dark,
                }}>
                  Rechtsform
                </label>
                <select
                  value={form.companyType}
                  onChange={(e) => setForm({ ...form, companyType: e.target.value })}
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
                  <option value="GmbH">GmbH</option>
                  <option value="UG">UG</option>
                  <option value="AG">AG</option>
                  <option value="KG">KG</option>
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
                  value={form.vatId}
                  onChange={(e) => setForm({ ...form, vatId: e.target.value })}
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

            {/* Contact */}
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 16,
              fontWeight: 600,
              margin: '24px 0 20px',
              color: colors.dark,
            }}>
              Kontaktdaten
            </h3>

            <div style={{ marginBottom: 20 }}>
              <label style={{
                display: 'block',
                fontSize: 14,
                fontWeight: 500,
                marginBottom: 8,
                color: colors.dark,
              }}>
                Ansprechpartner
              </label>
              <input
                type="text"
                value={form.contactName}
                onChange={(e) => setForm({ ...form, contactName: e.target.value })}
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

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
              <div>
                <label style={{
                  display: 'block',
                  fontSize: 14,
                  fontWeight: 500,
                  marginBottom: 8,
                  color: colors.dark,
                }}>
                  E-Mail
                </label>
                <input
                  type="email"
                  value={form.contactEmail}
                  onChange={(e) => setForm({ ...form, contactEmail: e.target.value })}
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
                  Telefon
                </label>
                <input
                  type="tel"
                  value={form.contactPhone}
                  onChange={(e) => setForm({ ...form, contactPhone: e.target.value })}
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

            {/* Address */}
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 16,
              fontWeight: 600,
              margin: '24px 0 20px',
              color: colors.dark,
            }}>
              Adresse
            </h3>

            <div style={{ marginBottom: 20 }}>
              <label style={{
                display: 'block',
                fontSize: 14,
                fontWeight: 500,
                marginBottom: 8,
                color: colors.dark,
              }}>
                Straße
              </label>
              <input
                type="text"
                value={form.street}
                onChange={(e) => setForm({ ...form, street: e.target.value })}
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

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 20, marginBottom: 32 }}>
              <div>
                <label style={{
                  display: 'block',
                  fontSize: 14,
                  fontWeight: 500,
                  marginBottom: 8,
                  color: colors.dark,
                }}>
                  PLZ
                </label>
                <input
                  type="text"
                  value={form.postalCode}
                  onChange={(e) => setForm({ ...form, postalCode: e.target.value })}
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
                  Stadt
                </label>
                <input
                  type="text"
                  value={form.city}
                  onChange={(e) => setForm({ ...form, city: e.target.value })}
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

            {/* Actions */}
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={() => router.push(`/partner/customers/${customerId}`)}
                style={{
                  padding: '12px 24px',
                  backgroundColor: colors.lightGray,
                  color: colors.dark,
                  border: 'none',
                  borderRadius: 10,
                  fontSize: 15,
                  fontWeight: 500,
                  cursor: 'pointer',
                  fontFamily: "'Poppins', Arial, sans-serif",
                }}
              >
                Abbrechen
              </button>
              <button
                type="submit"
                disabled={saving}
                style={{
                  padding: '12px 24px',
                  backgroundColor: saving ? colors.midGray : colors.orange,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 10,
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: saving ? 'not-allowed' : 'pointer',
                  fontFamily: "'Poppins', Arial, sans-serif",
                  boxShadow: saving ? 'none' : `0 4px 12px ${colors.orange}40`,
                }}
              >
                {saving ? 'Wird gespeichert...' : 'Speichern'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
