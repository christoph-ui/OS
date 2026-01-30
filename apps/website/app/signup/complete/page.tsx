'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import styles from '../signup.module.css';

export default function SignupCompletePage() {
  const router = useRouter();

  useEffect(() => {
    // Auto-redirect after 5 seconds
    const timer = setTimeout(() => {
      router.push('/onboarding');
    }, 5000);

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className={styles.signupContainer}>
      <div className={styles.signupBox} style={{ maxWidth: '600px', textAlign: 'center' }}>
        {/* Success Icon */}
        <div style={{
          width: '80px',
          height: '80px',
          margin: '0 auto 2rem',
          backgroundColor: '#d9775720',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '3rem',
        }}>
          ✓
        </div>

        <h1>Willkommen bei 0711!</h1>
        <p className={styles.subtitle} style={{ fontSize: '1.1rem', marginBottom: '2rem' }}>
          Ihr Konto wurde erfolgreich erstellt
        </p>

        <div style={{
          textAlign: 'left',
          padding: '2rem',
          backgroundColor: '#f5f5f5',
          borderRadius: '12px',
          marginBottom: '2rem',
        }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 600 }}>
            Nächste Schritte:
          </h3>
          <ol style={{ paddingLeft: '1.5rem', lineHeight: '1.8' }}>
            <li>
              <strong>E-Mail bestätigen</strong>
              <br />
              <span style={{ fontSize: '0.9rem', color: '#666' }}>
                Prüfen Sie Ihren Posteingang für den Bestätigungslink
              </span>
            </li>
            <li style={{ marginTop: '1rem' }}>
              <strong>Onboarding abschließen</strong>
              <br />
              <span style={{ fontSize: '0.9rem', color: '#666' }}>
                Laden Sie Ihre Daten hoch und wählen Sie MCPs
              </span>
            </li>
            <li style={{ marginTop: '1rem' }}>
              <strong>Loslegen!</strong>
              <br />
              <span style={{ fontSize: '0.9rem', color: '#666' }}>
                Zugriff auf Ihre personalisierte KI-Plattform
              </span>
            </li>
          </ol>
        </div>

        <div style={{
          padding: '1.5rem',
          backgroundColor: '#e8f4f8',
          borderRadius: '8px',
          marginBottom: '2rem',
        }}>
          <p style={{ margin: 0, fontSize: '0.95rem' }}>
            📧 <strong>Wichtig:</strong> Bitte überprüfen Sie auch Ihren Spam-Ordner
          </p>
        </div>

        <button
          onClick={() => router.push('/onboarding')}
          className={styles.submitButton}
          style={{ marginBottom: '1rem' }}
        >
          Jetzt Onboarding starten →
        </button>

        <p style={{ fontSize: '0.9rem', color: '#666' }}>
          Sie werden automatisch in 5 Sekunden weitergeleitet...
        </p>

        <div style={{
          marginTop: '2rem',
          paddingTop: '2rem',
          borderTop: '1px solid #ddd',
        }}>
          <p style={{ fontSize: '0.9rem', color: '#666' }}>
            Benötigen Sie Hilfe?{' '}
            <a href="mailto:support@0711.io" style={{ color: 'var(--orange)' }}>
              support@0711.io
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
