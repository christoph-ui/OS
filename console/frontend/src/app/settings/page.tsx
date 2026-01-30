'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { User, Users, Shield, Building2, CreditCard, ChevronRight } from 'lucide-react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
};

interface UserData {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  permissions: Record<string, boolean>;
}

interface CustomerData {
  id: string;
  company_name: string;
  tier: string;
}

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [customer, setCustomer] = useState<CustomerData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const token = localStorage.getItem('0711_token');
      if (!token) {
        router.push('/login');
        return;
      }

      // Decode JWT to get user info
      const payload = JSON.parse(atob(token.split('.')[1]));

      // Fetch full user data
      const response = await fetch(`http://localhost:4080/api/users/${payload.user_id}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to load user');

      const userData = await response.json();
      setUser(userData);

      // Get customer data if applicable
      if (payload.customer_id) {
        const customerResponse = await fetch(`http://localhost:4080/api/customers/${payload.customer_id}`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (customerResponse.ok) {
          const customerData = await customerResponse.json();
          setCustomer(customerData);
        }
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    } finally {
      setLoading(false);
    }
  };

  const settingsSections = [
    {
      id: 'profile',
      title: 'Profile',
      description: 'Manage your personal information',
      icon: User,
      color: colors.blue,
      path: '/settings/profile',
      available: true,
    },
    {
      id: 'team',
      title: 'Team',
      description: 'Invite and manage team members',
      icon: Users,
      color: colors.green,
      path: '/settings/team',
      available: user?.role === 'customer_admin' || user?.permissions?.['users.invite'],
    },
    {
      id: 'security',
      title: 'Security',
      description: 'Password and authentication settings',
      icon: Shield,
      color: colors.orange,
      path: '/settings/security',
      available: true,
    },
    {
      id: 'company',
      title: 'Company',
      description: 'Organization details and settings',
      icon: Building2,
      color: colors.midGray,
      path: '/settings/company',
      available: user?.role === 'customer_admin',
    },
    {
      id: 'billing',
      title: 'Billing',
      description: 'Subscription and payment information',
      icon: CreditCard,
      color: colors.dark,
      path: '/settings/billing',
      available: user?.permissions?.['billing.view'],
    },
  ];

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: colors.light,
        fontFamily: "'Lora', Georgia, serif",
      }}>
        <div style={{ textAlign: 'center', color: colors.midGray }}>
          <div style={{ fontSize: 32, marginBottom: 16 }}>⟳</div>
          <div>Loading settings...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: colors.light,
      fontFamily: "'Lora', Georgia, serif",
    }}>
      {/* Header */}
      <header style={{
        backgroundColor: '#fff',
        borderBottom: `1.5px solid ${colors.lightGray}`,
        padding: '24px 40px',
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <button
            onClick={() => router.push('/')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 16px',
              marginBottom: 16,
              backgroundColor: colors.lightGray,
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              color: colors.dark,
              cursor: 'pointer',
              fontFamily: "'Lora', Georgia, serif",
            }}
          >
            ← Back to Console
          </button>

          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 32,
            fontWeight: 600,
            margin: '0 0 8px',
            color: colors.dark,
          }}>
            Settings
          </h1>

          {user && customer && (
            <p style={{
              fontSize: 15,
              color: colors.midGray,
              margin: 0,
            }}>
              {user.first_name} {user.last_name} • {customer.company_name}
            </p>
          )}
        </div>
      </header>

      {/* Content */}
      <main style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: '40px',
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
          gap: 24,
        }}>
          {settingsSections
            .filter(section => section.available)
            .map((section) => {
              const Icon = section.icon;

              return (
                <button
                  key={section.id}
                  onClick={() => router.push(section.path)}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 20,
                    padding: 24,
                    backgroundColor: '#fff',
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 16,
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.borderColor = section.color;
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = `0 8px 24px ${section.color}15`;
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.borderColor = colors.lightGray;
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  <div style={{
                    width: 48,
                    height: 48,
                    borderRadius: 12,
                    backgroundColor: `${section.color}15`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    <Icon size={24} color={section.color} />
                  </div>

                  <div style={{ flex: 1 }}>
                    <h3 style={{
                      fontFamily: "'Poppins', Arial, sans-serif",
                      fontSize: 18,
                      fontWeight: 600,
                      margin: '0 0 8px',
                      color: colors.dark,
                    }}>
                      {section.title}
                    </h3>
                    <p style={{
                      fontSize: 14,
                      color: colors.midGray,
                      margin: 0,
                      lineHeight: 1.5,
                    }}>
                      {section.description}
                    </p>
                  </div>

                  <ChevronRight size={20} color={colors.midGray} style={{ flexShrink: 0 }} />
                </button>
              );
            })}
        </div>

        {/* Help Section */}
        <div style={{
          marginTop: 48,
          padding: 24,
          backgroundColor: '#fff',
          border: `1.5px solid ${colors.lightGray}`,
          borderRadius: 16,
        }}>
          <h3 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 18,
            fontWeight: 600,
            margin: '0 0 12px',
            color: colors.dark,
          }}>
            Need Help?
          </h3>
          <p style={{
            fontSize: 14,
            color: colors.midGray,
            margin: 0,
            lineHeight: 1.6,
          }}>
            Contact us at{' '}
            <a href="mailto:support@0711.io" style={{ color: colors.orange, textDecoration: 'none' }}>
              support@0711.io
            </a>
            {' '}or check our{' '}
            <a href="https://docs.0711.io" target="_blank" rel="noopener noreferrer" style={{ color: colors.orange, textDecoration: 'none' }}>
              documentation
            </a>
            .
          </p>
        </div>
      </main>
    </div>
  );
}
