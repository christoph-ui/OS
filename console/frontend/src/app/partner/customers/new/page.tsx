'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import PartnerHeader from '@/components/PartnerHeader';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
};

interface CustomerForm {
  companyName: string;
  contactName: string;
  contactEmail: string;
  contactPhone: string;
  companyType: string;
  tier: string;
  vatId: string;
  street: string;
  city: string;
  postalCode: string;
  country: string;
  sendInvitation: boolean;
}

export default function NewCustomerPage() {
  const router = useRouter();
  const [form, setForm] = useState<CustomerForm>({
    companyName: '',
    contactName: '',
    contactEmail: '',
    contactPhone: '',
    companyType: 'GmbH',
    tier: 'starter',
    vatId: '',
    street: '',
    city: '',
    postalCode: '',
    country: 'DE',
    sendInvitation: true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4080/api/partners/customers', {
        method: 'POST',
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
          tier: form.tier,
          vat_id: form.vatId,
          street: form.street,
          city: form.city,
          postal_code: form.postalCode,
          country: form.country,
          send_invitation: form.sendInvitation,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Kunde konnte nicht erstellt werden');
      }

      const data = await response.json();

      // Success - redirect to onboarding
      router.push(`/partner/customers/${data.id}/onboarding`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Erstellen');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PartnerHeader title="Neuer Kunde" />

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
              fontSize: 18,
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
                Firmenname *
              </label>
              <input
                type="text"
                value={form.companyName}
                onChange={(e) => setForm({ ...form, companyName: e.target.value })}
                required
                placeholder="Eaton GmbH"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 15,
                  outline: 'none',
                  transition: 'border 0.2s',
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
                    cursor: 'pointer',
                  }}
                >
                  <option value="GmbH">GmbH</option>
                  <option value="UG">UG</option>
                  <option value="AG">AG</option>
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
                  value={form.vatId}
                  onChange={(e) => setForm({ ...form, vatId: e.target.value })}
                  placeholder="DE123456789"
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

            {/* Contact Info */}
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 18,
              fontWeight: 600,
              margin: '32px 0 20px',
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
                Ansprechpartner *
              </label>
              <input
                type="text"
                value={form.contactName}
                onChange={(e) => setForm({ ...form, contactName: e.target.value })}
                required
                placeholder="Max Mustermann"
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
                  E-Mail *
                </label>
                <input
                  type="email"
                  value={form.contactEmail}
                  onChange={(e) => setForm({ ...form, contactEmail: e.target.value })}
                  required
                  placeholder="max@eaton.de"
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
                  placeholder="+49 711 1234567"
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
              fontSize: 18,
              fontWeight: 600,
              margin: '32px 0 20px',
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
                placeholder="Hauptstraße 123"
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

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 20, marginBottom: 20 }}>
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
                  placeholder="70173"
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
                  placeholder="Stuttgart"
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

            {/* Tier Selection */}
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 18,
              fontWeight: 600,
              margin: '32px 0 20px',
              color: colors.dark,
            }}>
              Tarif
            </h3>

            <div style={{ marginBottom: 20 }}>
              <select
                value={form.tier}
                onChange={(e) => setForm({ ...form, tier: e.target.value })}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 15,
                  outline: 'none',
                  backgroundColor: '#fff',
                  cursor: 'pointer',
                }}
              >
                <option value="starter">Starter (5-20 Mitarbeiter)</option>
                <option value="professional">Professional (20-50 Mitarbeiter)</option>
                <option value="business">Business (50-200 Mitarbeiter)</option>
                <option value="enterprise">Enterprise (200+ Mitarbeiter)</option>
              </select>
            </div>

            {/* Send Invitation */}
            <div style={{
              padding: 16,
              backgroundColor: colors.light,
              borderRadius: 8,
              marginBottom: 32,
            }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                cursor: 'pointer',
                fontSize: 14,
              }}>
                <input
                  type="checkbox"
                  checked={form.sendInvitation}
                  onChange={(e) => setForm({ ...form, sendInvitation: e.target.checked })}
                  style={{ width: 18, height: 18, cursor: 'pointer' }}
                />
                <span>
                  Einladungs-E-Mail an den Kunden senden
                </span>
              </label>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={() => router.back()}
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
                disabled={loading}
                style={{
                  padding: '12px 24px',
                  backgroundColor: loading ? colors.midGray : colors.orange,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 10,
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontFamily: "'Poppins', Arial, sans-serif",
                  boxShadow: loading ? 'none' : `0 4px 12px ${colors.orange}40`,
                  transition: 'all 0.2s',
                }}
              >
                {loading ? 'Wird erstellt...' : 'Kunde erstellen'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
