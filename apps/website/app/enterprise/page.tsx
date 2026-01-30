'use client';

import { useState } from 'react';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import styles from './enterprise.module.css';

export default function EnterprisePage() {
  const [form, setForm] = useState({
    companyName: '',
    contactName: '',
    email: '',
    phone: '',
    employeeCount: '500+',
    message: '',
  });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // In production: Send to CRM/Email
      await new Promise(resolve => setTimeout(resolve, 1000));

      console.log('Enterprise contact request:', form);
      setSubmitted(true);
    } catch (error) {
      console.error('Error submitting:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navigation variant="light" />

      <div className={styles.container}>
        <div className={styles.content}>
          {/* Header */}
          <div className={styles.header}>
            <h1>Enterprise</h1>
            <p className={styles.subtitle}>
              Maßgeschneiderte Lösungen für Großunternehmen und Konzerne
            </p>
          </div>

          {!submitted ? (
            <div className={styles.grid}>
              {/* Left: Features */}
              <div className={styles.features}>
                <h2>Enterprise Features</h2>

                <div className={styles.feature}>
                  <div className={styles.featureIcon}>🏢</div>
                  <div>
                    <h3>Dedicated Infrastructure</h3>
                    <p>Isolierte GPU-Cluster, private LoRAs, dedizierte Lakehouse-Instanzen</p>
                  </div>
                </div>

                <div className={styles.feature}>
                  <div className={styles.featureIcon}>🔒</div>
                  <div>
                    <h3>On-Premise & Air-Gap</h3>
                    <p>Vollständig offline betreibbar, keine externe Verbindung nötig</p>
                  </div>
                </div>

                <div className={styles.feature}>
                  <div className={styles.featureIcon}>🛡️</div>
                  <div>
                    <h3>Compliance & Security</h3>
                    <p>ISO 27001, BSI C5, DSGVO, SOC 2, individuelle Audits</p>
                  </div>
                </div>

                <div className={styles.feature}>
                  <div className={styles.featureIcon}>🤝</div>
                  <div>
                    <h3>Premium Support</h3>
                    <p>24/7 Telefon-Support, dedizierter Customer Success Manager, SLA 99.9%</p>
                  </div>
                </div>

                <div className={styles.feature}>
                  <div className={styles.featureIcon}>🔧</div>
                  <div>
                    <h3>Custom MCPs</h3>
                    <p>Wir entwickeln maßgeschneiderte MCPs für Ihre spezifischen Prozesse</p>
                  </div>
                </div>

                <div className={styles.feature}>
                  <div className={styles.featureIcon}>📊</div>
                  <div>
                    <h3>Training & Onboarding</h3>
                    <p>Dediziertes Training-Programm für Ihre Teams, Workshops, Dokumentation</p>
                  </div>
                </div>

                <div className={styles.pricing}>
                  <h3>Pricing</h3>
                  <p>
                    Individuelle Angebote ab €25.000/Monat
                    <br />
                    <span style={{ fontSize: '0.9rem', opacity: 0.7 }}>
                      Abhängig von Anzahl der Nutzer, MCPs, und Datenvolumen
                    </span>
                  </p>
                </div>
              </div>

              {/* Right: Contact Form */}
              <div className={styles.formContainer}>
                <h2>Kontakt aufnehmen</h2>
                <p style={{ marginBottom: '2rem', color: '#b0aea5' }}>
                  Unser Enterprise-Team meldet sich innerhalb von 24 Stunden
                </p>

                <form onSubmit={handleSubmit} className={styles.form}>
                  <div className={styles.formGroup}>
                    <label>Unternehmensname *</label>
                    <input
                      type="text"
                      value={form.companyName}
                      onChange={(e) => setForm({ ...form, companyName: e.target.value })}
                      required
                      placeholder="Ihre Firma GmbH"
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
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label>Geschäftliche E-Mail *</label>
                    <input
                      type="email"
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                      required
                      placeholder="max@firma.de"
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label>Telefon</label>
                    <input
                      type="tel"
                      value={form.phone}
                      onChange={(e) => setForm({ ...form, phone: e.target.value })}
                      placeholder="+49 711 123456"
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label>Unternehmensgröße</label>
                    <select
                      value={form.employeeCount}
                      onChange={(e) => setForm({ ...form, employeeCount: e.target.value })}
                    >
                      <option value="100-500">100-500 Mitarbeiter</option>
                      <option value="500-1000">500-1.000 Mitarbeiter</option>
                      <option value="1000-5000">1.000-5.000 Mitarbeiter</option>
                      <option value="5000+">5.000+ Mitarbeiter</option>
                    </select>
                  </div>

                  <div className={styles.formGroup}>
                    <label>Ihre Anforderungen</label>
                    <textarea
                      value={form.message}
                      onChange={(e) => setForm({ ...form, message: e.target.value })}
                      placeholder="Beschreiben Sie Ihre Anforderungen, geplante Einsatzgebiete, besondere Compliance-Anforderungen..."
                      rows={4}
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className={styles.submitButton}
                  >
                    {loading ? 'Wird gesendet...' : 'Angebot anfordern'}
                  </button>
                </form>

                <p style={{
                  marginTop: '1.5rem',
                  fontSize: '0.85rem',
                  color: '#b0aea5',
                  textAlign: 'center',
                }}>
                  Oder direkt anrufen: <strong>+49 711 0711 0711</strong>
                </p>
              </div>
            </div>
          ) : (
            <div className={styles.successMessage}>
              <div style={{
                fontSize: '4rem',
                marginBottom: '1rem',
              }}>
                ✓
              </div>
              <h2>Vielen Dank!</h2>
              <p>
                Ihre Anfrage wurde gesendet. Unser Enterprise-Team wird sich innerhalb von 24 Stunden bei Ihnen melden.
              </p>
              <p style={{ marginTop: '2rem' }}>
                <a href="/" style={{ color: '#d97757' }}>
                  ← Zurück zur Startseite
                </a>
              </p>
            </div>
          )}
        </div>
      </div>

      <Footer />
    </>
  );
}
