'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import PartnerHeader from '@/components/PartnerHeader';

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

interface Customer {
  id: string;
  company_name: string;
  contact_email: string;
  contact_name?: string;
  contact_phone?: string;
  tier: string;
  status: string;
  onboarding_status: string;
  created_at: string;
  street?: string;
  city?: string;
  postal_code?: string;
  vat_id?: string;
}

interface DeploymentInfo {
  status: string;
  vllm_url?: string;
  lakehouse_url?: string;
  embeddings_url?: string;
  deployed_at?: string;
}

interface UsageStats {
  total_queries: number;
  documents_ingested: number;
  storage_used_mb: number;
  last_activity?: string;
}

export default function CustomerDetailPage() {
  const router = useRouter();
  const params = useParams();
  const customerId = params?.id as string;

  const [customer, setCustomer] = useState<Customer | null>(null);
  const [deployment, setDeployment] = useState<DeploymentInfo | null>(null);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'info' | 'deployment' | 'usage'>('info');
  const [deploymentLoading, setDeploymentLoading] = useState(false);

  useEffect(() => {
    loadCustomer();
    loadDeployment();
    loadUsage();
  }, [customerId]);

  const loadCustomer = async () => {
    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch(`http://localhost:4080/api/partners/customers/${customerId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to load customer');

      const data = await response.json();
      setCustomer(data);
    } catch (error) {
      console.error('Error loading customer:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDeployment = async () => {
    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch(`http://localhost:4080/api/deployments/?customer_id=${customerId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.deployments && data.deployments.length > 0) {
          setDeployment({
            status: data.deployments[0].status,
            deployed_at: data.deployments[0].created_at,
          });
        }
      }
    } catch (error) {
      console.error('Error loading deployment:', error);
    }
  };

  const loadUsage = async () => {
    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch(`http://localhost:4080/api/partners/customers/${customerId}/usage`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setUsage({
          total_queries: data.total_queries || 0,
          documents_ingested: data.documents_ingested || 0,
          storage_used_mb: data.storage_used_mb || 0,
          last_activity: data.last_activity,
        });
      }
    } catch (error) {
      console.error('Error loading usage:', error);
      // Fallback to empty stats
      setUsage({
        total_queries: 0,
        documents_ingested: 0,
        storage_used_mb: 0,
      });
    }
  };

  const startDeployment = async () => {
    if (!customer) return;

    setDeploymentLoading(true);
    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4080/api/deployments/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: `${customer.company_name} Deployment`,
          customer_id: customerId,
          deployment_type: 'managed',
          cloud_provider: 'aws',
          region: 'eu-central-1'
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Deployment konnte nicht gestartet werden');
      }

      const data = await response.json();
      alert(`Deployment erfolgreich gestartet!\nLicense Key: ${data.license_key}`);

      // Reload deployment status
      await loadDeployment();
    } catch (error) {
      console.error('Error starting deployment:', error);
      alert(error instanceof Error ? error.message : 'Fehler beim Deployment-Start');
    } finally {
      setDeploymentLoading(false);
    }
  };

  if (loading) {
    return (
      <div>
        <PartnerHeader title="Kunde" />
        <div style={{ padding: 40, textAlign: 'center', color: colors.midGray }}>
          Lädt...
        </div>
      </div>
    );
  }

  if (!customer) {
    return (
      <div>
        <PartnerHeader title="Kunde nicht gefunden" />
        <div style={{ padding: 40, textAlign: 'center', color: colors.midGray }}>
          <p>Kunde wurde nicht gefunden oder Sie haben keine Berechtigung.</p>
          <button
            onClick={() => router.push('/partner/customers')}
            style={{
              marginTop: 16,
              padding: '10px 20px',
              backgroundColor: colors.orange,
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Zurück zur Liste
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PartnerHeader title={customer.company_name} />

      <div style={{ padding: 40 }}>
        {/* Header Actions */}
        <div style={{
          display: 'flex',
          gap: 12,
          marginBottom: 32,
        }}>
          {customer.onboarding_status === 'not_started' && !deployment && (
            <button
              onClick={() => router.push(`/partner/customers/${customerId}/onboarding`)}
              style={{
                padding: '10px 20px',
                backgroundColor: colors.orange,
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s',
                boxShadow: `0 4px 12px ${colors.orange}40`,
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateY(-1px)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              🚀 Onboarding starten
            </button>
          )}

          {(customer.onboarding_status === 'completed' || deployment) && (
            <button
              onClick={async () => {
                try {
                  const token = localStorage.getItem('0711_token');
                  const response = await fetch(
                    `http://localhost:4080/api/partners/customers/${customerId}/impersonate`,
                    {
                      method: 'POST',  // CRITICAL: Must be POST!
                      headers: {'Authorization': `Bearer ${token}`}
                    }
                  );

                  if (!response.ok) throw new Error('Auth failed');

                  const data = await response.json();
                  const url = `http://localhost:4020/?impersonate_token=${encodeURIComponent(data.token)}&customer=${encodeURIComponent(data.customer_name)}`;
                  window.open(url, '_blank');
                } catch (error) {
                  alert('Fehler: ' + (error as Error).message);
                }
              }}
              style={{
                padding: '10px 20px',
                backgroundColor: colors.green,
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s',
                boxShadow: `0 4px 12px ${colors.green}40`,
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateY(-1px)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              🖥 Console öffnen
            </button>
          )}

          <button
            onClick={() => router.push(`/partner/customers/${customerId}/edit`)}
            style={{
              padding: '10px 20px',
              backgroundColor: colors.blue,
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#5a8bb7'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = colors.blue}
          >
            ✏ Bearbeiten
          </button>
          <button
            onClick={() => router.push('/partner/customers')}
            style={{
              padding: '10px 20px',
              backgroundColor: colors.lightGray,
              color: colors.dark,
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = colors.midGray}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = colors.lightGray}
          >
            ← Zurück
          </button>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          gap: 4,
          marginBottom: 24,
          borderBottom: `2px solid ${colors.lightGray}`,
        }}>
          {[
            { id: 'info', label: 'Informationen' },
            { id: 'deployment', label: 'Deployment' },
            { id: 'usage', label: 'Nutzung' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                padding: '12px 24px',
                backgroundColor: 'transparent',
                border: 'none',
                borderBottom: activeTab === tab.id ? `2px solid ${colors.orange}` : '2px solid transparent',
                color: activeTab === tab.id ? colors.orange : colors.midGray,
                fontSize: 15,
                fontWeight: activeTab === tab.id ? 600 : 400,
                cursor: 'pointer',
                marginBottom: -2,
                transition: 'all 0.2s',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'info' && (
          <div style={{
            backgroundColor: '#fff',
            borderRadius: 16,
            padding: 32,
            border: `1.5px solid ${colors.lightGray}`,
          }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 32,
            }}>
              {/* Left Column */}
              <div>
                <h3 style={{
                  fontFamily: "'Poppins', Arial, sans-serif",
                  fontSize: 16,
                  fontWeight: 600,
                  margin: '0 0 20px',
                  color: colors.dark,
                }}>
                  Firmendaten
                </h3>

                <InfoRow label="Firma" value={customer.company_name} />
                <InfoRow label="USt-IdNr." value={customer.vat_id || '-'} />
                <InfoRow label="Tier" value={
                  <span style={{
                    padding: '4px 12px',
                    backgroundColor: `${colors.blue}15`,
                    borderRadius: 6,
                    fontSize: 12,
                    color: colors.blue,
                    fontWeight: 600,
                  }}>
                    {customer.tier}
                  </span>
                } />
                <InfoRow label="Status" value={
                  <span style={{
                    padding: '4px 12px',
                    backgroundColor: customer.status === 'active' ? `${colors.green}15` : `${colors.midGray}15`,
                    borderRadius: 6,
                    fontSize: 12,
                    color: customer.status === 'active' ? colors.green : colors.midGray,
                    fontWeight: 600,
                  }}>
                    {customer.status}
                  </span>
                } />
              </div>

              {/* Right Column */}
              <div>
                <h3 style={{
                  fontFamily: "'Poppins', Arial, sans-serif",
                  fontSize: 16,
                  fontWeight: 600,
                  margin: '0 0 20px',
                  color: colors.dark,
                }}>
                  Kontaktdaten
                </h3>

                <InfoRow label="Ansprechpartner" value={customer.contact_name || '-'} />
                <InfoRow label="E-Mail" value={customer.contact_email} />
                <InfoRow label="Telefon" value={customer.contact_phone || '-'} />
                <InfoRow label="Erstellt" value={new Date(customer.created_at).toLocaleDateString('de-DE')} />
              </div>
            </div>

            {(customer.street || customer.city) && (
              <>
                <div style={{
                  height: 1,
                  backgroundColor: colors.lightGray,
                  margin: '32px 0',
                }} />

                <div>
                  <h3 style={{
                    fontFamily: "'Poppins', Arial, sans-serif",
                    fontSize: 16,
                    fontWeight: 600,
                    margin: '0 0 20px',
                    color: colors.dark,
                  }}>
                    Adresse
                  </h3>
                  <p style={{ margin: 0, lineHeight: 1.6, color: colors.dark }}>
                    {customer.street && <>{customer.street}<br /></>}
                    {customer.postal_code} {customer.city}
                  </p>
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === 'deployment' && (
          <div style={{
            backgroundColor: '#fff',
            borderRadius: 16,
            padding: 32,
            border: `1.5px solid ${colors.lightGray}`,
          }}>
            {deployment ? (
              <>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  marginBottom: 24,
                }}>
                  <div style={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: deployment.status === 'active' ? colors.green : colors.orange,
                  }} />
                  <span style={{
                    fontSize: 18,
                    fontWeight: 600,
                    color: colors.dark,
                  }}>
                    Status: {deployment.status === 'active' ? 'Aktiv' : 'Inaktiv'}
                  </span>
                </div>

                <div style={{
                  display: 'grid',
                  gap: 16,
                  marginBottom: 24,
                }}>
                  <InfoRow label="Deployed am" value={
                    deployment.deployed_at
                      ? new Date(deployment.deployed_at).toLocaleString('de-DE')
                      : '-'
                  } />
                  <InfoRow label="vLLM Service" value={deployment.vllm_url || 'http://localhost:9200'} />
                  <InfoRow label="Lakehouse Service" value={deployment.lakehouse_url || 'Internal (Docker Network)'} />
                  <InfoRow label="Embeddings Service" value={deployment.embeddings_url || 'http://localhost:9201'} />
                </div>

                {/* Console Access */}
                <div style={{
                  padding: 20,
                  backgroundColor: `${colors.green}15`,
                  borderRadius: 12,
                  border: `2px solid ${colors.green}`,
                }}>
                  <h4 style={{
                    fontSize: 16,
                    fontWeight: 600,
                    margin: '0 0 12px',
                    color: colors.dark,
                  }}>
                    🎯 Customer Console Access
                  </h4>
                  <p style={{
                    fontSize: 13,
                    color: colors.midGray,
                    margin: '0 0 16px',
                    lineHeight: 1.6,
                  }}>
                    Für Support & Demo: Sie können sich temporär als Kunde anmelden.
                    <br />
                    ⚠️ Alle Aktionen werden im Audit-Log protokolliert.
                  </p>
                  <button
                    onClick={async () => {
                      try {
                        const token = localStorage.getItem('0711_token');
                        const response = await fetch(
                          `http://localhost:4080/api/partners/customers/${customerId}/impersonate`,
                          {
                            method: 'POST',  // CRITICAL: Must be POST!
                            headers: {'Authorization': `Bearer ${token}`}
                          }
                        );

                        if (!response.ok) {
                          throw new Error('Impersonate failed');
                        }

                        const data = await response.json();

                        // Open Console with token in URL (robust, no postMessage timing issues)
                        const consoleUrl = `http://localhost:4020/?impersonate_token=${encodeURIComponent(data.token)}&customer=${encodeURIComponent(data.customer_name)}`;
                        window.open(consoleUrl, '_blank');

                        alert(`✓ Console wird geöffnet.\n\nSie sind angemeldet als: ${data.customer_name}\nToken gültig für: 1 Stunde\n\n⚠️ Alle Aktionen werden protokolliert.`);
                      } catch (error) {
                        alert('Fehler beim Anmelden: ' + (error as Error).message);
                      }
                    }}
                    style={{
                      padding: '12px 24px',
                      backgroundColor: colors.green,
                      color: '#fff',
                      border: 'none',
                      borderRadius: 10,
                      fontSize: 15,
                      fontWeight: 600,
                      cursor: 'pointer',
                      boxShadow: `0 4px 12px ${colors.green}40`,
                    }}
                  >
                    🔓 Als Kunde anmelden (Impersonate)
                  </button>
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: 40, color: colors.midGray }}>
                <p style={{ margin: '0 0 16px' }}>Noch kein Deployment vorhanden</p>
                <button
                  onClick={startDeployment}
                  disabled={deploymentLoading}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: deploymentLoading ? colors.midGray : colors.orange,
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: deploymentLoading ? 'not-allowed' : 'pointer',
                    opacity: deploymentLoading ? 0.7 : 1,
                  }}
                >
                  {deploymentLoading ? 'Wird gestartet...' : 'Deployment starten'}
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'usage' && (
          <div style={{
            backgroundColor: '#fff',
            borderRadius: 16,
            padding: 32,
            border: `1.5px solid ${colors.lightGray}`,
          }}>
            {usage && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: 24,
              }}>
                <StatCard
                  label="Gesamt Queries"
                  value={usage.total_queries.toLocaleString()}
                  icon="💬"
                  color={colors.blue}
                />
                <StatCard
                  label="Dokumente"
                  value={usage.documents_ingested.toLocaleString()}
                  icon="📄"
                  color={colors.green}
                />
                <StatCard
                  label="Storage"
                  value={`${usage.storage_used_mb.toLocaleString()} MB`}
                  icon="💾"
                  color={colors.orange}
                />
                <StatCard
                  label="Letzte Aktivität"
                  value={usage.last_activity ? new Date(usage.last_activity).toLocaleDateString('de-DE') : '-'}
                  icon="⏱"
                  color={colors.midGray}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      padding: '12px 0',
      borderBottom: `1px solid ${colors.lightGray}`,
    }}>
      <span style={{ color: colors.midGray, fontSize: 14 }}>{label}</span>
      <span style={{ color: colors.dark, fontSize: 14, fontWeight: 500 }}>{value}</span>
    </div>
  );
}

function StatCard({ label, value, icon, color }: { label: string; value: string; icon: string; color: string }) {
  return (
    <div style={{
      padding: 20,
      backgroundColor: colors.light,
      borderRadius: 12,
      border: `1px solid ${colors.lightGray}`,
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 8,
      }}>
        <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px', color: colors.midGray, fontWeight: 600 }}>
          {label}
        </span>
        <span style={{ fontSize: 20 }}>{icon}</span>
      </div>
      <p style={{
        margin: 0,
        fontSize: 24,
        fontWeight: 600,
        color: color,
        fontFamily: "'Poppins', Arial, sans-serif",
      }}>
        {value}
      </p>
    </div>
  );
}
