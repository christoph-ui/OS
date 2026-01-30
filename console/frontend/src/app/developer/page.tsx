'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DeveloperLayout from '@/components/developer/DeveloperLayout';
import { Package, DollarSign, Users, TrendingUp } from 'lucide-react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
};

interface DeveloperStats {
  total_mcps: number;
  approved_mcps: number;
  total_installations: number;
  monthly_revenue: number;
  average_rating: number;
}

interface MCP {
  id: string;
  name: string;
  display_name: string;
  status: string;
  installations: number;
  revenue: number;
}

export default function DeveloperDashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DeveloperStats | null>(null);
  const [mcps, setMcps] = useState<MCP[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('0711_developer_token');
    if (!token) {
      router.push('/developer/login');
      return;
    }

    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const token = localStorage.getItem('0711_developer_token');

      // Load developer profile
      const profileRes = await fetch('http://localhost:4080/api/mcp-developers/me', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (profileRes.ok) {
        const profile = await profile.json();
        setStats({
          total_mcps: profile.total_mcps || 0,
          approved_mcps: profile.approved_mcps || 0,
          total_installations: profile.total_installations || 0,
          monthly_revenue: profile.monthly_revenue || 0,
          average_rating: profile.average_rating || 0,
        });
      }

      // Load MCPs
      const mcpsRes = await fetch('http://localhost:4080/api/mcp-developers/mcps/my', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (mcpsRes.ok) {
        const data = await mcpsRes.json();
        setMcps(data.mcps || []);
      }
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    { label: 'Total MCPs', value: stats?.total_mcps || 0, icon: Package, color: colors.blue },
    { label: 'Active Installations', value: stats?.total_installations || 0, icon: Users, color: colors.green },
    { label: 'Monthly Revenue', value: `€${stats?.monthly_revenue || 0}`, icon: DollarSign, color: colors.orange },
    { label: 'Avg Rating', value: (stats?.average_rating || 0).toFixed(1), icon: TrendingUp, color: colors.blue },
  ];

  if (loading) {
    return (
      <DeveloperLayout>
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
      </DeveloperLayout>
    );
  }

  return (
    <DeveloperLayout>
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
            Developer Dashboard
          </h1>
          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: 0,
          }}>
            Track your MCPs and earnings
          </p>
        </header>

        {/* Stats Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 20,
          marginBottom: 40,
        }}>
          {statCards.map((card) => {
            const Icon = card.icon;

            return (
              <div
                key={card.label}
                style={{
                  padding: 24,
                  backgroundColor: '#fff',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 16,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <div style={{
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    backgroundColor: `${card.color}15`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <Icon size={20} color={card.color} />
                  </div>
                  <div style={{
                    fontSize: 13,
                    color: colors.midGray,
                  }}>
                    {card.label}
                  </div>
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
            );
          })}
        </div>

        {/* Recent MCPs */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          padding: 32,
          border: `1.5px solid ${colors.lightGray}`,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 18,
              fontWeight: 600,
              margin: 0,
              color: colors.dark,
            }}>
              Your MCPs
            </h3>

            <button
              onClick={() => router.push('/developer/mcps/new')}
              style={{
                padding: '10px 20px',
                backgroundColor: colors.orange,
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                fontFamily: "'Poppins', Arial, sans-serif",
              }}
            >
              Submit New MCP
            </button>
          </div>

          {mcps.length > 0 ? (
            <div style={{ display: 'grid', gap: 16 }}>
              {mcps.map((mcp) => (
                <div
                  key={mcp.id}
                  onClick={() => router.push(`/developer/mcps/${mcp.id}`)}
                  style={{
                    padding: 20,
                    backgroundColor: colors.light,
                    borderRadius: 12,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.backgroundColor = colors.lightGray;
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.backgroundColor = colors.light;
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h4 style={{
                        fontSize: 16,
                        fontWeight: 600,
                        margin: '0 0 8px',
                        color: colors.dark,
                      }}>
                        {mcp.display_name}
                      </h4>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 13, color: colors.midGray }}>
                        <span>{mcp.installations} installations</span>
                        <span>€{mcp.revenue}/mo</span>
                        <span style={{
                          padding: '2px 8px',
                          backgroundColor: mcp.status === 'approved' ? `${colors.green}15` : `${colors.orange}15`,
                          color: mcp.status === 'approved' ? colors.green : colors.orange,
                          borderRadius: 4,
                          fontSize: 11,
                          fontWeight: 600,
                        }}>
                          {mcp.status}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{
              padding: 40,
              textAlign: 'center',
              backgroundColor: colors.light,
              borderRadius: 12,
            }}>
              <Package size={48} color={colors.midGray} style={{ margin: '0 auto 16px' }} />
              <p style={{ fontSize: 15, color: colors.midGray, margin: '0 0 16px' }}>
                No MCPs submitted yet
              </p>
              <button
                onClick={() => router.push('/developer/mcps/new')}
                style={{
                  padding: '10px 20px',
                  backgroundColor: colors.orange,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontFamily: "'Poppins', Arial, sans-serif",
                }}
              >
                Submit Your First MCP
              </button>
            </div>
          )}
        </div>
      </div>
    </DeveloperLayout>
  );
}
