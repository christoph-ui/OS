import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import Link from 'next/link';
import styles from './pricing.module.css';

const SAVERS_PACKS = [
  {
    name: 'Trial',
    price: 250,
    savers: 100,
    featured: false,
    bestFor: 'Developers, evaluation, testing',
    includes: [
      'Self-hosted platform',
      'Intelligence Orchestrator Core',
      'Local Mixtral 8x7B + LoRA',
      'MCP SDK + Developer Kit',
      '100 Savers',
      'Community support'
    ]
  },
  {
    name: 'Starter',
    price: 2000,
    savers: 1250,
    featured: true,
    bestFor: 'Small teams, production workloads',
    includes: [
      'Managed hosting OR on-premise',
      'Intelligence Orchestrator Core',
      'Local Mixtral 8x7B + LoRA',
      'Unified Lakehouse',
      '1,250 Savers',
      'MCP marketplace access',
      'Savers dashboard + analytics',
      'Email support'
    ]
  },
  {
    name: 'Growth',
    price: 8750,
    savers: 6750,
    featured: false,
    bestFor: 'Mid-market, enterprise teams',
    includes: [
      'Everything in Starter',
      '6,750 Savers',
      'Priority support',
      'Advanced analytics',
      'Quarterly ROI reports',
      'Team management',
      'Savers rollover (6 months)'
    ]
  },
  {
    name: 'Enterprise',
    price: null,
    isContactSales: true,
    featured: false,
    bestFor: 'Large organizations, custom requirements',
    includes: [
      'Everything in Growth',
      'Custom Savers allocation',
      'Volume pricing',
      'Dedicated account manager',
      'Custom MCP development',
      'SLA guarantees',
      '24/7 priority support',
      'Multi-region deployment',
      'Executive quarterly reviews'
    ]
  }
];

const LOYALTY_TIERS = [
  {
    tier: 'Bronze',
    icon: '🥉',
    threshold: '0-5,000',
    description: 'Starting out with the platform. Standard access to all features.',
    perks: ['Standard email support', 'Access to all Savers packs', 'Community resources', 'Monthly usage reports']
  },
  {
    tier: 'Silver',
    icon: '🥈',
    threshold: '5,000-25,000',
    description: 'Active user. Get more Savers with every purchase and priority access.',
    perks: ['Everything in Bronze', 'Extra 10% Savers on all purchases', 'Priority email support (12h response)', 'Early access to new MCPs', 'Quarterly ROI strategy reports']
  },
  {
    tier: 'Gold',
    icon: '🥇',
    threshold: '25,000-100,000',
    description: 'Power user. Significant savings on Savers purchases and premium support.',
    perks: ['Everything in Silver', 'Extra 20% Savers on all purchases', 'Slack/Teams priority support', 'One free connector MCP per month (€500 value)', 'Monthly ROI review calls', 'Beta feature access']
  },
  {
    tier: 'Platinum',
    icon: '💎',
    threshold: '100,000+',
    description: 'Enterprise champion. Maximum Savers bonuses and white-glove service.',
    perks: ['Everything in Gold', 'Extra 30% Savers on all purchases', 'Dedicated account manager', 'Custom MCP development (one per year)', 'SLA guarantees (99.9% uptime)', '24/7 priority support', 'Quarterly executive strategy sessions']
  }
];

const PLATFORM_PLANS = [
  {
    name: 'Developer',
    price: 'FREE',
    savers: '100/month',
    features: [
      'Self-hosted only',
      '100 Savers/month (auto-replenish)',
      'Unlimited local inference',
      'MCP SDK + Developer Kit',
      'Publish to marketplace',
      'Community support'
    ],
    cta: 'Download Free',
    ctaLink: '#developer'
  },
  {
    name: 'Starter',
    price: '€2,500',
    period: '/month',
    savers: '1,250/month',
    features: [
      'Managed hosting OR on-premise',
      '1,250 Savers/month (auto-replenish)',
      'Unlimited local inference',
      'Savers dashboard + ROI tracking',
      'Email support (24h response)',
      'Unused Savers roll over (6 months)'
    ],
    cta: 'Get Started',
    ctaLink: '/signup',
    featured: true
  },
  {
    name: 'Growth',
    price: '€5,000',
    period: '/month',
    savers: '2,500/month',
    features: [
      'Everything in Starter',
      '2,500 Savers/month included',
      'Priority support',
      'Quarterly ROI reports',
      'Team management (unlimited users)'
    ],
    cta: 'Get Started',
    ctaLink: '/signup'
  }
];

const MCP_CONSUMPTION = [
  {
    mcp: 'LAW MCP',
    baseFee: 1000,
    saversRange: '0.5-4',
    example: 'Contract review (100 pages)',
    consultantCost: '€2,000',
    consultantTime: '4 hours lawyer',
    saversCost: '4 Savers (€8)'
  },
  {
    mcp: 'CTAX MCP',
    baseFee: 1000,
    saversRange: '3-8',
    example: 'Annual tax filing',
    consultantCost: '€3,200',
    consultantTime: '8 hours tax advisor',
    saversCost: '8 Savers (€16)'
  },
  {
    mcp: 'Research MCP',
    baseFee: 800,
    saversRange: '2-10',
    example: 'Full market research report',
    consultantCost: '€3,000',
    consultantTime: '10 hours consultant',
    saversCost: '10 Savers (€20)'
  },
  {
    mcp: 'Tender MCP',
    baseFee: 1000,
    saversRange: '1-15',
    example: 'Complete proposal (50 pages)',
    consultantCost: '€3,750',
    consultantTime: '15 hours team',
    saversCost: '15 Savers (€30)'
  },
  {
    mcp: 'ETIM MCP',
    baseFee: 600,
    saversRange: '0.1/SKU',
    example: '100 SKU classification',
    consultantCost: '€1,200',
    consultantTime: '8 hours manual',
    saversCost: '8 Savers (€16)'
  },
  {
    mcp: 'FP&A MCP',
    baseFee: 800,
    saversRange: '1-5',
    example: 'Scenario modeling',
    consultantCost: '€1,500',
    consultantTime: '5 hours analyst',
    saversCost: '5 Savers (€10)'
  }
];

const CONNECTOR_MCPS = [
  { name: 'SAP Connector', price: 500 },
  { name: 'DATEV Connector', price: 400 },
  { name: 'Salesforce Connector', price: 450 },
  { name: 'Microsoft 365', price: 350 },
  { name: 'Slack', price: 300 },
  { name: 'Google Workspace', price: 350 }
];

const BASELINE_RATES = [
  { role: 'Corporate Lawyer', rate: 500, tasks: 'Contract review, legal opinions, M&A' },
  { role: 'Tax Advisor', rate: 400, tasks: 'Tax planning, compliance, filing' },
  { role: 'Management Consultant', rate: 300, tasks: 'Strategy, research, analysis' },
  { role: 'Financial Analyst', rate: 200, tasks: 'FP&A, modeling, forecasting' },
  { role: 'Product Manager', rate: 150, tasks: 'Classification, specs, roadmaps' }
];

export default function PricingPage() {
  return (
    <>
      <Navigation />

      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.heroEyebrow}>Pricing</div>
        <h1>
          Simple. <strong>Transparent.</strong>
        </h1>
        <p className={styles.heroSubtitle}>
          Prepaid credits for MCP usage. No hidden fees. No surprise bills. Full visibility into every request.
        </p>
      </section>

      {/* Savers Packs */}
      <section className={styles.saversPacks} id="savers">
        <div className={styles.sectionHeader}>
          <h2>Pricing</h2>
          <p>Choose your Savers allocation. Credits never expire.</p>
        </div>
        <div className={styles.packsGrid}>
          {SAVERS_PACKS.map((pack) => (
            <div key={pack.name} className={`${styles.packCard} ${pack.featured ? styles.featured : ''} ${pack.isContactSales ? styles.enterprise : ''}`}>
              {pack.featured && <div className={styles.packBadge}>Most Popular</div>}
              <h3>{pack.name}</h3>
              {pack.isContactSales ? (
                <>
                  <div className={styles.packPrice}>
                    <span className={styles.customLabel}>Custom</span>
                  </div>
                  <p className={styles.packBestFor}>{pack.bestFor}</p>
                  <ul className={styles.packIncludes}>
                    {pack.includes.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                  <Link href="mailto:enterprise@0711.ai" className={styles.btnSecondary}>
                    Contact Sales
                  </Link>
                </>
              ) : (
                <>
                  <div className={styles.packPrice}>
                    <span className={styles.amount}>€{pack.price?.toLocaleString() || 0}</span>
                  </div>
                  <p className={styles.packBestFor}>{pack.bestFor}</p>
                  <ul className={styles.packIncludes}>
                    {pack.includes.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                  <Link href="/signup" className={styles.btnPrimary}>
                    Get Started
                  </Link>
                </>
              )}
            </div>
          ))}
        </div>
        <p className={styles.packsNote}>
          Savers never expire. Use them anytime, across any MCP. Reload when needed.
        </p>
      </section>

      {/* Platform Subscriptions */}
      <section className={styles.subscriptions} id="subscriptions">
        <div className={styles.sectionHeader}>
          <h2>Platform Subscriptions (Optional)</h2>
          <p>Prefer monthly billing? Get auto-replenishing Savers every month.</p>
        </div>
        <div className={styles.subscriptionsGrid}>
          {PLATFORM_PLANS.map((plan) => (
            <div key={plan.name} className={`${styles.subscriptionCard} ${plan.featured ? styles.featured : ''}`}>
              {plan.featured && <div className={styles.packBadge}>Most Popular</div>}
              <h3>{plan.name}</h3>
              <div className={styles.subscriptionPrice}>
                <span className={styles.amount}>{plan.price}</span>
                {plan.period && <span className={styles.period}>{plan.period}</span>}
              </div>
              <div className={styles.subscriptionSavers}>Includes: {plan.savers}</div>
              <ul className={styles.subscriptionFeatures}>
                {plan.features.map((feature, idx) => (
                  <li key={idx}>
                    <span className={styles.check}>✓</span> {feature}
                  </li>
                ))}
              </ul>
              <Link href={plan.ctaLink} className={plan.featured ? styles.btnPrimary : styles.btnSecondary}>
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
        <p className={styles.subscriptionNote}>
          <strong>Note:</strong> Unused Savers from subscriptions roll over for 6 months. You can also buy additional Savers packs anytime.
        </p>
      </section>

      {/* MCP Marketplace Teaser */}
      <section className={styles.mcpTeaser}>
        <div className={styles.sectionHeader}>
          <h2>MCP Marketplace</h2>
          <p>Browse and subscribe to MCPs after signing up. Pricing visible in your dashboard.</p>
        </div>
        <div className={styles.mcpCategories}>
          <div className={styles.categoryCard}>
            <h4>Business Process MCPs</h4>
            <p>LAW, CTAX, Research, Tender, FP&A, Product Management</p>
          </div>
          <div className={styles.categoryCard}>
            <h4>Connector MCPs</h4>
            <p>SAP, DATEV, Salesforce, Slack, Microsoft 365, Google Workspace</p>
          </div>
          <div className={styles.categoryCard}>
            <h4>Community MCPs</h4>
            <p>Built by developers, available in marketplace after login</p>
          </div>
        </div>
        <p className={styles.mcpNote}>
          <strong>Pricing:</strong> Each MCP has a base subscription + consumes Savers per request. Full pricing visible in marketplace after signup.
        </p>
      </section>

      {/* Deployment Benefits */}
      <section className={styles.comparison} id="deployment-benefits">
        <div className={styles.sectionHeader}>
          <h2>Why European Data Centers vs. On-Premise?</h2>
          <p>Choose based on your operational requirements and compliance needs.</p>
        </div>

        <div className={styles.comparisonTable}>
          <div className={styles.comparisonCol}>
            <h4>🇪🇺 European Sovereign Cloud</h4>
            <p className={styles.deploymentDesc}>
              Fully managed infrastructure in DSGVO-certified data centers. Zero operations burden.
            </p>
            <ul className={styles.benefitsList}>
              <li><strong>Zero Operations:</strong> No DevOps team needed. We handle infrastructure, updates, monitoring, and scaling.</li>
              <li><strong>Fast Deployment:</strong> 10 minutes from signup to live system. No hardware procurement, no setup delays.</li>
              <li><strong>Guaranteed Uptime:</strong> 99.9% SLA with automatic failover across Frankfurt, Amsterdam, and Zürich.</li>
              <li><strong>European Data Residency:</strong> Choose your region. Data never crosses borders. DSGVO compliance built-in.</li>
              <li><strong>Predictable Costs:</strong> Fixed monthly subscription. No hardware CapEx, no surprise infrastructure bills.</li>
              <li><strong>Automatic Updates:</strong> Platform improvements deployed continuously. You approve, we execute.</li>
              <li><strong>Elastic Scaling:</strong> Add users and capacity instantly. No hardware upgrades needed.</li>
            </ul>
            <p className={styles.idealFor}>
              <strong>Ideal for:</strong> Scale-ups, mid-market companies (&lt;200 employees), teams without dedicated DevOps, fast-growth scenarios.
            </p>
          </div>

          <div className={styles.comparisonCol}>
            <h4>🏢 On-Premise Deployment</h4>
            <p className={styles.deploymentDesc}>
              Complete platform ownership. Deploy on your infrastructure with unlimited usage rights.
            </p>
            <ul className={styles.benefitsList}>
              <li><strong>Total Control:</strong> Your hardware, your network, your security policies. Nothing leaves your facility.</li>
              <li><strong>Unlimited Usage:</strong> No Savers consumption limits. Run unlimited inference, unlimited MCPs, unlimited scale.</li>
              <li><strong>Air-Gapped Options:</strong> Deploy in classified networks, defense facilities, or completely offline environments.</li>
              <li><strong>Custom Infrastructure:</strong> Use existing GPUs, integrate with your monitoring, deploy across multiple sites.</li>
              <li><strong>Regulatory Compliance:</strong> Meet industry-specific requirements (defense, banking, healthcare) that mandate on-premise.</li>
              <li><strong>Long-Term Economics:</strong> One-time license + annual support. No recurring platform fees after initial investment.</li>
              <li><strong>Full Source Access:</strong> Modify platform, build custom integrations, maintain independently if needed.</li>
            </ul>
            <p className={styles.idealFor}>
              <strong>Ideal for:</strong> Regulated industries, defense contractors, enterprises (200+ employees), air-gapped requirements, heavy usage scenarios.
            </p>
          </div>
        </div>

        <div className={styles.decisionGuide}>
          <h3>Decision Guide</h3>
          <p><strong>Choose Sovereign Cloud if:</strong> You want zero ops burden, fast deployment, predictable monthly costs, and your data sensitivity allows managed European hosting.</p>
          <p><strong>Choose On-Premise if:</strong> You need air-gapped deployment, have regulatory requirements for on-premise, expect very heavy usage (unlimited Savers matters), or have existing GPU infrastructure.</p>
          <p className={styles.hybrid}><strong>Hybrid Option:</strong> Start with Sovereign Cloud, migrate to On-Premise later. Your data exports fully, deployment configurations are portable.</p>
        </div>
      </section>

      {/* Developer Section */}
      <section className={styles.developer} id="developer">
        <div className={styles.developerHeader}>
          <h2>Developer Program</h2>
          <p>Build MCPs. Earn Revenue. Shape the Ecosystem.</p>
        </div>

        <div className={styles.developerContent}>
          {/* Free Edition */}
          <div className={styles.developerEdition}>
            <h3>FREE Developer Edition</h3>
            <p className={styles.lead}>Everything you need to build, test, and publish MCPs.</p>

            <div className={styles.developerFeatures}>
              <div className={styles.featureCol}>
                <h4>Platform Access</h4>
                <ul>
                  <li>Full 0711 platform (self-hosted)</li>
                  <li>Intelligence Orchestrator Core</li>
                  <li>Local Mixtral 8x7B + LoRA</li>
                  <li>Unified Lakehouse</li>
                  <li>100 Savers/month (testing credits)</li>
                </ul>
              </div>
              <div className={styles.featureCol}>
                <h4>Developer Tools</h4>
                <ul>
                  <li>Complete MCP SDK (Python)</li>
                  <li>CLI tools (create, test, validate)</li>
                  <li>Local testing environment</li>
                  <li>Savers consumption simulator</li>
                  <li>Integration templates</li>
                </ul>
              </div>
              <div className={styles.featureCol}>
                <h4>Marketplace</h4>
                <ul>
                  <li>Publish unlimited MCPs</li>
                  <li>Set your own pricing</li>
                  <li>70-85% revenue share</li>
                  <li>One-click customer deployment</li>
                  <li>Monthly payouts (Stripe)</li>
                </ul>
              </div>
            </div>

            <div className={styles.developerCta}>
              <Link href="https://github.com/0711/mcp-sdk" className={styles.btnPrimary}>
                Download SDK
              </Link>
              <Link href="https://docs.0711.io/developers" className={styles.btnSecondary}>
                Read Docs
              </Link>
              <Link href="https://discord.gg/0711-dev" className={styles.btnSecondary}>
                Join Discord
              </Link>
            </div>
          </div>

          {/* SDK Example */}
          <div className={styles.sdkExample}>
            <h3>Build an MCP in Minutes</h3>
            <pre className={styles.codeBlock}>
{`from mcp_sdk import BaseMCP, tool

class InvoiceProcessingMCP(BaseMCP):
    name = "invoice-processing"
    description = "Automated invoice processing"

    # Your pricing
    base_fee = 500  # EUR/month
    savers_rate = 0.5  # Per invoice processed

    @tool
    async def process_invoice(self, pdf_path: str):
        """Extract data from invoice PDF"""
        # Use local Mixtral (free)
        data = await self.llm.extract(pdf_path)

        # Store in lakehouse
        await self.lakehouse.save("invoices", data)

        return data

# Deploy locally for testing
0711 mcp deploy --local

# Publish to marketplace when ready
0711 mcp publish --pricing "€500/month + 0.5 Savers/invoice"`}
            </pre>
          </div>

          {/* Revenue Model */}
          <div className={styles.revenueModel}>
            <h3>Your Revenue Potential</h3>
            <div className={styles.revenueExample}>
              <div className={styles.revenueInputs}>
                <h4>Your MCP Pricing:</h4>
                <ul>
                  <li>Base fee: €500/month</li>
                  <li>Savers rate: 0.5/request</li>
                </ul>
              </div>
              <div className={styles.revenueCalc}>
                <h4>With 50 Customers:</h4>
                <ul>
                  <li>Base fees: €25,000/month × 70% = <strong>€17,500</strong></li>
                  <li>Savers usage: Avg 50 Savers/customer × 70% = 1,750 Savers × €2 = <strong>€3,500</strong></li>
                  <li className={styles.revTotal}>Total Monthly Revenue: <strong>€21,000</strong></li>
                  <li className={styles.revAnnual}>Annual: <strong>€252,000</strong></li>
                </ul>
              </div>
            </div>
          </div>

          {/* Developer Tiers */}
          <div className={styles.developerTiers}>
            <h3>Level Up Your Revenue Share</h3>
            <table>
              <thead>
                <tr>
                  <th>Tier</th>
                  <th>Customers</th>
                  <th>Revenue Share</th>
                  <th>Testing Savers</th>
                  <th>Perks</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Hobbyist</td>
                  <td>0-10</td>
                  <td>70%</td>
                  <td>100/month</td>
                  <td>Community support</td>
                </tr>
                <tr>
                  <td>Professional</td>
                  <td>10-50</td>
                  <td>75%</td>
                  <td>500/month</td>
                  <td>Priority support, featured listing</td>
                </tr>
                <tr>
                  <td>Partner</td>
                  <td>50-200</td>
                  <td>80%</td>
                  <td>2,000/month</td>
                  <td>Co-marketing, partner manager</td>
                </tr>
                <tr>
                  <td>Premier</td>
                  <td>200+</td>
                  <td>85%</td>
                  <td>5,000/month</td>
                  <td>Joint roadmap, enterprise intros</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Developer Resources */}
          <div className={styles.developerResources}>
            <h3>Developer Resources</h3>
            <div className={styles.resourcesGrid}>
              <div className={styles.resourceCard}>
                <h4>📚 Documentation</h4>
                <ul>
                  <li>SDK Reference</li>
                  <li>MCP Architecture Guide</li>
                  <li>Publishing Checklist</li>
                  <li>Pricing Guide</li>
                </ul>
                <Link href="https://docs.0711.io/sdk">Read Docs</Link>
              </div>
              <div className={styles.resourceCard}>
                <h4>🎮 Community</h4>
                <ul>
                  <li>Discord Server</li>
                  <li>Weekly Office Hours</li>
                  <li>MCP Showcase</li>
                  <li>Bounty Board</li>
                </ul>
                <Link href="https://discord.gg/0711-dev">Join Discord</Link>
              </div>
              <div className={styles.resourceCard}>
                <h4>💻 GitHub</h4>
                <ul>
                  <li>MCP SDK Repository</li>
                  <li>Example MCPs</li>
                  <li>Starter Templates</li>
                  <li>Issue Tracker</li>
                </ul>
                <Link href="https://github.com/0711/mcp-sdk">View on GitHub</Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className={styles.faq}>
        <div className={styles.sectionHeader}>
          <h2>Common Questions</h2>
        </div>
        <div className={styles.faqGrid}>
          <div className={styles.faqItem}>
            <h4>What are Savers?</h4>
            <p>Savers are our prepaid currency. 1 Saver represents 1 hour of consultant work saved. Buy Savers in packs, use them to power MCP requests. They never expire.</p>
          </div>
          <div className={styles.faqItem}>
            <h4>How do Savers work with subscriptions?</h4>
            <p>Subscriptions include auto-replenishing Savers each month (100-2,500 depending on plan). You can also buy additional Savers packs anytime. Unused subscription Savers roll over for 6 months.</p>
          </div>
          <div className={styles.faqItem}>
            <h4>What happens when I run out of Savers?</h4>
            <p>You'll get alerts at 80% and 100% usage. Buy more Savers instantly or enable auto-reload. MCPs will pause until you reload (no surprise charges).</p>
          </div>
          <div className={styles.faqItem}>
            <h4>Can I share Savers across my team?</h4>
            <p>Yes! Savers are pooled at the company level. All team members draw from the same balance. Track usage per user in the dashboard.</p>
          </div>
          <div className={styles.faqItem}>
            <h4>How does the loyalty program work?</h4>
            <p>Your tier is based on lifetime Savers used (not purchased). More you use the platform, the more bonus Savers you get on future purchases. Silver = +10%, Gold = +20%, Platinum = +30%.</p>
          </div>
          <div className={styles.faqItem}>
            <h4>How do I build and sell MCPs?</h4>
            <p>Download the free Developer Edition, use our SDK to build MCPs, publish to the marketplace. You set pricing (base fee + Savers rate), we handle billing and distribution. You keep 70-85% of revenue.</p>
          </div>
          <div className={styles.faqItem}>
            <h4>Are MCPs charged in Savers AND subscription fees?</h4>
            <p>Yes. MCPs have a base subscription (€600-1,500/month) plus consume Savers per request. Base fee covers infrastructure and updates. Savers consumption varies by task complexity.</p>
          </div>
          <div className={styles.faqItem}>
            <h4>Can I use my own LLM API keys?</h4>
            <p>Yes (BYOK). Add your OpenAI/Anthropic/Google keys. MCPs will still consume Savers for the request (we charge for orchestration), but you pay token costs directly to providers.</p>
          </div>
        </div>
      </section>

      {/* Enterprise CTA */}
      <section className={styles.enterpriseCta} id="contact">
        <h2>Need a Custom Plan?</h2>
        <p>Volume Savers pricing, dedicated support, custom MCP development.</p>
        <Link href="mailto:enterprise@0711.ai" className={styles.btnPrimary}>
          Contact Sales
        </Link>
      </section>

      <Footer />
    </>
  );
}
