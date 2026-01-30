'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
};

interface PartnerSignupForm {
  companyName: string;
  contactName: string;
  email: string;
  password: string;
  phone?: string;
  street?: string;
  city?: string;
  postalCode?: string;
  vatId?: string;
}

export default function PartnerSignupPage() {
  const router = useRouter();
  const [form, setForm] = useState<PartnerSignupForm>({
    companyName: '',
    contactName: '',
    email: '',
    password: '',
  });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:4080/api/partners/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: form.companyName,
          contact_name: form.contactName,
          contact_email: form.email,
          password: form.password,
          contact_phone: form.phone,
          street: form.street,
          city: form.city,
          postal_code: form.postalCode,
          country: 'DE',
          vat_id: form.vatId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registrierung fehlgeschlagen');
      }

      // Success - redirect to login
      router.push('/partner-login?registered=true');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registrierung fehlgeschlagen');
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
      padding: '2rem',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '520px',
        padding: '3rem',
        backgroundColor: '#1a1a19',
        borderRadius: '16px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            color: colors.light,
            fontSize: '2rem',
            marginBottom: '0.5rem',
          }}>
            Partner Portal
          </h1>
          <p style={{
            fontFamily: "'Lora', Georgia, serif",
            color: colors.midGray,
            margin: 0,
          }}>
            Verwalten Sie mehrere 0711-Kunden
          </p>
        </div>

        {error && (
          <div style={{
            background: '#3d1f1f',
            border: `1px solid ${colors.orange}`,
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1.5rem',
            color: '#ff8a80',
            fontSize: '0.875rem',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <FormField
            label="Firmenname *"
            type="text"
            value={form.companyName}
            onChange={(v) => setForm({ ...form, companyName: v })}
            required
            placeholder="TechConsult GmbH"
          />

          <FormField
            label="Ihr Name *"
            type="text"
            value={form.contactName}
            onChange={(v) => setForm({ ...form, contactName: v })}
            required
            placeholder="Max Mustermann"
          />

          <FormField
            label="E-Mail *"
            type="email"
            value={form.email}
            onChange={(v) => setForm({ ...form, email: v })}
            required
            placeholder="max@techconsult.de"
          />

          <FormField
            label="Passwort *"
            type="password"
            value={form.password}
            onChange={(v) => setForm({ ...form, password: v })}
            required
            minLength={8}
            placeholder="Mindestens 8 Zeichen"
          />

          <FormField
            label="Telefon"
            type="tel"
            value={form.phone || ''}
            onChange={(v) => setForm({ ...form, phone: v })}
            placeholder="+49 711 12345678"
          />

          {/* Advanced Fields Toggle */}
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            style={{
              width: '100%',
              padding: '0.75rem',
              background: 'transparent',
              border: '1px dashed #444',
              borderRadius: '8px',
              color: colors.midGray,
              fontSize: '0.875rem',
              cursor: 'pointer',
              marginBottom: '1rem',
              fontFamily: "'Poppins', Arial, sans-serif",
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.borderColor = colors.orange;
              e.currentTarget.style.color = colors.orange;
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.borderColor = '#444';
              e.currentTarget.style.color = colors.midGray;
            }}
          >
            {showAdvanced ? '▼' : '▶'} Erweiterte Angaben
          </button>

          {showAdvanced && (
            <>
              <FormField
                label="Straße"
                value={form.street || ''}
                onChange={(v) => setForm({ ...form, street: v })}
                placeholder="Musterstraße 123"
              />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
                <FormField
                  label="PLZ"
                  value={form.postalCode || ''}
                  onChange={(v) => setForm({ ...form, postalCode: v })}
                  placeholder="70173"
                />
                <FormField
                  label="Stadt"
                  value={form.city || ''}
                  onChange={(v) => setForm({ ...form, city: v })}
                  placeholder="Stuttgart"
                />
              </div>

              <FormField
                label="USt-IdNr."
                value={form.vatId || ''}
                onChange={(v) => setForm({ ...form, vatId: v })}
                placeholder="DE123456789"
              />
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '1rem',
              background: loading ? '#666' : colors.orange,
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              fontFamily: "'Poppins', Arial, sans-serif",
              transition: 'all 0.3s ease',
              marginTop: '1rem',
            }}
            onMouseOver={(e) => {
              if (!loading) {
                e.currentTarget.style.background = '#c86647';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }
            }}
            onMouseOut={(e) => {
              if (!loading) {
                e.currentTarget.style.background = colors.orange;
                e.currentTarget.style.transform = 'translateY(0)';
              }
            }}
          >
            {loading ? 'Wird erstellt...' : 'Registrieren'}
          </button>
        </form>

        <div style={{
          textAlign: 'center',
          marginTop: '1.5rem',
          color: '#666',
          fontSize: '0.875rem',
        }}>
          Bereits Partner?{' '}
          <a
            href="/partner-login"
            style={{
              color: colors.orange,
              textDecoration: 'none',
              fontWeight: 500,
            }}
          >
            Zum Login
          </a>
        </div>
      </div>
    </div>
  );
}

function FormField({
  label,
  type = 'text',
  value,
  onChange,
  required = false,
  placeholder = '',
  minLength,
}: {
  label: string;
  type?: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  placeholder?: string;
  minLength?: number;
}) {
  return (
    <div style={{ marginBottom: '1.25rem' }}>
      <label style={{
        display: 'block',
        color: colors.midGray,
        marginBottom: '0.5rem',
        fontSize: '0.875rem',
        fontFamily: "'Poppins', Arial, sans-serif",
      }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        placeholder={placeholder}
        minLength={minLength}
        style={{
          width: '100%',
          padding: '0.875rem',
          background: colors.dark,
          border: '1px solid #333',
          borderRadius: '8px',
          color: colors.light,
          fontSize: '1rem',
          fontFamily: "'Lora', Georgia, serif",
          transition: 'border-color 0.2s',
        }}
        onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
        onBlur={(e) => e.currentTarget.style.borderColor = '#333'}
      />
    </div>
  );
}
