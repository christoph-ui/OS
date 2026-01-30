'use client';

import { useState, useEffect } from 'react';
import { Search, Grid, List, Download, Star, Check, Zap, Database, Share2, Brain } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
};

interface Connector {
  id: string;
  name: string;
  display_name: string;
  short_description: string;
  icon: string;
  category: string;
  pricing_model: string;
  price_per_month_cents: number;
  rating: number;
  install_count: number;
  verified: boolean;
  featured: boolean;
}

interface Category {
  id: string;
  name: string;
  display_name: string;
  icon: string;
  connector_count: number;
}

const categoryIcons: Record<string, any> = {
  data_sources: Database,
  ai_models: Brain,
  outputs: Share2,
};

export default function ConnectorCatalog() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [installedIds, setInstalledIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [installing, setInstalling] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [selectedCategory, searchQuery]);

  const loadData = async () => {
    try {
      // Load categories
      const catRes = await fetch('http://localhost:4080/api/connectors/categories');
      const catData = await catRes.json();
      setCategories(catData.categories || []);

      // Load connectors
      let url = 'http://localhost:4080/api/connectors?';
      if (searchQuery) url += `search=${encodeURIComponent(searchQuery)}&`;
      if (selectedCategory) url += `category=${selectedCategory}&`;

      const conRes = await fetch(url);
      const conData = await conRes.json();
      setConnectors(conData.connectors || []);

      // Load installed
      const token = localStorage.getItem('0711_token');
      if (token) {
        const instRes = await fetch('http://localhost:4080/api/connectors/installed', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const instData = await instRes.json();
        setInstalledIds(new Set((instData.connections || []).map((c: any) => c.connector_id)));
      }
    } catch (error) {
      console.error('Error loading connectors:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInstall = async (connectorId: string) => {
    setInstalling(connectorId);
    try {
      const token = localStorage.getItem('0711_token');
      const res = await fetch(`http://localhost:4080/api/connectors/${connectorId}/install`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        setInstalledIds(prev => new Set([...prev, connectorId]));
      }
    } catch (error) {
      console.error('Install failed:', error);
    } finally {
      setInstalling(null);
    }
  };

  const formatPrice = (connector: Connector) => {
    if (connector.pricing_model === 'free') return 'Free';
    if (connector.price_per_month_cents) {
      return `€${(connector.price_per_month_cents / 100).toFixed(0)}/mo`;
    }
    return 'Custom';
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: colors.light }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#fff',
        borderBottom: `1px solid ${colors.lightGray}`,
        padding: '24px 40px',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
            <div>
              <h1 style={{
                fontFamily: "'Poppins', sans-serif",
                fontSize: 28,
                fontWeight: 600,
                color: colors.dark,
                margin: 0,
              }}>
                Connector Catalog
              </h1>
              <p style={{ color: colors.midGray, margin: '4px 0 0', fontSize: 14 }}>
                Connect data sources, AI models, and output channels
              </p>
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => setViewMode('grid')}
                style={{
                  padding: 8,
                  backgroundColor: viewMode === 'grid' ? colors.dark : 'transparent',
                  color: viewMode === 'grid' ? '#fff' : colors.midGray,
                  border: `1px solid ${colors.lightGray}`,
                  borderRadius: 6,
                  cursor: 'pointer',
                }}
              >
                <Grid size={18} />
              </button>
              <button
                onClick={() => setViewMode('list')}
                style={{
                  padding: 8,
                  backgroundColor: viewMode === 'list' ? colors.dark : 'transparent',
                  color: viewMode === 'list' ? '#fff' : colors.midGray,
                  border: `1px solid ${colors.lightGray}`,
                  borderRadius: 6,
                  cursor: 'pointer',
                }}
              >
                <List size={18} />
              </button>
            </div>
          </div>

          {/* Search */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            backgroundColor: colors.light,
            border: `1px solid ${colors.lightGray}`,
            borderRadius: 10,
            padding: '12px 16px',
            maxWidth: 500,
          }}>
            <Search size={18} color={colors.midGray} />
            <input
              type="text"
              placeholder="Search connectors..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                flex: 1,
                border: 'none',
                backgroundColor: 'transparent',
                fontSize: 15,
                outline: 'none',
                color: colors.dark,
              }}
            />
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '32px 40px' }}>
        <div style={{ display: 'flex', gap: 32 }}>
          {/* Sidebar - Categories */}
          <div style={{ width: 240, flexShrink: 0 }}>
            <div style={{
              backgroundColor: '#fff',
              borderRadius: 12,
              border: `1px solid ${colors.lightGray}`,
              overflow: 'hidden',
              position: 'sticky',
              top: 120,
            }}>
              <div style={{ padding: '16px 20px', borderBottom: `1px solid ${colors.lightGray}` }}>
                <h3 style={{
                  fontFamily: "'Poppins', sans-serif",
                  fontSize: 13,
                  fontWeight: 600,
                  color: colors.midGray,
                  margin: 0,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}>
                  Categories
                </h3>
              </div>

              <button
                onClick={() => setSelectedCategory(null)}
                style={{
                  width: '100%',
                  padding: '14px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  backgroundColor: selectedCategory === null ? `${colors.orange}10` : 'transparent',
                  border: 'none',
                  borderLeft: `3px solid ${selectedCategory === null ? colors.orange : 'transparent'}`,
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s',
                }}
              >
                <Zap size={18} color={selectedCategory === null ? colors.orange : colors.midGray} />
                <span style={{
                  fontSize: 14,
                  color: selectedCategory === null ? colors.orange : colors.dark,
                  fontWeight: selectedCategory === null ? 600 : 400,
                }}>
                  All Connectors
                </span>
              </button>

              {categories.map(cat => {
                const Icon = categoryIcons[cat.id] || Database;
                const isSelected = selectedCategory === cat.id;
                return (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedCategory(cat.id)}
                    style={{
                      width: '100%',
                      padding: '14px 20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      backgroundColor: isSelected ? `${colors.orange}10` : 'transparent',
                      border: 'none',
                      borderLeft: `3px solid ${isSelected ? colors.orange : 'transparent'}`,
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.15s',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <Icon size={18} color={isSelected ? colors.orange : colors.midGray} />
                      <span style={{
                        fontSize: 14,
                        color: isSelected ? colors.orange : colors.dark,
                        fontWeight: isSelected ? 600 : 400,
                      }}>
                        {cat.display_name}
                      </span>
                    </div>
                    <span style={{
                      fontSize: 12,
                      color: colors.midGray,
                      backgroundColor: colors.light,
                      padding: '2px 8px',
                      borderRadius: 10,
                    }}>
                      {cat.connector_count}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Main Content - Connectors */}
          <div style={{ flex: 1 }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: 60, color: colors.midGray }}>
                Loading connectors...
              </div>
            ) : connectors.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 60, color: colors.midGray }}>
                No connectors found
              </div>
            ) : viewMode === 'grid' ? (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                gap: 20,
              }}>
                {connectors.map(connector => (
                  <ConnectorCard
                    key={connector.id}
                    connector={connector}
                    isInstalled={installedIds.has(connector.id)}
                    isInstalling={installing === connector.id}
                    onInstall={() => handleInstall(connector.id)}
                    formatPrice={formatPrice}
                  />
                ))}
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {connectors.map(connector => (
                  <ConnectorRow
                    key={connector.id}
                    connector={connector}
                    isInstalled={installedIds.has(connector.id)}
                    isInstalling={installing === connector.id}
                    onInstall={() => handleInstall(connector.id)}
                    formatPrice={formatPrice}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Grid Card Component
function ConnectorCard({
  connector,
  isInstalled,
  isInstalling,
  onInstall,
  formatPrice,
}: {
  connector: Connector;
  isInstalled: boolean;
  isInstalling: boolean;
  onInstall: () => void;
  formatPrice: (c: Connector) => string;
}) {
  return (
    <div style={{
      backgroundColor: '#fff',
      borderRadius: 12,
      border: `1px solid ${colors.lightGray}`,
      overflow: 'hidden',
      transition: 'all 0.2s',
      cursor: 'pointer',
    }}
    onMouseOver={(e) => {
      e.currentTarget.style.borderColor = colors.orange + '60';
      e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.08)';
    }}
    onMouseOut={(e) => {
      e.currentTarget.style.borderColor = colors.lightGray;
      e.currentTarget.style.boxShadow = 'none';
    }}
    >
      <div style={{ padding: 24 }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 16 }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 10,
            backgroundColor: colors.dark + '08',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 20,
          }}>
            {connector.icon || '📦'}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h3 style={{
                fontFamily: "'Poppins', sans-serif",
                fontSize: 16,
                fontWeight: 600,
                color: colors.dark,
                margin: 0,
              }}>
                {connector.display_name}
              </h3>
              {connector.verified && (
                <span style={{
                  backgroundColor: colors.blue + '20',
                  color: colors.blue,
                  fontSize: 10,
                  fontWeight: 600,
                  padding: '2px 6px',
                  borderRadius: 4,
                }}>
                  VERIFIED
                </span>
              )}
            </div>
            <p style={{
              fontSize: 13,
              color: colors.midGray,
              margin: '4px 0 0',
              lineHeight: 1.4,
            }}>
              {connector.short_description}
            </p>
          </div>
        </div>

        {/* Stats */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          marginBottom: 20,
          paddingBottom: 16,
          borderBottom: `1px solid ${colors.lightGray}`,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Star size={14} color={colors.midGray} fill={colors.midGray} />
            <span style={{ fontSize: 13, color: colors.midGray }}>
              {connector.rating?.toFixed(1) || '5.0'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Download size={14} color={colors.midGray} />
            <span style={{ fontSize: 13, color: colors.midGray }}>
              {connector.install_count?.toLocaleString() || '0'}
            </span>
          </div>
          <span style={{
            fontSize: 12,
            color: colors.midGray,
            backgroundColor: colors.light,
            padding: '2px 8px',
            borderRadius: 4,
          }}>
            {connector.category}
          </span>
        </div>

        {/* Footer */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{
            fontFamily: "'Poppins', sans-serif",
            fontSize: 18,
            fontWeight: 600,
            color: colors.dark,
          }}>
            {formatPrice(connector)}
          </span>

          {isInstalled ? (
            <button style={{
              padding: '10px 20px',
              backgroundColor: colors.green + '15',
              color: colors.green,
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              cursor: 'default',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}>
              <Check size={16} />
              Installed
            </button>
          ) : (
            <button
              onClick={(e) => { e.stopPropagation(); onInstall(); }}
              disabled={isInstalling}
              style={{
                padding: '10px 20px',
                backgroundColor: isInstalling ? colors.midGray : colors.orange,
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 600,
                cursor: isInstalling ? 'wait' : 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {isInstalling ? 'Installing...' : 'Install'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// List Row Component
function ConnectorRow({
  connector,
  isInstalled,
  isInstalling,
  onInstall,
  formatPrice,
}: {
  connector: Connector;
  isInstalled: boolean;
  isInstalling: boolean;
  onInstall: () => void;
  formatPrice: (c: Connector) => string;
}) {
  return (
    <div style={{
      backgroundColor: '#fff',
      borderRadius: 10,
      border: `1px solid ${colors.lightGray}`,
      padding: '16px 24px',
      display: 'flex',
      alignItems: 'center',
      gap: 20,
      transition: 'all 0.15s',
      cursor: 'pointer',
    }}
    onMouseOver={(e) => {
      e.currentTarget.style.borderColor = colors.orange + '60';
    }}
    onMouseOut={(e) => {
      e.currentTarget.style.borderColor = colors.lightGray;
    }}
    >
      <div style={{
        width: 44,
        height: 44,
        borderRadius: 8,
        backgroundColor: colors.dark + '08',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 18,
        flexShrink: 0,
      }}>
        {connector.icon || '📦'}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <h3 style={{
            fontFamily: "'Poppins', sans-serif",
            fontSize: 15,
            fontWeight: 600,
            color: colors.dark,
            margin: 0,
          }}>
            {connector.display_name}
          </h3>
          {connector.verified && (
            <span style={{
              backgroundColor: colors.blue + '20',
              color: colors.blue,
              fontSize: 10,
              fontWeight: 600,
              padding: '2px 6px',
              borderRadius: 4,
            }}>
              VERIFIED
            </span>
          )}
        </div>
        <p style={{
          fontSize: 13,
          color: colors.midGray,
          margin: '2px 0 0',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}>
          {connector.short_description}
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <Star size={14} color={colors.midGray} fill={colors.midGray} />
        <span style={{ fontSize: 13, color: colors.midGray }}>
          {connector.rating?.toFixed(1) || '5.0'}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <Download size={14} color={colors.midGray} />
        <span style={{ fontSize: 13, color: colors.midGray }}>
          {connector.install_count?.toLocaleString() || '0'}
        </span>
      </div>

      <span style={{
        fontFamily: "'Poppins', sans-serif",
        fontSize: 15,
        fontWeight: 600,
        color: colors.dark,
        minWidth: 80,
        textAlign: 'right',
      }}>
        {formatPrice(connector)}
      </span>

      {isInstalled ? (
        <button style={{
          padding: '8px 16px',
          backgroundColor: colors.green + '15',
          color: colors.green,
          border: 'none',
          borderRadius: 6,
          fontSize: 13,
          fontWeight: 600,
          cursor: 'default',
          display: 'flex',
          alignItems: 'center',
          gap: 4,
          minWidth: 100,
          justifyContent: 'center',
        }}>
          <Check size={14} />
          Installed
        </button>
      ) : (
        <button
          onClick={(e) => { e.stopPropagation(); onInstall(); }}
          disabled={isInstalling}
          style={{
            padding: '8px 16px',
            backgroundColor: isInstalling ? colors.midGray : colors.orange,
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            fontSize: 13,
            fontWeight: 600,
            cursor: isInstalling ? 'wait' : 'pointer',
            minWidth: 100,
          }}
        >
          {isInstalling ? 'Installing...' : 'Install'}
        </button>
      )}
    </div>
  );
}
