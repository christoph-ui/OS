'use client';

import React, { useState, useMemo } from 'react';

// ============================================================================
// EXPERT MARKETPLACE - Company view for discovering experts
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
  CTAX: { id: 'CTAX', name: 'German Tax', icon: '📊', color: theme.colors.orange },
  FPA: { id: 'FPA', name: 'FP&A', icon: '📈', color: theme.colors.blue },
  TENDER: { id: 'TENDER', name: 'Tender', icon: '📋', color: theme.colors.green },
  PRICING: { id: 'PRICING', name: 'Pricing', icon: '💰', color: theme.colors.purple },
  ETIM: { id: 'ETIM', name: 'Product Class', icon: '🏷️', color: '#5ab5b5' },
  LEGAL: { id: 'LEGAL', name: 'Legal', icon: '⚖️', color: theme.colors.dark },
  HR: { id: 'HR', name: 'HR & Talent', icon: '👥', color: '#e8a87c' },
  REVENUE: { id: 'REVENUE', name: 'Revenue', icon: '🎯', color: theme.colors.orange },
};

interface ExpertCard {
  id: string;
  firstName: string;
  lastName: string;
  avatar: string;
  headline: string;
  rating: number;
  totalReviews: number;
  mcps: string[];
  rateMin: number;
  rateMax: number;
  slotsAvailable: number;
  avgResponseTime: string;
  yearsExperience: number;
  industries: string[];
  languages: string[];
  automationRate: number;
  matchScore?: number;
  matchReasons?: string[];
}

const MOCK_EXPERTS: ExpertCard[] = [
  {
    id: '1',
    firstName: 'Sarah',
    lastName: 'Müller',
    avatar: 'SM',
    headline: 'Senior Tax Specialist | 12+ years',
    rating: 4.9,
    totalReviews: 47,
    mcps: ['CTAX', 'FPA', 'LEGAL'],
    rateMin: 3600,
    rateMax: 4200,
    slotsAvailable: 3,
    avgResponseTime: '< 2 hours',
    yearsExperience: 12,
    industries: ['Tech/SaaS', 'Manufacturing', 'Retail'],
    languages: ['German', 'English'],
    automationRate: 92,
  },
  {
    id: '2',
    firstName: 'Michael',
    lastName: 'Koch',
    avatar: 'MK',
    headline: 'FP&A Expert | Ex-McKinsey',
    rating: 4.8,
    totalReviews: 32,
    mcps: ['FPA', 'CTAX', 'REVENUE'],
    rateMin: 3800,
    rateMax: 4500,
    slotsAvailable: 5,
    avgResponseTime: '< 3 hours',
    yearsExperience: 10,
    industries: ['Tech/SaaS', 'Finance', 'E-commerce'],
    languages: ['German', 'English', 'French'],
    automationRate: 88,
  },
  {
    id: '3',
    firstName: 'Anna',
    lastName: 'Lehmann',
    avatar: 'AL',
    headline: 'Corporate Lawyer | M&A Specialist',
    rating: 4.7,
    totalReviews: 28,
    mcps: ['LEGAL'],
    rateMin: 4500,
    rateMax: 5200,
    slotsAvailable: 2,
    avgResponseTime: '< 4 hours',
    yearsExperience: 8,
    industries: ['Tech/SaaS', 'Finance', 'Healthcare'],
    languages: ['German', 'English'],
    automationRate: 85,
  },
  {
    id: '4',
    firstName: 'Thomas',
    lastName: 'Weber',
    avatar: 'TW',
    headline: 'Product Classification Expert',
    rating: 4.9,
    totalReviews: 51,
    mcps: ['ETIM', 'PRICING'],
    rateMin: 3200,
    rateMax: 3800,
    slotsAvailable: 4,
    avgResponseTime: '< 1 hour',
    yearsExperience: 15,
    industries: ['Manufacturing', 'Retail', 'E-commerce'],
    languages: ['German', 'English', 'Italian'],
    automationRate: 96,
  },
  {
    id: '5',
    firstName: 'Lisa',
    lastName: 'Schmidt',
    avatar: 'LS',
    headline: 'Tax & Audit Specialist',
    rating: 4.8,
    totalReviews: 39,
    mcps: ['CTAX', 'FPA'],
    rateMin: 3400,
    rateMax: 4000,
    slotsAvailable: 6,
    avgResponseTime: '< 2 hours',
    yearsExperience: 9,
    industries: ['Manufacturing', 'Retail', 'Logistics'],
    languages: ['German', 'English'],
    automationRate: 90,
  },
  {
    id: '6',
    firstName: 'David',
    lastName: 'Fischer',
    avatar: 'DF',
    headline: 'Tender & RFP Specialist',
    rating: 4.6,
    totalReviews: 24,
    mcps: ['TENDER', 'PRICING'],
    rateMin: 3500,
    rateMax: 4200,
    slotsAvailable: 3,
    avgResponseTime: '< 3 hours',
    yearsExperience: 7,
    industries: ['Tech/SaaS', 'Consulting', 'Construction'],
    languages: ['German', 'English', 'Spanish'],
    automationRate: 82,
  },
];

interface Filters {
  mcps: string[];
  industry: string;
  priceRange: [number, number];
  availability: 'any' | 'available';
  languages: string[];
  sortBy: 'match' | 'rating' | 'experience' | 'price_low' | 'price_high';
}

// Matching algorithm
const calculateMatchScore = (expert: ExpertCard, filters: Filters, companyNeeds: any = {}) => {
  let score = 0;
  const reasons: string[] = [];

  // MCP overlap (40% weight)
  if (filters.mcps.length > 0) {
    const mcpMatch = filters.mcps.filter(m => expert.mcps.includes(m)).length / filters.mcps.length;
    score += mcpMatch * 40;
    if (mcpMatch >= 0.67) {
      reasons.push(`Strong ${filters.mcps.slice(0, 2).map(m => MCP_CATALOG[m as keyof typeof MCP_CATALOG].name).join(' + ')} expertise`);
    }
  } else {
    score += 20; // No MCP filter = partial credit
  }

  // Industry match (20% weight)
  if (filters.industry && filters.industry !== 'any') {
    if (expert.industries.includes(filters.industry)) {
      score += 20;
      reasons.push(`${filters.industry} experience`);
    }
  } else {
    score += 10; // No industry filter = partial credit
  }

  // Price alignment (15% weight)
  const avgRate = (expert.rateMin + expert.rateMax) / 2;
  const [minPrice, maxPrice] = filters.priceRange;
  if (avgRate >= minPrice && avgRate <= maxPrice) {
    score += 15;
    reasons.push('Within budget');
  } else if (avgRate < minPrice + 500 || avgRate > maxPrice - 500) {
    score += 7; // Close to budget
  }

  // Availability (10% weight)
  if (expert.slotsAvailable > 0) {
    score += 10;
    reasons.push('Available now');
  }

  // Response time (10% weight)
  const responseHours = parseFloat(expert.avgResponseTime.match(/\d+/)?.[0] || '5');
  if (responseHours <= 2) {
    score += 10;
    reasons.push(`<${responseHours}hr response`);
  } else if (responseHours <= 4) {
    score += 5;
  }

  // AI automation rate (5% weight)
  if (expert.automationRate >= 90) {
    score += 5;
  } else if (expert.automationRate >= 85) {
    score += 3;
  }

  return {
    score: Math.min(Math.round(score), 100),
    reasons: reasons.slice(0, 3), // Top 3 reasons
  };
};

const ExpertMarketplace: React.FC = () => {
  const [filters, setFilters] = useState<Filters>({
    mcps: [],
    industry: 'any',
    priceRange: [2000, 6000],
    availability: 'any',
    languages: ['German'],
    sortBy: 'match',
  });

  const [selectedExpert, setSelectedExpert] = useState<string | null>(null);

  // Calculate match scores and filter experts
  const filteredExperts = useMemo(() => {
    let experts = MOCK_EXPERTS.map(expert => {
      const { score, reasons } = calculateMatchScore(expert, filters);
      return {
        ...expert,
        matchScore: score,
        matchReasons: reasons,
      };
    });

    // Filter by availability
    if (filters.availability === 'available') {
      experts = experts.filter(e => e.slotsAvailable > 0);
    }

    // Filter by languages
    if (filters.languages.length > 0) {
      experts = experts.filter(e =>
        filters.languages.every(lang => e.languages.includes(lang))
      );
    }

    // Sort
    switch (filters.sortBy) {
      case 'match':
        experts.sort((a, b) => (b.matchScore || 0) - (a.matchScore || 0));
        break;
      case 'rating':
        experts.sort((a, b) => b.rating - a.rating);
        break;
      case 'experience':
        experts.sort((a, b) => b.yearsExperience - a.yearsExperience);
        break;
      case 'price_low':
        experts.sort((a, b) => a.rateMin - b.rateMin);
        break;
      case 'price_high':
        experts.sort((a, b) => b.rateMax - a.rateMax);
        break;
    }

    return experts;
  }, [filters]);

  const toggleMcp = (mcpId: string) => {
    setFilters(prev => ({
      ...prev,
      mcps: prev.mcps.includes(mcpId)
        ? prev.mcps.filter(m => m !== mcpId)
        : [...prev.mcps, mcpId],
    }));
  };

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
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <a href="/" style={{
            fontFamily: "'Poppins', sans-serif",
            fontSize: '24px',
            fontWeight: 600,
            textDecoration: 'none',
            color: theme.colors.dark,
          }}>
            0711<span style={{ color: theme.colors.orange }}>.</span>
          </a>
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <a href="/company/dashboard" style={{
              fontFamily: "'Poppins', sans-serif",
              fontSize: '14px',
              color: theme.colors.midGray,
              textDecoration: 'none',
            }}>
              My Experts
            </a>
            <button style={{
              padding: '10px 20px',
              borderRadius: '100px',
              border: 'none',
              background: theme.colors.dark,
              color: 'white',
              fontFamily: "'Poppins', sans-serif",
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer',
            }}>
              Account
            </button>
          </div>
        </div>
      </nav>

      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '40px 20px' }}>
        {/* Header */}
        <div style={{ marginBottom: '40px' }}>
          <h1 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '32px', fontWeight: 600, marginBottom: '8px' }}>
            Find Your Perfect Expert
          </h1>
          <p style={{ color: theme.colors.midGray, fontSize: '16px' }}>
            {filteredExperts.length} experts match your criteria
          </p>
        </div>

        {/* Filters */}
        <div style={{
          background: 'white',
          borderRadius: '20px',
          padding: '32px',
          marginBottom: '32px',
          border: `1px solid ${theme.colors.lightGray}`,
        }}>
          {/* MCP Selection */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontFamily: "'Poppins', sans-serif", fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>
              What expertise do you need?
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {Object.values(MCP_CATALOG).map(mcp => {
                const isSelected = filters.mcps.includes(mcp.id);
                return (
                  <button
                    key={mcp.id}
                    onClick={() => toggleMcp(mcp.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '10px 16px',
                      borderRadius: '100px',
                      border: 'none',
                      background: isSelected ? mcp.color : theme.colors.lightGray,
                      color: isSelected ? 'white' : theme.colors.dark,
                      fontFamily: "'Poppins', sans-serif",
                      fontSize: '14px',
                      fontWeight: 500,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <span>{mcp.icon}</span>
                    <span>{mcp.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Other Filters */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            {/* Industry */}
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
                Industry
              </label>
              <select
                value={filters.industry}
                onChange={(e) => setFilters(prev => ({ ...prev, industry: e.target.value }))}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  border: `1px solid ${theme.colors.lightGray}`,
                  fontFamily: "'Lora', serif",
                  fontSize: '14px',
                  background: 'white',
                }}
              >
                <option value="any">Any Industry</option>
                <option value="Tech/SaaS">Tech/SaaS</option>
                <option value="Manufacturing">Manufacturing</option>
                <option value="Retail">Retail</option>
                <option value="Finance">Finance</option>
                <option value="Healthcare">Healthcare</option>
                <option value="E-commerce">E-commerce</option>
                <option value="Logistics">Logistics</option>
              </select>
            </div>

            {/* Price Range */}
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
                Budget (€/month)
              </label>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  type="number"
                  value={filters.priceRange[0]}
                  onChange={(e) => setFilters(prev => ({
                    ...prev,
                    priceRange: [parseInt(e.target.value), prev.priceRange[1]],
                  }))}
                  style={{
                    width: '80px',
                    padding: '10px',
                    borderRadius: '10px',
                    border: `1px solid ${theme.colors.lightGray}`,
                    fontFamily: "'Lora', serif",
                    fontSize: '14px',
                  }}
                />
                <span>-</span>
                <input
                  type="number"
                  value={filters.priceRange[1]}
                  onChange={(e) => setFilters(prev => ({
                    ...prev,
                    priceRange: [prev.priceRange[0], parseInt(e.target.value)],
                  }))}
                  style={{
                    width: '80px',
                    padding: '10px',
                    borderRadius: '10px',
                    border: `1px solid ${theme.colors.lightGray}`,
                    fontFamily: "'Lora', serif",
                    fontSize: '14px',
                  }}
                />
              </div>
            </div>

            {/* Availability */}
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
                Availability
              </label>
              <select
                value={filters.availability}
                onChange={(e) => setFilters(prev => ({ ...prev, availability: e.target.value as any }))}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  border: `1px solid ${theme.colors.lightGray}`,
                  fontFamily: "'Lora', serif",
                  fontSize: '14px',
                  background: 'white',
                }}
              >
                <option value="any">Any</option>
                <option value="available">Available Now</option>
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
                Sort By
              </label>
              <select
                value={filters.sortBy}
                onChange={(e) => setFilters(prev => ({ ...prev, sortBy: e.target.value as any }))}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  border: `1px solid ${theme.colors.lightGray}`,
                  fontFamily: "'Lora', serif",
                  fontSize: '14px',
                  background: 'white',
                }}
              >
                <option value="match">Best Match</option>
                <option value="rating">Highest Rated</option>
                <option value="experience">Most Experience</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
              </select>
            </div>
          </div>
        </div>

        {/* Expert Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '24px' }}>
          {filteredExperts.map(expert => (
            <div
              key={expert.id}
              style={{
                background: 'white',
                borderRadius: '20px',
                padding: '28px',
                border: `1px solid ${theme.colors.lightGray}`,
                position: 'relative',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 20px 40px rgba(20,20,19,0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
              onClick={() => window.location.href = `/experts/${expert.id}`}
            >
              {/* Match Badge */}
              {expert.matchScore && expert.matchScore >= 80 && (
                <div style={{
                  position: 'absolute',
                  top: '20px',
                  right: '20px',
                  padding: '6px 12px',
                  borderRadius: '100px',
                  background: theme.colors.green,
                  color: 'white',
                  fontFamily: "'Poppins', sans-serif",
                  fontSize: '12px',
                  fontWeight: 600,
                }}>
                  {expert.matchScore}% Match ★
                </div>
              )}

              {/* Avatar & Name */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '16px',
                  background: `linear-gradient(135deg, ${theme.colors.orange}, ${theme.colors.blue})`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '24px',
                  fontFamily: "'Poppins', sans-serif",
                  fontWeight: 600,
                  color: 'white',
                  flexShrink: 0,
                }}>
                  {expert.avatar}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <h3 style={{
                    fontFamily: "'Poppins', sans-serif",
                    fontSize: '18px',
                    fontWeight: 600,
                    marginBottom: '4px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {expert.firstName} {expert.lastName}
                  </h3>
                  <p style={{ fontSize: '13px', color: theme.colors.midGray }}>
                    {expert.headline}
                  </p>
                </div>
              </div>

              {/* Rating */}
              <div style={{ display: 'flex', gap: '6px', marginBottom: '16px', alignItems: 'center' }}>
                <span style={{ fontSize: '18px' }}>⭐</span>
                <span style={{ fontFamily: "'Poppins', sans-serif", fontWeight: 600, fontSize: '15px' }}>
                  {expert.rating}
                </span>
                <span style={{ fontSize: '13px', color: theme.colors.midGray }}>
                  ({expert.totalReviews} reviews)
                </span>
              </div>

              {/* MCPs */}
              <div style={{ display: 'flex', gap: '6px', marginBottom: '16px', flexWrap: 'wrap' }}>
                {expert.mcps.map(mcpId => {
                  const mcp = MCP_CATALOG[mcpId as keyof typeof MCP_CATALOG];
                  return (
                    <span key={mcpId} style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      background: `${mcp.color}15`,
                      color: mcp.color,
                      fontSize: '12px',
                      fontFamily: "'Poppins', sans-serif",
                      fontWeight: 500,
                    }}>
                      <span>{mcp.icon}</span>
                      <span>{mcp.name}</span>
                    </span>
                  );
                })}
              </div>

              {/* Stats */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '12px',
                padding: '16px',
                background: theme.colors.light,
                borderRadius: '12px',
                marginBottom: '16px',
              }}>
                <div>
                  <p style={{ fontSize: '11px', color: theme.colors.midGray, marginBottom: '2px' }}>Rate</p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '14px', fontWeight: 600, color: theme.colors.green }}>
                    €{expert.rateMin.toLocaleString()}-{expert.rateMax.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: '11px', color: theme.colors.midGray, marginBottom: '2px' }}>Response</p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '14px', fontWeight: 600 }}>
                    {expert.avgResponseTime}
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: '11px', color: theme.colors.midGray, marginBottom: '2px' }}>Availability</p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '14px', fontWeight: 600, color: expert.slotsAvailable > 0 ? theme.colors.green : theme.colors.red }}>
                    {expert.slotsAvailable > 0 ? `${expert.slotsAvailable} slots` : 'Full'}
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: '11px', color: theme.colors.midGray, marginBottom: '2px' }}>AI Rate</p>
                  <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '14px', fontWeight: 600, color: theme.colors.blue }}>
                    {expert.automationRate}%
                  </p>
                </div>
              </div>

              {/* Match Reasons */}
              {expert.matchReasons && expert.matchReasons.length > 0 && (
                <div style={{ marginBottom: '16px' }}>
                  <p style={{ fontSize: '12px', fontWeight: 600, color: theme.colors.green, marginBottom: '6px' }}>
                    Why this expert:
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {expert.matchReasons.map((reason, i) => (
                      <p key={i} style={{ fontSize: '12px', color: theme.colors.midGray }}>
                        ✓ {reason}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    window.location.href = `/experts/${expert.id}`;
                  }}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: '100px',
                    border: 'none',
                    background: theme.colors.orange,
                    color: 'white',
                    fontFamily: "'Poppins', sans-serif",
                    fontSize: '14px',
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  View Profile
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    alert('Consultation request sent!');
                  }}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: '100px',
                    border: `1.5px solid ${theme.colors.dark}`,
                    background: 'transparent',
                    color: theme.colors.dark,
                    fontFamily: "'Poppins', sans-serif",
                    fontSize: '14px',
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  Book
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* No Results */}
        {filteredExperts.length === 0 && (
          <div style={{
            background: 'white',
            borderRadius: '20px',
            padding: '60px',
            textAlign: 'center',
            border: `1px solid ${theme.colors.lightGray}`,
          }}>
            <p style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</p>
            <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '20px', fontWeight: 600, marginBottom: '8px' }}>
              No experts found
            </h3>
            <p style={{ color: theme.colors.midGray }}>
              Try adjusting your filters to see more results
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExpertMarketplace;
