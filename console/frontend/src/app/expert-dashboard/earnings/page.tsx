'use client';

import React, { useState } from 'react';
import { colors } from '@/lib/theme';
import {
  DollarSign, TrendingUp, CreditCard, Clock, ArrowUpRight,
  ArrowDownRight, Download, Calendar, ChevronRight, Wallet
} from 'lucide-react';

export default function ExpertEarnings() {
  const [period, setPeriod] = useState<'week' | 'month' | 'year'>('month');

  const stats = {
    totalEarnings: 12450,
    pendingPayout: 2340,
    availableBalance: 8750,
    totalBookings: 42,
  };

  const transactions = [
    { id: '1', type: 'earning', description: 'Consultation with Acme GmbH', amount: 35000, date: '2026-01-29', status: 'completed' },
    { id: '2', type: 'payout', description: 'Payout to DE89 3704 ****', amount: -85000, date: '2026-01-25', status: 'completed' },
    { id: '3', type: 'earning', description: 'Consultation with TechParts AG', amount: 52500, date: '2026-01-24', status: 'completed' },
    { id: '4', type: 'earning', description: 'Consultation with BuildSupply', amount: 35000, date: '2026-01-22', status: 'pending' },
    { id: '5', type: 'earning', description: 'Consultation with ElektroPro', amount: 26250, date: '2026-01-20', status: 'completed' },
    { id: '6', type: 'payout', description: 'Payout to DE89 3704 ****', amount: -120000, date: '2026-01-15', status: 'completed' },
  ];

  const monthlyEarnings = [
    { month: 'Aug', amount: 8500 },
    { month: 'Sep', amount: 12300 },
    { month: 'Oct', amount: 9800 },
    { month: 'Nov', amount: 15200 },
    { month: 'Dec', amount: 11400 },
    { month: 'Jan', amount: 12450 },
  ];

  const maxEarning = Math.max(...monthlyEarnings.map(m => m.amount));

  const formatCurrency = (cents: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(cents / 100);
  };

  const [showPayoutModal, setShowPayoutModal] = useState(false);

  return (
    <div>
      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 20,
        marginBottom: 32,
      }}>
        <StatCard
          icon={<DollarSign size={24} />}
          label="Total Earnings"
          value={formatCurrency(stats.totalEarnings * 100)}
          subtext="This month"
          trend="+12%"
          positive
        />
        <StatCard
          icon={<Wallet size={24} />}
          label="Available Balance"
          value={formatCurrency(stats.availableBalance * 100)}
          subtext="Ready to withdraw"
          color={colors.green}
        />
        <StatCard
          icon={<Clock size={24} />}
          label="Pending"
          value={formatCurrency(stats.pendingPayout * 100)}
          subtext="Being processed"
          color={colors.orange}
        />
        <StatCard
          icon={<Calendar size={24} />}
          label="Bookings"
          value={stats.totalBookings.toString()}
          subtext="This month"
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
        {/* Chart */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 16,
          border: `1px solid ${colors.lightGray}`,
          padding: 24,
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 24,
          }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: colors.dark, margin: 0 }}>
              Earnings Overview
            </h2>
            <div style={{ display: 'flex', gap: 8 }}>
              {['week', 'month', 'year'].map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p as any)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: period === p ? colors.orange : 'transparent',
                    color: period === p ? 'white' : colors.midGray,
                    border: period === p ? 'none' : `1px solid ${colors.lightGray}`,
                    borderRadius: 6,
                    fontSize: 13,
                    cursor: 'pointer',
                    textTransform: 'capitalize',
                  }}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Simple Bar Chart */}
          <div style={{
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-between',
            height: 200,
            padding: '20px 0',
          }}>
            {monthlyEarnings.map((m, i) => (
              <div key={m.month} style={{ textAlign: 'center', flex: 1 }}>
                <div style={{
                  height: `${(m.amount / maxEarning) * 150}px`,
                  backgroundColor: i === monthlyEarnings.length - 1 ? colors.orange : colors.orange + '40',
                  borderRadius: '4px 4px 0 0',
                  margin: '0 8px',
                  transition: 'height 0.3s ease',
                }} />
                <div style={{ fontSize: 12, color: colors.midGray, marginTop: 8 }}>{m.month}</div>
                <div style={{ fontSize: 11, color: colors.dark, fontWeight: 500 }}>
                  €{(m.amount / 100).toFixed(0)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Payout Card */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 16,
          border: `1px solid ${colors.lightGray}`,
          padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: colors.dark, margin: '0 0 20px' }}>
            Request Payout
          </h2>

          <div style={{
            padding: 20,
            backgroundColor: colors.green + '10',
            borderRadius: 12,
            marginBottom: 20,
          }}>
            <div style={{ fontSize: 13, color: colors.midGray, marginBottom: 4 }}>Available</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: colors.green }}>
              {formatCurrency(stats.availableBalance * 100)}
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 14, fontWeight: 500, color: colors.dark, marginBottom: 8 }}>
              Payout Method
            </div>
            <div style={{
              padding: 16,
              backgroundColor: colors.light,
              borderRadius: 10,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}>
              <CreditCard size={20} color={colors.midGray} />
              <div>
                <div style={{ fontSize: 14, color: colors.dark }}>Bank Transfer</div>
                <div style={{ fontSize: 12, color: colors.midGray }}>DE89 3704 •••• •••• 1234</div>
              </div>
            </div>
          </div>

          <button
            onClick={() => setShowPayoutModal(true)}
            style={{
              width: '100%',
              padding: '14px',
              backgroundColor: colors.green,
              color: 'white',
              border: 'none',
              borderRadius: 10,
              fontSize: 15,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
          >
            <Wallet size={18} />
            Request Payout
          </button>

          <div style={{ fontSize: 12, color: colors.midGray, textAlign: 'center', marginTop: 12 }}>
            Payouts are processed within 2-3 business days
          </div>
        </div>
      </div>

      {/* Transactions */}
      <div style={{
        marginTop: 24,
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
            Transaction History
          </h2>
          <button style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 16px',
            backgroundColor: 'transparent',
            border: `1px solid ${colors.lightGray}`,
            borderRadius: 8,
            fontSize: 13,
            color: colors.dark,
            cursor: 'pointer',
          }}>
            <Download size={16} />
            Export
          </button>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: colors.light }}>
              <th style={thStyle}>Date</th>
              <th style={thStyle}>Description</th>
              <th style={thStyle}>Status</th>
              <th style={{ ...thStyle, textAlign: 'right' }}>Amount</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => (
              <tr key={tx.id} style={{ borderBottom: `1px solid ${colors.lightGray}` }}>
                <td style={tdStyle}>
                  {new Date(tx.date).toLocaleDateString('de-DE', { month: 'short', day: 'numeric' })}
                </td>
                <td style={tdStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: 32,
                      height: 32,
                      borderRadius: 8,
                      backgroundColor: tx.type === 'earning' ? colors.green + '15' : colors.blue + '15',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: tx.type === 'earning' ? colors.green : colors.blue,
                    }}>
                      {tx.type === 'earning' ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                    </div>
                    <span>{tx.description}</span>
                  </div>
                </td>
                <td style={tdStyle}>
                  <span style={{
                    padding: '4px 10px',
                    backgroundColor: tx.status === 'completed' ? colors.green + '15' : colors.orange + '15',
                    color: tx.status === 'completed' ? colors.green : colors.orange,
                    borderRadius: 4,
                    fontSize: 12,
                    fontWeight: 500,
                  }}>
                    {tx.status}
                  </span>
                </td>
                <td style={{ ...tdStyle, textAlign: 'right' }}>
                  <span style={{
                    fontWeight: 600,
                    color: tx.amount > 0 ? colors.green : colors.dark,
                  }}>
                    {tx.amount > 0 ? '+' : ''}{formatCurrency(tx.amount)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, subtext, trend, positive, color }: any) {
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
        {subtext}
      </div>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  padding: '12px 24px',
  textAlign: 'left',
  fontSize: 13,
  fontWeight: 500,
  color: colors.midGray,
};

const tdStyle: React.CSSProperties = {
  padding: '16px 24px',
  fontSize: 14,
  color: colors.dark,
};
