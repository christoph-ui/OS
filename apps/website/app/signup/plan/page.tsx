'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import styles from './plan.module.css';

const PLANS = [
  {
    id: 'starter',
    name: 'Starter',
    price: 0,
    period: 'Kostenlos',
    features: [
      '1 MCP (CTAX oder ETIM)',
      '10 GB Datenspeicher',
      '1.000 Anfragen/Monat',
      'Community Support',
      'Self-Hosted',
    ],
    cta: 'Kostenlos starten',
    popular: false,
  },
  {
    id: 'professional',
    name: 'Professional',
    price: 990,
    period: '/Monat',
    features: [
      '5 MCPs',
      '100 GB Datenspeicher',
      '10.000 Anfragen/Monat',
      'E-Mail Support',
      'Self-Hosted oder Managed',
    ],
    cta: 'Plan wählen',
    popular: true,
  },
  {
    id: 'business',
    name: 'Business',
    price: 2990,
    period: '/Monat',
    features: [
      'Alle MCPs',
      '1 TB Datenspeicher',
      'Unbegrenzte Anfragen',
      'Telefon Support + SLA',
      'On-Premise Option',
      'DATEV Integration',
    ],
    cta: 'Plan wählen',
    popular: false,
  },
];

function PlanSelectionContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('annual');

  const handleContinue = async () => {
    if (!selectedPlan) return;

    try {
      // Save plan choice to backend
      await api.savePlanChoice(selectedPlan, billingCycle);

      if (selectedPlan === 'starter') {
        // Free plan - go directly to complete
        router.push('/signup/complete');
      } else {
        // Paid plan - go to payment
        router.push(`/signup/payment?plan=${selectedPlan}&cycle=${billingCycle}`);
      }
    } catch (error) {
      console.error('Failed to save plan choice:', error);
      // Continue anyway - plan will be saved in localStorage as fallback
      if (selectedPlan === 'starter') {
        router.push('/signup/complete');
      } else {
        router.push(`/signup/payment?plan=${selectedPlan}&cycle=${billingCycle}`);
      }
    }
  };

  return (
    <div className={styles.planContainer}>
      <h1>Wählen Sie Ihren Plan</h1>
      <p className={styles.subtitle}>Starten Sie kostenlos, upgraden Sie wenn Sie wachsen</p>

      {/* Billing toggle */}
      <div className={styles.billingToggle}>
        <button
          onClick={() => setBillingCycle('monthly')}
          className={billingCycle === 'monthly' ? styles.active : ''}
        >
          Monatlich
        </button>
        <button
          onClick={() => setBillingCycle('annual')}
          className={billingCycle === 'annual' ? styles.active : ''}
        >
          Jährlich (-20%)
        </button>
      </div>

      {/* Plans grid */}
      <div className={styles.plansGrid}>
        {PLANS.map((plan) => (
          <div
            key={plan.id}
            onClick={() => setSelectedPlan(plan.id)}
            className={`${styles.planCard} ${selectedPlan === plan.id ? styles.selected : ''} ${
              plan.popular ? styles.popular : ''
            }`}
          >
            {plan.popular && <div className={styles.popularBadge}>BELIEBT</div>}

            <h3>{plan.name}</h3>

            <div className={styles.price}>
              <span className={styles.amount}>
                {plan.price === 0
                  ? '€0'
                  : `€${billingCycle === 'annual' ? Math.round(plan.price * 0.8) : plan.price}`}
              </span>
              <span className={styles.period}>{plan.period}</span>
            </div>

            <ul className={styles.features}>
              {plan.features.map((feature, i) => (
                <li key={i}>
                  <span className={styles.checkmark}>✓</span>
                  {feature}
                </li>
              ))}
            </ul>

            <button className={styles.selectButton}>
              {selectedPlan === plan.id ? '✓ Ausgewählt' : plan.cta}
            </button>
          </div>
        ))}
      </div>

      {/* Enterprise CTA */}
      <div className={styles.enterpriseBox}>
        <h3>Enterprise</h3>
        <p>Individuelle Preise, On-Premise, DATEV-Integration, dedizierter Support</p>
        <Link href="/enterprise">Vertrieb kontaktieren</Link>
      </div>

      {/* Continue button */}
      {selectedPlan && (
        <div className={styles.continueBar}>
          <div>
            <span className={styles.selectedLabel}>Ausgewählt: </span>
            <span className={styles.selectedPlan}>
              {PLANS.find((p) => p.id === selectedPlan)?.name}
            </span>
          </div>
          <button onClick={handleContinue} className={styles.continueButton}>
            Weiter zur Zahlung →
          </button>
        </div>
      )}
    </div>
  );
}

export default function PlanSelectionPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <PlanSelectionContent />
    </Suspense>
  );
}
