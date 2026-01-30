'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AdminLayout from '@/components/admin/AdminLayout';
import { Search, Filter, Eye, XCircle, CheckCircle, Clock } from 'lucide-react';

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

interface Customer {
  id: string;
  company_name: string;
  contact_email: string;
  tier: string;
  status: string;
  created_at: string;
  onboarding_status: string;
}

export default function AdminCustomersPage() {
  const router = useRouter();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [tierFilter, setTierFilter] = useState('all');

  useEffect(() => {
    loadCustomers();
  }, [statusFilter, tierFilter]);

  const loadCustomers = async () => {
    try {
      const token = localStorage.getItem('0711_admin_token');

      const params = new URLSearchParams({ page: '1', page_size: '50' });
      if (statusFilter !== 'all') params.append('status', statusFilter);
      if (tierFilter !== 'all') params.append('tier', tierFilter);

      const response = await fetch(`http://localhost:4080/api/admin/customers?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setCustomers(data.customers || []);
      }
    } catch (error) {
      console.error('Error loading customers:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCustomers = customers.filter(c =>
    c.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.contact_email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    const config = {
      active: { label: 'Active', color: colors.green, icon: CheckCircle },
      churned: { label: 'Churned', color: colors.red, icon: XCircle },
      suspended: { label: 'Suspended', color: colors.orange, icon: Clock },
    }[status] || { label: status, color: colors.midGray, icon: Clock };

    const Icon = config.icon;

    return (
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '4px 12px',
        backgroundColor: `${config.color}15`,
        color: config.color,
        borderRadius: 6,
        fontSize: 12,
        fontWeight: 600,
      }}>
        <Icon size={14} />
        {config.label}
      </span>
    );
  };

  const getTierBadge = (tier: string) => {
    const colors_tier = {
      starter: colors.blue,
      professional: colors.green,
      business: colors.orange,
      enterprise: colors.red,
    }[tier] || colors.midGray;

    return (
      <span style={{
        padding: '4px 12px',
        backgroundColor: `${colors_tier}15`,
        color: colors_tier,
        borderRadius: 6,
        fontSize: 12,
        fontWeight: 600,
      }}>
        {tier.replace(/\b\w/g, l => l.toUpperCase())}
      </span>
    );
  };

  return (
    <AdminLayout>
      <div style={{ padding: 40 }}>
        {/* Header */}
        <header style={{ marginBottom: 32 }}>
          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 32,
            fontWeight: 600,
            margin: '0 0 8px',
            color: colors.dark,
          }}>
            Customer Management
          </h1>
          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: 0,
          }}>
            {filteredCustomers.length} customer{filteredCustomers.length !== 1 ? 's' : ''}
          </p>
        </header>

        {/* Filters */}
        <div style={{
          display: 'flex',
          gap: 16,
          marginBottom: 24,
        }}>
          {/* Search */}
          <div style={{ flex: 1, position: 'relative' }}>
            <Search
              size={18}
              color={colors.midGray}
              style={{
                position: 'absolute',
                left: 16,
                top: '50%',
                transform: 'translateY(-50%)',
              }}
            />
            <input
              type="text"
              placeholder="Search customers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 16px 12px 48px',
                border: `1.5px solid ${colors.lightGray}`,
                borderRadius: 10,
                fontSize: 15,
                outline: 'none',
                backgroundColor: '#fff',
              }}
              onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
              onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: '12px 16px',
              border: `1.5px solid ${colors.lightGray}`,
              borderRadius: 10,
              fontSize: 14,
              outline: 'none',
              backgroundColor: '#fff',
              cursor: 'pointer',
            }}
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="churned">Churned</option>
            <option value="suspended">Suspended</option>
          </select>

          {/* Tier Filter */}
          <select
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value)}
            style={{
              padding: '12px 16px',
              border: `1.5px solid ${colors.lightGray}`,
              borderRadius: 10,
              fontSize: 14,
              outline: 'none',
              backgroundColor: '#fff',
              cursor: 'pointer',
            }}
          >
            <option value="all">All Tiers</option>
            <option value="starter">Starter</option>
            <option value="professional">Professional</option>
            <option value="business">Business</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>

        {/* Customers Table */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          border: `1.5px solid ${colors.lightGray}`,
          overflow: 'hidden',
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: colors.lightGray }}>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Company
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Contact
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Tier
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Status
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Onboarding
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Created
                </th>
                <th style={{ padding: '16px 24px', textAlign: 'right', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredCustomers.map((customer, idx) => (
                <tr
                  key={customer.id}
                  style={{
                    borderBottom: idx < filteredCustomers.length - 1 ? `1px solid ${colors.lightGray}` : 'none',
                  }}
                >
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                      {customer.company_name}
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ fontSize: 13, color: colors.midGray }}>
                      {customer.contact_email}
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    {getTierBadge(customer.tier)}
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    {getStatusBadge(customer.status)}
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ fontSize: 13, color: colors.midGray }}>
                      {customer.onboarding_status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ fontSize: 13, color: colors.midGray }}>
                      {new Date(customer.created_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px', textAlign: 'right' }}>
                    <button
                      onClick={() => window.open(`http://localhost:4020/?customer_id=${customer.id}`, '_blank')}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '8px 16px',
                        backgroundColor: colors.lightGray,
                        border: 'none',
                        borderRadius: 6,
                        fontSize: 13,
                        cursor: 'pointer',
                        fontFamily: "'Poppins', Arial, sans-serif",
                      }}
                      title="View customer console"
                    >
                      <Eye size={14} />
                      View
                    </button>
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
