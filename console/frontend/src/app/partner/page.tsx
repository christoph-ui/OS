'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import PartnerHeader from '@/components/PartnerHeader';
import { DashboardSkeleton } from '@/components/LoadingSkeleton';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
};

interface DashboardData {
  partner_id: string;
  company_name: string;
  total_customers: number;
  active_customers: number;
  total_revenue: number;
  customers_onboarding: number;
  recent_customers: any[];
}

export default function PartnerDashboard() {
  const router = useRouter();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4080/api/partners/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to load dashboard');

      const data = await response.json();
      setDashboard(data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div>
        <PartnerHeader title="Dashboard" />
        <DashboardSkeleton />
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div>
        <PartnerHeader title="Dashboard" />
        <div style={{ padding: 40, textAlign: 'center', color: colors.midGray }}>
          Fehler beim Laden der Daten
        </div>
      </div>
    );
  }

  const stats = [
    {
      label: 'Gesamt Kunden',
      value: dashboard.total_customers,
      color: colors.blue,
      icon: '👥',
    },
    {
      label: 'Aktive Kunden',
      value: dashboard.active_customers,
      color: colors.green,
      icon: '✓',
    },
    {
      label: 'Onboarding',
      value: dashboard.customers_onboarding,
      color: colors.orange,
      icon: '⚙',
    },
    {
      label: 'Revenue',
      value: `€${dashboard.total_revenue.toLocaleString()}`,
      color: colors.dark,
      icon: '€',
    },
  ];

  return (
    <div>
      <PartnerHeader title="Dashboard" />

      <div style={{ padding: 40 }}>
        {/* Quick Action */}
        <div style={{ marginBottom: 40 }}>
          <button
            onClick={() => router.push('/partner/customers/new')}
            style={{
              padding: '12px 24px',
              backgroundColor: colors.orange,
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              fontSize: 15,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: "'Poppins', Arial, sans-serif",
              boxShadow: `0 4px 12px ${colors.orange}40`,
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-1px)';
              e.currentTarget.style.boxShadow = `0 6px 20px ${colors.orange}50`;
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = `0 4px 12px ${colors.orange}40`;
            }}
          >
            + Neuer Kunde
          </button>
        </div>

        {/* Stats Grid */}
        <div
          className="stats-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: 24,
            marginBottom: 40,
          }}
        >
          {stats.map((stat, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: '#fff',
                borderRadius: 16,
                padding: 24,
                border: `1.5px solid ${colors.lightGray}`,
                boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
              }}
            >
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 12,
              }}>
                <p style={{
                  fontSize: 13,
                  color: colors.midGray,
                  margin: 0,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  fontWeight: 600,
                }}>
                  {stat.label}
                </p>
                <span style={{ fontSize: 24 }}>{stat.icon}</span>
              </div>
              <p style={{
                fontSize: 32,
                fontWeight: 600,
                margin: 0,
                color: stat.color,
                fontFamily: "'Poppins', Arial, sans-serif",
              }}>
                {stat.value}
              </p>
            </div>
          ))}
        </div>

        {/* Recent Customers */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          border: `1.5px solid ${colors.lightGray}`,
          overflow: 'hidden',
        }}>
          <div style={{
            padding: '20px 24px',
            borderBottom: `1px solid ${colors.lightGray}`,
          }}>
            <h2 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 18,
              fontWeight: 600,
              margin: 0,
              color: colors.dark,
            }}>
              Neueste Kunden
            </h2>
          </div>

          {dashboard.recent_customers.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: colors.light }}>
                    <th style={{
                      padding: '12px 24px',
                      textAlign: 'left',
                      fontSize: 12,
                      fontWeight: 600,
                      color: colors.midGray,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}>
                      Firma
                    </th>
                    <th style={{
                      padding: '12px 24px',
                      textAlign: 'left',
                      fontSize: 12,
                      fontWeight: 600,
                      color: colors.midGray,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}>
                      Tier
                    </th>
                    <th style={{
                      padding: '12px 24px',
                      textAlign: 'left',
                      fontSize: 12,
                      fontWeight: 600,
                      color: colors.midGray,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}>
                      Status
                    </th>
                    <th style={{
                      padding: '12px 24px',
                      textAlign: 'left',
                      fontSize: 12,
                      fontWeight: 600,
                      color: colors.midGray,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}>
                      Erstellt
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.recent_customers.map((customer, idx) => (
                    <tr
                      key={customer.id}
                      style={{
                        borderTop: `1px solid ${colors.lightGray}`,
                        cursor: 'pointer',
                        transition: 'background 0.15s',
                      }}
                      onClick={() => router.push(`/partner/customers`)}
                      onMouseOver={(e) => e.currentTarget.style.backgroundColor = colors.light}
                      onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <td style={{ padding: '16px 24px', fontSize: 14 }}>
                        {customer.company_name}
                      </td>
                      <td style={{ padding: '16px 24px', fontSize: 14 }}>
                        <span style={{
                          padding: '4px 12px',
                          backgroundColor: `${colors.blue}15`,
                          borderRadius: 6,
                          fontSize: 12,
                          color: colors.blue,
                          fontWeight: 600,
                        }}>
                          {customer.tier}
                        </span>
                      </td>
                      <td style={{ padding: '16px 24px', fontSize: 14 }}>
                        <span style={{
                          padding: '4px 12px',
                          backgroundColor: customer.status === 'active' ? `${colors.green}15` : `${colors.midGray}15`,
                          borderRadius: 6,
                          fontSize: 12,
                          color: customer.status === 'active' ? colors.green : colors.midGray,
                          fontWeight: 600,
                        }}>
                          {customer.status}
                        </span>
                      </td>
                      <td style={{ padding: '16px 24px', fontSize: 14, color: colors.midGray }}>
                        {new Date(customer.created_at).toLocaleDateString('de-DE')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{
              padding: 60,
              textAlign: 'center',
              color: colors.midGray,
            }}>
              <p style={{ margin: 0, fontSize: 15 }}>
                Noch keine Kunden erstellt
              </p>
              <button
                onClick={() => router.push('/partner/customers/new')}
                style={{
                  marginTop: 16,
                  padding: '10px 20px',
                  backgroundColor: colors.orange,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Ersten Kunden erstellen
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Responsive Styles */}
      <style jsx global>{`
        @media (max-width: 768px) {
          .stats-grid {
            grid-template-columns: 1fr !important;
          }

          table {
            font-size: 13px !important;
          }

          th, td {
            padding: 10px 12px !important;
          }
        }

        @media (max-width: 480px) {
          .stats-grid {
            gap: 16px !important;
          }
        }
      `}</style>
    </div>
  );
}
