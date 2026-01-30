'use client';

import React, { useState } from 'react';
import { colors } from '@/lib/theme';
import {
  Camera, Save, Plus, X, Star, MapPin, Globe, Mail, Phone
} from 'lucide-react';

export default function ExpertProfile() {
  const [profile, setProfile] = useState({
    displayName: 'Dr. Stefan Weber',
    title: 'Corporate Tax Specialist',
    bio: 'Former Big 4 tax advisor with 15+ years experience in German corporate tax law. Specialist in transfer pricing and international tax structures.',
    hourlyRate: 350,
    location: 'Munich, Germany',
    languages: ['German', 'English'],
    expertiseAreas: ['Corporate Tax', 'Transfer Pricing', 'M&A Tax', 'VAT'],
    email: 'stefan.weber@example.com',
    phone: '+49 89 123 4567',
    website: 'https://weber-tax.de',
    linkedIn: 'linkedin.com/in/stefanweber',
  });

  const [newExpertise, setNewExpertise] = useState('');
  const [newLanguage, setNewLanguage] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaving(false);
  };

  const addExpertise = () => {
    if (newExpertise && !profile.expertiseAreas.includes(newExpertise)) {
      setProfile({
        ...profile,
        expertiseAreas: [...profile.expertiseAreas, newExpertise],
      });
      setNewExpertise('');
    }
  };

  const removeExpertise = (area: string) => {
    setProfile({
      ...profile,
      expertiseAreas: profile.expertiseAreas.filter(a => a !== area),
    });
  };

  const addLanguage = () => {
    if (newLanguage && !profile.languages.includes(newLanguage)) {
      setProfile({
        ...profile,
        languages: [...profile.languages, newLanguage],
      });
      setNewLanguage('');
    }
  };

  const removeLanguage = (lang: string) => {
    setProfile({
      ...profile,
      languages: profile.languages.filter(l => l !== lang),
    });
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      {/* Header Card */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 32,
        marginBottom: 24,
      }}>
        <div style={{ display: 'flex', gap: 24 }}>
          {/* Avatar */}
          <div style={{ position: 'relative' }}>
            <div style={{
              width: 120,
              height: 120,
              borderRadius: '50%',
              backgroundColor: colors.orange + '20',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 48,
              fontWeight: 600,
              color: colors.orange,
            }}>
              {profile.displayName[0]}
            </div>
            <button style={{
              position: 'absolute',
              bottom: 0,
              right: 0,
              width: 36,
              height: 36,
              borderRadius: '50%',
              backgroundColor: colors.orange,
              border: '3px solid white',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Camera size={16} color="white" />
            </button>
          </div>

          {/* Basic Info */}
          <div style={{ flex: 1 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div>
                <label style={labelStyle}>Display Name</label>
                <input
                  type="text"
                  value={profile.displayName}
                  onChange={(e) => setProfile({ ...profile, displayName: e.target.value })}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>Professional Title</label>
                <input
                  type="text"
                  value={profile.title}
                  onChange={(e) => setProfile({ ...profile, title: e.target.value })}
                  style={inputStyle}
                />
              </div>
            </div>

            <div style={{ marginTop: 16 }}>
              <label style={labelStyle}>Bio</label>
              <textarea
                value={profile.bio}
                onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                rows={3}
                style={{ ...inputStyle, resize: 'vertical' }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Pricing & Location */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 32,
        marginBottom: 24,
      }}>
        <h2 style={sectionTitleStyle}>Pricing & Location</h2>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <label style={labelStyle}>Hourly Rate (€)</label>
            <input
              type="number"
              value={profile.hourlyRate}
              onChange={(e) => setProfile({ ...profile, hourlyRate: parseInt(e.target.value) })}
              style={inputStyle}
            />
          </div>
          <div>
            <label style={labelStyle}>Location</label>
            <div style={{ position: 'relative' }}>
              <MapPin size={18} color={colors.midGray} style={{ position: 'absolute', left: 12, top: 12 }} />
              <input
                type="text"
                value={profile.location}
                onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                style={{ ...inputStyle, paddingLeft: 40 }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Expertise Areas */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 32,
        marginBottom: 24,
      }}>
        <h2 style={sectionTitleStyle}>Expertise Areas</h2>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          {profile.expertiseAreas.map((area) => (
            <span
              key={area}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 16px',
                backgroundColor: colors.orange + '15',
                color: colors.orange,
                borderRadius: 20,
                fontSize: 14,
                fontWeight: 500,
              }}
            >
              {area}
              <button
                onClick={() => removeExpertise(area)}
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                  display: 'flex',
                }}
              >
                <X size={16} color={colors.orange} />
              </button>
            </span>
          ))}
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            value={newExpertise}
            onChange={(e) => setNewExpertise(e.target.value)}
            placeholder="Add expertise area..."
            style={{ ...inputStyle, flex: 1 }}
            onKeyPress={(e) => e.key === 'Enter' && addExpertise()}
          />
          <button
            onClick={addExpertise}
            style={{
              padding: '0 20px',
              backgroundColor: colors.orange,
              color: 'white',
              border: 'none',
              borderRadius: 8,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <Plus size={18} /> Add
          </button>
        </div>
      </div>

      {/* Languages */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 32,
        marginBottom: 24,
      }}>
        <h2 style={sectionTitleStyle}>Languages</h2>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          {profile.languages.map((lang) => (
            <span
              key={lang}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 16px',
                backgroundColor: colors.blue + '15',
                color: colors.blue,
                borderRadius: 20,
                fontSize: 14,
                fontWeight: 500,
              }}
            >
              {lang}
              <button
                onClick={() => removeLanguage(lang)}
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                  display: 'flex',
                }}
              >
                <X size={16} color={colors.blue} />
              </button>
            </span>
          ))}
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <select
            value={newLanguage}
            onChange={(e) => setNewLanguage(e.target.value)}
            style={{ ...inputStyle, flex: 1 }}
          >
            <option value="">Select language...</option>
            <option value="German">German</option>
            <option value="English">English</option>
            <option value="French">French</option>
            <option value="Spanish">Spanish</option>
            <option value="Italian">Italian</option>
            <option value="Dutch">Dutch</option>
            <option value="Polish">Polish</option>
          </select>
          <button
            onClick={addLanguage}
            style={{
              padding: '0 20px',
              backgroundColor: colors.blue,
              color: 'white',
              border: 'none',
              borderRadius: 8,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <Plus size={18} /> Add
          </button>
        </div>
      </div>

      {/* Contact Information */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 32,
        marginBottom: 24,
      }}>
        <h2 style={sectionTitleStyle}>Contact Information</h2>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <label style={labelStyle}>Email</label>
            <div style={{ position: 'relative' }}>
              <Mail size={18} color={colors.midGray} style={{ position: 'absolute', left: 12, top: 12 }} />
              <input
                type="email"
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                style={{ ...inputStyle, paddingLeft: 40 }}
              />
            </div>
          </div>
          <div>
            <label style={labelStyle}>Phone</label>
            <div style={{ position: 'relative' }}>
              <Phone size={18} color={colors.midGray} style={{ position: 'absolute', left: 12, top: 12 }} />
              <input
                type="tel"
                value={profile.phone}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                style={{ ...inputStyle, paddingLeft: 40 }}
              />
            </div>
          </div>
          <div>
            <label style={labelStyle}>Website</label>
            <div style={{ position: 'relative' }}>
              <Globe size={18} color={colors.midGray} style={{ position: 'absolute', left: 12, top: 12 }} />
              <input
                type="url"
                value={profile.website}
                onChange={(e) => setProfile({ ...profile, website: e.target.value })}
                style={{ ...inputStyle, paddingLeft: 40 }}
              />
            </div>
          </div>
          <div>
            <label style={labelStyle}>LinkedIn</label>
            <input
              type="text"
              value={profile.linkedIn}
              onChange={(e) => setProfile({ ...profile, linkedIn: e.target.value })}
              style={inputStyle}
            />
          </div>
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
          <Save size={18} />
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 14,
  fontWeight: 500,
  color: colors.dark,
  marginBottom: 8,
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px 16px',
  border: `1px solid ${colors.lightGray}`,
  borderRadius: 8,
  fontSize: 14,
  outline: 'none',
  backgroundColor: 'white',
};

const sectionTitleStyle: React.CSSProperties = {
  fontSize: 18,
  fontWeight: 600,
  color: colors.dark,
  margin: '0 0 20px',
};
