'use client';

import { useEffect, useState } from 'react';
import PartnerHeader from '@/components/PartnerHeader';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  green: '#788c5d',
};

interface PartnerForm {
  companyName: string;
  contactEmail: string;
  contactPhone: string;
  street: string;
  city: string;
  postalCode: string;
  country: string;
  vatId: string;
}

export default function PartnerSettingsPage() {
  const [form, setForm] = useState<PartnerForm>({
    companyName: '',
    contactEmail: '',
    contactPhone: '',
    street: '',
    city: '',
    postalCode: '',
    country: 'DE',
    vatId: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadPartnerProfile();
  }, []);

  const loadPartnerProfile = async () => {
    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4080/api/partners/me', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to load profile');

      const partner = await response.json();
      setForm({
        companyName: partner.company_name || '',
        contactEmail: partner.contact_email || '',
        contactPhone: partner.contact_phone || '',
        street: partner.street || '',
        city: partner.city || '',
        postalCode: partner.postal_code || '',
        country: partner.country || 'DE',
        vatId: partner.vat_id || '',
      });

      // Update localStorage
      localStorage.setItem('0711_partner', JSON.stringify(partner));
    } catch (error) {
      console.error('Error loading profile:', error);
      setError('Profil konnte nicht geladen werden');
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
      const response = await fetch('http://localhost:4080/api/partners/me', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          company_name: form.companyName,
          contact_email: form.contactEmail,
          contact_phone: form.contactPhone,
          street: form.street,
          city: form.city,
          postal_code: form.postalCode,
          country: form.country,
          vat_id: form.vatId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Profil konnte nicht gespeichert werden');
      }

      const updatedPartner = await response.json();
      localStorage.setItem('0711_partner', JSON.stringify(updatedPartner));

      setSuccess('Profil erfolgreich gespeichert!');

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Speichern');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div>
        <PartnerHeader title="Einstellungen" />
        <div style={{ padding: 40, textAlign: 'center', color: colors.midGray }}>
          Lädt...
        </div>
      </div>
    );
  }

  return (
    <div>
      <PartnerHeader title="Einstellungen" />

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

        {success && (
          <div style={{
            padding: '12px 16px',
            backgroundColor: '#efe',
            border: `1px solid ${colors.green}`,
            borderRadius: '8px',
            color: colors.green,
            fontSize: '14px',
            marginBottom: '24px',
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
            {/* Company Info */}
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 18,
              fontWeight: 600,
              margin: '0 0 24px',
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

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 32 }}>
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
              fontSize: 18,
              fontWeight: 600,
              margin: '32px 0 24px',
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

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 1fr', gap: 20, marginBottom: 20 }}>
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

              <div>
                <label style={{
                  display: 'block',
                  fontSize: 14,
                  fontWeight: 500,
                  marginBottom: 8,
                  color: colors.dark,
                }}>
                  Land
                </label>
                <select
                  value={form.country}
                  onChange={(e) => setForm({ ...form, country: e.target.value })}
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

            {/* Actions */}
            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              paddingTop: 24,
              borderTop: `1px solid ${colors.lightGray}`,
            }}>
              <button
                type="submit"
                disabled={saving}
                style={{
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
                {saving ? 'Wird gespeichert...' : 'Änderungen speichern'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
