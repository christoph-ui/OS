'use client';

import React, { useState } from 'react';
import { colors } from '@/lib/theme';
import {
  DollarSign, TrendingUp, Users, Calendar, Download,
  ArrowUpRight, CreditCard, Wallet, ChevronRight
} from 'lucide-react';

export default function PartnerEarnings() {
  const [period, setPeriod] = useState<'month' | 'quarter' | 'year'>('month');

  const stats = {
    totalCommissions: 45600,
    pendingPayout: 8400,
    activeCustomers: 12,
    avgPerCustomer: 3800,
  };

  const customerCommissions = [
    { id: '1', name: 'Acme GmbH', plan: 'Enterprise', mrr: 2999, commission: 450, status: 'active' },
    { id: '2', name: 'TechParts AG', plan: 'Professional', mrr: 999, commission: 150, status: 'active' },
    { id: '3', name: 'BuildSupply', plan: 'Enterprise', mrr: 2999, commission: 450, status: 'active' },
    { id: '4', name: 'ElektroPro', plan: 'Professional', mrr: 999, commission: 150, status: 'active' },
    { id: '5', name: 'SanitärPlus', plan: 'Starter', mrr: 299, commission: 45, status: 'trial' },
  ];

  const payoutHistory = [
    { id: '1', date: '2026-01-15', amount: 12000, status: 'completed' },
    { id: '2', date: '2025-12-15', amount: 10500, status: 'completed' },
    { id: '3', date: '2025-11-15', amount: 11200, status: 'completed' },
  ];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 24, fontWeight: 600, color: colors.dark, margin: '0 0 8px' }}>
          Earnings & Commissions
        </h1>
        <p style={{ fontSize: 15, color: colors.midGray, margin: 0 }}>
          Track your referral commissions and payouts
        </p>
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 20,
        marginBottom: 32,
      }}>
        <StatCard
          icon={<DollarSign size={24} />}
          label="Total Commissions"
          value={formatCurrency(stats.totalCommissions)}
          trend="+18%"
          positive
        />
        <StatCard
          icon={<Wallet size={24} />}
          label="Pending Payout"
          value={formatCurrency(stats.pendingPayout)}
          subtext="Next payout: Feb 15"
          color={colors.green}
        />
        <StatCard
          icon={<Users size={24} />}
          label="Active Customers"
          value={stats.activeCustomers.toString()}
          subtext="Generating commission"
        />
        <StatCard
          icon={<TrendingUp size={24} />}
          label="Avg per Customer"
          value={formatCurrency(stats.avgPerCustomer)}
          subtext="Monthly"
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
        {/* Customer Commissions */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 16,
          border: `1px solid ${colors.lightGray}`,
          overflow: 'hidden',
        }}>
          <div style={{
            padding: '20px 24px',
            borderBottom: `1px solid ${colors.lightGray}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: colors.dark, margin: 0 }}>
              Customer Commissions
            </h2>
            <div style={{ display: 'flex', gap: 8 }}>
              {['month', 'quarter', 'year'].map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p as any)}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: period === p ? colors.orange : 'transparent',
                    color: period === p ? 'white' : colors.midGray,
                    border: period === p ? 'none' : `1px solid ${colors.lightGray}`,
                    borderRadius: 6,
                    fontSize: 12,
                    cursor: 'pointer',
                    textTransform: 'capitalize',
                  }}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: colors.light }}>
                <th style={thStyle}>Customer</th>
                <th style={thStyle}>Plan</th>
                <th style={thStyle}>MRR</th>
                <th style={thStyle}>Commission (15%)</th>
                <th style={thStyle}>Status</th>
              </tr>
            </thead>
            <tbody>
              {customerCommissions.map((customer) => (
                <tr key={customer.id} style={{ borderBottom: `1px solid ${colors.lightGray}` }}>
                  <td style={tdStyle}>
                    <div style={{ fontWeight: 500 }}>{customer.name}</div>
                  </td>
                  <td style={tdStyle}>{customer.plan}</td>
                  <td style={tdStyle}>{formatCurrency(customer.mrr)}</td>
                  <td style={{ ...tdStyle, color: colors.green, fontWeight: 600 }}>
                    {formatCurrency(customer.commission)}
                  </td>
                  <td style={tdStyle}>
                    <span style={{
                      padding: '4px 10px',
                      backgroundColor: customer.status === 'active' ? colors.green + '15' : colors.orange + '15',
                      color: customer.status === 'active' ? colors.green : colors.orange,
                      borderRadius: 4,
                      fontSize: 12,
                      fontWeight: 500,
                    }}>
                      {customer.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Payout Sidebar */}
        <div>
          {/* Request Payout Card */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: 16,
            border: `1px solid ${colors.lightGray}`,
            padding: 24,
            marginBottom: 24,
          }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: colors.dark, margin: '0 0 16px' }}>
              Request Payout
            </h3>

            <div style={{
              padding: 20,
              backgroundColor: colors.green + '10',
              borderRadius: 12,
              marginBottom: 16,
              textAlign: 'center',
            }}>
              <div style={{ fontSize: 13, color: colors.midGray, marginBottom: 4 }}>Available</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: colors.green }}>
                {formatCurrency(stats.pendingPayout)}
              </div>
            </div>

            <div style={{
              padding: 12,
              backgroundColor: colors.light,
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              marginBottom: 16,
            }}>
              <CreditCard size={18} color={colors.midGray} />
              <div style={{ fontSize: 13 }}>
                <div style={{ color: colors.dark }}>Bank Transfer</div>
                <div style={{ color: colors.midGray }}>DE89 •••• 1234</div>
              </div>
            </div>

            <button style={{
              width: '100%',
              padding: '12px',
              backgroundColor: colors.green,
              color: 'white',
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
            }}>
              Request Payout
            </button>
          </div>

          {/* Payout History */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: 16,
            border: `1px solid ${colors.lightGray}`,
            padding: 24,
          }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: colors.dark, margin: '0 0 16px' }}>
              Payout History
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {payoutHistory.map((payout) => (
                <div
                  key={payout.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: 12,
                    backgroundColor: colors.light,
                    borderRadius: 8,
                  }}
                >
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 500, color: colors.dark }}>
                      {formatCurrency(payout.amount)}
                    </div>
                    <div style={{ fontSize: 12, color: colors.midGray }}>
                      {new Date(payout.date).toLocaleDateString('de-DE')}
                    </div>
                  </div>
                  <span style={{
                    padding: '4px 8px',
                    backgroundColor: colors.green + '15',
                    color: colors.green,
                    borderRadius: 4,
                    fontSize: 11,
                    fontWeight: 500,
                  }}>
                    {payout.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, trend, positive, subtext, color }: any) {
  const cardColor = color || colors.orange;
  
  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: 16,
      border: `1px solid ${colors.lightGray}`,
      padding: 24,
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 16,
      }}>
        <div style={{
          width: 48,
          height: 48,
          borderRadius: 12,
          backgroundColor: cardColor + '15',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: cardColor,
        }}>
          {icon}
        </div>
        {trend && (
          <span style={{
            fontSize: 13,
            fontWeight: 600,
            color: positive ? colors.green : colors.red,
            backgroundColor: positive ? colors.green + '15' : colors.red + '15',
            padding: '4px 8px',
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            gap: 4,
          }}>
            <TrendingUp size={14} />
            {trend}
          </span>
        )}
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color: colors.dark, marginBottom: 4 }}>
        {value}
      </div>
      <div style={{ fontSize: 14, color: colors.midGray }}>
        {subtext || label}
      </div>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  padding: '12px 20px',
  textAlign: 'left',
  fontSize: 13,
  fontWeight: 500,
  color: colors.midGray,
};

const tdStyle: React.CSSProperties = {
  padding: '16px 20px',
  fontSize: 14,
  color: colors.dark,
};
