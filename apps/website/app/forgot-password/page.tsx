'use client';

import { useState } from 'react';
import Link from 'next/link';
import styles from '../signup/signup.module.css';

// Get API URL from environment variable (production-safe)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4080';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        throw new Error('Failed to send reset email');
      }

      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className={styles.signupContainer}>
        <div className={styles.signupBox}>
          <div style={{
            textAlign: 'center',
            padding: '2rem 0',
          }}>
            <div style={{
              fontSize: '4rem',
              marginBottom: '1rem',
            }}>
              📧
            </div>
            <h1>E-Mail gesendet!</h1>
            <p className={styles.subtitle}>
              Wir haben Ihnen einen Link zum Zurücksetzen des Passworts an <strong>{email}</strong> gesendet.
            </p>
            <p style={{
              marginTop: '2rem',
              padding: '1rem',
              backgroundColor: '#f5f5f5',
              borderRadius: '8px',
              fontSize: '0.9rem',
              color: '#666',
            }}>
              Bitte überprüfen Sie auch Ihren Spam-Ordner.
              <br />
              Der Link ist 1 Stunde gültig.
            </p>
            <Link
              href="/login"
              className={styles.submitButton}
              style={{ display: 'inline-block', marginTop: '2rem', textDecoration: 'none' }}
            >
              Zurück zum Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.signupContainer}>
      <div className={styles.signupBox}>
        <h1>Passwort zurücksetzen</h1>
        <p className={styles.subtitle}>
          Geben Sie Ihre E-Mail-Adresse ein und wir senden Ihnen einen Link zum Zurücksetzen.
        </p>

        {error && (
          <div className={styles.error}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label>E-Mail *</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="max@mustermann.de"
              className={styles.input}
              autoComplete="email"
            />
          </div>

          <button type="submit" disabled={loading} className={styles.submitButton}>
            {loading ? 'Wird gesendet...' : 'Reset-Link senden'}
          </button>
        </form>

        <p className={styles.loginPrompt}>
          Doch erinnert?{' '}
          <Link href="/login">Zurück zum Login</Link>
        </p>
      </div>
    </div>
  );
}
