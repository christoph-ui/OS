import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import Link from 'next/link';
import styles from './builders.module.css';

const BLOODSUCKERS = [
  {
    icon: '🧛',
    title: 'Management Consultants',
    cost: '€2.500/day',
    sins: [
      'Borrowing your watch to tell you the time',
      '200-slide decks',
      '"Best practices"',
      'Junior analysts at senior prices',
      'Leaving before implementation',
    ],
    replacement: 'Research & Intelligence MCP',
    savings: '€2.500/month instead of €2.500/day',
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
    savings: 'German tax law, fully automated. 195.000 cases trained',
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

export default function BuildersPage() {
  return (
    <>
      <Navigation variant="light" />

      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <div className={styles.heroEyebrow}>Built for Builders</div>
          <h1>
            For the ones who <strong>actually build things</strong>
          </h1>
          <p className={styles.heroSubtitle}>
            Not the ones who schedule meetings about building things. Not the ones who bill you for
            explaining why building things is complicated. The ones who build.
          </p>
          <div className={styles.heroNav}>
            <Link href="#founders">For Founders</Link>
            <Link href="#ceos">For CEOs</Link>
            <Link href="#ctos">For CTOs</Link>
            <Link href="#liberation" className={styles.special}>
              The Bloodsuckers
            </Link>
          </div>
        </div>
      </section>

      {/* Founders Section */}
      <section className={styles.personaSection} id="founders">
        <div className={styles.personaContent}>
          <div className={styles.personaText}>
            <h3>For Founders</h3>
            <h2>You didn't start a company to <strong>manage vendors</strong></h2>
            <p className={styles.lead}>You started it to change something. To build something. To prove something was possible. Somewhere along the way, you became a full-time manager of consultants, tools, and processes.</p>
            <ul className={styles.personaPoints}>
              <li>
                <div className={styles.pointIcon}>◆</div>
                <div className={styles.pointContent}>
                  <h4>Back to Building</h4>
                  <p>Stop managing software. Stop coordinating consultants. Get back to the work that matters.</p>
                </div>
              </li>
              <li>
                <div className={styles.pointIcon}>◆</div>
                <div className={styles.pointContent}>
                  <h4>Day-One Infrastructure</h4>
                  <p>Enterprise-grade capabilities without enterprise-grade complexity. Install in one day, not one year.</p>
                </div>
              </li>
              <li>
                <div className={styles.pointIcon}>◆</div>
                <div className={styles.pointContent}>
                  <h4>Capital Efficiency</h4>
                  <p>Stop burning runway on consultants and tools. Put that money into product, team, and growth.</p>
                </div>
              </li>
              <li>
                <div className={styles.pointIcon}>◆</div>
                <div className={styles.pointContent}>
                  <h4>Compete With Giants</h4>
                  <p>20 people with 0711 outperform 200 people with legacy infrastructure. That's not marketing—it's math.</p>
                </div>
              </li>
            </ul>
          </div>
          <div className={styles.personaVisual}>
            <div className={styles.visualQuote}>
              "I used to spend <span>60% of my time</span> managing the business of running a business. Now I spend 60% of my time <span>actually running the business</span>."
            </div>
          </div>
        </div>
      </section>

      {/* CEOs Section */}
      <section className={`${styles.personaSection} ${styles.alt}`} id="ceos">
        <div className={`${styles.personaContent} ${styles.reverse}`}>
          <div className={styles.personaText}>
            <h3>For CEOs</h3>
            <h2>You're not paid to <strong>babysit infrastructure</strong></h2>
            <p className={styles.lead}>Your board doesn't care about your ERP migration timeline. Your investors don't care about your integration roadmap. They care about growth, margin, and speed. Everything else is noise.</p>
            <ul className={styles.personaPoints}>
              <li>
                <div className={styles.pointIcon}>◆</div>
                <div className={styles.pointContent}>
                  <h4>Instant Clarity</h4>
                  <p>One system. One truth. Ask anything about your business and get an answer in seconds, not weeks.</p>
                </div>
              </li>
              <li>
                <div className={styles.pointIcon}>◆</div>
                <div className={styles.pointContent}>
                  <h4>70% Cost Reduction</h4>
                  <p>Eliminate the consultant layer, the tool sprawl, the integration projects. Redeploy that capital to growth.</p>
                </div>
              </li>
              <li>
                <div className={styles.pointIcon}>◆</div>
                <div className={styles.pointContent}>
                  <h4>10x Decision Speed</h4>
                  <p>No more waiting for reports. No more aligning stakeholders. The answer is always available.</p>
                </div>
              </li>
              <li>
                <div className={styles.pointIcon}>◆</div>
                <div className={styles.pointContent}>
                  <h4>M&A Ready</h4>
                  <p>Integrate acquisitions in days, not years. One platform absorbs any business structure.</p>
                </div>
              </li>
            </ul>
          </div>
          <div className={styles.personaVisual}>
            <div className={styles.visualStat}>
              <div className={styles.number}>90</div>
              <div className={styles.label}>Days to positive ROI</div>
            </div>
            <div className={styles.visualStat}>
              <div className={styles.number}>3–8M€</div>
              <div className={styles.label}>Annual savings at 12 months</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTOs Section */}
      <section className={`${styles.personaSection} ${styles.dark}`} id="ctos">
        <div className={styles.personaContent}>
          <div className={styles.personaText}>
            <h3>For CTOs & Dev Gods</h3>
            <h2>Finally, infrastructure that <strong>doesn't insult your intelligence</strong></h2>
            <p className={styles.lead}>You've spent years cleaning up after enterprise software vendors. Patching their bugs. Building around their limitations. Explaining to leadership why "simple" integrations take six months. We built 0711 for you.</p>
            <ul className={styles.personaPoints}>
              <li>
                <div className={styles.pointIcon}>◆</div>
                <div className={styles.pointContent}>
                  <h4>Real Architecture</h4>
                  <p>Unified Lakehouse. Ray compute fabric. vLLM inference. DSPy pipelines. Not a slide deck—actual technology.</p>
                </div>
              </li>
              <li>
                <div className={styles.pointIcon}>◆</div>
                <div className={styles.pointContent}>
                  <h4>Local-First LLM</h4>
                  <p>Your data never leaves your infrastructure. Mixtral base with LoRA hot-swapping. You control everything.</p>
                </div>
              </li>
              <li>
                <div className={styles.pointIcon}>◆</div>
                <div className={styles.pointContent}>
                  <h4>MCP SDK</h4>
                  <p>Build custom capabilities in Python. Publish to the marketplace or keep them internal. Your code, your rules.</p>
                </div>
              </li>
              <li>
                <div className={styles.pointIcon}>◆</div>
                <div className={styles.pointContent}>
                  <h4>No More Vendor Lock-In</h4>
                  <p>Open standards. Portable data. Export anything anytime. Because we're confident you won't want to.</p>
                </div>
              </li>
            </ul>
          </div>
          <div className={styles.personaVisual}>
            <div className={styles.visualQuote}>
              "For the first time in my career, I don't hate the enterprise software I'm responsible for. <span>It actually works.</span>"
            </div>
          </div>
        </div>
      </section>

      {/* Law MCP Section */}
      <section className={styles.lawMcpSection}>
        <div className={styles.lawMcpContent}>
          <div className={styles.lawMcpText}>
            <h3>Introducing</h3>
            <h2>The <strong>Law MCP</strong></h2>
            <p className={styles.description}>Because legal shouldn't cost more than engineering. Contract review, compliance checking, regulatory analysis—all at 1% of the cost of a junior associate.</p>
            <ul className={styles.lawCapabilities}>
              <li><span className={styles.check}>✓</span> Contract review & redlining (German/English)</li>
              <li><span className={styles.check}>✓</span> NDA and agreement generation</li>
              <li><span className={styles.check}>✓</span> Regulatory compliance scanning</li>
              <li><span className={styles.check}>✓</span> DSGVO / GDPR analysis</li>
              <li><span className={styles.check}>✓</span> Employment law guidance</li>
              <li><span className={styles.check}>✓</span> Corporate governance templates</li>
              <li><span className={styles.check}>✓</span> M&A due diligence support</li>
              <li><span className={styles.check}>✓</span> Litigation risk assessment</li>
            </ul>
          </div>
          <div className={styles.lawMcpVisual}>
            <h4>The Comparison</h4>
            <div className={styles.lawComparison}>
              <div className={`${styles.lawComparisonCol} ${styles.old}`}>
                <h5>Law Firm</h5>
                <ul>
                  <li>€500/hour</li>
                  <li>4-week turnaround</li>
                  <li>Junior does the work</li>
                  <li>Partner bills for "review"</li>
                  <li>10 pages of caveats</li>
                  <li>No institutional memory</li>
                </ul>
              </div>
              <div className={`${styles.lawComparisonCol} ${styles.new}`}>
                <h5>Law MCP</h5>
                <ul>
                  <li>€3.000/month flat</li>
                  <li>4-minute turnaround</li>
                  <li>AI does the work</li>
                  <li>You review if you want</li>
                  <li>Clear recommendations</li>
                  <li>Learns your preferences</li>
                </ul>
              </div>
            </div>
            <div className={styles.lawPrice}>
              <span className={styles.amount}>€3.000</span>
              <span className={styles.period}>/month</span>
              <span className={styles.vs}>vs. <s>€50.000+/month</s> at a law firm</span>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className={styles.ctaSection} id="contact">
        <h2>
          Ready to <strong>liberate</strong> your company?
        </h2>
        <p>
          Stop paying people to complicate your business. Start building with the people who
          actually create value.
        </p>
        <Link href="mailto:freedom@0711.ai" className={styles.btnPrimary}>
          Declare Independence
        </Link>
      </section>

      <Footer />
    </>
  );
}
