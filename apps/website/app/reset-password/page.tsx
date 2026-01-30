'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import styles from '../signup/signup.module.css';

// Get API URL from environment variable (production-safe)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4080';

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token') || '';

  const [form, setForm] = useState({
    password: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (form.password !== form.confirmPassword) {
      setError('Passwörter stimmen nicht überein');
      setLoading(false);
      return;
    }

    if (form.password.length < 8) {
      setError('Passwort muss mindestens 8 Zeichen lang sein');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          new_password: form.password,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to reset password');
      }

      // Success - redirect to login
      router.push('/login?reset=success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className={styles.signupContainer}>
        <div className={styles.signupBox}>
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>⚠️</div>
            <h1>Ungültiger Link</h1>
            <p className={styles.subtitle}>
              Dieser Passwort-Reset-Link ist ungültig oder abgelaufen.
            </p>
            <Link
              href="/forgot-password"
              className={styles.submitButton}
              style={{ display: 'inline-block', marginTop: '2rem', textDecoration: 'none' }}
            >
              Neuen Link anfordern
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.signupContainer}>
      <div className={styles.signupBox}>
        <h1>Neues Passwort</h1>
        <p className={styles.subtitle}>
          Wählen Sie ein sicheres neues Passwort für Ihr Konto
        </p>

        {error && (
          <div className={styles.error}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label>Neues Passwort *</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
              minLength={8}
              placeholder="Mindestens 8 Zeichen"
              className={styles.input}
              autoComplete="new-password"
            />
            <small style={{ color: '#666', fontSize: '0.85rem' }}>
              Mindestens 8 Zeichen, empfohlen: Buchstaben, Zahlen, Sonderzeichen
            </small>
          </div>

          <div className={styles.formGroup}>
            <label>Passwort bestätigen *</label>
            <input
              type="password"
              value={form.confirmPassword}
              onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
              required
              minLength={8}
              placeholder="Passwort wiederholen"
              className={styles.input}
              autoComplete="new-password"
            />
          </div>

          {form.password && form.confirmPassword && (
            <div style={{
              padding: '0.75rem 1rem',
              marginBottom: '1rem',
              borderRadius: '8px',
              backgroundColor: form.password === form.confirmPassword ? '#e8f5e9' : '#fee',
              border: `1px solid ${form.password === form.confirmPassword ? '#4caf50' : '#f44336'}`,
              fontSize: '0.9rem',
              color: form.password === form.confirmPassword ? '#2e7d32' : '#c62828',
            }}>
              {form.password === form.confirmPassword ? '✓ Passwörter stimmen überein' : '✗ Passwörter stimmen nicht überein'}
            </div>
          )}

          <button type="submit" disabled={loading || form.password !== form.confirmPassword} className={styles.submitButton}>
            {loading ? 'Wird geändert...' : 'Passwort ändern'}
          </button>
        </form>

        <p className={styles.loginPrompt}>
          <Link href="/login">Zurück zum Login</Link>
        </p>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
