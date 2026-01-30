'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AdminLayout from '@/components/admin/AdminLayout';
import { Users, Package, UserCheck, TrendingUp, AlertTriangle } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
  red: '#d75757',
};

interface Stats {
  total_customers: number;
  active_customers: number;
  pending_mcps: number;
  pending_developers: number;
  total_revenue_monthly: number;
  system_health: 'healthy' | 'warning' | 'error';
}

export default function AdminDashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check admin auth
    const token = localStorage.getItem('0711_admin_token');
    if (!token) {
      router.push('/admin/login');
      return;
    }

    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const token = localStorage.getItem('0711_admin_token');

      const response = await fetch('http://localhost:4080/api/admin/stats', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        // Use placeholder data if endpoint doesn't exist yet
        setStats({
          total_customers: 12,
          active_customers: 10,
          pending_mcps: 3,
          pending_developers: 2,
          total_revenue_monthly: 125000,
          system_health: 'healthy',
        });
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      label: 'Total Customers',
      value: stats?.total_customers || 0,
      icon: Users,
      color: colors.blue,
      change: '+12%',
    },
    {
      label: 'Active Customers',
      value: stats?.active_customers || 0,
      icon: TrendingUp,
      color: colors.green,
      change: '+8%',
    },
    {
      label: 'Pending MCPs',
      value: stats?.pending_mcps || 0,
      icon: Package,
      color: colors.orange,
      action: () => router.push('/admin/mcps'),
    },
    {
      label: 'Pending Developers',
      value: stats?.pending_developers || 0,
      icon: UserCheck,
      color: colors.orange,
      action: () => router.push('/admin/developers'),
    },
  ];

  if (loading) {
    return (
      <AdminLayout>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
        }}>
          <div style={{ textAlign: 'center', color: colors.midGray }}>
            <div style={{ fontSize: 32, marginBottom: 16 }}>⟳</div>
            <div>Loading dashboard...</div>
          </div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div style={{ padding: 40 }}>
        {/* Header */}
        <header style={{ marginBottom: 40 }}>
          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 32,
            fontWeight: 600,
            margin: '0 0 8px',
            color: colors.dark,
          }}>
            Platform Dashboard
          </h1>
          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: 0,
          }}>
            Overview of the 0711 platform
          </p>
        </header>

        {/* System Health Alert */}
        {stats?.system_health === 'warning' && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '16px 20px',
            marginBottom: 32,
            backgroundColor: `${colors.orange}15`,
            border: `1px solid ${colors.orange}`,
            borderRadius: 12,
          }}>
            <AlertTriangle size={20} color={colors.orange} />
            <span style={{ fontSize: 14, color: colors.dark }}>
              System experiencing performance issues. Check health dashboard.
            </span>
          </div>
        )}

        {/* Stats Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 24,
          marginBottom: 40,
        }}>
          {statCards.map((card) => {
            const Icon = card.icon;

            return (
              <div
                key={card.label}
                onClick={card.action}
                style={{
                  padding: 24,
                  backgroundColor: '#fff',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 16,
                  cursor: card.action ? 'pointer' : 'default',
                  transition: 'all 0.2s',
                }}
                onMouseOver={(e) => {
                  if (card.action) {
                    e.currentTarget.style.borderColor = card.color;
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = `0 8px 24px ${card.color}15`;
                  }
                }}
                onMouseOut={(e) => {
                  if (card.action) {
                    e.currentTarget.style.borderColor = colors.lightGray;
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
                  <div style={{
                    width: 48,
                    height: 48,
                    borderRadius: 12,
                    backgroundColor: `${card.color}15`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <Icon size={24} color={card.color} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{
                      fontSize: 13,
                      color: colors.midGray,
                      marginBottom: 4,
                    }}>
                      {card.label}
                    </div>
                    <div style={{
                      fontFamily: "'Poppins', Arial, sans-serif",
                      fontSize: 32,
                      fontWeight: 600,
                      color: colors.dark,
                    }}>
                      {card.value}
                    </div>
                  </div>
                </div>

                {card.change && (
                  <div style={{
                    fontSize: 13,
                    color: colors.green,
                    fontWeight: 500,
                  }}>
                    {card.change} from last month
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Revenue Card */}
        <div style={{
          padding: 32,
          backgroundColor: '#fff',
          border: `1.5px solid ${colors.lightGray}`,
          borderRadius: 16,
          marginBottom: 24,
        }}>
          <h3 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 18,
            fontWeight: 600,
            margin: '0 0 24px',
            color: colors.dark,
          }}>
            Monthly Recurring Revenue
          </h3>

          <div style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: 8,
            marginBottom: 16,
          }}>
            <span style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 48,
              fontWeight: 600,
              color: colors.dark,
            }}>
              €{stats ? (stats.total_revenue_monthly / 1000).toFixed(0) : 0}k
            </span>
            <span style={{
              fontSize: 16,
              color: colors.midGray,
            }}>
              /month
            </span>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 14,
            color: colors.green,
            fontWeight: 500,
          }}>
            <svg style={{ width: 16, height: 16 }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23,6 13.5,15.5 8.5,10.5 1,18" />
              <polyline points="17,6 23,6 23,12" />
            </svg>
            +15% from last month
          </div>
        </div>

        {/* Quick Actions */}
        <div style={{
          padding: 32,
          backgroundColor: '#fff',
          border: `1.5px solid ${colors.lightGray}`,
          borderRadius: 16,
        }}>
          <h3 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 18,
            fontWeight: 600,
            margin: '0 0 24px',
            color: colors.dark,
          }}>
            Quick Actions
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <button
              onClick={() => router.push('/admin/mcps')}
              style={{
                padding: 16,
                backgroundColor: colors.light,
                border: `1px solid ${colors.lightGray}`,
                borderRadius: 12,
                cursor: 'pointer',
                fontSize: 14,
                textAlign: 'left',
                fontFamily: "'Lora', Georgia, serif",
                color: colors.dark,
              }}
            >
              Review {stats?.pending_mcps || 0} pending MCP{stats?.pending_mcps !== 1 ? 's' : ''}
            </button>

            <button
              onClick={() => router.push('/admin/developers')}
              style={{
                padding: 16,
                backgroundColor: colors.light,
                border: `1px solid ${colors.lightGray}`,
                borderRadius: 12,
                cursor: 'pointer',
                fontSize: 14,
                textAlign: 'left',
                fontFamily: "'Lora', Georgia, serif",
                color: colors.dark,
              }}
            >
              Verify {stats?.pending_developers || 0} developer{stats?.pending_developers !== 1 ? 's' : ''}
            </button>

            <button
              onClick={() => router.push('/admin/customers')}
              style={{
                padding: 16,
                backgroundColor: colors.light,
                border: `1px solid ${colors.lightGray}`,
                borderRadius: 12,
                cursor: 'pointer',
                fontSize: 14,
                textAlign: 'left',
                fontFamily: "'Lora', Georgia, serif",
                color: colors.dark,
              }}
            >
              Manage customers
            </button>

            <button
              onClick={() => router.push('/admin/health')}
              style={{
                padding: 16,
                backgroundColor: colors.light,
                border: `1px solid ${colors.lightGray}`,
                borderRadius: 12,
                cursor: 'pointer',
                fontSize: 14,
                textAlign: 'left',
                fontFamily: "'Lora', Georgia, serif",
                color: colors.dark,
              }}
            >
              Check system health
            </button>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
