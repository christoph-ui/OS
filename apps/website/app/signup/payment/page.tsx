'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import api from '@/lib/api';
import Link from 'next/link';
import styles from '../signup.module.css';

function PaymentContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const plan = searchParams.get('plan') || 'professional';
  const cycle = searchParams.get('cycle') || 'annual';

  const [paymentMethod, setPaymentMethod] = useState<'card' | 'invoice' | 'sepa'>('invoice');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [invoiceData, setInvoiceData] = useState({
    vatId: '',
    billingEmail: '',
    poNumber: '',
  });

  const PRICING = {
    professional: {
      monthly: 990,
      annual: 9504, // 20% discount
    },
    business: {
      monthly: 2990,
      annual: 28704,
    },
  };

  const planPrice = PRICING[plan as keyof typeof PRICING]?.[cycle as keyof typeof PRICING.professional] || 990;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (paymentMethod === 'invoice') {
        // Create subscription with invoice payment
        const response = await api.createInvoiceSubscription({
          plan,
          billingCycle: cycle,
          vatId: invoiceData.vatId,
          billingEmail: invoiceData.billingEmail,
          poNumber: invoiceData.poNumber,
        });

        // Redirect to onboarding
        router.push('/onboarding');
      } else if (paymentMethod === 'card') {
        // TODO: Stripe card payment
        setError('Kreditkartenzahlung wird bald verfügbar sein. Bitte wählen Sie "Rechnung".');
      } else {
        // SEPA
        setError('SEPA-Lastschrift wird bald verfügbar sein. Bitte wählen Sie "Rechnung".');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Payment failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.signupContainer}>
      <div className={styles.signupBox} style={{ maxWidth: '600px' }}>
        <h1>Zahlungsinformationen</h1>
        <p className={styles.subtitle}>
          {plan === 'professional' ? 'Professional' : 'Business'} Plan -{' '}
          €{planPrice.toLocaleString('de-DE')} /{' '}
          {cycle === 'annual' ? 'Jahr' : 'Monat'}
        </p>

        {cycle === 'annual' && (
          <div style={{
            padding: '12px 16px',
            backgroundColor: '#d9775715',
            border: '1px solid #d97757',
            borderRadius: '8px',
            marginBottom: '2rem',
            fontSize: '0.9rem',
            color: '#141413',
          }}>
            💰 Sie sparen 20% mit jährlicher Zahlung
          </div>
        )}

        {error && (
          <div className={styles.error}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Payment Method Selection */}
          <div className={styles.formGroup}>
            <label>Zahlungsmethode</label>
            <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
              <button
                type="button"
                onClick={() => setPaymentMethod('invoice')}
                className={styles.input}
                style={{
                  flex: 1,
                  padding: '16px',
                  border: paymentMethod === 'invoice' ? '2px solid var(--orange)' : '1px solid #ddd',
                  backgroundColor: paymentMethod === 'invoice' ? '#d9775710' : '#fff',
                  cursor: 'pointer',
                  fontWeight: paymentMethod === 'invoice' ? '600' : '400',
                }}
              >
                📄 Rechnung
                <div style={{ fontSize: '0.8rem', marginTop: '4px', color: '#666' }}>
                  30 Tage Zahlungsziel
                </div>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod('card')}
                className={styles.input}
                style={{
                  flex: 1,
                  padding: '16px',
                  border: paymentMethod === 'card' ? '2px solid var(--orange)' : '1px solid #ddd',
                  backgroundColor: paymentMethod === 'card' ? '#d9775710' : '#fff',
                  cursor: 'pointer',
                  fontWeight: paymentMethod === 'card' ? '600' : '400',
                  opacity: 0.5,
                }}
                disabled
              >
                💳 Karte
                <div style={{ fontSize: '0.8rem', marginTop: '4px', color: '#666' }}>
                  Bald verfügbar
                </div>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod('sepa')}
                className={styles.input}
                style={{
                  flex: 1,
                  padding: '16px',
                  border: paymentMethod === 'sepa' ? '2px solid var(--orange)' : '1px solid #ddd',
                  backgroundColor: paymentMethod === 'sepa' ? '#d9775710' : '#fff',
                  cursor: 'pointer',
                  fontWeight: paymentMethod === 'sepa' ? '600' : '400',
                  opacity: 0.5,
                }}
                disabled
              >
                🏦 SEPA
                <div style={{ fontSize: '0.8rem', marginTop: '4px', color: '#666' }}>
                  Bald verfügbar
                </div>
              </button>
            </div>
          </div>

          {paymentMethod === 'invoice' && (
            <>
              <div className={styles.formGroup}>
                <label>USt-IdNr (optional)</label>
                <input
                  type="text"
                  value={invoiceData.vatId}
                  onChange={(e) => setInvoiceData({ ...invoiceData, vatId: e.target.value })}
                  placeholder="DE123456789"
                  className={styles.input}
                />
                <small style={{ color: '#666', fontSize: '0.85rem' }}>
                  Für Reverse-Charge-Verfahren (EU B2B)
                </small>
              </div>

              <div className={styles.formGroup}>
                <label>Rechnungs-E-Mail</label>
                <input
                  type="email"
                  value={invoiceData.billingEmail}
                  onChange={(e) => setInvoiceData({ ...invoiceData, billingEmail: e.target.value })}
                  placeholder="buchhaltung@firma.de"
                  className={styles.input}
                />
              </div>

              <div className={styles.formGroup}>
                <label>Bestellnummer (optional)</label>
                <input
                  type="text"
                  value={invoiceData.poNumber}
                  onChange={(e) => setInvoiceData({ ...invoiceData, poNumber: e.target.value })}
                  placeholder="PO-2025-001"
                  className={styles.input}
                />
              </div>
            </>
          )}

          <button type="submit" disabled={loading} className={styles.submitButton}>
            {loading ? 'Wird verarbeitet...' : 'Subscription erstellen'}
          </button>
        </form>

        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          backgroundColor: '#f5f5f5',
          borderRadius: '8px',
          fontSize: '0.85rem',
          color: '#666',
        }}>
          <strong>Hinweis:</strong> Nach der Bestätigung erhalten Sie:
          <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
            <li>Zugang zum Onboarding-Wizard</li>
            <li>Ihre Rechnung per E-Mail (bei Rechnungszahlung)</li>
            <li>Lizenzschlüssel für Self-Hosted Deployment</li>
          </ul>
        </div>

        <p className={styles.loginPrompt} style={{ marginTop: '2rem' }}>
          <Link href="/signup/plan">← Zurück zur Planauswahl</Link>
        </p>
      </div>
    </div>
  );
}

export default function PaymentPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <PaymentContent />
    </Suspense>
  );
}
