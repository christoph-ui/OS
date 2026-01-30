'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Star, MapPin, Clock, Euro, Calendar, MessageSquare, Filter, ChevronRight } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
};

interface Expert {
  id: string;
  user_id: string;
  display_name: string;
  title: string;
  bio: string;
  avatar_url?: string;
  expertise_areas: string[];
  hourly_rate_cents: number;
  currency: string;
  rating: number;
  total_reviews: number;
  total_engagements: number;
  response_time_hours: number;
  location: string;
  languages: string[];
  verified: boolean;
  featured: boolean;
  available: boolean;
}

const sampleExperts: Expert[] = [
  {
    id: '1',
    user_id: 'u1',
    display_name: 'Dr. Stefan Weber',
    title: 'Corporate Tax Specialist',
    bio: 'Former Big 4 tax advisor with 15+ years experience in German corporate tax law. Specialist in transfer pricing and international tax structures.',
    expertise_areas: ['Corporate Tax', 'Transfer Pricing', 'M&A Tax', 'VAT'],
    hourly_rate_cents: 35000,
    currency: 'EUR',
    rating: 4.9,
    total_reviews: 127,
    total_engagements: 89,
    response_time_hours: 2,
    location: 'Munich, Germany',
    languages: ['German', 'English'],
    verified: true,
    featured: true,
    available: true,
  },
  {
    id: '2',
    user_id: 'u2',
    display_name: 'Maria Schmidt',
    title: 'ETIM Classification Expert',
    bio: 'Product data specialist with deep knowledge of ETIM, ECLASS, and BMEcat standards. Helped 50+ manufacturers standardize their product catalogs.',
    expertise_areas: ['ETIM', 'ECLASS', 'BMEcat', 'PIM'],
    hourly_rate_cents: 22000,
    currency: 'EUR',
    rating: 4.8,
    total_reviews: 94,
    total_engagements: 156,
    response_time_hours: 4,
    location: 'Stuttgart, Germany',
    languages: ['German', 'English', 'French'],
    verified: true,
    featured: true,
    available: true,
  },
  {
    id: '3',
    user_id: 'u3',
    display_name: 'Thomas Müller',
    title: 'Public Tender Consultant',
    bio: 'Expert in German public procurement law (GWB, VgV). Successfully supported €500M+ in tender submissions.',
    expertise_areas: ['Public Tenders', 'Procurement', 'GWB/VgV', 'EU Tenders'],
    hourly_rate_cents: 28000,
    currency: 'EUR',
    rating: 4.7,
    total_reviews: 62,
    total_engagements: 45,
    response_time_hours: 6,
    location: 'Berlin, Germany',
    languages: ['German', 'English'],
    verified: true,
    featured: false,
    available: true,
  },
  {
    id: '4',
    user_id: 'u4',
    display_name: 'Laura Fischer',
    title: 'E-Commerce Integration Specialist',
    bio: 'Shopify, Amazon, eBay integration expert. Specialized in multi-channel product syndication and marketplace optimization.',
    expertise_areas: ['Shopify', 'Amazon SP-API', 'eBay', 'Multi-Channel'],
    hourly_rate_cents: 18000,
    currency: 'EUR',
    rating: 4.9,
    total_reviews: 201,
    total_engagements: 312,
    response_time_hours: 1,
    location: 'Hamburg, Germany',
    languages: ['German', 'English'],
    verified: true,
    featured: true,
    available: true,
  },
  {
    id: '5',
    user_id: 'u5',
    display_name: 'Prof. Hans Richter',
    title: 'AI/ML Consultant',
    bio: 'Former professor of machine learning. Specialized in NLP, computer vision, and AI product development.',
    expertise_areas: ['Machine Learning', 'NLP', 'Computer Vision', 'MLOps'],
    hourly_rate_cents: 45000,
    currency: 'EUR',
    rating: 5.0,
    total_reviews: 34,
    total_engagements: 21,
    response_time_hours: 24,
    location: 'Zürich, Switzerland',
    languages: ['German', 'English'],
    verified: true,
    featured: false,
    available: false,
  },
];

const expertiseCategories = [
  'All',
  'Corporate Tax',
  'ETIM/ECLASS',
  'Public Tenders',
  'E-Commerce',
  'AI/ML',
  'Legal',
];

export default function ExpertsMarketplace() {
  const router = useRouter();
  const [experts, setExperts] = useState<Expert[]>(sampleExperts);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [showAvailableOnly, setShowAvailableOnly] = useState(false);
  const [sortBy, setSortBy] = useState<'rating' | 'price' | 'reviews'>('rating');

  const filteredExperts = experts
    .filter(expert => {
      const matchesSearch = !searchQuery ||
        expert.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        expert.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        expert.expertise_areas.some(e => e.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesCategory = selectedCategory === 'All' ||
        expert.expertise_areas.some(e => e.toLowerCase().includes(selectedCategory.toLowerCase()));

      const matchesAvailability = !showAvailableOnly || expert.available;

      return matchesSearch && matchesCategory && matchesAvailability;
    })
    .sort((a, b) => {
      if (sortBy === 'rating') return b.rating - a.rating;
      if (sortBy === 'price') return a.hourly_rate_cents - b.hourly_rate_cents;
      if (sortBy === 'reviews') return b.total_reviews - a.total_reviews;
      return 0;
    });

  return (
    <div style={{ minHeight: '100vh', backgroundColor: colors.light }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#fff',
        borderBottom: `1px solid ${colors.lightGray}`,
        padding: '24px 40px',
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <h1 style={{
            fontFamily: "'Poppins', sans-serif",
            fontSize: 28,
            fontWeight: 600,
            color: colors.dark,
            margin: '0 0 4px',
          }}>
            Expert Marketplace
          </h1>
          <p style={{ color: colors.midGray, margin: 0, fontSize: 14 }}>
            Connect with verified experts for personalized consulting
          </p>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 40px' }}>
        {/* Search & Filters */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: 12,
          border: `1px solid ${colors.lightGray}`,
          padding: 24,
          marginBottom: 24,
        }}>
          <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
            {/* Search */}
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              backgroundColor: colors.light,
              border: `1px solid ${colors.lightGray}`,
              borderRadius: 10,
              padding: '12px 16px',
            }}>
              <Search size={18} color={colors.midGray} />
              <input
                type="text"
                placeholder="Search experts by name, skill, or expertise..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  flex: 1,
                  border: 'none',
                  backgroundColor: 'transparent',
                  fontSize: 15,
                  outline: 'none',
                  color: colors.dark,
                }}
              />
            </div>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              style={{
                padding: '12px 16px',
                backgroundColor: '#fff',
                border: `1px solid ${colors.lightGray}`,
                borderRadius: 10,
                fontSize: 14,
                color: colors.dark,
                cursor: 'pointer',
              }}
            >
              <option value="rating">Sort: Top Rated</option>
              <option value="price">Sort: Lowest Price</option>
              <option value="reviews">Sort: Most Reviews</option>
            </select>

            {/* Available Toggle */}
            <button
              onClick={() => setShowAvailableOnly(!showAvailableOnly)}
              style={{
                padding: '12px 20px',
                backgroundColor: showAvailableOnly ? colors.green + '15' : '#fff',
                color: showAvailableOnly ? colors.green : colors.dark,
                border: `1px solid ${showAvailableOnly ? colors.green : colors.lightGray}`,
                borderRadius: 10,
                fontSize: 14,
                fontWeight: 500,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <Clock size={16} />
              Available Now
            </button>
          </div>

          {/* Category Pills */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {expertiseCategories.map(cat => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: selectedCategory === cat ? colors.orange : colors.light,
                  color: selectedCategory === cat ? '#fff' : colors.dark,
                  border: 'none',
                  borderRadius: 20,
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Results Count */}
        <div style={{ marginBottom: 16, color: colors.midGray, fontSize: 14 }}>
          {filteredExperts.length} expert{filteredExperts.length !== 1 ? 's' : ''} found
        </div>

        {/* Expert Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {filteredExperts.map(expert => (
            <ExpertCard
              key={expert.id}
              expert={expert}
              onClick={() => router.push(`/experts/${expert.id}`)}
            />
          ))}
        </div>

        {filteredExperts.length === 0 && (
          <div style={{
            textAlign: 'center',
            padding: 60,
            backgroundColor: '#fff',
            borderRadius: 12,
            border: `1px solid ${colors.lightGray}`,
          }}>
            <p style={{ color: colors.midGray, margin: 0 }}>
              No experts found matching your criteria
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function ExpertCard({ expert, onClick }: { expert: Expert; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      style={{
        backgroundColor: '#fff',
        borderRadius: 12,
        border: `1px solid ${colors.lightGray}`,
        padding: 24,
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
      onMouseOver={(e) => {
        e.currentTarget.style.borderColor = colors.orange + '60';
        e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.06)';
      }}
      onMouseOut={(e) => {
        e.currentTarget.style.borderColor = colors.lightGray;
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      <div style={{ display: 'flex', gap: 20 }}>
        {/* Avatar */}
        <div style={{
          width: 80,
          height: 80,
          borderRadius: 12,
          backgroundColor: colors.dark + '10',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 28,
          fontWeight: 600,
          color: colors.dark + '60',
          flexShrink: 0,
        }}>
          {expert.display_name.split(' ').map(n => n[0]).join('')}
        </div>

        {/* Info */}
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 8 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <h3 style={{
                  fontFamily: "'Poppins', sans-serif",
                  fontSize: 18,
                  fontWeight: 600,
                  color: colors.dark,
                  margin: 0,
                }}>
                  {expert.display_name}
                </h3>
                {expert.verified && (
                  <span style={{
                    fontSize: 10,
                    fontWeight: 600,
                    color: colors.blue,
                    backgroundColor: colors.blue + '15',
                    padding: '2px 8px',
                    borderRadius: 4,
                  }}>
                    VERIFIED
                  </span>
                )}
                {expert.featured && (
                  <span style={{
                    fontSize: 10,
                    fontWeight: 600,
                    color: colors.orange,
                    backgroundColor: colors.orange + '15',
                    padding: '2px 8px',
                    borderRadius: 4,
                  }}>
                    TOP RATED
                  </span>
                )}
              </div>
              <p style={{
                fontSize: 14,
                color: colors.midGray,
                margin: '4px 0 0',
              }}>
                {expert.title}
              </p>
            </div>

            {/* Price */}
            <div style={{ textAlign: 'right' }}>
              <div style={{
                fontFamily: "'Poppins', sans-serif",
                fontSize: 22,
                fontWeight: 600,
                color: colors.dark,
              }}>
                €{(expert.hourly_rate_cents / 100).toFixed(0)}
                <span style={{ fontSize: 14, fontWeight: 400, color: colors.midGray }}>/hr</span>
              </div>
            </div>
          </div>

          {/* Bio */}
          <p style={{
            fontSize: 14,
            color: colors.dark + 'cc',
            margin: '12px 0',
            lineHeight: 1.5,
          }}>
            {expert.bio}
          </p>

          {/* Tags */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
            {expert.expertise_areas.map(area => (
              <span
                key={area}
                style={{
                  fontSize: 12,
                  color: colors.dark,
                  backgroundColor: colors.light,
                  padding: '4px 12px',
                  borderRadius: 6,
                }}
              >
                {area}
              </span>
            ))}
          </div>

          {/* Stats Row */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 24,
            paddingTop: 16,
            borderTop: `1px solid ${colors.lightGray}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Star size={16} color={colors.orange} fill={colors.orange} />
              <span style={{ fontSize: 14, fontWeight: 600, color: colors.dark }}>
                {expert.rating.toFixed(1)}
              </span>
              <span style={{ fontSize: 13, color: colors.midGray }}>
                ({expert.total_reviews} reviews)
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <MapPin size={16} color={colors.midGray} />
              <span style={{ fontSize: 13, color: colors.midGray }}>
                {expert.location}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Clock size={16} color={colors.midGray} />
              <span style={{ fontSize: 13, color: colors.midGray }}>
                Responds in ~{expert.response_time_hours}h
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <MessageSquare size={16} color={colors.midGray} />
              <span style={{ fontSize: 13, color: colors.midGray }}>
                {expert.languages.join(', ')}
              </span>
            </div>

            <div style={{ marginLeft: 'auto' }}>
              {expert.available ? (
                <span style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  fontSize: 13,
                  fontWeight: 600,
                  color: colors.green,
                }}>
                  <span style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: colors.green,
                  }} />
                  Available
                </span>
              ) : (
                <span style={{
                  fontSize: 13,
                  color: colors.midGray,
                }}>
                  Unavailable
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Arrow */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          color: colors.midGray,
        }}>
          <ChevronRight size={24} />
        </div>
      </div>
    </div>
  );
}
