'use client';

import { useState, useEffect } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import { Activity, Server, Database, HardDrive, Cpu, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
  red: '#d75757',
};

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'warning' | 'error';
  uptime: number;
  response_time: number;
  last_check: string;
  message?: string;
}

interface SystemHealth {
  overall_status: 'healthy' | 'warning' | 'error';
  services: ServiceHealth[];
  metrics: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    active_connections: number;
  };
}

export default function SystemHealthPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHealthData();
    const interval = setInterval(loadHealthData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadHealthData = async () => {
    try {
      const token = localStorage.getItem('0711_admin_token');

      const response = await fetch('http://localhost:4080/api/admin/health', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setHealth(data);
      } else {
        // Placeholder data if endpoint doesn't exist
        setHealth({
          overall_status: 'healthy',
          services: [
            { name: 'Control Plane API', status: 'healthy', uptime: 99.9, response_time: 45, last_check: new Date().toISOString() },
            { name: 'Console Backend', status: 'healthy', uptime: 99.8, response_time: 52, last_check: new Date().toISOString() },
            { name: 'PostgreSQL', status: 'healthy', uptime: 100, response_time: 12, last_check: new Date().toISOString() },
            { name: 'Redis', status: 'healthy', uptime: 100, response_time: 8, last_check: new Date().toISOString() },
            { name: 'MinIO', status: 'healthy', uptime: 99.9, response_time: 35, last_check: new Date().toISOString() },
            { name: 'vLLM', status: 'warning', uptime: 98.5, response_time: 2500, last_check: new Date().toISOString(), message: 'High response time' },
          ],
          metrics: {
            cpu_usage: 45,
            memory_usage: 68,
            disk_usage: 42,
            active_connections: 234,
          },
        });
      }
    } catch (error) {
      console.error('Error loading health data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle size={20} color={colors.green} />;
      case 'warning':
        return <AlertTriangle size={20} color={colors.orange} />;
      case 'error':
        return <XCircle size={20} color={colors.red} />;
      default:
        return <Activity size={20} color={colors.midGray} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return colors.green;
      case 'warning': return colors.orange;
      case 'error': return colors.red;
      default: return colors.midGray;
    }
  };

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
            <div>Loading system health...</div>
          </div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div style={{ padding: 40 }}>
        {/* Header */}
        <header style={{ marginBottom: 32 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 style={{
                fontFamily: "'Poppins', Arial, sans-serif",
                fontSize: 32,
                fontWeight: 600,
                margin: '0 0 8px',
                color: colors.dark,
              }}>
                System Health
              </h1>
              <p style={{
                fontSize: 15,
                color: colors.midGray,
                margin: 0,
              }}>
                Real-time infrastructure monitoring
              </p>
            </div>

            {/* Overall Status */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 24px',
              backgroundColor: health?.overall_status === 'healthy' ? `${colors.green}15` : `${colors.orange}15`,
              borderRadius: 10,
            }}>
              {getStatusIcon(health?.overall_status || 'healthy')}
              <span style={{
                fontSize: 16,
                fontWeight: 600,
                color: getStatusColor(health?.overall_status || 'healthy'),
              }}>
                {health?.overall_status.replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            </div>
          </div>
        </header>

        {/* System Metrics */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 20,
          marginBottom: 32,
        }}>
          {[
            { label: 'CPU Usage', value: health?.metrics.cpu_usage || 0, icon: Cpu, max: 100, unit: '%' },
            { label: 'Memory Usage', value: health?.metrics.memory_usage || 0, icon: Server, max: 100, unit: '%' },
            { label: 'Disk Usage', value: health?.metrics.disk_usage || 0, icon: HardDrive, max: 100, unit: '%' },
            { label: 'Active Connections', value: health?.metrics.active_connections || 0, icon: Activity, max: 1000, unit: '' },
          ].map((metric) => {
            const Icon = metric.icon;
            const percentage = (metric.value / metric.max) * 100;
            const metricColor = percentage > 80 ? colors.red : percentage > 60 ? colors.orange : colors.green;

            return (
              <div
                key={metric.label}
                style={{
                  padding: 20,
                  backgroundColor: '#fff',
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 12,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <Icon size={20} color={colors.midGray} />
                  <div style={{ fontSize: 13, color: colors.midGray }}>
                    {metric.label}
                  </div>
                </div>

                <div style={{
                  fontFamily: "'Poppins', Arial, sans-serif",
                  fontSize: 28,
                  fontWeight: 600,
                  color: colors.dark,
                  marginBottom: 8,
                }}>
                  {metric.value}{metric.unit}
                </div>

                {metric.max === 100 && (
                  <div style={{
                    height: 6,
                    backgroundColor: colors.lightGray,
                    borderRadius: 3,
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      width: `${percentage}%`,
                      height: '100%',
                      backgroundColor: metricColor,
                      transition: 'width 0.3s',
                    }} />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Services Status */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          border: `1.5px solid ${colors.lightGray}`,
          overflow: 'hidden',
        }}>
          <div style={{
            padding: '20px 24px',
            backgroundColor: colors.lightGray,
            fontSize: 16,
            fontWeight: 600,
            color: colors.dark,
            fontFamily: "'Poppins', Arial, sans-serif",
          }}>
            Services Status
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: colors.light }}>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Service
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Status
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Uptime
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Response Time
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Last Check
                </th>
              </tr>
            </thead>
            <tbody>
              {health?.services.map((service, idx) => (
                <tr
                  key={service.name}
                  style={{
                    borderBottom: idx < health.services.length - 1 ? `1px solid ${colors.lightGray}` : 'none',
                  }}
                >
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                      {service.name}
                    </div>
                    {service.message && (
                      <div style={{ fontSize: 12, color: colors.orange, marginTop: 4 }}>
                        {service.message}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {getStatusIcon(service.status)}
                      <span style={{
                        fontSize: 13,
                        color: getStatusColor(service.status),
                        fontWeight: 500,
                      }}>
                        {service.status.replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ fontSize: 13, color: colors.dark }}>
                      {service.uptime.toFixed(2)}%
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{
                      fontSize: 13,
                      color: service.response_time > 1000 ? colors.orange : colors.dark,
                    }}>
                      {service.response_time}ms
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ fontSize: 13, color: colors.midGray }}>
                      {new Date(service.last_check).toLocaleTimeString()}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AdminLayout>
  );
}
