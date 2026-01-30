'use client';

import { useState } from 'react';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import Link from 'next/link';
import styles from './experts.module.css';

const EXPERTS_DATA = [
  {
    avatar: 'SM',
    name: 'Sarah M.',
    title: 'Finance Expert',
    story: 'I left McKinsey after 8 years. Now I deliver more value in 4 hours than I did in 4 weeks. And I see my kids every day.',
    monthly: '€35k',
    clients: '7',
    hours: '25h',
  },
  {
    avatar: 'MK',
    name: 'Marcus K.',
    title: 'Tax Specialist',
    story: 'I was a Steuerberater assistant making €45k. Now I run CTAX for 9 businesses and finally earn what I\'m worth.',
    monthly: '€22k',
    clients: '9',
    hours: '30h',
  },
  {
    avatar: 'LT',
    name: 'Lisa T.',
    title: 'Full-Stack 0711',
    story: 'I work from Lisbon with 4 premium clients. €45k/month, 20 hours/week. This is what freedom looks like.',
    monthly: '€45k',
    clients: '4',
    hours: '20h',
  },
];

export default function ExpertsPage() {
  const [showExpertModal, setShowExpertModal] = useState(false);
  const [showCompanyModal, setShowCompanyModal] = useState(false);

  return (
    <>
      <Navigation variant="light" />

      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <div className={styles.heroLabel}>Introducing 0711 Expert Network</div>
          <h1>
            Work <strong>Different.</strong>
          </h1>
          <p className={styles.heroSub}>
            One expert. Ten companies. Infinite leverage.
            <br />
            This is the future of work.
          </p>
          <div className={styles.heroCta}>
            <button className={styles.btnPrimary} onClick={() => setShowExpertModal(true)}>
              Join the Revolution
            </button>
            <Link href="#how-it-works" className={styles.btnSecondary}>
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className={styles.problem}>
        <div className={styles.container}>
          <div className={styles.problemContent}>
            <h2>
              The old economy paid for <strong>presence.</strong>
              <br />
              The new economy pays for <strong>output.</strong>
            </h2>
            <ul className={styles.problemList}>
              <li>Companies hire full-time people for part-time problems.</li>
              <li>Talent is trapped in single jobs, capped at single salaries.</li>
              <li>Consultants charge €2,000 a day to make PowerPoints.</li>
              <li>Everyone works 60 hours. Nobody ships 60 hours of value.</li>
            </ul>
            <p className={styles.problemQuote}>
              "We've confused being busy with being productive.
              <br />
              That confusion costs the economy trillions."
            </p>
          </div>
        </div>
      </section>

      {/* Revolution */}
      <section className={styles.revolution}>
        <div className={styles.container}>
          <h2>
            What if one person
            <br />
            <span>could do the work of ten?</span>
          </h2>
          <p className={styles.revolutionSub}>
            Not by working harder. By working with AI that actually works.
          </p>
          <div className={styles.mathBox}>
            <div className={styles.mathEquation}>
              <div className={styles.mathItem}>
                <div className={styles.mathNumber}>1</div>
                <div className={styles.mathLabel}>Expert</div>
              </div>
              <div className={styles.mathSymbol}>+</div>
              <div className={styles.mathItem}>
                <div className={styles.mathNumber}>AI</div>
                <div className={styles.mathLabel}>0711 Platform</div>
              </div>
              <div className={styles.mathSymbol}>=</div>
              <div className={styles.mathItem}>
                <div className={styles.mathNumber}>10</div>
                <div className={styles.mathLabel}>Companies Served</div>
              </div>
            </div>
            <p className={styles.mathResult}>
              <strong>10x the output. 80% less cost. Everyone wins.</strong>
            </p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className={styles.howItWorks} id="how-it-works">
        <div className={styles.container}>
          <h2>Beautifully simple.</h2>
          <p className={styles.sectionSub}>
            The best technology disappears. You just see the results.
          </p>
          <div className={styles.steps}>
            <div className={styles.step}>
              <div className={styles.stepNumber}>01</div>
              <h3>You sign up</h3>
              <p>Expert or company. Sixty seconds. No sales calls. No demos. Just start.</p>
            </div>
            <div className={styles.step}>
              <div className={styles.stepNumber}>02</div>
              <h3>AI matches you</h3>
              <p>Experts find companies that need them. Companies find experts that get them. Instantly.</p>
            </div>
            <div className={styles.step}>
              <div className={styles.stepNumber}>03</div>
              <h3>Work happens</h3>
              <p>The expert operates your MCPs. AI does 90% of the work. You get 100% of the results.</p>
            </div>
            <div className={styles.step}>
              <div className={styles.stepNumber}>04</div>
              <h3>You scale</h3>
              <p>Experts add clients. Companies add experts. The platform learns. Everyone grows.</p>
            </div>
          </div>
        </div>
      </section>

      {/* For Experts */}
      <section className={styles.forExperts} id="for-experts">
        <div className={styles.container}>
          <div className={styles.splitContent}>
            <div>
              <h2>For <span>Experts</span></h2>
              <p style={{ fontSize: '1.2rem', marginBottom: '2rem', opacity: 0.9 }}>
                You're not a freelancer. You're not a consultant.<br />
                You're an AI-powered operator.
              </p>
              <ul className={styles.expertBenefits}>
                <li>
                  <div className={styles.benefitIcon}>💰</div>
                  <div className={styles.benefitText}>
                    <strong>Earn €20-50k/month</strong>
                    <span>Serve 5-10 clients simultaneously with AI leverage</span>
                  </div>
                </li>
                <li>
                  <div className={styles.benefitIcon}>✅</div>
                  <div className={styles.benefitText}>
                    <strong>Get paid. Guaranteed.</strong>
                    <span>Weekly payouts, every Friday. Escrow protection. No chasing invoices.</span>
                  </div>
                </li>
                <li>
                  <div className={styles.benefitIcon}>⏰</div>
                  <div className={styles.benefitText}>
                    <strong>Work 25 hours, not 60</strong>
                    <span>AI handles the grunt work. You handle the judgment.</span>
                  </div>
                </li>
                <li>
                  <div className={styles.benefitIcon}>🌍</div>
                  <div className={styles.benefitText}>
                    <strong>Work from anywhere</strong>
                    <span>Your clients are in the cloud. You can be too.</span>
                  </div>
                </li>
              </ul>
            </div>
            <div className={styles.expertStats}>
              <div className={styles.statCard}>
                <div className={styles.statNumber}>90%</div>
                <div className={styles.statLabel}>You keep of earnings</div>
              </div>
              <div className={styles.statCard}>
                <div className={styles.statNumber}>Fri</div>
                <div className={styles.statLabel}>Weekly payouts</div>
              </div>
              <div className={styles.statCard}>
                <div className={styles.statNumber}>4.9★</div>
                <div className={styles.statLabel}>Average expert rating</div>
              </div>
              <div className={styles.statCard}>
                <div className={styles.statNumber}>7</div>
                <div className={styles.statLabel}>Average clients per expert</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* For Companies */}
      <section className={styles.forCompanies} id="for-companies">
        <div className={styles.container}>
          <div className={styles.splitContent}>
            <div>
              <h2>For <span>Companies</span></h2>
              <p style={{ fontSize: '1.2rem', marginBottom: '2rem', color: 'var(--mid-gray)' }}>
                Stop hiring full-time for part-time problems.<br />
                Get world-class operators on demand.
              </p>
              <ul className={styles.companyBenefits}>
                <li>
                  <div className={styles.benefitIcon}>⚡</div>
                  <div className={styles.benefitText}>
                    <strong>Hire in 60 seconds</strong>
                    <span>No recruiters. No interviews. Just matched to perfect experts.</span>
                  </div>
                </li>
                <li>
                  <div className={styles.benefitIcon}>💎</div>
                  <div className={styles.benefitText}>
                    <strong>Pay 80% less</strong>
                    <span>€3k/month instead of €180k/year for better results.</span>
                  </div>
                </li>
                <li>
                  <div className={styles.benefitIcon}>💳</div>
                  <div className={styles.benefitText}>
                    <strong>One invoice. Done.</strong>
                    <span>We handle all payments. No contracts with experts. No admin.</span>
                  </div>
                </li>
                <li>
                  <div className={styles.benefitIcon}>📊</div>
                  <div className={styles.benefitText}>
                    <strong>See everything</strong>
                    <span>Real-time dashboards. Every task tracked. Full transparency.</span>
                  </div>
                </li>
              </ul>
            </div>
            <div className={styles.comparisonTable}>
              <div className={styles.comparisonHeader}>
                <div></div>
                <div>Traditional</div>
                <div>0711 Expert</div>
              </div>
              <div className={styles.comparisonRow}>
                <div>CFO</div>
                <div className={styles.old}>€180k/year</div>
                <div className={styles.new}>€36k/year</div>
              </div>
              <div className={styles.comparisonRow}>
                <div>Tax Advisor</div>
                <div className={styles.old}>€120k/year</div>
                <div className={styles.new}>€24k/year</div>
              </div>
              <div className={styles.comparisonRow}>
                <div>Marketing Lead</div>
                <div className={styles.old}>€95k/year</div>
                <div className={styles.new}>€30k/year</div>
              </div>
              <div className={styles.comparisonRow}>
                <div>Hiring Time</div>
                <div className={styles.old}>3-6 months</div>
                <div className={styles.new}>60 seconds</div>
              </div>
              <div className={styles.comparisonRow}>
                <div>Output Quality</div>
                <div className={styles.old}>Variable</div>
                <div className={styles.new}>10x with AI</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Profiles */}
      <section className={styles.profiles}>
        <div className={styles.container}>
          <h2>The new working class.</h2>
          <p className={styles.sectionSub}>Real people. Real results. Real freedom.</p>
          <div className={styles.profileGrid}>
            {EXPERTS_DATA.map((expert, idx) => (
              <div key={idx} className={styles.profileCard}>
                <div className={styles.profileHeader}>
                  <div className={styles.profileAvatar}>{expert.avatar}</div>
                  <div className={styles.profileInfo}>
                    <h3>{expert.name}</h3>
                    <span>{expert.title}</span>
                  </div>
                </div>
                <p className={styles.profileStory}>{expert.story}</p>
                <div className={styles.profileStats}>
                  <div className={styles.profileStat}>
                    <div className={styles.profileStatValue}>{expert.monthly}</div>
                    <div className={styles.profileStatLabel}>monthly</div>
                  </div>
                  <div className={styles.profileStat}>
                    <div className={styles.profileStatValue}>{expert.clients}</div>
                    <div className={styles.profileStatLabel}>clients</div>
                  </div>
                  <div className={styles.profileStat}>
                    <div className={styles.profileStatValue}>{expert.hours}</div>
                    <div className={styles.profileStatLabel}>per week</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Payments */}
      <section className={styles.payments} id="payments">
        <div className={styles.container}>
          <div className={styles.paymentsHeader}>
            <h2>Money flows. <span>Seamlessly.</span></h2>
            <p className={styles.sectionSub}>
              We handle everything. You focus on the work.
            </p>
          </div>

          <div className={styles.paymentFlow}>
            <div className={styles.flowStep}>
              <div className={`${styles.flowIcon} ${styles.companyIcon}`}>🏢</div>
              <div className={styles.flowLabel}>Company</div>
              <div className={styles.flowAction}>Pays monthly</div>
            </div>
            <div className={styles.flowArrow}>→</div>
            <div className={styles.flowStep}>
              <div className={`${styles.flowIcon} ${styles.platformIcon}`}>0711</div>
              <div className={styles.flowLabel}>Platform</div>
              <div className={styles.flowAction}>Holds & distributes</div>
            </div>
            <div className={styles.flowArrow}>→</div>
            <div className={styles.flowStep}>
              <div className={`${styles.flowIcon} ${styles.expertIcon}`}>🚀</div>
              <div className={styles.flowLabel}>Expert</div>
              <div className={styles.flowAction}>Gets paid weekly</div>
            </div>
          </div>

          <div className={styles.paymentFeatures}>
            <div className={styles.paymentCard}>
              <div className={styles.paymentCardIcon}>🔒</div>
              <h3>Escrow Protection</h3>
              <p>Funds are secured before work begins. Experts always get paid. Companies only pay for delivered work.</p>
            </div>
            <div className={styles.paymentCard}>
              <div className={styles.paymentCardIcon}>⚡</div>
              <h3>Weekly Payouts</h3>
              <p>Experts receive payments every Friday. No waiting 30, 60, or 90 days. Your money, when you need it.</p>
            </div>
            <div className={styles.paymentCard}>
              <div className={styles.paymentCardIcon}>📊</div>
              <h3>Full Transparency</h3>
              <p>Real-time dashboards for both sides. Track every euro. Download invoices instantly. No surprises.</p>
            </div>
            <div className={styles.paymentCard}>
              <div className={styles.paymentCardIcon}>🌍</div>
              <h3>Global Payments</h3>
              <p>EUR, USD, GBP. Bank transfer, SEPA, or Wise. Pay and get paid anywhere in the world.</p>
            </div>
          </div>

          <div className={styles.pricingStructure}>
            <h3>Simple, transparent pricing</h3>
            <div className={styles.pricingBoxes}>
              <div className={`${styles.pricingBox} ${styles.expertPricing}`}>
                <div className={styles.pricingLabel}>For Experts</div>
                <div className={styles.pricingRate}>90%</div>
                <div className={styles.pricingDesc}>You keep</div>
                <ul className={styles.pricingIncludes}>
                  <li>Weekly payouts</li>
                  <li>Payment protection</li>
                  <li>Tax documentation</li>
                  <li>Multi-currency support</li>
                </ul>
                <div className={styles.pricingFee}>10% platform fee</div>
              </div>
              <div className={`${styles.pricingBox} ${styles.companyPricing}`}>
                <div className={styles.pricingLabel}>For Companies</div>
                <div className={styles.pricingRate}>0%</div>
                <div className={styles.pricingDesc}>No added fees</div>
                <ul className={styles.pricingIncludes}>
                  <li>Pay expert rate only</li>
                  <li>Monthly invoicing</li>
                  <li>Escrow protection</li>
                  <li>Instant receipts</li>
                </ul>
                <div className={styles.pricingFee}>Expert rates as listed</div>
              </div>
            </div>
          </div>

          <div className={styles.trustBadges}>
            <div className={styles.trustBadge}>
              <span className={styles.trustNumber}>€2.4M+</span>
              <span className={styles.trustLabel}>Processed monthly</span>
            </div>
            <div className={styles.trustBadge}>
              <span className={styles.trustNumber}>100%</span>
              <span className={styles.trustLabel}>On-time payouts</span>
            </div>
            <div className={styles.trustBadge}>
              <span className={styles.trustNumber}>24h</span>
              <span className={styles.trustLabel}>Dispute resolution</span>
            </div>
            <div className={styles.trustBadge}>
              <span className={styles.trustNumber}>PCI-DSS</span>
              <span className={styles.trustLabel}>Compliant</span>
            </div>
          </div>
        </div>
      </section>

      {/* Manifesto */}
      <section className={styles.manifesto}>
        <div className={styles.manifestoContent}>
          <blockquote>
            "0711 Experts don't bill hours.<br />
            They <strong>deliver results.</strong><br /><br />
            They don't attend meetings.<br />
            They <strong>ship outcomes.</strong><br /><br />
            They don't work for one boss.<br />
            They <strong>serve many clients.</strong>"
          </blockquote>
          <ul className={styles.manifestoLines}>
            <li>This is the liberation of knowledge work.</li>
            <li>This is the end of corporate overhead.</li>
            <li>This is the future of how companies operate.</li>
          </ul>
          <p className={styles.manifestoCta}>One expert. Ten clients. Infinite leverage.</p>
        </div>
      </section>

      {/* Sign Up */}
      <section className={styles.signup} id="signup">
        <div className={styles.container}>
          <h2>Choose your path.</h2>
          <p className={styles.sectionSub}>Both lead to freedom. Pick yours.</p>
          <div className={styles.signupPaths}>
            <div className={`${styles.signupCard} ${styles.expert}`}>
              <div className={styles.signupIcon}>🚀</div>
              <h3>Become an Expert</h3>
              <div className={styles.signupLabel}>For operators & specialists</div>
              <p>Master the 0711 MCPs. Serve multiple clients. Build your empire.</p>
              <ul className={styles.signupFeatures}>
                <li>Free certification program</li>
                <li>Guaranteed first clients</li>
                <li>Weekly payouts (every Friday)</li>
                <li>Keep 90% of everything you earn</li>
                <li>Work from anywhere</li>
              </ul>
              <button className={styles.btn} onClick={() => setShowExpertModal(true)}>
                Apply as Expert
              </button>
            </div>
            <div className={`${styles.signupCard} ${styles.company}`}>
              <div className={styles.signupIcon}>🏢</div>
              <h3>Hire Experts</h3>
              <div className={styles.signupLabel}>For companies</div>
              <p>Get AI-powered operators on demand. Pay for output, not presence.</p>
              <ul className={styles.signupFeatures}>
                <li>Matched in 60 seconds</li>
                <li>80% cheaper than hiring</li>
                <li>One monthly invoice</li>
                <li>No added platform fees</li>
                <li>Cancel anytime</li>
              </ul>
              <button className={styles.btn} onClick={() => setShowCompanyModal(true)}>
                Find Your Expert
              </button>
            </div>
          </div>
        </div>
      </section>

      <Footer />

      {/* Expert Modal */}
      {showExpertModal && (
        <div className={styles.modalOverlay} onClick={() => setShowExpertModal(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <button className={styles.modalClose} onClick={() => setShowExpertModal(false)}>
              ×
            </button>
            <div className={styles.modalContent}>
              <h3>Join the Expert Network</h3>
              <p style={{ marginBottom: '32px', color: 'var(--mid-gray)' }}>
                Choose your path to freedom
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <Link
                  href="/expert-signup"
                  className={styles.btnPrimary}
                  style={{ textAlign: 'center', textDecoration: 'none', padding: '16px 32px' }}
                >
                  🚀 Apply as New Expert
                </Link>
                <Link
                  href="/expert-login"
                  className={styles.btnSecondary}
                  style={{ textAlign: 'center', textDecoration: 'none', padding: '16px 32px' }}
                >
                  🔑 Login (Existing Expert)
                </Link>
              </div>

              <p style={{ marginTop: '24px', fontSize: '14px', color: 'var(--mid-gray)', textAlign: 'center' }}>
                New experts approved within 2-5 business days
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Company Modal (placeholder) */}
      {showCompanyModal && (
        <div className={styles.modalOverlay} onClick={() => setShowCompanyModal(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <button className={styles.modalClose} onClick={() => setShowCompanyModal(false)}>
              ×
            </button>
            <div className={styles.modalContent}>
              <h3>Find Your Expert</h3>
              <p>Company signup form coming soon...</p>
              <button className={styles.btnPrimary} onClick={() => setShowCompanyModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
