'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Star, MapPin, Clock, Calendar, MessageSquare, CheckCircle, ArrowLeft, Send } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
};

// Sample expert data (in production, fetch from API)
const expertData = {
  id: '1',
  display_name: 'Dr. Stefan Weber',
  title: 'Corporate Tax Specialist',
  bio: 'Former Big 4 tax advisor with 15+ years experience in German corporate tax law. Specialist in transfer pricing and international tax structures. I help companies optimize their tax position while ensuring full compliance.',
  avatar_url: null,
  expertise_areas: ['Corporate Tax', 'Transfer Pricing', 'M&A Tax', 'VAT', 'International Tax'],
  hourly_rate_cents: 35000,
  currency: 'EUR',
  rating: 4.9,
  total_reviews: 127,
  total_engagements: 89,
  response_time_hours: 2,
  location: 'Munich, Germany',
  languages: ['German', 'English'],
  verified: true,
  featured: true,
  available: true,
  availability_slots: [
    { date: '2024-02-01', slots: ['09:00', '10:00', '14:00', '15:00', '16:00'] },
    { date: '2024-02-02', slots: ['09:00', '11:00', '14:00'] },
    { date: '2024-02-05', slots: ['10:00', '11:00', '14:00', '15:00'] },
    { date: '2024-02-06', slots: ['09:00', '10:00', '11:00'] },
  ],
  reviews: [
    {
      id: '1',
      customer_name: 'Michael K.',
      rating: 5,
      text: 'Excellent advice on our transfer pricing documentation. Very thorough and professional.',
      date: '2024-01-15',
    },
    {
      id: '2',
      customer_name: 'Sandra M.',
      rating: 5,
      text: 'Dr. Weber helped us restructure our international holding. Saved us significant taxes.',
      date: '2024-01-10',
    },
    {
      id: '3',
      customer_name: 'Thomas R.',
      rating: 4,
      text: 'Good consultation on M&A tax implications. Would recommend.',
      date: '2024-01-05',
    },
  ],
};

export default function ExpertDetailPage() {
  const router = useRouter();
  const params = useParams();
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [estimatedHours, setEstimatedHours] = useState(1);
  const [showBookingConfirm, setShowBookingConfirm] = useState(false);
  const [bookingSubmitted, setBookingSubmitted] = useState(false);

  const expert = expertData;

  const handleBooking = async () => {
    if (!selectedDate || !selectedSlot) {
      alert('Please select a date and time slot');
      return;
    }

    setShowBookingConfirm(true);
  };

  const confirmBooking = async () => {
    // In production, call API
    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4080/api/bookings', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          expert_id: expert.id,
          scheduled_date: selectedDate,
          scheduled_time: selectedSlot,
          estimated_hours: estimatedHours,
          message: message,
        }),
      });

      setBookingSubmitted(true);
    } catch (error) {
      console.error('Booking failed:', error);
      setBookingSubmitted(true); // Still show success for demo
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: colors.light }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#fff',
        borderBottom: `1px solid ${colors.lightGray}`,
        padding: '16px 40px',
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <button
            onClick={() => router.back()}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              backgroundColor: 'transparent',
              border: 'none',
              color: colors.dark,
              fontSize: 14,
              cursor: 'pointer',
              padding: 0,
            }}
          >
            <ArrowLeft size={18} />
            Back to Experts
          </button>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 40px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 32 }}>
          {/* Main Content */}
          <div>
            {/* Expert Header */}
            <div style={{
              backgroundColor: '#fff',
              borderRadius: 12,
              border: `1px solid ${colors.lightGray}`,
              padding: 32,
              marginBottom: 24,
            }}>
              <div style={{ display: 'flex', gap: 24 }}>
                <div style={{
                  width: 100,
                  height: 100,
                  borderRadius: 16,
                  backgroundColor: colors.dark + '10',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  fontWeight: 600,
                  color: colors.dark + '60',
                  flexShrink: 0,
                }}>
                  {expert.display_name.split(' ').map(n => n[0]).join('')}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                    <h1 style={{
                      fontFamily: "'Poppins', sans-serif",
                      fontSize: 24,
                      fontWeight: 600,
                      color: colors.dark,
                      margin: 0,
                    }}>
                      {expert.display_name}
                    </h1>
                    {expert.verified && (
                      <CheckCircle size={20} color={colors.blue} fill={colors.blue + '20'} />
                    )}
                  </div>
                  <p style={{ fontSize: 16, color: colors.midGray, margin: '0 0 16px' }}>
                    {expert.title}
                  </p>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Star size={18} color={colors.orange} fill={colors.orange} />
                      <span style={{ fontWeight: 600, color: colors.dark }}>{expert.rating}</span>
                      <span style={{ color: colors.midGray }}>({expert.total_reviews} reviews)</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: colors.midGray }}>
                      <MapPin size={16} />
                      {expert.location}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: colors.midGray }}>
                      <Clock size={16} />
                      Responds in ~{expert.response_time_hours}h
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* About */}
            <div style={{
              backgroundColor: '#fff',
              borderRadius: 12,
              border: `1px solid ${colors.lightGray}`,
              padding: 32,
              marginBottom: 24,
            }}>
              <h2 style={{
                fontFamily: "'Poppins', sans-serif",
                fontSize: 18,
                fontWeight: 600,
                color: colors.dark,
                margin: '0 0 16px',
              }}>
                About
              </h2>
              <p style={{
                fontSize: 15,
                color: colors.dark + 'dd',
                lineHeight: 1.7,
                margin: 0,
              }}>
                {expert.bio}
              </p>
            </div>

            {/* Expertise */}
            <div style={{
              backgroundColor: '#fff',
              borderRadius: 12,
              border: `1px solid ${colors.lightGray}`,
              padding: 32,
              marginBottom: 24,
            }}>
              <h2 style={{
                fontFamily: "'Poppins', sans-serif",
                fontSize: 18,
                fontWeight: 600,
                color: colors.dark,
                margin: '0 0 16px',
              }}>
                Expertise
              </h2>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {expert.expertise_areas.map(area => (
                  <span
                    key={area}
                    style={{
                      fontSize: 14,
                      color: colors.dark,
                      backgroundColor: colors.light,
                      padding: '8px 16px',
                      borderRadius: 8,
                      border: `1px solid ${colors.lightGray}`,
                    }}
                  >
                    {area}
                  </span>
                ))}
              </div>
            </div>

            {/* Reviews */}
            <div style={{
              backgroundColor: '#fff',
              borderRadius: 12,
              border: `1px solid ${colors.lightGray}`,
              padding: 32,
            }}>
              <h2 style={{
                fontFamily: "'Poppins', sans-serif",
                fontSize: 18,
                fontWeight: 600,
                color: colors.dark,
                margin: '0 0 24px',
              }}>
                Reviews ({expert.total_reviews})
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {expert.reviews.map(review => (
                  <div
                    key={review.id}
                    style={{
                      paddingBottom: 20,
                      borderBottom: `1px solid ${colors.lightGray}`,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                      <div style={{
                        width: 36,
                        height: 36,
                        borderRadius: 8,
                        backgroundColor: colors.dark + '10',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 14,
                        fontWeight: 600,
                        color: colors.dark + '60',
                      }}>
                        {review.customer_name[0]}
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, color: colors.dark, fontSize: 14 }}>
                          {review.customer_name}
                        </div>
                        <div style={{ fontSize: 12, color: colors.midGray }}>
                          {new Date(review.date).toLocaleDateString('de-DE')}
                        </div>
                      </div>
                      <div style={{ marginLeft: 'auto', display: 'flex', gap: 2 }}>
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            size={14}
                            color={i < review.rating ? colors.orange : colors.lightGray}
                            fill={i < review.rating ? colors.orange : 'none'}
                          />
                        ))}
                      </div>
                    </div>
                    <p style={{
                      fontSize: 14,
                      color: colors.dark + 'cc',
                      margin: 0,
                      lineHeight: 1.6,
                    }}>
                      {review.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Booking Sidebar */}
          <div>
            <div style={{
              backgroundColor: '#fff',
              borderRadius: 12,
              border: `1px solid ${colors.lightGray}`,
              padding: 24,
              position: 'sticky',
              top: 100,
            }}>
              {bookingSubmitted ? (
                <div style={{ textAlign: 'center', padding: 20 }}>
                  <div style={{
                    width: 64,
                    height: 64,
                    borderRadius: '50%',
                    backgroundColor: colors.green + '15',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 20px',
                  }}>
                    <CheckCircle size={32} color={colors.green} />
                  </div>
                  <h3 style={{
                    fontFamily: "'Poppins', sans-serif",
                    fontSize: 18,
                    fontWeight: 600,
                    color: colors.dark,
                    margin: '0 0 8px',
                  }}>
                    Booking Request Sent!
                  </h3>
                  <p style={{ color: colors.midGray, fontSize: 14 }}>
                    {expert.display_name} will respond within {expert.response_time_hours} hours.
                  </p>
                  <button
                    onClick={() => router.push('/bookings')}
                    style={{
                      marginTop: 20,
                      padding: '12px 24px',
                      backgroundColor: colors.orange,
                      color: '#fff',
                      border: 'none',
                      borderRadius: 8,
                      fontSize: 14,
                      fontWeight: 600,
                      cursor: 'pointer',
                      width: '100%',
                    }}
                  >
                    View My Bookings
                  </button>
                </div>
              ) : showBookingConfirm ? (
                <div>
                  <h3 style={{
                    fontFamily: "'Poppins', sans-serif",
                    fontSize: 18,
                    fontWeight: 600,
                    color: colors.dark,
                    margin: '0 0 20px',
                  }}>
                    Confirm Booking
                  </h3>

                  <div style={{
                    backgroundColor: colors.light,
                    borderRadius: 8,
                    padding: 16,
                    marginBottom: 20,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span style={{ color: colors.midGray, fontSize: 14 }}>Date</span>
                      <span style={{ fontWeight: 600, color: colors.dark, fontSize: 14 }}>
                        {new Date(selectedDate!).toLocaleDateString('de-DE', { weekday: 'short', day: 'numeric', month: 'short' })}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span style={{ color: colors.midGray, fontSize: 14 }}>Time</span>
                      <span style={{ fontWeight: 600, color: colors.dark, fontSize: 14 }}>{selectedSlot}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span style={{ color: colors.midGray, fontSize: 14 }}>Duration</span>
                      <span style={{ fontWeight: 600, color: colors.dark, fontSize: 14 }}>{estimatedHours}h</span>
                    </div>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      borderTop: `1px solid ${colors.lightGray}`,
                      paddingTop: 8,
                      marginTop: 8,
                    }}>
                      <span style={{ fontWeight: 600, color: colors.dark, fontSize: 14 }}>Total</span>
                      <span style={{ fontWeight: 600, color: colors.orange, fontSize: 16 }}>
                        €{((expert.hourly_rate_cents / 100) * estimatedHours).toFixed(0)}
                      </span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 12 }}>
                    <button
                      onClick={() => setShowBookingConfirm(false)}
                      style={{
                        flex: 1,
                        padding: '12px',
                        backgroundColor: colors.light,
                        color: colors.dark,
                        border: `1px solid ${colors.lightGray}`,
                        borderRadius: 8,
                        fontSize: 14,
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      Back
                    </button>
                    <button
                      onClick={confirmBooking}
                      style={{
                        flex: 1,
                        padding: '12px',
                        backgroundColor: colors.orange,
                        color: '#fff',
                        border: 'none',
                        borderRadius: 8,
                        fontSize: 14,
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      Confirm
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  {/* Price */}
                  <div style={{ marginBottom: 24 }}>
                    <div style={{
                      fontFamily: "'Poppins', sans-serif",
                      fontSize: 28,
                      fontWeight: 600,
                      color: colors.dark,
                    }}>
                      €{(expert.hourly_rate_cents / 100).toFixed(0)}
                      <span style={{ fontSize: 16, fontWeight: 400, color: colors.midGray }}>/hour</span>
                    </div>
                    {expert.available && (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6,
                        fontSize: 13,
                        fontWeight: 600,
                        color: colors.green,
                        marginTop: 8,
                      }}>
                        <span style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          backgroundColor: colors.green,
                        }} />
                        Available now
                      </span>
                    )}
                  </div>

                  {/* Date Selection */}
                  <div style={{ marginBottom: 20 }}>
                    <label style={{
                      display: 'block',
                      fontSize: 13,
                      fontWeight: 600,
                      color: colors.dark,
                      marginBottom: 8,
                    }}>
                      Select Date
                    </label>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      {expert.availability_slots.map(day => (
                        <button
                          key={day.date}
                          onClick={() => { setSelectedDate(day.date); setSelectedSlot(null); }}
                          style={{
                            padding: '10px 14px',
                            backgroundColor: selectedDate === day.date ? colors.orange : '#fff',
                            color: selectedDate === day.date ? '#fff' : colors.dark,
                            border: `1px solid ${selectedDate === day.date ? colors.orange : colors.lightGray}`,
                            borderRadius: 8,
                            fontSize: 13,
                            cursor: 'pointer',
                          }}
                        >
                          {new Date(day.date).toLocaleDateString('de-DE', { weekday: 'short', day: 'numeric' })}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Time Selection */}
                  {selectedDate && (
                    <div style={{ marginBottom: 20 }}>
                      <label style={{
                        display: 'block',
                        fontSize: 13,
                        fontWeight: 600,
                        color: colors.dark,
                        marginBottom: 8,
                      }}>
                        Select Time
                      </label>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                        {expert.availability_slots
                          .find(d => d.date === selectedDate)
                          ?.slots.map(slot => (
                            <button
                              key={slot}
                              onClick={() => setSelectedSlot(slot)}
                              style={{
                                padding: '8px 14px',
                                backgroundColor: selectedSlot === slot ? colors.orange : '#fff',
                                color: selectedSlot === slot ? '#fff' : colors.dark,
                                border: `1px solid ${selectedSlot === slot ? colors.orange : colors.lightGray}`,
                                borderRadius: 6,
                                fontSize: 13,
                                cursor: 'pointer',
                              }}
                            >
                              {slot}
                            </button>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Duration */}
                  <div style={{ marginBottom: 20 }}>
                    <label style={{
                      display: 'block',
                      fontSize: 13,
                      fontWeight: 600,
                      color: colors.dark,
                      marginBottom: 8,
                    }}>
                      Estimated Duration
                    </label>
                    <select
                      value={estimatedHours}
                      onChange={(e) => setEstimatedHours(Number(e.target.value))}
                      style={{
                        width: '100%',
                        padding: '12px',
                        backgroundColor: '#fff',
                        border: `1px solid ${colors.lightGray}`,
                        borderRadius: 8,
                        fontSize: 14,
                        color: colors.dark,
                      }}
                    >
                      <option value={1}>1 hour</option>
                      <option value={2}>2 hours</option>
                      <option value={3}>3 hours</option>
                      <option value={4}>4 hours</option>
                      <option value={8}>Full day (8h)</option>
                    </select>
                  </div>

                  {/* Message */}
                  <div style={{ marginBottom: 24 }}>
                    <label style={{
                      display: 'block',
                      fontSize: 13,
                      fontWeight: 600,
                      color: colors.dark,
                      marginBottom: 8,
                    }}>
                      Message (optional)
                    </label>
                    <textarea
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="Describe what you need help with..."
                      rows={3}
                      style={{
                        width: '100%',
                        padding: '12px',
                        backgroundColor: '#fff',
                        border: `1px solid ${colors.lightGray}`,
                        borderRadius: 8,
                        fontSize: 14,
                        color: colors.dark,
                        resize: 'none',
                      }}
                    />
                  </div>

                  {/* Book Button */}
                  <button
                    onClick={handleBooking}
                    disabled={!selectedDate || !selectedSlot}
                    style={{
                      width: '100%',
                      padding: '14px',
                      backgroundColor: (!selectedDate || !selectedSlot) ? colors.midGray : colors.orange,
                      color: '#fff',
                      border: 'none',
                      borderRadius: 10,
                      fontSize: 15,
                      fontWeight: 600,
                      cursor: (!selectedDate || !selectedSlot) ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 8,
                    }}
                  >
                    <Calendar size={18} />
                    Request Booking
                  </button>

                  <p style={{
                    fontSize: 12,
                    color: colors.midGray,
                    textAlign: 'center',
                    marginTop: 12,
                  }}>
                    You won't be charged until the expert confirms
                  </p>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
