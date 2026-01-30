'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import DeveloperLayout from '@/components/developer/DeveloperLayout';
import { Package, Users, DollarSign, TrendingUp, Calendar, Download } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
};

interface MCPAnalytics {
  mcp_id: string;
  display_name: string;
  status: string;
  total_installations: number;
  active_installations: number;
  total_revenue: number;
  monthly_revenue: number;
  average_rating: number;
  total_api_calls: number;
  installation_trend: Array<{ date: string; count: number }>;
  revenue_trend: Array<{ month: string; amount: number }>;
}

export default function MCPAnalyticsPage() {
  const router = useRouter();
  const params = useParams();
  const mcpId = params.id as string;

  const [analytics, setAnalytics] = useState<MCPAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, [mcpId]);

  const loadAnalytics = async () => {
    try {
      const token = localStorage.getItem('0711_developer_token');

      const response = await fetch(`http://localhost:4080/api/mcp-developers/mcps/${mcpId}/analytics`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      } else {
        // Placeholder data
        setAnalytics({
          mcp_id: mcpId,
          display_name: 'Sample MCP',
          status: 'approved',
          total_installations: 45,
          active_installations: 42,
          total_revenue: 3150,
          monthly_revenue: 1050,
          average_rating: 4.7,
          total_api_calls: 12450,
          installation_trend: [],
          revenue_trend: [],
        });
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

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
            <div>Loading analytics...</div>
          </div>
        </div>
      </DeveloperLayout>
    );
  }

  return (
    <DeveloperLayout>
      <div style={{ padding: 40 }}>
        {/* Header */}
        <header style={{ marginBottom: 32 }}>
          <button
            onClick={() => router.push('/developer')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 16px',
              marginBottom: 16,
              backgroundColor: colors.lightGray,
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              color: colors.dark,
              cursor: 'pointer',
              fontFamily: "'Lora', Georgia, serif",
            }}
          >
            ← Back to Dashboard
          </button>

          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 32,
            fontWeight: 600,
            margin: '0 0 8px',
            color: colors.dark,
          }}>
            {analytics?.display_name}
          </h1>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{
              padding: '4px 12px',
              backgroundColor: analytics?.status === 'approved' ? `${colors.green}15` : `${colors.orange}15`,
              color: analytics?.status === 'approved' ? colors.green : colors.orange,
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 600,
            }}>
              {analytics?.status.replace(/\b\w/g, l => l.toUpperCase())}
            </span>
          </div>
        </header>

        {/* Key Metrics */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 20,
          marginBottom: 32,
        }}>
          {[
            { label: 'Total Installations', value: analytics?.total_installations || 0, icon: Package, color: colors.blue },
            { label: 'Active Users', value: analytics?.active_installations || 0, icon: Users, color: colors.green },
            { label: 'Monthly Revenue', value: `€${analytics?.monthly_revenue || 0}`, icon: DollarSign, color: colors.orange },
            { label: 'Average Rating', value: (analytics?.average_rating || 0).toFixed(1), icon: TrendingUp, color: colors.blue },
          ].map((metric) => {
            const Icon = metric.icon;

            return (
              <div
                key={metric.label}
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
                    backgroundColor: `${metric.color}15`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <Icon size={20} color={metric.color} />
                  </div>
                  <div style={{ fontSize: 13, color: colors.midGray }}>
                    {metric.label}
                  </div>
                </div>

                <div style={{
                  fontFamily: "'Poppins', Arial, sans-serif",
                  fontSize: 32,
                  fontWeight: 600,
                  color: colors.dark,
                }}>
                  {metric.value}
                </div>
              </div>
            );
          })}
        </div>

        {/* Revenue Breakdown */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          padding: 32,
          border: `1.5px solid ${colors.lightGray}`,
          marginBottom: 24,
        }}>
          <h3 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 18,
            fontWeight: 600,
            margin: '0 0 24px',
            color: colors.dark,
          }}>
            Revenue Breakdown
          </h3>

          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 24,
            padding: 24,
            backgroundColor: colors.light,
            borderRadius: 12,
          }}>
            <div>
              <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                Total Revenue (All Time)
              </div>
              <div style={{
                fontFamily: "'Poppins', Arial, sans-serif",
                fontSize: 28,
                fontWeight: 600,
                color: colors.dark,
              }}>
                €{analytics?.total_revenue || 0}
              </div>
            </div>

            <div>
              <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                Your Share (70%)
              </div>
              <div style={{
                fontFamily: "'Poppins', Arial, sans-serif",
                fontSize: 28,
                fontWeight: 600,
                color: colors.green,
              }}>
                €{((analytics?.total_revenue || 0) * 0.7).toFixed(0)}
              </div>
            </div>
          </div>
        </div>

        {/* API Usage */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          padding: 32,
          border: `1.5px solid ${colors.lightGray}`,
        }}>
          <h3 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 18,
            fontWeight: 600,
            margin: '0 0 24px',
            color: colors.dark,
          }}>
            Usage Statistics
          </h3>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 24,
            padding: 24,
            backgroundColor: colors.light,
            borderRadius: 12,
          }}>
            <div>
              <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                Total API Calls
              </div>
              <div style={{
                fontSize: 24,
                fontWeight: 600,
                color: colors.dark,
              }}>
                {(analytics?.total_api_calls || 0).toLocaleString()}
              </div>
            </div>

            <div>
              <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                Avg Calls/Installation
              </div>
              <div style={{
                fontSize: 24,
                fontWeight: 600,
                color: colors.dark,
              }}>
                {analytics?.active_installations
                  ? Math.round((analytics.total_api_calls || 0) / analytics.active_installations)
                  : 0}
              </div>
            </div>

            <div>
              <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                Churn Rate
              </div>
              <div style={{
                fontSize: 24,
                fontWeight: 600,
                color: colors.dark,
              }}>
                {analytics?.total_installations
                  ? (((analytics.total_installations - analytics.active_installations) / analytics.total_installations) * 100).toFixed(1)
                  : 0}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </DeveloperLayout>
  );
}
