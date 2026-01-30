'use client';

import React, { useState } from 'react';
import { colors } from '@/lib/theme';
import {
  Clock, Calendar, Plus, X, Check, ChevronLeft, ChevronRight
} from 'lucide-react';

interface TimeSlot {
  start: string;
  end: string;
}

interface DayAvailability {
  enabled: boolean;
  slots: TimeSlot[];
}

type WeekAvailability = {
  [key: string]: DayAvailability;
};

export default function ExpertAvailability() {
  const [availability, setAvailability] = useState<WeekAvailability>({
    monday: { enabled: true, slots: [{ start: '09:00', end: '12:00' }, { start: '14:00', end: '18:00' }] },
    tuesday: { enabled: true, slots: [{ start: '09:00', end: '12:00' }, { start: '14:00', end: '18:00' }] },
    wednesday: { enabled: true, slots: [{ start: '09:00', end: '12:00' }, { start: '14:00', end: '18:00' }] },
    thursday: { enabled: true, slots: [{ start: '09:00', end: '12:00' }, { start: '14:00', end: '18:00' }] },
    friday: { enabled: true, slots: [{ start: '09:00', end: '12:00' }, { start: '14:00', end: '17:00' }] },
    saturday: { enabled: false, slots: [] },
    sunday: { enabled: false, slots: [] },
  });

  const [currentWeek, setCurrentWeek] = useState(new Date());
  const [blockedDates, setBlockedDates] = useState<string[]>(['2026-02-05', '2026-02-06']);
  const [saving, setSaving] = useState(false);

  const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
  const dayLabels: { [key: string]: string } = {
    monday: 'Monday',
    tuesday: 'Tuesday',
    wednesday: 'Wednesday',
    thursday: 'Thursday',
    friday: 'Friday',
    saturday: 'Saturday',
    sunday: 'Sunday',
  };

  const toggleDay = (day: string) => {
    setAvailability({
      ...availability,
      [day]: {
        ...availability[day],
        enabled: !availability[day].enabled,
        slots: !availability[day].enabled ? [{ start: '09:00', end: '17:00' }] : [],
      },
    });
  };

  const addSlot = (day: string) => {
    const lastSlot = availability[day].slots[availability[day].slots.length - 1];
    const newStart = lastSlot ? lastSlot.end : '09:00';
    setAvailability({
      ...availability,
      [day]: {
        ...availability[day],
        slots: [...availability[day].slots, { start: newStart, end: '18:00' }],
      },
    });
  };

  const removeSlot = (day: string, index: number) => {
    setAvailability({
      ...availability,
      [day]: {
        ...availability[day],
        slots: availability[day].slots.filter((_, i) => i !== index),
      },
    });
  };

  const updateSlot = (day: string, index: number, field: 'start' | 'end', value: string) => {
    const newSlots = [...availability[day].slots];
    newSlots[index] = { ...newSlots[index], [field]: value };
    setAvailability({
      ...availability,
      [day]: {
        ...availability[day],
        slots: newSlots,
      },
    });
  };

  const handleSave = async () => {
    setSaving(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaving(false);
  };

  // Generate week dates
  const getWeekDates = () => {
    const startOfWeek = new Date(currentWeek);
    startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay() + 1);
    
    return Array.from({ length: 7 }, (_, i) => {
      const date = new Date(startOfWeek);
      date.setDate(date.getDate() + i);
      return date;
    });
  };

  const weekDates = getWeekDates();

  const toggleBlockedDate = (dateStr: string) => {
    if (blockedDates.includes(dateStr)) {
      setBlockedDates(blockedDates.filter(d => d !== dateStr));
    } else {
      setBlockedDates([...blockedDates, dateStr]);
    }
  };

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      {/* Weekly Schedule */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 32,
        marginBottom: 24,
      }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: colors.dark, margin: '0 0 8px' }}>
          Weekly Schedule
        </h2>
        <p style={{ fontSize: 14, color: colors.midGray, margin: '0 0 24px' }}>
          Set your regular working hours. Customers can book during these times.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {days.map((day) => (
            <div
              key={day}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 16,
                padding: 16,
                backgroundColor: availability[day].enabled ? colors.light : 'transparent',
                borderRadius: 12,
                border: `1px solid ${availability[day].enabled ? colors.lightGray : 'transparent'}`,
              }}
            >
              {/* Day toggle */}
              <div style={{ width: 120, display: 'flex', alignItems: 'center', gap: 12 }}>
                <button
                  onClick={() => toggleDay(day)}
                  style={{
                    width: 44,
                    height: 24,
                    borderRadius: 12,
                    backgroundColor: availability[day].enabled ? colors.orange : colors.lightGray,
                    border: 'none',
                    cursor: 'pointer',
                    position: 'relative',
                    transition: 'background-color 0.2s',
                  }}
                >
                  <div style={{
                    width: 20,
                    height: 20,
                    borderRadius: '50%',
                    backgroundColor: 'white',
                    position: 'absolute',
                    top: 2,
                    left: availability[day].enabled ? 22 : 2,
                    transition: 'left 0.2s',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                  }} />
                </button>
                <span style={{
                  fontSize: 14,
                  fontWeight: 500,
                  color: availability[day].enabled ? colors.dark : colors.midGray,
                }}>
                  {dayLabels[day]}
                </span>
              </div>

              {/* Time slots */}
              <div style={{ flex: 1 }}>
                {availability[day].enabled ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {availability[day].slots.map((slot, index) => (
                      <div key={index} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <input
                          type="time"
                          value={slot.start}
                          onChange={(e) => updateSlot(day, index, 'start', e.target.value)}
                          style={timeInputStyle}
                        />
                        <span style={{ color: colors.midGray }}>to</span>
                        <input
                          type="time"
                          value={slot.end}
                          onChange={(e) => updateSlot(day, index, 'end', e.target.value)}
                          style={timeInputStyle}
                        />
                        {availability[day].slots.length > 1 && (
                          <button
                            onClick={() => removeSlot(day, index)}
                            style={{
                              width: 28,
                              height: 28,
                              borderRadius: 6,
                              backgroundColor: colors.red + '15',
                              border: 'none',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: colors.red,
                            }}
                          >
                            <X size={14} />
                          </button>
                        )}
                      </div>
                    ))}
                    <button
                      onClick={() => addSlot(day)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '6px 12px',
                        backgroundColor: 'transparent',
                        border: `1px dashed ${colors.lightGray}`,
                        borderRadius: 6,
                        color: colors.midGray,
                        fontSize: 13,
                        cursor: 'pointer',
                        width: 'fit-content',
                      }}
                    >
                      <Plus size={14} /> Add time slot
                    </button>
                  </div>
                ) : (
                  <span style={{ fontSize: 14, color: colors.midGray }}>Unavailable</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Calendar Block Off */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 32,
        marginBottom: 24,
      }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: colors.dark, margin: '0 0 8px' }}>
          Block Specific Dates
        </h2>
        <p style={{ fontSize: 14, color: colors.midGray, margin: '0 0 24px' }}>
          Click on dates to block them. Blocked dates won't be available for booking.
        </p>

        {/* Week Navigation */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}>
          <button
            onClick={() => {
              const prev = new Date(currentWeek);
              prev.setDate(prev.getDate() - 7);
              setCurrentWeek(prev);
            }}
            style={navButtonStyle}
          >
            <ChevronLeft size={20} />
          </button>
          <span style={{ fontSize: 16, fontWeight: 600, color: colors.dark }}>
            {weekDates[0].toLocaleDateString('de-DE', { month: 'long', year: 'numeric' })}
          </span>
          <button
            onClick={() => {
              const next = new Date(currentWeek);
              next.setDate(next.getDate() + 7);
              setCurrentWeek(next);
            }}
            style={navButtonStyle}
          >
            <ChevronRight size={20} />
          </button>
        </div>

        {/* Week Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 8 }}>
          {weekDates.map((date, i) => {
            const dateStr = date.toISOString().split('T')[0];
            const isBlocked = blockedDates.includes(dateStr);
            const isToday = date.toDateString() === new Date().toDateString();
            const isPast = date < new Date(new Date().setHours(0, 0, 0, 0));
            const dayKey = days[i];
            const isAvailable = availability[dayKey]?.enabled && !isBlocked && !isPast;

            return (
              <button
                key={dateStr}
                onClick={() => !isPast && toggleBlockedDate(dateStr)}
                disabled={isPast}
                style={{
                  padding: 16,
                  backgroundColor: isBlocked ? colors.red + '15' : isAvailable ? colors.green + '10' : colors.light,
                  border: isToday ? `2px solid ${colors.orange}` : `1px solid ${colors.lightGray}`,
                  borderRadius: 10,
                  cursor: isPast ? 'not-allowed' : 'pointer',
                  opacity: isPast ? 0.5 : 1,
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                  {dayLabels[dayKey].slice(0, 3)}
                </div>
                <div style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color: isBlocked ? colors.red : colors.dark,
                }}>
                  {date.getDate()}
                </div>
                {isBlocked && (
                  <div style={{ fontSize: 10, color: colors.red, marginTop: 4 }}>
                    Blocked
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Save Button */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            padding: '14px 32px',
            backgroundColor: colors.orange,
            color: 'white',
            border: 'none',
            borderRadius: 10,
            fontSize: 15,
            fontWeight: 600,
            cursor: saving ? 'not-allowed' : 'pointer',
            opacity: saving ? 0.7 : 1,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <Check size={18} />
          {saving ? 'Saving...' : 'Save Availability'}
        </button>
      </div>
    </div>
  );
}

const timeInputStyle: React.CSSProperties = {
  padding: '8px 12px',
  border: `1px solid ${colors.lightGray}`,
  borderRadius: 6,
  fontSize: 14,
  backgroundColor: 'white',
  outline: 'none',
};

const navButtonStyle: React.CSSProperties = {
  width: 36,
  height: 36,
  borderRadius: 8,
  backgroundColor: 'transparent',
  border: `1px solid ${colors.lightGray}`,
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: colors.dark,
};
