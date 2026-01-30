'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Calendar, Clock, User, Euro, Check, X, MessageSquare, ChevronRight } from 'lucide-react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
  red: '#c75050',
};

interface Booking {
  id: string;
  expert_name: string;
  expert_title: string;
  scheduled_date: string;
  scheduled_time: string;
  estimated_hours: number;
  total_amount: number;
  status: 'pending' | 'accepted' | 'confirmed' | 'completed' | 'declined' | 'cancelled';
  message?: string;
  created_at: string;
}

const sampleBookings: Booking[] = [
  {
    id: '1',
    expert_name: 'Dr. Stefan Weber',
    expert_title: 'Corporate Tax Specialist',
    scheduled_date: '2024-02-01',
    scheduled_time: '10:00',
    estimated_hours: 2,
    total_amount: 700,
    status: 'confirmed',
    message: 'Need help with transfer pricing documentation',
    created_at: '2024-01-28T10:00:00Z',
  },
  {
    id: '2',
    expert_name: 'Maria Schmidt',
    expert_title: 'ETIM Classification Expert',
    scheduled_date: '2024-02-05',
    scheduled_time: '14:00',
    estimated_hours: 4,
    total_amount: 880,
    status: 'pending',
    message: 'Classify 10,000 electrical products',
    created_at: '2024-01-29T14:30:00Z',
  },
  {
    id: '3',
    expert_name: 'Laura Fischer',
    expert_title: 'E-Commerce Integration Specialist',
    scheduled_date: '2024-01-20',
    scheduled_time: '09:00',
    estimated_hours: 3,
    total_amount: 540,
    status: 'completed',
    message: 'Set up Amazon SP-API integration',
    created_at: '2024-01-15T08:00:00Z',
  },
];

const statusConfig: Record<string, { label: string; color: string; bg: string }> = {
  pending: { label: 'Pending', color: colors.orange, bg: colors.orange + '15' },
  accepted: { label: 'Accepted', color: colors.blue, bg: colors.blue + '15' },
  confirmed: { label: 'Confirmed', color: colors.green, bg: colors.green + '15' },
  completed: { label: 'Completed', color: colors.dark, bg: colors.lightGray },
  declined: { label: 'Declined', color: colors.red, bg: colors.red + '15' },
  cancelled: { label: 'Cancelled', color: colors.midGray, bg: colors.lightGray },
};

export default function BookingsPage() {
  const router = useRouter();
  const [bookings, setBookings] = useState<Booking[]>(sampleBookings);
  const [filter, setFilter] = useState<'all' | 'upcoming' | 'past'>('all');

  const filteredBookings = bookings.filter(booking => {
    const bookingDate = new Date(booking.scheduled_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (filter === 'upcoming') {
      return bookingDate >= today && !['completed', 'cancelled', 'declined'].includes(booking.status);
    }
    if (filter === 'past') {
      return bookingDate < today || ['completed', 'cancelled', 'declined'].includes(booking.status);
    }
    return true;
  });

  return (
    <div style={{ minHeight: '100vh', backgroundColor: colors.light }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#fff',
        borderBottom: `1px solid ${colors.lightGray}`,
        padding: '24px 40px',
      }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h1 style={{
                fontFamily: "'Poppins', sans-serif",
                fontSize: 28,
                fontWeight: 600,
                color: colors.dark,
                margin: '0 0 4px',
              }}>
                My Bookings
              </h1>
              <p style={{ color: colors.midGray, margin: 0, fontSize: 14 }}>
                Manage your expert consultations
              </p>
            </div>

            <button
              onClick={() => router.push('/experts')}
              style={{
                padding: '12px 24px',
                backgroundColor: colors.orange,
                color: '#fff',
                border: 'none',
                borderRadius: 10,
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              + Book New Expert
            </button>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 40px' }}>
        {/* Filter Tabs */}
        <div style={{
          display: 'flex',
          gap: 8,
          marginBottom: 24,
        }}>
          {[
            { key: 'all', label: 'All Bookings' },
            { key: 'upcoming', label: 'Upcoming' },
            { key: 'past', label: 'Past' },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key as any)}
              style={{
                padding: '10px 20px',
                backgroundColor: filter === tab.key ? colors.dark : '#fff',
                color: filter === tab.key ? '#fff' : colors.dark,
                border: `1px solid ${filter === tab.key ? colors.dark : colors.lightGray}`,
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Bookings List */}
        {filteredBookings.length === 0 ? (
          <div style={{
            backgroundColor: '#fff',
            borderRadius: 12,
            border: `1px solid ${colors.lightGray}`,
            padding: 60,
            textAlign: 'center',
          }}>
            <Calendar size={48} color={colors.midGray} style={{ marginBottom: 16 }} />
            <p style={{ color: colors.midGray, margin: 0 }}>
              No bookings found
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {filteredBookings.map(booking => (
              <BookingCard key={booking.id} booking={booking} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function BookingCard({ booking }: { booking: Booking }) {
  const status = statusConfig[booking.status];

  return (
    <div style={{
      backgroundColor: '#fff',
      borderRadius: 12,
      border: `1px solid ${colors.lightGray}`,
      padding: 24,
      transition: 'all 0.2s',
      cursor: 'pointer',
    }}
    onMouseOver={(e) => {
      e.currentTarget.style.borderColor = colors.orange + '60';
    }}
    onMouseOut={(e) => {
      e.currentTarget.style.borderColor = colors.lightGray;
    }}
    >
      <div style={{ display: 'flex', gap: 20 }}>
        {/* Avatar */}
        <div style={{
          width: 56,
          height: 56,
          borderRadius: 12,
          backgroundColor: colors.dark + '10',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 20,
          fontWeight: 600,
          color: colors.dark + '60',
          flexShrink: 0,
        }}>
          {booking.expert_name.split(' ').map(n => n[0]).join('')}
        </div>

        {/* Info */}
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 8 }}>
            <div>
              <h3 style={{
                fontFamily: "'Poppins', sans-serif",
                fontSize: 17,
                fontWeight: 600,
                color: colors.dark,
                margin: '0 0 2px',
              }}>
                {booking.expert_name}
              </h3>
              <p style={{ fontSize: 13, color: colors.midGray, margin: 0 }}>
                {booking.expert_title}
              </p>
            </div>

            <span style={{
              fontSize: 12,
              fontWeight: 600,
              color: status.color,
              backgroundColor: status.bg,
              padding: '4px 12px',
              borderRadius: 6,
            }}>
              {status.label}
            </span>
          </div>

          {booking.message && (
            <p style={{
              fontSize: 14,
              color: colors.dark + 'cc',
              margin: '12px 0',
              padding: 12,
              backgroundColor: colors.light,
              borderRadius: 8,
            }}>
              "{booking.message}"
            </p>
          )}

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 20,
            marginTop: 16,
            paddingTop: 16,
            borderTop: `1px solid ${colors.lightGray}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Calendar size={16} color={colors.midGray} />
              <span style={{ fontSize: 14, color: colors.dark }}>
                {new Date(booking.scheduled_date).toLocaleDateString('de-DE', {
                  weekday: 'short',
                  day: 'numeric',
                  month: 'short',
                })}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Clock size={16} color={colors.midGray} />
              <span style={{ fontSize: 14, color: colors.dark }}>
                {booking.scheduled_time} ({booking.estimated_hours}h)
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Euro size={16} color={colors.midGray} />
              <span style={{ fontSize: 14, fontWeight: 600, color: colors.dark }}>
                €{booking.total_amount}
              </span>
            </div>

            <div style={{ marginLeft: 'auto' }}>
              {booking.status === 'confirmed' && (
                <button style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '8px 16px',
                  backgroundColor: colors.green,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 6,
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}>
                  <MessageSquare size={14} />
                  Join Call
                </button>
              )}

              {booking.status === 'pending' && (
                <span style={{ fontSize: 13, color: colors.midGray }}>
                  Waiting for expert response...
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
