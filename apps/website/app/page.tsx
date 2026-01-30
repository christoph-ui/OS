import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import Link from 'next/link';
import styles from './page.module.css';
import {
  Building2, Cloud, Shield, TrendingDown,
  Unlock, Zap, GraduationCap, Wrench,
  CheckCircle, Flag, Award
} from 'lucide-react';

export default function HomePage() {
  const sovereigntyCards = [
    {
      icon: Shield,
      title: "German Data Sovereignty",
      description: "Your data never touches US clouds. DSGVO compliance by design, not by workaround. Full audit trail on European soil."
    },
    {
      icon: TrendingDown,
      title: "Full Savers Control",
      description: "Buy Savers—our currency representing consultant hours saved. Use MCPs, track consumption in real-time, reload when needed. Full transparency, zero surprises."
    },
    {
      icon: Unlock,
      title: "Zero Vendor Lock-In",
      description: "Your data is portable. Your models are yours. Leave anytime with full export. (But you won't want to.)"
    },
    {
      icon: Zap,
      title: "Always Available",
      description: "No API downtime. No rate limits. No \"sorry, Claude is at capacity.\" Your brain, your availability guarantee."
    },
    {
      icon: GraduationCap,
      title: "Continuous Learning",
      description: "Your AI brain gets smarter every day from YOUR operations, YOUR data, YOUR processes. Not diluted across millions of users."
    },
    {
      icon: Wrench,
      title: "Hybrid When You Need It",
      description: "Need a global LLM for edge cases? Call it when YOU choose. Claude, GPT-4, Gemini—use any model for specific tasks. But 95% of operations run local. YOU control when external LLMs are involved."
    }
  ];

  const trustBadges = [
    { icon: Flag, text: "Digital Sovereign Cloud Partner" },
    { icon: Award, text: "Made in Germany" },
    { icon: CheckCircle, text: "DSGVO-Certified Data Centers" },
    { icon: Shield, text: "Zero US Cloud Dependency" }
  ];

  const features = [
    {
      icon: '◆',
      color: 'orange',
      title: 'Product & Engineering',
      desc: 'From 40 engineers to 5 high-impact builders. AI-driven development with zero waste and maximum velocity.',
    },
    {
      icon: '◆',
      color: 'blue',
      title: 'Pricing & Monetization',
      desc: 'Pricing as science, not guesswork. One analyst delivers maximum revenue per customer.',
    },
    {
      icon: '◆',
      color: 'green',
      title: 'Finance & FP&A',
      desc: 'Fully automated. Live dashboards. CFO playbooks. 70-90% cost reduction.',
    },
    {
      icon: '◆',
      color: 'orange',
      title: 'Marketing Growth',
      desc: 'AI-generated campaigns. 10x output at 10% of the cost. Two people, infinite reach.',
    },
    {
      icon: '◆',
      color: 'blue',
      title: 'Research & Intelligence',
      desc: 'One person replaces entire analysis teams. AI research that actually delivers insights.',
    },
    {
      icon: '◆',
      color: 'green',
      title: 'Operations & Support',
      desc: 'AI-first workflows. 80% self-resolving support. Automated everything.',
    },
  ];

  return (
    <>
      <Navigation />

      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <div className={styles.heroEyebrow}>The End of Enterprise Software</div>
          <h1>
            Your brain.
            <br />
            <strong>Your choice.</strong>
          </h1>
          <p className={styles.heroSubtitle}>
            A complete AI operating system that runs on YOUR pick of infrastructure. Local on-premise or in one of our digital sovereign hosting centers in Europe.
          </p>
          <div className={styles.heroTech}>
            <span><span className={styles.dot}></span>Mixtral + LoRA</span>
            <span><span className={styles.dot}></span>German Engineering</span>
            <span><span className={styles.dot}></span>Zero US Cloud Dependency</span>
          </div>
          <div className={styles.heroCta}>
            <Link href="#deployment" className={styles.btnPrimary}>
              Transform Your Company
            </Link>
            <Link href="#how" className={styles.btnSecondary}>
              See How It Works
            </Link>
            <Link href="#deployment-compare" className={styles.btnOutlineOrange}>
              Choose Your Deployment
            </Link>
          </div>
        </div>
      </section>

      {/* Manifesto */}
      <section className={styles.manifesto}>
        <div className={styles.manifestoContent}>
          <h2>
            Here's the truth about <strong>enterprise AI</strong>:
          </h2>
          <p>Everyone wants you dependent. On their APIs. On their clouds. On their pricing. On their terms.</p>
          <p>
            They'll tell you it's "easier" to send your data to their servers. They'll promise "simple integration" with their metered APIs. They'll charge you per token, raise prices whenever they want, and hold your competitive advantage hostage.
          </p>

          <div className={styles.manifestoDivider} />

          <h2>
            We asked a <strong>different question</strong>:
          </h2>
          <p className={styles.manifestoQuestion}>What if your company had its own brain?</p>
          <p className={styles.manifestoQuestion}>Not rented. Not metered. Not dependent.</p>
          <p className={styles.manifestoQuestion}>
            What if it ran where YOU choose—on your hardware, or in a European data center that respects your sovereignty?
          </p>
          <p className={styles.highlight} style={{ marginTop: '2rem', fontSize: '1.4rem' }}>
            Your brain. Your rules. Your location.
          </p>
        </div>
      </section>

      {/* Deployment Choice */}
      <section className={styles.deployment} id="deployment">
        <div className={styles.deploymentHeader}>
          <h2>Two Paths. Same Brain. You Choose.</h2>
          <p>Maximum control or zero operations. Either way, you own the intelligence.</p>
        </div>
        <div className={styles.deploymentGrid}>
          <div className={`${styles.deploymentCard} ${styles.onPremise}`}>
            <div className={styles.deploymentIcon}>
              <Building2 size={40} strokeWidth={1.5} />
            </div>
            <h3>On-Premise</h3>
            <div className={styles.subtitle}>Your Hardware. Your Network. Your Team.</div>

            <div className={styles.pricingLabel}>Custom License</div>

            <ul>
              <li>Deploy on your own infrastructure</li>
              <li>H100/A100 or CPU-only mode</li>
              <li>100% data sovereignty guaranteed</li>
              <li>Unlimited Savers (no usage limits)</li>
              <li>One-time license + annual support</li>
            </ul>
            <div className={styles.deploymentCode}>
              ./install-0711.sh --license=<span>YOUR-KEY</span>
            </div>
            <p className={styles.deploymentPerfect}><strong>Best for:</strong> Regulated industries, defense, finance, 200+ employees</p>
            <p className={styles.deploymentTime}>Setup: 1 day</p>

            <Link href="mailto:sales@0711.ai" className={styles.btnDeployment}>
              Contact Sales
            </Link>
          </div>
          <div className={`${styles.deploymentCard} ${styles.sovereignCloud}`}>
            <div className={styles.popularBadge}>Most Popular</div>
            <div className={styles.deploymentIcon}>
              <Cloud size={40} strokeWidth={1.5} />
            </div>
            <h3>European Sovereign Cloud</h3>
            <div className={styles.subtitle}>Our Infrastructure. Your Control. European Soil.</div>

            <div className={styles.pricingTiers}>
              <div className={styles.tier}>
                <div className={styles.tierName}>Starter</div>
                <div className={styles.tierPrice}>€2,500/month</div>
                <div className={styles.tierFeature}>1,250 Savers/month · 5 team members · Email support</div>
              </div>
              <div className={styles.tier}>
                <div className={styles.tierName}>Growth</div>
                <div className={styles.tierPrice}>€5,000/month</div>
                <div className={styles.tierFeature}>2,500 Savers/month · 20 team members · Priority support</div>
              </div>
            </div>

            <ul>
              <li>Digital sovereign data centers (Germany/Netherlands)</li>
              <li>DSGVO/GDPR compliant by design</li>
              <li>Fully managed (zero ops burden)</li>
              <li>Dedicated per-customer containers + LoRA</li>
            </ul>
            <div className={styles.deploymentCode}>
              Upload data → Select MCPs → <span>10 minutes to live</span>
            </div>
            <p className={styles.deploymentPerfect}><strong>Best for:</strong> Scale-ups, mid-market, &lt;200 employees</p>
            <p className={styles.deploymentTime}>Setup: 10 minutes · Frankfurt/Amsterdam/Zürich</p>

            <Link href="/signup" className={styles.btnDeployment}>
              Get Started
            </Link>
          </div>
        </div>
      </section>

      {/* Both Include */}
      <section className={styles.bothInclude}>
        <div className={styles.bothIncludeContent}>
          <h3>Both Deployments Include:</h3>
          <div className={styles.includeGrid}>
            <div className={styles.includeItem}>
              <span className={styles.check}>✓</span>
              Mixtral 8x7B-Instruct with per-customer LoRA fine-tuning
            </div>
            <div className={styles.includeItem}>
              <span className={styles.check}>✓</span>
              Unified Lakehouse (Delta Lake + LanceDB + Graph)
            </div>
            <div className={styles.includeItem}>
              <span className={styles.check}>✓</span>
              7+ specialized MCPs (Tax, Legal, Product, Finance...)
            </div>
            <div className={styles.includeItem}>
              <span className={styles.check}>✓</span>
              Optional hybrid mode (call any global LLM when YOU choose)
            </div>
            <div className={styles.includeItem}>
              <span className={styles.check}>✓</span>
              Hot-swappable LoRA adapters (&lt;1s switching)
            </div>
            <div className={styles.includeItem}>
              <span className={styles.check}>✓</span>
              Continuous learning from your operations
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className={styles.howItWorks} id="how">
        <div className={styles.sectionHeader}>
          <h2>Radically Simple. Wherever You Deploy.</h2>
          <p>We've eliminated everything that doesn't matter. What's left is pure momentum.</p>
        </div>
        <div className={styles.steps}>
          <div className={styles.step}>
            <div className={styles.stepNumber}>01</div>
            <h3>Choose deployment</h3>
            <p>On-premise or European sovereign cloud. Your call. Same capabilities either way.</p>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNumber}>02</div>
            <h3>Talk to it</h3>
            <p>Drop your data in—messy, scattered, imperfect. Your AI brain ingests it. Data stays where YOU put it.</p>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNumber}>03</div>
            <h3>It learns</h3>
            <p>Builds its own memory. Fine-tunes itself with LoRA on YOUR operations. Zero data leakage.</p>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNumber}>04</div>
            <h3>It orchestrates</h3>
            <p>Finance, legal, product, marketing—seven engines running on one brain. YOUR infrastructure.</p>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNumber}>05</div>
            <h3>You win</h3>
            <p>Twenty people with their own AI brain outperform 200 people renting someone else's.</p>
          </div>
        </div>
      </section>

      {/* Results */}
      <section className={styles.results} id="results">
        <div className={styles.sectionHeader}>
          <h2>The Numbers Don't Lie</h2>
          <p>Real results from companies that own their intelligence.</p>
        </div>
        <div className={styles.resultsGrid}>
          <div className={styles.resultItem}>
            <h3>10x</h3>
            <p>Faster Execution</p>
          </div>
          <div className={styles.resultItem}>
            <h3>70%</h3>
            <p>Cost Reduction</p>
          </div>
          <div className={styles.resultItem}>
            <h3>1</h3>
            <p>Day to Deploy</p>
          </div>
          <div className={styles.resultItem}>
            <h3>0</h3>
            <p>US Cloud Dependencies</p>
          </div>
          <div className={styles.resultItem}>
            <h3>100%</h3>
            <p>European Data Sovereignty</p>
          </div>
          <div className={styles.resultItem}>
            <h3>0</h3>
            <p>Meetings Required</p>
          </div>
        </div>
      </section>

      {/* Sovereignty Matters */}
      <section className={styles.sovereignty} id="sovereignty">
        <div className={styles.sectionHeader}>
          <h2>Why Companies Choose 0711</h2>
          <p>Independence isn't a feature. It's the foundation.</p>
        </div>
        <div className={styles.sovereigntyGrid}>
          {sovereigntyCards.map((card, idx) => (
            <div key={idx} className={styles.sovereigntyCard}>
              <div className={styles.sovereigntyIcon}>
                <card.icon size={32} strokeWidth={1.5} />
              </div>
              <h3>{card.title}</h3>
              <p>{card.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Vision */}
      <section className={styles.vision} id="vision">
        <div className={styles.visionContent}>
          <h2>Where This All Leads</h2>
          <p className={styles.visionStatement}>
            A world where European companies <strong>own</strong> their intelligence, not rent it from Silicon Valley. Where your competitive advantage lives on YOUR infrastructure—or European data centers that respect your sovereignty—not someone else's cloud. Where DSGVO compliance is <strong>built-in</strong>, not bolted on.
          </p>
          <p className={styles.visionStatement} style={{ marginTop: '2rem' }}>
            This isn't about better software. It's about <strong>independence</strong>.
          </p>
        </div>
      </section>

      {/* Technical Credibility */}
      <section className={styles.technical} id="technical">
        <div className={styles.sectionHeader}>
          <h2>Real Architecture. Real Local. Real European.</h2>
          <p>The complete stack—yours, wherever you deploy.</p>
        </div>
        <div className={styles.techGrid}>
          <div className={styles.techCategory}>
            <h3>Intelligence Core</h3>
            <ul>
              <li>Mixtral 8x7B-Instruct (open weights, no external dependency)</li>
              <li>Per-customer LoRA adapters (hot-swappable &lt;1s)</li>
              <li>Optional global LLM calls (Claude, GPT-4, Gemini—when YOU choose)</li>
            </ul>
          </div>
          <div className={styles.techCategory}>
            <h3>Memory & Storage</h3>
            <ul>
              <li>Unified Lakehouse: Delta Lake + LanceDB + Neo4j Graph</li>
              <li>MinIO (S3-compatible) or your storage backend</li>
              <li>All data stays in your deployment zone</li>
            </ul>
          </div>
          <div className={styles.techCategory}>
            <h3>Orchestration</h3>
            <ul>
              <li>Ray Serve for distributed compute</li>
              <li>MCP (Model Context Protocol) for domain-specific reasoning</li>
              <li>7+ specialized MCPs: Tax (CTAX), Legal, Product, Finance...</li>
            </ul>
          </div>
          <div className={styles.techCategory}>
            <h3>Deployment Options</h3>
            <ul>
              <li>On-Premise: Docker containers, Kubernetes-ready, H100/A100 or CPU</li>
              <li>Sovereign Cloud: Frankfurt, Amsterdam, Zürich data centers</li>
              <li>Location Guarantee: Choose your region, data never crosses borders</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className={styles.features} id="features">
        <div className={styles.sectionHeader}>
          <h2>Seven Engines. One Brain. Your Choice of Location.</h2>
          <p>All powered by YOUR AI, running where YOU choose.</p>
        </div>
        <div className={styles.featureGrid}>
          {features.map((feature, idx) => (
            <div key={idx} className={styles.featureCard}>
              <div className={styles.featureBadge}>On-Premise + Cloud</div>
              <div className={`${styles.featureIcon} ${styles[feature.color]}`}>{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Comparison */}
      <section className={styles.comparison}>
        <div className={styles.comparisonContent}>
          <div className={styles.sectionHeader}>
            <h2>The Old Way vs. The 0711 Way</h2>
          </div>
          <div className={styles.comparisonGrid}>
            <div className={`${styles.comparisonCol} ${styles.old}`}>
              <h3>Yesterday</h3>
              <ul>
                <li>US cloud dependency</li>
                <li>Data leaves your control</li>
                <li>Per-token metered billing</li>
                <li>Vendor lock-in</li>
                <li>Integration hell</li>
                <li>Consultant armies</li>
                <li>Manual everything</li>
              </ul>
            </div>
            <div className={`${styles.comparisonCol} ${styles.new}`}>
              <h3>0711</h3>
              <ul>
                <li>European sovereignty OR on-premise</li>
                <li>Data stays where you choose</li>
                <li>Fixed predictable costs</li>
                <li>Open standards, portable</li>
                <li>Zero integration needed</li>
                <li>Self-optimizing system</li>
                <li>Automated by default</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Quote */}
      <section className={styles.quoteSection}>
        <blockquote>
          The most sophisticated thing in the world is <span>simplicity</span>. The most powerful thing is <span>sovereignty</span>. We built both.
        </blockquote>
      </section>

      {/* Testimonial */}
      <section className={styles.testimonial}>
        <div className={styles.testimonialContent}>
          <p className={styles.testimonialQuote}>
            "We evaluated AWS/Azure AI solutions. All required sending data to US clouds. 0711 gave us the choice: our on-premise hardware or their Frankfurt data center. Same brain, our rules."
          </p>
          <p className={styles.testimonialAuthor}>— <strong>CISO, German Manufacturing Company</strong></p>
        </div>
      </section>

      {/* Trust Badges */}
      <section className={styles.trustBadges}>
        <div className={styles.badgesContainer}>
          {trustBadges.map((badge, idx) => (
            <div key={idx} className={styles.badge}>
              <span className={styles.badgeIcon}>
                <badge.icon size={20} strokeWidth={1.5} />
              </span>
              {badge.text}
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className={styles.ctaSection} id="contact">
        <h2>
          Ready to build <strong>your own brain</strong>?
        </h2>
        <p>
          Choose your deployment. On-premise or European sovereign cloud. Either way, you own the intelligence.
        </p>
        <div className={styles.ctaButtons}>
          <Link href="/signup" className={styles.btnPrimary}>
            Get Started: On-Premise
          </Link>
          <Link href="/signup" className={styles.btnSecondary}>
            Get Started: Sovereign Cloud
          </Link>
          <Link href="#deployment-compare" className={styles.btnOutlineOrange}>
            Compare Deployments
          </Link>
        </div>
        <div className={styles.ctaLinks}>
          <Link href="/pricing">Pricing</Link>
          <Link href="/builders">For Builders</Link>
          <Link href="#technical">Architecture</Link>
          <Link href="/experts">Expert Network</Link>
        </div>
        <div className={styles.taglines}>
          <p className={styles.tagline}>Installs in one day. Not one quarter. Not one year. One day.</p>
          <p className={styles.tagline}>Data stays in Europe. Not California. Not Virginia. Europe.</p>
        </div>
      </section>

      <Footer />
    </>
  );
}
