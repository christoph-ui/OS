'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { colors } from '@/lib/theme';
import {
  Calendar, DollarSign, Star, TrendingUp, Clock, Users,
  ArrowRight, ChevronRight, CheckCircle, XCircle, AlertCircle
} from 'lucide-react';

export default function ExpertDashboard() {
  const router = useRouter();
  const [stats, setStats] = useState({
    totalEarnings: 12450,
    pendingPayouts: 2340,
    totalBookings: 47,
    completedBookings: 42,
    rating: 4.8,
    totalReviews: 38,
    responseRate: 95,
    avgResponseTime: 2.4,
  });

  const upcomingBookings = [
    {
      id: '1',
      customer: 'Acme GmbH',
      topic: 'ETIM Classification Review',
      date: '2026-01-31',
      time: '10:00',
      duration: 60,
      status: 'confirmed',
    },
    {
      id: '2',
      customer: 'TechParts AG',
      topic: 'Product Data Migration Strategy',
      date: '2026-01-31',
      time: '14:30',
      duration: 90,
      status: 'pending',
    },
    {
      id: '3',
      customer: 'BuildSupply',
      topic: 'BMECat Setup Consultation',
      date: '2026-02-01',
      time: '09:00',
      duration: 60,
      status: 'confirmed',
    },
  ];

  const recentActivity = [
    { type: 'booking', message: 'New booking request from Acme GmbH', time: '2 hours ago' },
    { type: 'review', message: 'You received a 5-star review!', time: '5 hours ago' },
    { type: 'payout', message: 'Payout of €850 processed', time: '1 day ago' },
    { type: 'booking', message: 'Booking completed with TechParts AG', time: '2 days ago' },
  ];

  const formatCurrency = (cents: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(cents / 100);
  };

  return (
    <div>
      {/* Stats Grid */}
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
          change="+12%"
          positive
        />
        <StatCard
          icon={<Calendar size={24} />}
          label="Total Bookings"
          value={stats.totalBookings.toString()}
          subtext={`${stats.completedBookings} completed`}
        />
        <StatCard
          icon={<Star size={24} />}
          label="Rating"
          value={stats.rating.toString()}
          subtext={`${stats.totalReviews} reviews`}
        />
        <StatCard
          icon={<Clock size={24} />}
          label="Avg Response"
          value={`${stats.avgResponseTime}h`}
          subtext={`${stats.responseRate}% response rate`}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
        {/* Upcoming Bookings */}
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
            marginBottom: 20,
          }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: colors.dark, margin: 0 }}>
              Upcoming Bookings
            </h2>
            <button
              onClick={() => router.push('/expert-dashboard/bookings')}
              style={{
                backgroundColor: 'transparent',
                border: 'none',
                color: colors.orange,
                fontSize: 14,
                fontWeight: 500,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              View All <ChevronRight size={16} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {upcomingBookings.map((booking) => (
              <div
                key={booking.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  padding: 16,
                  backgroundColor: colors.light,
                  borderRadius: 12,
                  cursor: 'pointer',
                }}
                onClick={() => router.push(`/expert-dashboard/bookings/${booking.id}`)}
              >
                <div style={{
                  width: 48,
                  height: 48,
                  borderRadius: 10,
                  backgroundColor: booking.status === 'confirmed' ? colors.green + '20' : colors.orange + '20',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: booking.status === 'confirmed' ? colors.green : colors.orange,
                }}>
                  {booking.status === 'confirmed' ? <CheckCircle size={24} /> : <AlertCircle size={24} />}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 15, fontWeight: 600, color: colors.dark }}>
                    {booking.customer}
                  </div>
                  <div style={{ fontSize: 13, color: colors.midGray }}>
                    {booking.topic}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 14, fontWeight: 500, color: colors.dark }}>
                    {new Date(booking.date).toLocaleDateString('de-DE', { weekday: 'short', month: 'short', day: 'numeric' })}
                  </div>
                  <div style={{ fontSize: 13, color: colors.midGray }}>
                    {booking.time} · {booking.duration}min
                  </div>
                </div>

                <ChevronRight size={20} color={colors.midGray} />
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 16,
          border: `1px solid ${colors.lightGray}`,
          padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: colors.dark, margin: '0 0 20px' }}>
            Recent Activity
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {recentActivity.map((activity, i) => (
              <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: activity.type === 'review' ? colors.orange : 
                                   activity.type === 'payout' ? colors.green : colors.blue,
                  marginTop: 6,
                }} />
                <div>
                  <div style={{ fontSize: 14, color: colors.dark }}>{activity.message}</div>
                  <div style={{ fontSize: 12, color: colors.midGray }}>{activity.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div style={{
        marginTop: 24,
        backgroundColor: 'white',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 24,
      }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: colors.dark, margin: '0 0 20px' }}>
          Quick Actions
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          <QuickAction
            icon={<Calendar size={20} />}
            label="Set Availability"
            onClick={() => router.push('/expert-dashboard/availability')}
          />
          <QuickAction
            icon={<Users size={20} />}
            label="View Profile"
            onClick={() => router.push('/expert-dashboard/profile')}
          />
          <QuickAction
            icon={<DollarSign size={20} />}
            label="Request Payout"
            onClick={() => router.push('/expert-dashboard/earnings')}
          />
          <QuickAction
            icon={<Star size={20} />}
            label="View Reviews"
            onClick={() => router.push('/expert-dashboard/profile#reviews')}
          />
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, change, positive, subtext }: any) {
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
          backgroundColor: colors.orange + '15',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: colors.orange,
        }}>
          {icon}
        </div>
        {change && (
          <span style={{
            fontSize: 13,
            fontWeight: 600,
            color: positive ? colors.green : colors.red,
            backgroundColor: positive ? colors.green + '15' : colors.red + '15',
            padding: '4px 8px',
            borderRadius: 6,
          }}>
            {change}
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

function QuickAction({ icon, label, onClick }: any) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: 16,
        backgroundColor: colors.light,
        border: `1px solid ${colors.lightGray}`,
        borderRadius: 12,
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = colors.orange;
        e.currentTarget.style.backgroundColor = colors.orange + '08';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = colors.lightGray;
        e.currentTarget.style.backgroundColor = colors.light;
      }}
    >
      <div style={{ color: colors.orange }}>{icon}</div>
      <span style={{ fontSize: 14, fontWeight: 500, color: colors.dark }}>{label}</span>
    </button>
  );
}
