'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { CreditCard, Download, Calendar, CheckCircle, XCircle } from 'lucide-react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
  red: '#d75757',
};

interface Subscription {
  id: string;
  tier: string;
  status: string;
  billing_cycle: string;
  next_billing_date: string;
  amount: number;
}

interface Invoice {
  id: string;
  invoice_number: string;
  amount: number;
  status: string;
  issue_date: string;
  due_date: string;
  pdf_url: string;
}

export default function BillingSettingsPage() {
  const router = useRouter();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadBillingData();
  }, []);

  const loadBillingData = async () => {
    try {
      const token = localStorage.getItem('0711_token');
      if (!token) {
        router.push('/login');
        return;
      }

      // Load subscription
      const subResponse = await fetch('http://localhost:4080/api/subscriptions/current', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (subResponse.ok) {
        const subData = await subResponse.json();
        setSubscription(subData);
      }

      // Load invoices
      const invoicesResponse = await fetch('http://localhost:4080/api/invoices/', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (invoicesResponse.ok) {
        const invoicesData = await invoicesResponse.json();
        setInvoices(invoicesData.invoices || []);
      }
    } catch (error) {
      console.error('Error loading billing data:', error);
      setError('Failed to load billing information');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const config = {
      active: { label: 'Active', color: colors.green, icon: CheckCircle },
      past_due: { label: 'Past Due', color: colors.red, icon: XCircle },
      cancelled: { label: 'Cancelled', color: colors.midGray, icon: XCircle },
      paid: { label: 'Paid', color: colors.green, icon: CheckCircle },
      pending: { label: 'Pending', color: colors.orange, icon: Calendar },
      overdue: { label: 'Overdue', color: colors.red, icon: XCircle },
    }[status] || { label: status, color: colors.midGray, icon: Calendar };

    const Icon = config.icon;

    return (
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '4px 12px',
        backgroundColor: `${config.color}15`,
        color: config.color,
        borderRadius: 6,
        fontSize: 12,
        fontWeight: 600,
      }}>
        <Icon size={14} />
        {config.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: colors.light,
      }}>
        <div style={{ textAlign: 'center', color: colors.midGray }}>
          <div style={{ fontSize: 32, marginBottom: 16 }}>⟳</div>
          <div>Loading billing information...</div>
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
            onClick={() => router.push('/settings')}
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
            ← Back to Settings
          </button>

          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 32,
            fontWeight: 600,
            margin: '0 0 8px',
            color: colors.dark,
          }}>
            Billing & Subscription
          </h1>

          <p style={{
            fontSize: 15,
            color: colors.midGray,
            margin: 0,
          }}>
            Manage your subscription and view invoices
          </p>
        </div>
      </header>

      {/* Content */}
      <main style={{ maxWidth: 1200, margin: '0 auto', padding: 40 }}>
        {error && (
          <div style={{
            padding: '12px 16px',
            marginBottom: 24,
            backgroundColor: '#fee',
            border: '1px solid #fcc',
            borderRadius: 8,
            color: '#c00',
            fontSize: 14,
          }}>
            {error}
          </div>
        )}

        {/* Current Subscription */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          padding: 32,
          border: `1.5px solid ${colors.lightGray}`,
          marginBottom: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
            <div style={{
              width: 48,
              height: 48,
              borderRadius: 12,
              backgroundColor: `${colors.blue}15`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <CreditCard size={24} color={colors.blue} />
            </div>
            <div>
              <h3 style={{
                fontFamily: "'Poppins', Arial, sans-serif",
                fontSize: 18,
                fontWeight: 600,
                margin: 0,
                color: colors.dark,
              }}>
                Current Subscription
              </h3>
              <p style={{
                fontSize: 14,
                color: colors.midGray,
                margin: '4px 0 0',
              }}>
                {subscription ? `${subscription.tier.replace(/\b\w/g, l => l.toUpperCase())} Plan` : 'No active subscription'}
              </p>
            </div>
          </div>

          {subscription ? (
            <div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: 24,
                padding: 24,
                backgroundColor: colors.light,
                borderRadius: 12,
                marginBottom: 24,
              }}>
                <div>
                  <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                    Status
                  </div>
                  <div>
                    {getStatusBadge(subscription.status)}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                    Billing Cycle
                  </div>
                  <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                    {subscription.billing_cycle === 'monthly' ? 'Monthly' : 'Yearly'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>
                    Next Billing
                  </div>
                  <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                    {new Date(subscription.next_billing_date).toLocaleDateString()}
                  </div>
                </div>
              </div>

              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: 20,
                backgroundColor: `${colors.orange}10`,
                borderRadius: 12,
              }}>
                <div>
                  <div style={{ fontSize: 13, color: colors.midGray, marginBottom: 4 }}>
                    Amount
                  </div>
                  <div style={{
                    fontFamily: "'Poppins', Arial, sans-serif",
                    fontSize: 28,
                    fontWeight: 600,
                    color: colors.dark,
                  }}>
                    €{subscription.amount.toLocaleString()}
                    <span style={{ fontSize: 16, fontWeight: 400, color: colors.midGray }}>
                      /{subscription.billing_cycle === 'monthly' ? 'mo' : 'yr'}
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => window.open('https://billing.stripe.com/p/login/test', '_blank')}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: colors.orange,
                    color: '#fff',
                    border: 'none',
                    borderRadius: 10,
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontFamily: "'Poppins', Arial, sans-serif",
                    boxShadow: `0 4px 12px ${colors.orange}40`,
                  }}
                >
                  Manage Subscription
                </button>
              </div>
            </div>
          ) : (
            <div style={{
              padding: 32,
              textAlign: 'center',
              backgroundColor: colors.light,
              borderRadius: 12,
            }}>
              <p style={{ fontSize: 15, color: colors.midGray, margin: '0 0 16px' }}>
                No active subscription
              </p>
              <button
                onClick={() => window.open('http://localhost:4000/pricing', '_blank')}
                style={{
                  padding: '12px 24px',
                  backgroundColor: colors.orange,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 10,
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontFamily: "'Poppins', Arial, sans-serif",
                }}
              >
                View Plans
              </button>
            </div>
          )}
        </div>

        {/* Invoices */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: 16,
          padding: 32,
          border: `1.5px solid ${colors.lightGray}`,
        }}>
          <h3 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 18,
            fontWeight: 600,
            margin: '0 0 24px',
            color: colors.dark,
          }}>
            Invoices
          </h3>

          {invoices.length > 0 ? (
            <div style={{
              border: `1px solid ${colors.lightGray}`,
              borderRadius: 12,
              overflow: 'hidden',
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: colors.light }}>
                    <th style={{ padding: '16px 20px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                      Invoice
                    </th>
                    <th style={{ padding: '16px 20px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                      Issue Date
                    </th>
                    <th style={{ padding: '16px 20px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                      Due Date
                    </th>
                    <th style={{ padding: '16px 20px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                      Amount
                    </th>
                    <th style={{ padding: '16px 20px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                      Status
                    </th>
                    <th style={{ padding: '16px 20px', textAlign: 'right', fontSize: 13, fontWeight: 600, color: colors.dark }}>
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((invoice, idx) => (
                    <tr
                      key={invoice.id}
                      style={{
                        borderBottom: idx < invoices.length - 1 ? `1px solid ${colors.lightGray}` : 'none',
                      }}
                    >
                      <td style={{ padding: '16px 20px' }}>
                        <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                          {invoice.invoice_number}
                        </div>
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        <div style={{ fontSize: 13, color: colors.midGray }}>
                          {new Date(invoice.issue_date).toLocaleDateString()}
                        </div>
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        <div style={{ fontSize: 13, color: colors.midGray }}>
                          {new Date(invoice.due_date).toLocaleDateString()}
                        </div>
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        <div style={{ fontSize: 14, color: colors.dark, fontWeight: 500 }}>
                          €{invoice.amount.toLocaleString()}
                        </div>
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        {getStatusBadge(invoice.status)}
                      </td>
                      <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                        <button
                          onClick={() => window.open(invoice.pdf_url, '_blank')}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 6,
                            padding: '8px 16px',
                            backgroundColor: colors.lightGray,
                            border: 'none',
                            borderRadius: 6,
                            fontSize: 13,
                            cursor: 'pointer',
                            fontFamily: "'Poppins', Arial, sans-serif",
                          }}
                        >
                          <Download size={14} />
                          PDF
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{
              padding: 40,
              textAlign: 'center',
              backgroundColor: colors.light,
              borderRadius: 12,
            }}>
              <svg
                style={{
                  width: 48,
                  height: 48,
                  color: colors.midGray,
                  margin: '0 auto 16px',
                }}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
              <p style={{ fontSize: 15, color: colors.midGray, margin: 0 }}>
                No invoices yet
              </p>
            </div>
          )}
        </div>

        {/* Payment Method */}
        <div style={{
          marginTop: 24,
          backgroundColor: '#fff',
          borderRadius: 16,
          padding: 32,
          border: `1.5px solid ${colors.lightGray}`,
        }}>
          <h3 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 18,
            fontWeight: 600,
            margin: '0 0 16px',
            color: colors.dark,
          }}>
            Payment Method
          </h3>

          <div style={{
            padding: 20,
            backgroundColor: colors.light,
            borderRadius: 12,
            fontSize: 14,
            color: colors.midGray,
          }}>
            Payment methods are managed through Stripe. Click "Manage Subscription" above to update your payment details.
          </div>
        </div>
      </main>
    </div>
  );
}
