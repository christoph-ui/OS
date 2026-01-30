'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Link from 'next/link';
import styles from './dashboard.module.css';

function DashboardContent() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      // Check if logged in
      const token = localStorage.getItem('0711_token');
      if (!token) {
        router.push('/login');
        return;
      }

      // Load subscription and deployments
      const [subscription, deployments] = await Promise.all([
        api.getCurrentSubscription(),
        api.listDeployments(),
      ]);

      setData({ subscription, deployments });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      // If unauthorized, redirect to login
      if (err instanceof Error && err.message.includes('401')) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          {error}
          <br />
          <Link href="/login">Go to Login</Link>
        </div>
      </div>
    );
  }

  const { subscription, deployments } = data || {};

  return (
    <div className={styles.container}>
      <div className={styles.content}>
        {/* Header */}
        <header className={styles.header}>
          <div>
            <h1>Dashboard</h1>
            <p>Verwalten Sie Ihr 0711 Konto</p>
          </div>
          <Link href="/" className={styles.homeLink}>
            ← Zur Startseite
          </Link>
        </header>

        {/* Main Grid */}
        <div className={styles.grid}>
          {/* Subscription Card */}
          <div className={styles.card}>
            <h2>💳 Subscription</h2>
            {subscription ? (
              <>
                <div className={styles.statRow}>
                  <span>Plan:</span>
                  <strong>{subscription.plan || 'Starter'}</strong>
                </div>
                <div className={styles.statRow}>
                  <span>Status:</span>
                  <strong className={styles.statusActive}>
                    {subscription.status === 'active' ? 'Aktiv' : subscription.status}
                  </strong>
                </div>
                <div className={styles.statRow}>
                  <span>Preis:</span>
                  <strong>€{subscription.price_monthly || 0}/Monat</strong>
                </div>
                <div className={styles.statRow}>
                  <span>Nächste Rechnung:</span>
                  <span>{subscription.next_billing_date || 'N/A'}</span>
                </div>
                <Link href="/settings/subscription" className={styles.cardButton}>
                  Subscription verwalten
                </Link>
              </>
            ) : (
              <>
                <p>Kein aktives Abo</p>
                <Link href="/signup/plan" className={styles.cardButton}>
                  Plan auswählen
                </Link>
              </>
            )}
          </div>

          {/* Deployments Card */}
          <div className={styles.card}>
            <h2>🚀 Deployments</h2>
            {deployments && deployments.length > 0 ? (
              <>
                <div className={styles.deploymentList}>
                  {deployments.map((dep: any, idx: number) => (
                    <div key={idx} className={styles.deployment}>
                      <div>
                        <strong>{dep.name || `Deployment ${idx + 1}`}</strong>
                        <br />
                        <span style={{ fontSize: '0.85rem', color: '#666' }}>
                          {dep.deployment_type || 'managed'}
                        </span>
                      </div>
                      <a
                        href={dep.console_url || 'http://localhost:4020'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.deploymentLink}
                      >
                        Open →
                      </a>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <>
                <p>Keine Deployments</p>
                <Link href="/onboarding" className={styles.cardButton}>
                  Onboarding starten
                </Link>
              </>
            )}
          </div>

          {/* Usage Card */}
          <div className={styles.card}>
            <h2>📊 Nutzung (aktueller Monat)</h2>
            <div className={styles.statRow}>
              <span>Anfragen:</span>
              <strong>{data?.usage?.queries || 0}</strong>
            </div>
            <div className={styles.statRow}>
              <span>Datenspeicher:</span>
              <strong>{data?.usage?.storage_gb || 0} GB</strong>
            </div>
            <div className={styles.statRow}>
              <span>MCPs aktiv:</span>
              <strong>{data?.usage?.active_mcps || 3}</strong>
            </div>
            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{ width: `${(data?.usage?.queries || 0) / 100}%` }}
              />
            </div>
            <p style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.5rem' }}>
              {data?.usage?.queries || 0} / 10,000 Anfragen
            </p>
          </div>

          {/* Quick Actions */}
          <div className={styles.card}>
            <h2>⚡ Quick Actions</h2>
            <div className={styles.actionButtons}>
              <Link href="/onboarding" className={styles.actionButton}>
                🚀 Neues Deployment
              </Link>
              <Link href="/marketplace" className={styles.actionButton}>
                🔌 MCPs hinzufügen
              </Link>
              <Link href="/settings" className={styles.actionButton}>
                ⚙️ Einstellungen
              </Link>
              <a
                href="mailto:support@0711.io"
                className={styles.actionButton}
              >
                💬 Support kontaktieren
              </a>
            </div>
          </div>
        </div>

        {/* Bottom Links */}
        <div className={styles.bottomLinks}>
          <Link href="/docs">Dokumentation</Link>
          <Link href="/pricing">Pricing</Link>
          <Link href="/enterprise">Enterprise</Link>
          <button
            onClick={() => {
              localStorage.removeItem('0711_token');
              router.push('/login');
            }}
            className={styles.logoutButton}
          >
            Abmelden
          </button>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
