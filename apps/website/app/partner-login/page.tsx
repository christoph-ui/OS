'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import api from '@/lib/api';
import Link from 'next/link';
import styles from './partner-login.module.css';

export default function PartnerLoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [form, setForm] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    // Check if just registered
    if (searchParams.get('registered') === 'true') {
      setSuccess('Registrierung erfolgreich! Bitte melden Sie sich an.');
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await api.partnerLogin(form);

      // Store partner info
      localStorage.setItem('0711_partner', JSON.stringify(response.partner));
      localStorage.setItem('0711_user_id', response.user_id);

      // Redirect to Partner Console (Port 4020)
      window.location.href = 'http://localhost:4020/partner';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login fehlgeschlagen');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.loginContainer}>
      <div className={styles.loginBox}>
        <div className={styles.header}>
          <h1>Partner Portal</h1>
          <p className={styles.subtitle}>Anmeldung für Partner</p>
        </div>

        {error && (
          <div className={styles.error}>
            {error}
          </div>
        )}

        {success && (
          <div className={styles.success}>
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label>E-Mail</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
              placeholder="max@techconsult.de"
              className={styles.input}
              autoFocus
            />
          </div>

          <div className={styles.formGroup}>
            <label>Passwort</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
              placeholder="••••••••"
              className={styles.input}
            />
          </div>

          <button type="submit" disabled={loading} className={styles.submitButton}>
            {loading ? 'Wird angemeldet...' : 'Anmelden'}
          </button>
        </form>

        <div className={styles.signupPrompt}>
          Noch kein Partner?{' '}
          <Link href="/partner-signup">Jetzt registrieren</Link>
        </div>
      </div>
    </div>
  );
}
