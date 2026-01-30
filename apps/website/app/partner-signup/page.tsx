'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Link from 'next/link';
import styles from './partner-signup.module.css';

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
      await api.partnerSignup(form);

      // Success - redirect to login with message
      router.push('/partner-login?registered=true');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registrierung fehlgeschlagen');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.signupContainer}>
      <div className={styles.signupBox}>
        <div className={styles.header}>
          <h1>Partner Portal</h1>
          <p className={styles.subtitle}>Verwalten Sie mehrere 0711-Kunden</p>
        </div>

        {error && (
          <div className={styles.error}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label>Firmenname *</label>
            <input
              type="text"
              value={form.companyName}
              onChange={(e) => setForm({ ...form, companyName: e.target.value })}
              required
              placeholder="TechConsult GmbH"
              className={styles.input}
            />
          </div>

          <div className={styles.formGroup}>
            <label>Ihr Name *</label>
            <input
              type="text"
              value={form.contactName}
              onChange={(e) => setForm({ ...form, contactName: e.target.value })}
              required
              placeholder="Max Mustermann"
              className={styles.input}
            />
          </div>

          <div className={styles.formGroup}>
            <label>E-Mail *</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
              placeholder="max@techconsult.de"
              className={styles.input}
            />
          </div>

          <div className={styles.formGroup}>
            <label>Passwort *</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
              minLength={8}
              placeholder="Mindestens 8 Zeichen"
              className={styles.input}
            />
          </div>

          <div className={styles.formGroup}>
            <label>Telefon</label>
            <input
              type="tel"
              value={form.phone || ''}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              placeholder="+49 711 12345678"
              className={styles.input}
            />
          </div>

          {/* Advanced Fields */}
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={styles.toggleButton}
          >
            {showAdvanced ? '▼' : '▶'} Erweiterte Angaben
          </button>

          {showAdvanced && (
            <>
              <div className={styles.formGroup}>
                <label>Straße</label>
                <input
                  type="text"
                  value={form.street || ''}
                  onChange={(e) => setForm({ ...form, street: e.target.value })}
                  placeholder="Musterstraße 123"
                  className={styles.input}
                />
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label>PLZ</label>
                  <input
                    type="text"
                    value={form.postalCode || ''}
                    onChange={(e) => setForm({ ...form, postalCode: e.target.value })}
                    placeholder="70173"
                    className={styles.input}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label>Stadt</label>
                  <input
                    type="text"
                    value={form.city || ''}
                    onChange={(e) => setForm({ ...form, city: e.target.value })}
                    placeholder="Stuttgart"
                    className={styles.input}
                  />
                </div>
              </div>

              <div className={styles.formGroup}>
                <label>USt-IdNr.</label>
                <input
                  type="text"
                  value={form.vatId || ''}
                  onChange={(e) => setForm({ ...form, vatId: e.target.value })}
                  placeholder="DE123456789"
                  className={styles.input}
                />
              </div>
            </>
          )}

          <button type="submit" disabled={loading} className={styles.submitButton}>
            {loading ? 'Wird erstellt...' : 'Registrieren'}
          </button>
        </form>

        <div className={styles.loginPrompt}>
          Bereits Partner?{' '}
          <Link href="/partner-login">Zum Login</Link>
        </div>
      </div>
    </div>
  );
}
