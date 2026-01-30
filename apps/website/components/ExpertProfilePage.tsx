'use client';

import React from 'react';

// ============================================================================
// EXPERT PROFILE PAGE - Public-facing expert profiles
// ============================================================================

const theme = {
  colors: {
    dark: '#141413',
    light: '#faf9f5',
    midGray: '#b0aea5',
    lightGray: '#e8e6dc',
    orange: '#d97757',
    blue: '#6a9bcc',
    green: '#788c5d',
    red: '#c75a5a',
    purple: '#8b7fc7',
  }
};

const MCP_CATALOG = {
  CTAX: {
    id: 'CTAX',
    name: 'German Tax Engine',
    icon: '📊',
    color: theme.colors.orange,
    description: 'VAT returns, ELSTER filing, tax optimization, audit preparation',
  },
  FPA: {
    id: 'FPA',
    name: 'FP&A Automation',
    icon: '📈',
    color: theme.colors.blue,
    description: 'Forecasting, budgeting, variance analysis, financial dashboards',
  },
  LEGAL: {
    id: 'LEGAL',
    name: 'Legal Intelligence',
    icon: '⚖️',
    color: theme.colors.dark,
    description: 'Contract review, compliance, risk assessment, NDA generation',
  },
};

interface ExpertProfile {
  id: string;
  firstName: string;
  lastName: string;
  avatar: string;
  headline: string;
  bio: string;

  // Performance
  rating: number;
  totalReviews: number;
  completedJobs: number;

  // MCPs
  mcpExpertise: Array<{
    mcpId: string;
    proficiency: 'intermediate' | 'expert';
    yearsExperience: number;
    automationRate: number;
    certifications: string[];
  }>;

  // Details
  yearsExperience: number;
  languages: string[];
  industries: string[];
  tools: string[];
  location: string;
  timezone: string;

  // Pricing & Availability
  rateMin: number;
  rateMax: number;
  avgResponseTime: string;
  availabilityStatus: 'available' | 'limited' | 'full';
  slotsAvailable: number;

  // Certifications
  certifications: Array<{
    name: string;
    verified: boolean;
    issuer: string;
  }>;

  // Reviews
  reviews: Array<{
    id: string;
    companyName: string;
    rating: number;
    text: string;
    date: string;
  }>;
}

const MOCK_EXPERT: ExpertProfile = {
  id: 'exp_sarah_mueller',
  firstName: 'Sarah',
  lastName: 'Müller',
  avatar: 'SM',
  headline: 'Senior Tax Specialist | 12+ years in German Corporate Tax',
  bio: 'Experienced Steuerberater specializing in corporate tax, VAT, and financial planning. Previously Senior Manager at Big 4, now helping 7 companies optimize their tax strategy and financial operations using AI-powered automation.',

  rating: 4.9,
  totalReviews: 47,
  completedJobs: 156,

  mcpExpertise: [
    {
      mcpId: 'CTAX',
      proficiency: 'expert',
      yearsExperience: 12,
      automationRate: 95,
      certifications: ['Steuerberater (StB)', 'CTAX Master (Platinum)', 'DATEV Professional'],
    },
    {
      mcpId: 'FPA',
      proficiency: 'expert',
      yearsExperience: 8,
      automationRate: 90,
      certifications: ['CPA (US)', 'FPA Pro'],
    },
    {
      mcpId: 'LEGAL',
      proficiency: 'intermediate',
      yearsExperience: 5,
      automationRate: 85,
      certifications: ['Contract Review Certified'],
    },
  ],

  yearsExperience: 12,
  languages: ['German (native)', 'English (fluent)', 'French (basic)'],
  industries: ['Tech/SaaS', 'Manufacturing', 'Retail', 'Finance'],
  tools: ['DATEV', 'SAP', 'Excel', 'Power BI', 'SQL', 'Python'],
  location: 'Remote',
  timezone: 'CET (Berlin)',

  rateMin: 3600,
  rateMax: 4200,
  avgResponseTime: '< 2 hours',
  availabilityStatus: 'available',
  slotsAvailable: 3,

  certifications: [
    { name: 'Steuerberater (StB)', verified: true, issuer: 'German Tax Authority' },
    { name: 'CPA (US)', verified: true, issuer: 'AICPA' },
    { name: 'DATEV Professional', verified: true, issuer: 'DATEV' },
    { name: '0711 CTAX Master', verified: true, issuer: '0711 Platform' },
    { name: '0711 FPA Pro', verified: true, issuer: '0711 Platform' },
  ],

  reviews: [
    {
      id: 'r1',
      companyName: 'Tech Startup (Series A)',
      rating: 5,
      text: 'Sarah transformed our tax process from chaos to complete automation. We went from 3-day turnarounds to same-day results, and caught several optimization opportunities that saved us €50k in our first year.',
      date: 'Nov 2025',
    },
    {
      id: 'r2',
      companyName: 'Manufacturing SMB',
      rating: 5,
      text: 'Incredibly responsive and thorough. The AI handles 95% of routine work, but Sarah\'s strategic guidance during our audit was invaluable. Highly recommend.',
      date: 'Oct 2025',
    },
    {
      id: 'r3',
      companyName: 'Retail Company',
      rating: 5,
      text: 'Best decision we made this year. Sarah manages both our tax and FP&A needs, and the automation means we get real-time insights instead of waiting weeks for reports.',
      date: 'Sep 2025',
    },
  ],
};

const ExpertProfilePage: React.FC<{ expert?: ExpertProfile }> = ({ expert = MOCK_EXPERT }) => {
  const [showBookingModal, setShowBookingModal] = React.useState(false);

  return (
    <div style={{ minHeight: '100vh', background: theme.colors.light }}>
      {/* Navigation */}
      <nav style={{
        padding: '20px 40px',
        background: 'white',
        borderBottom: `1px solid ${theme.colors.lightGray}`,
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <a href="/" style={{
            fontFamily: "'Poppins', sans-serif",
            fontSize: '24px',
            fontWeight: 600,
            textDecoration: 'none',
            color: theme.colors.dark,
          }}>
            0711<span style={{ color: theme.colors.orange }}>.</span>
          </a>
          <a href="/marketplace" style={{
            fontFamily: "'Poppins', sans-serif",
            fontSize: '14px',
            color: theme.colors.midGray,
            textDecoration: 'none',
          }}>
            ← Back to Marketplace
          </a>
        </div>
      </nav>

      {/* Main Content */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '40px 20px' }}>
        {/* Hero Section */}
        <div style={{
          background: 'white',
          borderRadius: '20px',
          padding: '40px',
          marginBottom: '24px',
          border: `1px solid ${theme.colors.lightGray}`,
        }}>
          <div style={{ display: 'flex', gap: '32px', alignItems: 'flex-start' }}>
            {/* Avatar */}
            <div style={{
              width: '120px',
              height: '120px',
              borderRadius: '24px',
              background: `linear-gradient(135deg, ${theme.colors.orange}, ${theme.colors.blue})`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '48px',
              fontFamily: "'Poppins', sans-serif",
              fontWeight: 600,
              color: 'white',
              flexShrink: 0,
            }}>
              {expert.avatar}
            </div>

            {/* Info */}
            <div style={{ flex: 1 }}>
              <h1 style={{
                fontFamily: "'Poppins', sans-serif",
                fontSize: '32px',
                fontWeight: 600,
                marginBottom: '8px',
              }}>
                {expert.firstName} {expert.lastName}
              </h1>

              <p style={{
                fontSize: '18px',
                color: theme.colors.midGray,
                marginBottom: '16px',
              }}>
                {expert.headline}
              </p>

              <div style={{ display: 'flex', gap: '24px', marginBottom: '20px', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '20px' }}>⭐</span>
                  <span style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600 }}>
                    {expert.rating}
                  </span>
                  <span style={{ fontSize: '14px', color: theme.colors.midGray }}>
                    ({expert.totalReviews} reviews)
                  </span>
                </div>
                <div style={{ fontSize: '14px', color: theme.colors.midGray }}>
                  📍 {expert.location} ({expert.timezone})
                </div>
                <div style={{ fontSize: '14px', color: theme.colors.midGray }}>
                  ✓ {expert.completedJobs} completed jobs
                </div>
              </div>

              {/* MCP Badges */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
                {expert.mcpExpertise.map(mcp => {
                  const mcpInfo = MCP_CATALOG[mcp.mcpId as keyof typeof MCP_CATALOG];
                  return (
                    <span key={mcp.mcpId} style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px 16px',
                      borderRadius: '100px',
                      background: `${mcpInfo.color}15`,
                      color: mcpInfo.color,
                      fontFamily: "'Poppins', sans-serif",
                      fontSize: '14px',
                      fontWeight: 500,
                    }}>
                      <span>{mcpInfo.icon}</span>
                      <span>{mcpInfo.name}</span>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '100px',
                        background: mcpInfo.color,
                        color: 'white',
                        fontSize: '11px',
                      }}>
                        {mcp.automationRate}% AI
                      </span>
                    </span>
                  );
                })}
              </div>

              {/* Pricing & Availability */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '16px',
                padding: '20px',
                background: theme.colors.light,
                borderRadius: '16px',
              }}>
                <div>
                  <p style={{ fontSize: '12px', color: theme.colors.midGray, marginBottom: '4px' }}>
                    Monthly Rate
                  </p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '20px', fontWeight: 600, color: theme.colors.green }}>
                    €{expert.rateMin.toLocaleString()} - €{expert.rateMax.toLocaleString()}
                  </p>
                  <p style={{ fontSize: '11px', color: theme.colors.midGray }}>per client</p>
                </div>
                <div>
                  <p style={{ fontSize: '12px', color: theme.colors.midGray, marginBottom: '4px' }}>
                    Response Time
                  </p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '20px', fontWeight: 600 }}>
                    {expert.avgResponseTime}
                  </p>
                  <p style={{ fontSize: '11px', color: theme.colors.midGray }}>average</p>
                </div>
                <div>
                  <p style={{ fontSize: '12px', color: theme.colors.midGray, marginBottom: '4px' }}>
                    Availability
                  </p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '20px', fontWeight: 600, color: theme.colors.green }}>
                    {expert.slotsAvailable} slots
                  </p>
                  <p style={{ fontSize: '11px', color: theme.colors.midGray }}>available now</p>
                </div>
              </div>
            </div>

            {/* CTA */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', minWidth: '200px' }}>
              <button
                onClick={() => setShowBookingModal(true)}
                style={{
                  padding: '16px 24px',
                  borderRadius: '100px',
                  border: 'none',
                  background: theme.colors.orange,
                  color: 'white',
                  fontFamily: "'Poppins', sans-serif",
                  fontSize: '16px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                Request Consultation
              </button>
              <button style={{
                padding: '12px 24px',
                borderRadius: '100px',
                border: `1.5px solid ${theme.colors.dark}`,
                background: 'transparent',
                color: theme.colors.dark,
                fontFamily: "'Poppins', sans-serif",
                fontSize: '14px',
                fontWeight: 500,
                cursor: 'pointer',
              }}>
                💬 Send Message
              </button>
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          {/* Left Column */}
          <div>
            {/* About */}
            <div style={{
              background: 'white',
              borderRadius: '20px',
              padding: '32px',
              marginBottom: '24px',
              border: `1px solid ${theme.colors.lightGray}`,
            }}>
              <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '20px', fontWeight: 600, marginBottom: '16px' }}>
                About
              </h2>
              <p style={{ fontSize: '15px', lineHeight: '1.7', color: theme.colors.dark }}>
                {expert.bio}
              </p>
            </div>

            {/* MCP Expertise */}
            <div style={{
              background: 'white',
              borderRadius: '20px',
              padding: '32px',
              marginBottom: '24px',
              border: `1px solid ${theme.colors.lightGray}`,
            }}>
              <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '20px', fontWeight: 600, marginBottom: '24px' }}>
                MCP Expertise
              </h2>

              {expert.mcpExpertise.map(mcp => {
                const mcpInfo = MCP_CATALOG[mcp.mcpId as keyof typeof MCP_CATALOG];
                return (
                  <div key={mcp.mcpId} style={{
                    padding: '24px',
                    background: theme.colors.light,
                    borderRadius: '16px',
                    marginBottom: '16px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '16px' }}>
                      <div style={{
                        width: '56px',
                        height: '56px',
                        borderRadius: '12px',
                        background: `${mcpInfo.color}15`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '28px',
                        flexShrink: 0,
                      }}>
                        {mcpInfo.icon}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                          <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '18px', fontWeight: 600 }}>
                            {mcpInfo.name}
                          </h3>
                          <span style={{
                            padding: '4px 12px',
                            borderRadius: '100px',
                            background: mcpInfo.color,
                            color: 'white',
                            fontFamily: "'Poppins', sans-serif",
                            fontSize: '12px',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                          }}>
                            {mcp.proficiency}
                          </span>
                        </div>
                        <p style={{ fontSize: '14px', color: theme.colors.midGray, marginBottom: '12px' }}>
                          {mcpInfo.description}
                        </p>
                        <div style={{ display: 'flex', gap: '24px', fontSize: '13px' }}>
                          <div>
                            <span style={{ color: theme.colors.midGray }}>Experience: </span>
                            <span style={{ fontWeight: 600 }}>{mcp.yearsExperience} years</span>
                          </div>
                          <div>
                            <span style={{ color: theme.colors.midGray }}>AI Automation: </span>
                            <span style={{ fontWeight: 600, color: theme.colors.green }}>{mcp.automationRate}%</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Certifications for this MCP */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {mcp.certifications.map(cert => (
                        <span key={cert} style={{
                          padding: '4px 10px',
                          borderRadius: '6px',
                          background: 'white',
                          border: `1px solid ${theme.colors.lightGray}`,
                          fontSize: '11px',
                          fontFamily: "'Poppins', sans-serif",
                          fontWeight: 500,
                        }}>
                          ✓ {cert}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Reviews */}
            <div style={{
              background: 'white',
              borderRadius: '20px',
              padding: '32px',
              border: `1px solid ${theme.colors.lightGray}`,
            }}>
              <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '20px', fontWeight: 600, marginBottom: '24px' }}>
                Client Reviews ({expert.totalReviews})
              </h2>

              {expert.reviews.map(review => (
                <div key={review.id} style={{
                  padding: '24px',
                  background: theme.colors.light,
                  borderRadius: '16px',
                  marginBottom: '16px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <div>
                      <p style={{ fontFamily: "'Poppins', sans-serif", fontWeight: 600, marginBottom: '4px' }}>
                        {review.companyName}
                      </p>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        {[...Array(5)].map((_, i) => (
                          <span key={i} style={{ color: i < review.rating ? theme.colors.orange : theme.colors.lightGray }}>
                            ⭐
                          </span>
                        ))}
                      </div>
                    </div>
                    <p style={{ fontSize: '13px', color: theme.colors.midGray }}>
                      {review.date}
                    </p>
                  </div>
                  <p style={{ fontSize: '14px', lineHeight: '1.6', fontStyle: 'italic' }}>
                    "{review.text}"
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column */}
          <div>
            {/* Quick Stats */}
            <div style={{
              background: 'white',
              borderRadius: '20px',
              padding: '24px',
              marginBottom: '24px',
              border: `1px solid ${theme.colors.lightGray}`,
            }}>
              <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '20px' }}>
                Quick Stats
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <p style={{ fontSize: '12px', color: theme.colors.midGray, marginBottom: '4px' }}>
                    Total Experience
                  </p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600 }}>
                    {expert.yearsExperience} years
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: '12px', color: theme.colors.midGray, marginBottom: '4px' }}>
                    Completed Jobs
                  </p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600 }}>
                    {expert.completedJobs}
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: '12px', color: theme.colors.midGray, marginBottom: '4px' }}>
                    Client Rating
                  </p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, color: theme.colors.orange }}>
                    {expert.rating} ⭐
                  </p>
                </div>
              </div>
            </div>

            {/* Languages */}
            <div style={{
              background: 'white',
              borderRadius: '20px',
              padding: '24px',
              marginBottom: '24px',
              border: `1px solid ${theme.colors.lightGray}`,
            }}>
              <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>
                Languages
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {expert.languages.map(lang => (
                  <div key={lang} style={{ fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>✓</span>
                    <span>{lang}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Industries */}
            <div style={{
              background: 'white',
              borderRadius: '20px',
              padding: '24px',
              marginBottom: '24px',
              border: `1px solid ${theme.colors.lightGray}`,
            }}>
              <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>
                Industry Experience
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {expert.industries.map(industry => (
                  <span key={industry} style={{
                    padding: '6px 12px',
                    borderRadius: '8px',
                    background: theme.colors.light,
                    fontSize: '13px',
                    fontFamily: "'Poppins', sans-serif",
                    fontWeight: 500,
                  }}>
                    {industry}
                  </span>
                ))}
              </div>
            </div>

            {/* Tools */}
            <div style={{
              background: 'white',
              borderRadius: '20px',
              padding: '24px',
              marginBottom: '24px',
              border: `1px solid ${theme.colors.lightGray}`,
            }}>
              <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>
                Tools & Software
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {expert.tools.map(tool => (
                  <span key={tool} style={{
                    padding: '6px 12px',
                    borderRadius: '8px',
                    background: theme.colors.light,
                    fontSize: '13px',
                    fontFamily: "'Poppins', sans-serif",
                    fontWeight: 500,
                  }}>
                    {tool}
                  </span>
                ))}
              </div>
            </div>

            {/* Certifications */}
            <div style={{
              background: 'white',
              borderRadius: '20px',
              padding: '24px',
              border: `1px solid ${theme.colors.lightGray}`,
            }}>
              <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>
                Certifications
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {expert.certifications.map(cert => (
                  <div key={cert.name} style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '12px',
                    background: theme.colors.light,
                    borderRadius: '12px',
                  }}>
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '8px',
                      background: cert.verified ? theme.colors.green : theme.colors.lightGray,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontSize: '16px',
                      flexShrink: 0,
                    }}>
                      {cert.verified ? '✓' : '○'}
                    </div>
                    <div>
                      <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '14px', fontWeight: 500, marginBottom: '2px' }}>
                        {cert.name}
                      </p>
                      <p style={{ fontSize: '12px', color: theme.colors.midGray }}>
                        {cert.issuer}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Booking Modal */}
      {showBookingModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            background: 'white',
            borderRadius: '20px',
            padding: '40px',
            maxWidth: '500px',
            width: '90%',
          }}>
            <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, marginBottom: '16px' }}>
              Request Consultation
            </h2>
            <p style={{ fontSize: '14px', color: theme.colors.midGray, marginBottom: '24px' }}>
              Send a message to {expert.firstName} to discuss your needs. Response time: {expert.avgResponseTime}
            </p>

            <textarea
              placeholder="Tell the expert about your company and what you need help with..."
              rows={6}
              style={{
                width: '100%',
                padding: '16px',
                borderRadius: '12px',
                border: `1px solid ${theme.colors.lightGray}`,
                fontFamily: "'Lora', serif",
                fontSize: '14px',
                marginBottom: '24px',
                resize: 'vertical',
              }}
            />

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setShowBookingModal(false)}
                style={{
                  flex: 1,
                  padding: '14px',
                  borderRadius: '100px',
                  border: `1.5px solid ${theme.colors.dark}`,
                  background: 'transparent',
                  fontFamily: "'Poppins', sans-serif",
                  fontSize: '14px',
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  alert('Request sent! The expert will respond within 2 hours.');
                  setShowBookingModal(false);
                }}
                style={{
                  flex: 1,
                  padding: '14px',
                  borderRadius: '100px',
                  border: 'none',
                  background: theme.colors.orange,
                  color: 'white',
                  fontFamily: "'Poppins', sans-serif",
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Send Request
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExpertProfilePage;
