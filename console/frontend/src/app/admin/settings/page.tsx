'use client';

import { useState } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import { Key, Database, Bell, Shield, Save } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  red: '#d75757',
  green: '#788c5d',
};

export default function AdminSettingsPage() {
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <AdminLayout>
      {/* Header */}
      <div style={{ padding: '32px 40px', borderBottom: `1px solid ${colors.lightGray}` }}>
        <h1 style={{ fontSize: 28, fontWeight: 600, margin: 0, color: colors.dark }}>
          Platform Settings
        </h1>
        <p style={{ fontSize: 15, color: colors.midGray, margin: '8px 0 0' }}>
          Configure platform-wide settings and integrations
        </p>
      </div>

      <div style={{ padding: 40, maxWidth: 1000 }}>
        {saved && (
          <div style={{
            padding: 16,
            backgroundColor: `${colors.green}20`,
            border: `2px solid ${colors.green}`,
            borderRadius: 10,
            marginBottom: 24,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}>
            <Shield size={20} color={colors.green} />
            <span style={{ fontSize: 14, color: colors.green, fontWeight: 500 }}>
              Settings saved successfully
            </span>
          </div>
        )}

        {/* API Keys Section */}
        <div style={{
          backgroundColor: colors.light,
          border: `2px solid ${colors.lightGray}`,
          borderRadius: 12,
          padding: 24,
          marginBottom: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <Key size={20} color={colors.red} />
            <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>API Keys</h2>
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
              Stripe Secret Key
            </label>
            <input
              type="password"
              defaultValue="sk_test_***************"
              style={{
                width: '100%',
                padding: 12,
                border: `1.5px solid ${colors.lightGray}`,
                borderRadius: 8,
                fontSize: 14,
                fontFamily: 'monospace',
              }}
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
              OpenAI API Key (Cradle Vision)
            </label>
            <input
              type="password"
              defaultValue="sk-***************"
              style={{
                width: '100%',
                padding: 12,
                border: `1.5px solid ${colors.lightGray}`,
                borderRadius: 8,
                fontSize: 14,
                fontFamily: 'monospace',
              }}
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
              Hugging Face Token (Model Downloads)
            </label>
            <input
              type="password"
              defaultValue="hf_***************"
              style={{
                width: '100%',
                padding: 12,
                border: `1.5px solid ${colors.lightGray}`,
                borderRadius: 8,
                fontSize: 14,
                fontFamily: 'monospace',
              }}
            />
          </div>
        </div>

        {/* Database Configuration */}
        <div style={{
          backgroundColor: colors.light,
          border: `2px solid ${colors.lightGray}`,
          borderRadius: 12,
          padding: 24,
          marginBottom: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <Database size={20} color={colors.red} />
            <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>Database Configuration</h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
                PostgreSQL Host
              </label>
              <input
                type="text"
                defaultValue="localhost"
                disabled
                style={{
                  width: '100%',
                  padding: 12,
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 14,
                  backgroundColor: '#f5f5f5',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
                Port
              </label>
              <input
                type="text"
                defaultValue="4005"
                disabled
                style={{
                  width: '100%',
                  padding: 12,
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 14,
                  backgroundColor: '#f5f5f5',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
                Database
              </label>
              <input
                type="text"
                defaultValue="0711_control"
                disabled
                style={{
                  width: '100%',
                  padding: 12,
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 14,
                  backgroundColor: '#f5f5f5',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
                Status
              </label>
              <input
                type="text"
                defaultValue="✓ Connected"
                disabled
                style={{
                  width: '100%',
                  padding: 12,
                  border: `1.5px solid ${colors.green}`,
                  borderRadius: 8,
                  fontSize: 14,
                  backgroundColor: '#f5f5f5',
                  color: colors.green,
                  fontWeight: 500,
                }}
              />
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div style={{
          backgroundColor: colors.light,
          border: `2px solid ${colors.lightGray}`,
          borderRadius: 12,
          padding: 24,
          marginBottom: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <Bell size={20} color={colors.red} />
            <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>Notifications</h2>
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, cursor: 'pointer' }}>
            <input type="checkbox" defaultChecked style={{ width: 18, height: 18 }} />
            <span style={{ fontSize: 14 }}>Email notifications for new customer signups</span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, cursor: 'pointer' }}>
            <input type="checkbox" defaultChecked style={{ width: 18, height: 18 }} />
            <span style={{ fontSize: 14 }}>Email notifications for deployment failures</span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, cursor: 'pointer' }}>
            <input type="checkbox" style={{ width: 18, height: 18 }} />
            <span style={{ fontSize: 14 }}>Slack notifications for critical alerts</span>
          </label>
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          style={{
            padding: '14px 32px',
            backgroundColor: colors.red,
            color: colors.light,
            border: 'none',
            borderRadius: 10,
            fontSize: 15,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <Save size={18} />
          Save Settings
        </button>
      </div>
    </AdminLayout>
  );
}
