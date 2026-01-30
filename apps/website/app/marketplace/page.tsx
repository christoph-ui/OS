'use client';

import { useState, useEffect } from 'react';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import Link from 'next/link';
import styles from './marketplace.module.css';

// Get API URL from environment variable (production-safe)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4080';

interface MCP {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: string;
  price_monthly: number;
  featured: boolean;
  rating: number;
  install_count: number;
}

export default function MarketplacePage() {
  const [mcps, setMcps] = useState<MCP[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadMCPs();
  }, [selectedCategory]);

  const loadMCPs = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') {
        params.append('category', selectedCategory);
      }
      params.append('page_size', '50');

      const response = await fetch(`${API_URL}/api/mcps/?${params}`);
      const data = await response.json();

      setMcps(data.mcps || []);
    } catch (error) {
      console.error('Error loading MCPs:', error);
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    { id: 'all', label: 'All MCPs', count: mcps.length },
    { id: 'finance', label: 'Finance', icon: '💰' },
    { id: 'legal', label: 'Legal', icon: '⚖️' },
    { id: 'product', label: 'Product', icon: '📦' },
    { id: 'hr', label: 'HR', icon: '👥' },
    { id: 'operations', label: 'Operations', icon: '⚙️' },
    { id: 'compliance', label: 'Compliance', icon: '🛡️' },
  ];

  const filteredMCPs = mcps.filter(mcp =>
    searchQuery === '' ||
    mcp.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    mcp.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      <Navigation />

      <div className={styles.container}>
        {/* Hero */}
        <header className={styles.hero}>
          <h1>MCP Marketplace</h1>
          <p>Erweitern Sie Ihre 0711 Plattform mit spezialisierten AI-Modulen</p>
        </header>

        {/* Search & Filter */}
        <div className={styles.controls}>
          <div className={styles.searchBox}>
            <input
              type="text"
              placeholder="MCPs durchsuchen..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={styles.searchInput}
            />
          </div>

          <div className={styles.categories}>
            {categories.map(cat => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`${styles.categoryButton} ${selectedCategory === cat.id ? styles.active : ''}`}
              >
                {cat.icon && <span>{cat.icon}</span>}
                {cat.label}
                {cat.count !== undefined && <span className={styles.count}>({cat.count})</span>}
              </button>
            ))}
          </div>
        </div>

        {/* MCP Grid */}
        {loading ? (
          <div className={styles.loading}>Loading MCPs...</div>
        ) : (
          <div className={styles.mcpGrid}>
            {filteredMCPs.map((mcp) => (
              <Link
                key={mcp.id}
                href={`/marketplace/${mcp.id}`}
                className={styles.mcpCard}
              >
                {mcp.featured && <div className={styles.badge}>Featured</div>}

                <h3>{mcp.display_name || mcp.name}</h3>
                <p className={styles.mcpDescription}>{mcp.description}</p>

                <div className={styles.mcpMeta}>
                  <span className={styles.category}>{mcp.category}</span>
                  <span className={styles.rating}>⭐ {mcp.rating?.toFixed(1) || 'New'}</span>
                </div>

                <div className={styles.mcpFooter}>
                  <div className={styles.price}>
                    €{mcp.price_monthly || 0}<span>/mo</span>
                  </div>
                  <div className={styles.installs}>
                    {mcp.install_count || 0} installs
                  </div>
                </div>

                <button className={styles.installButton}>
                  Install MCP →
                </button>
              </Link>
            ))}

            {filteredMCPs.length === 0 && (
              <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>🔍</div>
                <h3>No MCPs found</h3>
                <p>Try a different category or search term</p>
              </div>
            )}
          </div>
        )}

        {/* CTA Section */}
        <div className={styles.buildCta}>
          <h2>Build Your Own MCP</h2>
          <p>Veröffentlichen Sie Ihre eigenen MCPs und verdienen Sie 70% der Umsätze</p>
          <Link href="/builders" className={styles.ctaButton}>
            Developer Portal →
          </Link>
        </div>
      </div>

      <Footer />
    </>
  );
}
