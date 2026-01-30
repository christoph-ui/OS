'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { colors } from '@/lib/theme';
import { 
  Sparkles, Zap, Database, Share2, Shield, Clock,
  ArrowRight, Check, MessageSquare, BarChart3, Package
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

  const onboardingOptions = [
    {
      id: 'quick',
      title: 'Quick Setup',
      subtitle: '4 steps • ~5 minutes',
      description: 'Upload your files, let AI analyze and deploy automatically.',
      icon: <Zap size={32} />,
      color: colors.orange,
      features: ['AI file analysis', 'Smart recommendations', 'One-click deploy'],
      href: '/onboarding',
    },
    {
      id: 'guided',
      title: 'Guided Setup',
      subtitle: '7 steps • ~15 minutes',
      description: 'Step-by-step wizard with detailed explanations.',
      icon: <Package size={32} />,
      color: colors.blue,
      features: ['Detailed explanations', 'Manual configuration', 'Full control'],
      href: '/onboarding',
    },
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
              0711 Console
            </span>
          </div>

          <nav style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
            <a href="#features" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Features</a>
            <a href="#start" style={{ color: colors.midGray, textDecoration: 'none', fontSize: 14 }}>Get Started</a>
            
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
              AI-Powered Product Intelligence
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
            Import your product data. Let AI enrich it. Publish to every channel. 
            German B2B intelligence platform for distributors and manufacturers.
          </p>

          <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
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
              onClick={() => router.push('/login')}
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
              <MessageSquare size={20} />
              Login to Console
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" style={{
        padding: '80px 40px',
        backgroundColor: 'white',
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
              Everything you need for B2B product data
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
                  backgroundColor: colors.light,
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

      {/* Onboarding Choice Section */}
      <section id="start" style={{
        padding: '80px 40px',
        backgroundColor: colors.light,
      }}>
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <h2 style={{
              fontSize: 36,
              fontWeight: 700,
              color: colors.dark,
              margin: '0 0 16px',
              fontFamily: "'Poppins', sans-serif",
            }}>
              Choose your setup
            </h2>
            <p style={{ fontSize: 18, color: colors.midGray, margin: 0 }}>
              Quick AI-powered setup or detailed guided wizard — your choice.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: 24,
          }}>
            {onboardingOptions.map((option) => (
              <button
                key={option.id}
                onClick={() => router.push(option.href + (option.id === 'quick' ? '/smart' : '/guided'))}
                style={{
                  padding: 32,
                  backgroundColor: 'white',
                  border: `2px solid ${colors.lightGray}`,
                  borderRadius: 16,
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = option.color;
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 12px 40px rgba(0,0,0,0.08)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = colors.lightGray;
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{
                  width: 64,
                  height: 64,
                  borderRadius: 16,
                  backgroundColor: option.color + '15',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: option.color,
                  marginBottom: 20,
                }}>
                  {option.icon}
                </div>

                <h3 style={{
                  fontSize: 24,
                  fontWeight: 600,
                  color: colors.dark,
                  margin: '0 0 4px',
                }}>
                  {option.title}
                </h3>

                <p style={{
                  fontSize: 14,
                  color: option.color,
                  fontWeight: 500,
                  margin: '0 0 16px',
                }}>
                  {option.subtitle}
                </p>

                <p style={{
                  fontSize: 15,
                  color: colors.midGray,
                  lineHeight: 1.6,
                  margin: '0 0 20px',
                }}>
                  {option.description}
                </p>

                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                  {option.features.map((feature, i) => (
                    <li key={i} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      fontSize: 14,
                      color: colors.dark,
                      marginBottom: 8,
                    }}>
                      <Check size={16} color={option.color} />
                      {feature}
                    </li>
                  ))}
                </ul>

                <div style={{
                  marginTop: 24,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  fontSize: 14,
                  fontWeight: 600,
                  color: option.color,
                }}>
                  Get Started <ArrowRight size={16} />
                </div>
              </button>
            ))}
          </div>

          <p style={{
            textAlign: 'center',
            marginTop: 32,
            fontSize: 14,
            color: colors.midGray,
          }}>
            Already have an account?{' '}
            <a 
              href="/login" 
              style={{ color: colors.orange, fontWeight: 500, textDecoration: 'none' }}
            >
              Login here
            </a>
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        padding: '40px',
        backgroundColor: colors.dark,
        color: colors.midGray,
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
            <span>German B2B Intelligence Platform</span>
          </div>
          <div style={{ fontSize: 14 }}>
            © 2026 0711 GmbH · Stuttgart
          </div>
        </div>
      </footer>
    </div>
  );
}
