'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { colors } from '@/lib/theme';
import {
  Calendar, Clock, CheckCircle, XCircle, AlertCircle,
  MessageSquare, Video, Phone, ChevronRight, Filter
} from 'lucide-react';

type BookingStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled';

interface Booking {
  id: string;
  customer: {
    name: string;
    company: string;
    avatar?: string;
  };
  topic: string;
  date: string;
  time: string;
  duration: number;
  status: BookingStatus;
  type: 'video' | 'phone' | 'chat';
  amount: number;
  notes?: string;
}

export default function ExpertBookings() {
  const router = useRouter();
  const [filter, setFilter] = useState<'all' | BookingStatus>('all');

  const bookings: Booking[] = [
    {
      id: '1',
      customer: { name: 'Hans Müller', company: 'Acme GmbH' },
      topic: 'ETIM Classification Review',
      date: '2026-01-31',
      time: '10:00',
      duration: 60,
      status: 'pending',
      type: 'video',
      amount: 35000,
      notes: 'Need help classifying 500 products into ETIM categories',
    },
    {
      id: '2',
      customer: { name: 'Maria Schmidt', company: 'TechParts AG' },
      topic: 'Product Data Migration Strategy',
      date: '2026-01-31',
      time: '14:30',
      duration: 90,
      status: 'confirmed',
      type: 'video',
      amount: 52500,
    },
    {
      id: '3',
      customer: { name: 'Thomas Weber', company: 'BuildSupply' },
      topic: 'BMECat Setup Consultation',
      date: '2026-02-01',
      time: '09:00',
      duration: 60,
      status: 'confirmed',
      type: 'phone',
      amount: 35000,
    },
    {
      id: '4',
      customer: { name: 'Anna Fischer', company: 'ElektroPro' },
      topic: 'Tax implications of B2B marketplace',
      date: '2026-01-28',
      time: '11:00',
      duration: 45,
      status: 'completed',
      type: 'video',
      amount: 26250,
    },
    {
      id: '5',
      customer: { name: 'Klaus Bauer', company: 'SanitärPlus' },
      topic: 'DATANORM export questions',
      date: '2026-01-25',
      time: '15:00',
      duration: 30,
      status: 'cancelled',
      type: 'chat',
      amount: 17500,
    },
  ];

  const filteredBookings = filter === 'all' 
    ? bookings 
    : bookings.filter(b => b.status === filter);

  const formatCurrency = (cents: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(cents / 100);
  };

  const getStatusColor = (status: BookingStatus) => {
    switch (status) {
      case 'pending': return colors.orange;
      case 'confirmed': return colors.blue;
      case 'completed': return colors.green;
      case 'cancelled': return colors.red;
    }
  };

  const getStatusIcon = (status: BookingStatus) => {
    switch (status) {
      case 'pending': return <AlertCircle size={16} />;
      case 'confirmed': return <CheckCircle size={16} />;
      case 'completed': return <CheckCircle size={16} />;
      case 'cancelled': return <XCircle size={16} />;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'video': return <Video size={16} />;
      case 'phone': return <Phone size={16} />;
      case 'chat': return <MessageSquare size={16} />;
    }
  };

  const handleAccept = (bookingId: string) => {
    console.log('Accept booking', bookingId);
    // API call to accept
  };

  const handleDecline = (bookingId: string) => {
    console.log('Decline booking', bookingId);
    // API call to decline
  };

  return (
    <div>
      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 16,
        marginBottom: 24,
      }}>
        {[
          { label: 'Pending', count: bookings.filter(b => b.status === 'pending').length, color: colors.orange },
          { label: 'Confirmed', count: bookings.filter(b => b.status === 'confirmed').length, color: colors.blue },
          { label: 'Completed', count: bookings.filter(b => b.status === 'completed').length, color: colors.green },
          { label: 'Cancelled', count: bookings.filter(b => b.status === 'cancelled').length, color: colors.midGray },
        ].map((stat) => (
          <div
            key={stat.label}
            style={{
              backgroundColor: 'white',
              borderRadius: 12,
              border: `1px solid ${colors.lightGray}`,
              padding: 20,
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <div style={{
              width: 48,
              height: 48,
              borderRadius: 10,
              backgroundColor: stat.color + '15',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: stat.color,
              fontSize: 20,
              fontWeight: 700,
            }}>
              {stat.count}
            </div>
            <div style={{ fontSize: 14, color: colors.midGray }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Filter Tabs */}
      <div style={{
        display: 'flex',
        gap: 8,
        marginBottom: 24,
        backgroundColor: 'white',
        padding: 8,
        borderRadius: 12,
        border: `1px solid ${colors.lightGray}`,
      }}>
        {['all', 'pending', 'confirmed', 'completed', 'cancelled'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f as any)}
            style={{
              padding: '10px 20px',
              backgroundColor: filter === f ? colors.orange : 'transparent',
              color: filter === f ? 'white' : colors.midGray,
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 500,
              cursor: 'pointer',
              textTransform: 'capitalize',
            }}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Bookings List */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        overflow: 'hidden',
      }}>
        {filteredBookings.length === 0 ? (
          <div style={{ padding: 60, textAlign: 'center', color: colors.midGray }}>
            No bookings found
          </div>
        ) : (
          filteredBookings.map((booking, i) => (
            <div
              key={booking.id}
              style={{
                padding: 24,
                borderBottom: i < filteredBookings.length - 1 ? `1px solid ${colors.lightGray}` : 'none',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', gap: 16, flex: 1 }}>
                  {/* Avatar */}
                  <div style={{
                    width: 48,
                    height: 48,
                    borderRadius: '50%',
                    backgroundColor: colors.blue + '20',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: colors.blue,
                    fontWeight: 600,
                    fontSize: 18,
                  }}>
                    {booking.customer.name[0]}
                  </div>

                  {/* Details */}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
                      <span style={{ fontSize: 16, fontWeight: 600, color: colors.dark }}>
                        {booking.customer.name}
                      </span>
                      <span style={{ fontSize: 14, color: colors.midGray }}>
                        {booking.customer.company}
                      </span>
                    </div>

                    <div style={{ fontSize: 15, color: colors.dark, marginBottom: 8 }}>
                      {booking.topic}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 13, color: colors.midGray }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Calendar size={14} />
                        {new Date(booking.date).toLocaleDateString('de-DE', { weekday: 'short', month: 'short', day: 'numeric' })}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Clock size={14} />
                        {booking.time} · {booking.duration}min
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        {getTypeIcon(booking.type)}
                        {booking.type}
                      </span>
                    </div>

                    {booking.notes && (
                      <div style={{
                        marginTop: 12,
                        padding: 12,
                        backgroundColor: colors.light,
                        borderRadius: 8,
                        fontSize: 13,
                        color: colors.dark,
                      }}>
                        {booking.notes}
                      </div>
                    )}
                  </div>
                </div>

                {/* Right side */}
                <div style={{ textAlign: 'right' }}>
                  <div style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '6px 12px',
                    backgroundColor: getStatusColor(booking.status) + '15',
                    color: getStatusColor(booking.status),
                    borderRadius: 6,
                    fontSize: 13,
                    fontWeight: 500,
                    marginBottom: 8,
                  }}>
                    {getStatusIcon(booking.status)}
                    {booking.status}
                  </div>

                  <div style={{ fontSize: 18, fontWeight: 600, color: colors.dark }}>
                    {formatCurrency(booking.amount)}
                  </div>

                  {booking.status === 'pending' && (
                    <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                      <button
                        onClick={() => handleDecline(booking.id)}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: 'transparent',
                          border: `1px solid ${colors.lightGray}`,
                          borderRadius: 6,
                          fontSize: 13,
                          color: colors.midGray,
                          cursor: 'pointer',
                        }}
                      >
                        Decline
                      </button>
                      <button
                        onClick={() => handleAccept(booking.id)}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: colors.green,
                          border: 'none',
                          borderRadius: 6,
                          fontSize: 13,
                          fontWeight: 600,
                          color: 'white',
                          cursor: 'pointer',
                        }}
                      >
                        Accept
                      </button>
                    </div>
                  )}

                  {booking.status === 'confirmed' && (
                    <button
                      style={{
                        marginTop: 12,
                        padding: '8px 16px',
                        backgroundColor: colors.blue,
                        border: 'none',
                        borderRadius: 6,
                        fontSize: 13,
                        fontWeight: 600,
                        color: 'white',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                      }}
                    >
                      <Video size={14} />
                      Join Call
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
