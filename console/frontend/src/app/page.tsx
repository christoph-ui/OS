'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { colors } from '@/lib/theme';
import { 
  Sparkles, Zap, Database, Share2, Shield, Clock,
  ArrowRight, Check, MessageSquare, BarChart3, Package,
  Users, Briefcase, Building2, Star, GraduationCap, HeartHandshake
} from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('0711_token');
    if (token) {
      setIsLoggedIn(true);
    }
  }, []);

  const features = [
    {
      icon: <Database size={24} />,
      title: 'Data Intelligence',
      description: 'Import BMECat, ETIM, DATANORM, CSV, Excel. AI understands your product data instantly.',
    },
    {
      icon: <Sparkles size={24} />,
      title: 'AI-Powered Enrichment',
      description: 'Generate descriptions, classify products, fill missing data with German-trained AI.',
    },
    {
      icon: <Share2 size={24} />,
      title: 'Multi-Channel Syndication',
      description: 'Publish to Amazon, eBay, your own shop. One source, all channels.',
    },
    {
      icon: <BarChart3 size={24} />,
      title: 'Market Intelligence',
      description: 'Monitor competitors, track prices, find tender opportunities automatically.',
    },
    {
      icon: <Shield size={24} />,
      title: 'German Compliance',
      description: 'DSGVO compliant. German hosting. Tax & legal experts built-in.',
    },
    {
      icon: <Clock size={24} />,
      title: '24h Time-to-Value',
      description: 'From data upload to live channels in one day. Not months.',
    },
  ];

  const userTypes = [
    {
      id: 'customer',
      title: 'For Businesses',
      subtitle: 'Distributors & Manufacturers',
      description: 'Manage your product data, enrich with AI, publish everywhere.',
      icon: <Building2 size={32} />,
      color: colors.orange,
      actions: [
        { label: 'Start Onboarding', href: '/onboarding', primary: true },
        { label: 'Login', href: '/login', primary: false },
      ],
    },
    {
      id: 'expert',
      title: 'For Experts',
      subtitle: 'Tax, Legal, ETIM, Data Specialists',
      description: 'Offer your expertise to businesses. Get paid for consultations.',
      icon: <GraduationCap size={32} />,
      color: colors.blue || '#6a9bcc',
      actions: [
        { label: 'Browse Experts', href: '/experts', primary: false },
        { label: 'Become an Expert', href: '/expert-signup', primary: true },
      ],
    },
    {
      id: 'partner',
      title: 'For Partners',
      subtitle: 'Agencies & Consultants',
      description: 'Manage multiple clients, white-label solutions, earn commissions.',
      icon: <HeartHandshake size={32} />,
      color: colors.green || '#788c5d',
      actions: [
        { label: 'Partner Portal', href: '/partner', primary: false },
        { label: 'Become a Partner', href: '/partner-signup', primary: true },
      ],
    },
  ];

  const expertCategories = [
    { name: 'Tax & Finance', count: 24, icon: '💰' },
    { name: 'ETIM & Classification', count: 18, icon: '🏭' },
    { name: 'Legal & Compliance', count: 12, icon: '⚖️' },
    { name: 'Data & PIM', count: 31, icon: '📊' },
    { name: 'E-Commerce', count: 27, icon: '🛒' },
    { name: 'Tender & Procurement', count: 9, icon: '📋' },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: colors.light,
      fontFamily: "'Inter', -apple-system, sans-serif",
    }}>
      {/* Header */}
      <header style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        backgroundColor: 'rgba(250, 249, 245, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: `1px solid ${colors.lightGray}`,
        zIndex: 100,
        padding: '16px 40px',
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              background: `linear-gradient(135deg, ${colors.orange}, ${colors.orange}dd)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 700,
              fontSize: 14,
            }}>
              07
            </div>
            <span style={{
              fontSize: 20,
              fontWeight: 600,
              color: colors.dark,
              fontFamily: "'Poppins', sans-serif",
            }}>
              0711
            </span>
          </div>

          <nav style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
            <a href="#features" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Features</a>
            <a href="/experts" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Experts</a>
            <a href="#start" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Get Started</a>
            <a href="/partner" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Partners</a>
            
            <div style={{ width: 1, height: 20, backgroundColor: colors.lightGray, margin: '0 8px' }} />
            
            {isLoggedIn ? (
              <button
                onClick={() => router.push('/dashboard')}
                style={{
                  padding: '10px 20px',
                  backgroundColor: colors.orange,
                  color: 'white',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                Dashboard <ArrowRight size={16} />
              </button>
            ) : (
              <div style={{ display: 'flex', gap: 12 }}>
                <button
                  onClick={() => router.push('/login')}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: 'transparent',
                    color: colors.dark,
                    border: `1px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 14,
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  Login
                </button>
                <button
                  onClick={() => router.push('/onboarding')}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: colors.orange,
                    color: 'white',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Start Free
                </button>
              </div>
            )}
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section style={{
        paddingTop: 160,
        paddingBottom: 80,
        textAlign: 'center',
        background: `linear-gradient(180deg, ${colors.light} 0%, white 100%)`,
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto', padding: '0 20px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 16px',
            backgroundColor: colors.orange + '15',
            borderRadius: 20,
            marginBottom: 24,
          }}>
            <Sparkles size={16} color={colors.orange} />
            <span style={{ fontSize: 14, color: colors.orange, fontWeight: 500 }}>
              AI-Powered B2B Intelligence Platform
            </span>
          </div>

          <h1 style={{
            fontSize: 56,
            fontWeight: 700,
            color: colors.dark,
            lineHeight: 1.1,
            margin: '0 0 24px',
            fontFamily: "'Poppins', sans-serif",
          }}>
            Your Products.{' '}
            <span style={{ color: colors.orange }}>Everywhere.</span>
          </h1>

          <p style={{
            fontSize: 20,
            color: colors.midGray,
            lineHeight: 1.6,
            margin: '0 0 40px',
            maxWidth: 600,
            marginLeft: 'auto',
            marginRight: 'auto',
          }}>
            Import product data. Enrich with AI. Publish to every channel. 
            Connect with domain experts. German B2B intelligence platform.
          </p>

          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => router.push('/onboarding')}
              style={{
                padding: '16px 32px',
                backgroundColor: colors.orange,
                color: 'white',
                border: 'none',
                borderRadius: 12,
                fontSize: 16,
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <Zap size={20} />
              Start Onboarding
            </button>
            <button
              onClick={() => router.push('/experts')}
              style={{
                padding: '16px 32px',
                backgroundColor: 'white',
                color: colors.dark,
                border: `2px solid ${colors.lightGray}`,
                borderRadius: 12,
                fontSize: 16,
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <Users size={20} />
              Find an Expert
            </button>
          </div>
        </div>
      </section>

      {/* User Types Section */}
      <section id="start" style={{
        padding: '80px 40px',
        backgroundColor: 'white',
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <h2 style={{
              fontSize: 36,
              fontWeight: 700,
              color: colors.dark,
              margin: '0 0 16px',
              fontFamily: "'Poppins', sans-serif",
            }}>
              Choose your path
            </h2>
            <p style={{ fontSize: 18, color: colors.midGray, margin: 0 }}>
              Whether you're a business, expert, or partner — we've got you covered.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 24,
          }}>
            {userTypes.map((type) => (
              <div
                key={type.id}
                style={{
                  padding: 32,
                  backgroundColor: colors.light,
                  borderRadius: 16,
                  border: `2px solid transparent`,
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = type.color;
                  e.currentTarget.style.transform = 'translateY(-4px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'transparent';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <div style={{
                  width: 64,
                  height: 64,
                  borderRadius: 16,
                  backgroundColor: type.color + '15',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: type.color,
                  marginBottom: 20,
                }}>
                  {type.icon}
                </div>

                <h3 style={{
                  fontSize: 22,
                  fontWeight: 600,
                  color: colors.dark,
                  margin: '0 0 4px',
                }}>
                  {type.title}
                </h3>
                <p style={{
                  fontSize: 14,
                  color: type.color,
                  fontWeight: 500,
                  margin: '0 0 12px',
                }}>
                  {type.subtitle}
                </p>
                <p style={{
                  fontSize: 15,
                  color: colors.midGray,
                  lineHeight: 1.6,
                  margin: '0 0 24px',
                }}>
                  {type.description}
                </p>

                <div style={{ display: 'flex', gap: 12 }}>
                  {type.actions.map((action, i) => (
                    <button
                      key={i}
                      onClick={() => router.push(action.href)}
                      style={{
                        flex: 1,
                        padding: '12px 16px',
                        backgroundColor: action.primary ? type.color : 'white',
                        color: action.primary ? 'white' : colors.dark,
                        border: action.primary ? 'none' : `1px solid ${colors.lightGray}`,
                        borderRadius: 8,
                        fontSize: 14,
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" style={{
        padding: '80px 40px',
        backgroundColor: colors.light,
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 60 }}>
            <h2 style={{
              fontSize: 36,
              fontWeight: 700,
              color: colors.dark,
              margin: '0 0 16px',
              fontFamily: "'Poppins', sans-serif",
            }}>
              Everything for B2B product data
            </h2>
            <p style={{ fontSize: 18, color: colors.midGray, margin: 0 }}>
              From import to all channels — one platform, one day.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 24,
          }}>
            {features.map((feature, i) => (
              <div
                key={i}
                style={{
                  padding: 32,
                  backgroundColor: 'white',
                  borderRadius: 16,
                  border: `1px solid ${colors.lightGray}`,
                }}
              >
                <div style={{
                  width: 48,
                  height: 48,
                  borderRadius: 12,
                  backgroundColor: colors.orange + '15',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: colors.orange,
                  marginBottom: 20,
                }}>
                  {feature.icon}
                </div>
                <h3 style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color: colors.dark,
                  margin: '0 0 12px',
                }}>
                  {feature.title}
                </h3>
                <p style={{
                  fontSize: 14,
                  color: colors.midGray,
                  lineHeight: 1.6,
                  margin: 0,
                }}>
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Experts Section */}
      <section style={{
        padding: '80px 40px',
        backgroundColor: 'white',
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 40 }}>
            <div>
              <h2 style={{
                fontSize: 36,
                fontWeight: 700,
                color: colors.dark,
                margin: '0 0 12px',
                fontFamily: "'Poppins', sans-serif",
              }}>
                Connect with Experts
              </h2>
              <p style={{ fontSize: 18, color: colors.midGray, margin: 0 }}>
                Domain specialists ready to help with tax, legal, data, and more.
              </p>
            </div>
            <button
              onClick={() => router.push('/experts')}
              style={{
                padding: '12px 24px',
                backgroundColor: colors.blue || '#6a9bcc',
                color: 'white',
                border: 'none',
                borderRadius: 10,
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              Browse All Experts <ArrowRight size={16} />
            </button>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(6, 1fr)',
            gap: 16,
          }}>
            {expertCategories.map((cat, i) => (
              <button
                key={i}
                onClick={() => router.push(`/experts?category=${encodeURIComponent(cat.name)}`)}
                style={{
                  padding: 24,
                  backgroundColor: colors.light,
                  border: `1px solid ${colors.lightGray}`,
                  borderRadius: 12,
                  cursor: 'pointer',
                  textAlign: 'center',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = colors.blue || '#6a9bcc';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = colors.lightGray;
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <div style={{ fontSize: 32, marginBottom: 12 }}>{cat.icon}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: colors.dark, marginBottom: 4 }}>
                  {cat.name}
                </div>
                <div style={{ fontSize: 12, color: colors.midGray }}>
                  {cat.count} experts
                </div>
              </button>
            ))}
          </div>

          <div style={{
            marginTop: 32,
            padding: 32,
            backgroundColor: (colors.blue || '#6a9bcc') + '10',
            borderRadius: 16,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <div>
              <h3 style={{ fontSize: 20, fontWeight: 600, color: colors.dark, margin: '0 0 8px' }}>
                Are you an expert?
              </h3>
              <p style={{ fontSize: 15, color: colors.midGray, margin: 0 }}>
                Share your knowledge, help businesses, earn money. Join our expert network.
              </p>
            </div>
            <button
              onClick={() => router.push('/expert-signup')}
              style={{
                padding: '14px 28px',
                backgroundColor: colors.blue || '#6a9bcc',
                color: 'white',
                border: 'none',
                borderRadius: 10,
                fontSize: 15,
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <Star size={18} />
              Become an Expert
            </button>
          </div>
        </div>
      </section>

      {/* Quick Links Section */}
      <section style={{
        padding: '60px 40px',
        backgroundColor: colors.dark,
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 40,
          }}>
            <div>
              <h4 style={{ color: 'white', fontSize: 14, fontWeight: 600, marginBottom: 16 }}>
                For Businesses
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <a href="/onboarding/smart" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Quick Setup (4 steps)</a>
                <a href="/onboarding/guided" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Guided Setup (7 steps)</a>
                <a href="/login" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Customer Login</a>
                <a href="/dashboard" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Dashboard</a>
              </div>
            </div>
            <div>
              <h4 style={{ color: 'white', fontSize: 14, fontWeight: 600, marginBottom: 16 }}>
                For Experts
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <a href="/experts" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Browse Experts</a>
                <a href="/expert-signup" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Become an Expert</a>
                <a href="/expert-login" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Expert Login</a>
                <a href="/bookings" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>My Bookings</a>
              </div>
            </div>
            <div>
              <h4 style={{ color: 'white', fontSize: 14, fontWeight: 600, marginBottom: 16 }}>
                For Partners
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <a href="/partner" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Partner Portal</a>
                <a href="/partner-signup" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Become a Partner</a>
                <a href="/partner-login" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Partner Login</a>
              </div>
            </div>
            <div>
              <h4 style={{ color: 'white', fontSize: 14, fontWeight: 600, marginBottom: 16 }}>
                Platform
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <a href="/connectors" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Connectors</a>
                <a href="/models" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>AI Models</a>
                <a href="/developer" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Developers</a>
                <a href="/admin" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Admin</a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        padding: '24px 40px',
        backgroundColor: colors.dark,
        borderTop: `1px solid ${colors.midGray}33`,
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ color: colors.orange, fontWeight: 700 }}>0711</span>
            <span style={{ color: colors.midGray, fontSize: 14 }}>German B2B Intelligence Platform</span>
          </div>
          <div style={{ fontSize: 14, color: colors.midGray }}>
            © 2026 0711 GmbH · Stuttgart
          </div>
        </div>
      </footer>
    </div>
  );
}
