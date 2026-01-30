'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Link from 'next/link';
import styles from './signup.module.css';

interface SignupForm {
  companyName: string;
  contactName: string;
  email: string;
  password: string;
  companyType: string;
  vatId?: string;
  street?: string;
  city?: string;
  postalCode?: string;
  contactPhone?: string;
}

export default function SignupPage() {
  const router = useRouter();
  const [form, setForm] = useState<SignupForm>({
    companyName: '',
    contactName: '',
    email: '',
    password: '',
    companyType: 'GmbH',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.signup(form);

      // Store token if provided (test mode or immediate login)
      if (response.token) {
        localStorage.setItem('0711_token', response.token);
        api.setToken(response.token);
      }

      // Store customer ID for later use
      if (response.customer_id) {
        localStorage.setItem('0711_customer_id', response.customer_id);
      }

      // Store signup data for onboarding wizard
      localStorage.setItem('signup_company_name', form.companyName);
      localStorage.setItem('signup_contact_name', form.contactName);
      localStorage.setItem('signup_contact_email', form.email);
      localStorage.setItem('signup_company_type', form.companyType);
      if (form.vatId) localStorage.setItem('signup_vat_id', form.vatId);

      // Redirect to plan selection
      router.push(`/signup/plan?email=${encodeURIComponent(form.email)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.signupContainer}>
      <div className={styles.signupBox}>
        <h1>Starten Sie mit 0711</h1>
        <p className={styles.subtitle}>Ihr KI-Betriebssystem in 5 Minuten</p>

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
              placeholder="Mustermann GmbH"
              className={styles.input}
            />
          </div>

          <div className={styles.formGroup}>
            <label>Rechtsform</label>
            <select
              value={form.companyType}
              onChange={(e) => setForm({ ...form, companyType: e.target.value })}
              className={styles.input}
            >
              <option value="GmbH">GmbH</option>
              <option value="UG">UG (haftungsbeschränkt)</option>
              <option value="AG">AG</option>
              <option value="KG">KG</option>
              <option value="OHG">OHG</option>
              <option value="Einzelunternehmen">Einzelunternehmen</option>
              <option value="Freiberufler">Freiberufler</option>
            </select>
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
              placeholder="max@mustermann.de"
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

          <button type="submit" disabled={loading} className={styles.submitButton}>
            {loading ? 'Wird erstellt...' : 'Konto erstellen'}
          </button>
        </form>

        <p className={styles.loginPrompt}>
          Bereits ein Konto?{' '}
          <Link href="/login">Anmelden</Link>
        </p>

        <div className={styles.enterpriseSection}>
          <p>Enterprise-Kunde?</p>
          <Link href="/enterprise" className={styles.enterpriseLink}>
            Vertrieb kontaktieren
          </Link>
        </div>
      </div>
    </div>
  );
}
