import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import Link from 'next/link';
import styles from './bloodsuckers.module.css';

const BLOODSUCKERS = [
  {
    icon: '🧛',
    title: 'Management Consultants',
    cost: '€2,500/day',
    sins: [
      'Borrowing your watch to tell you the time',
      '200-slide decks',
      '"Best practices"',
      'Junior analysts at senior prices',
      'Leaving before implementation',
    ],
    replacement: 'Research & Intelligence MCP',
    savings: '€2,500/month instead of €2,500/day',
  },
  {
    icon: '🦇',
    title: 'Corporate Lawyers',
    cost: '€500/hour',
    sins: [
      'Billing in 6-minute increments',
      '"Let me research that"',
      'Emails that cost €200',
      'Creating problems to solve',
      'Latin phrases nobody asked for',
    ],
    replacement: 'Law MCP + Contract Review LLM',
    savings: '95% of legal work automated',
  },
  {
    icon: '🩸',
    title: 'Tax Advisors',
    cost: '€400/hour',
    sins: [
      '"It depends"',
      'Charging you to explain their own mistakes',
      'Mysterious invoices',
      'Annual panic sessions',
      'Pessimism as a service',
    ],
    replacement: 'CTAX Engine',
    savings: 'German tax law, fully automated. 195,000 cases trained',
  },
  {
    icon: '🕷️',
    title: 'External Auditors',
    cost: '€350/hour',
    sins: [
      'Asking for the same document 47 times',
      'Finding nothing useful',
      '"Materiality thresholds"',
      'Missing actual fraud',
      'Opinions with more disclaimers than opinions',
    ],
    replacement: 'Finance & FP&A Engine',
    savings: 'Continuous audit. Real-time compliance. Zero surprises',
  },
  {
    icon: '🧟',
    title: '"Middle Management"',
    cost: '€120k/year',
    sins: [
      'Scheduling meetings about meetings',
      'Status updates about status updates',
      '"Let\'s take this offline"',
      '"Circle back"',
      'Being a human router for emails',
    ],
    replacement: 'Nothing',
    savings: 'That\'s the point. The work gets done without them',
  },
  {
    icon: '🦑',
    title: 'ERP Implementation Partners',
    cost: '€15M/project',
    sins: [
      '3-year timelines that become 7',
      '"Change requests"',
      'Blaming your processes',
      'Scope creep as business model',
      'Go-lives that require 47 workarounds',
    ],
    replacement: '0711 Intelligence Orchestrator',
    savings: '1 day install. Not 1 decade',
  },
];

export default function BloodsuckersPage() {
  return (
    <>
      <Navigation />

      <section className={styles.hero}>
        <div className={styles.warning}>⚠️ SATIRE WARNING ⚠️</div>
        <h1>
          A Fond Farewell to the <strong>Bloodsuckers</strong>
        </h1>
        <p className={styles.subtitle}>
          For everyone who ever wondered where all their money goes. Spoiler: It goes to these people.
        </p>
      </section>

      <section className={styles.bloodsuckers}>
        <div className={styles.grid}>
          {BLOODSUCKERS.map((bloodsucker, idx) => (
            <div key={idx} className={styles.card}>
              <div className={styles.cardHeader}>
                <div className={styles.icon}>{bloodsucker.icon}</div>
                <h3>{bloodsucker.title}</h3>
                <div className={styles.cost}>{bloodsucker.cost}</div>
              </div>

              <div className={styles.sins}>
                <p className={styles.sinsLabel}>Known for:</p>
                {bloodsucker.sins.map((sin, i) => (
                  <span key={i} className={styles.sin}>
                    {sin}
                  </span>
                ))}
              </div>

              <div className={styles.replacement}>
                <h4>Replaced by</h4>
                <p>
                  {bloodsucker.replacement}.{' '}
                  <span className={styles.savings}>{bloodsucker.savings}.</span>
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.quote}>
        <blockquote>
          "The best part of 0711 isn't what it does. It's <span>who it fires</span>."
        </blockquote>
        <cite>— Anonymous CFO, probably</cite>
      </section>

      <section className={styles.cta}>
        <h2>Ready to fire your consultants?</h2>
        <p>
          Stop paying people to complicate your business. Start building with the people who
          actually create value.
        </p>
        <Link href="/signup" className={styles.btnPrimary}>
          Get Started
        </Link>
        <Link href="/" className={styles.btnSecondary}>
          Back to Homepage
        </Link>
      </section>

      <Footer />
    </>
  );
}
