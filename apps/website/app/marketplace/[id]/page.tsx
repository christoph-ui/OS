'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import Link from 'next/link';
import styles from './detail.module.css';

// Get API URL from environment variable (production-safe)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4080';

export default function MCPDetailPage() {
  const params = useParams();
  const router = useRouter();
  const mcpId = params.id as string;

  const [mcp, setMcp] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [installing, setInstalling] = useState(false);

  useEffect(() => {
    loadMCP();
  }, [mcpId]);

  const loadMCP = async () => {
    try {
      const response = await fetch(`${API_URL}/api/mcps/${mcpId}`);
      if (!response.ok) throw new Error('MCP not found');

      const data = await response.json();
      setMcp(data);
    } catch (error) {
      console.error('Error loading MCP:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInstall = async () => {
    setInstalling(true);

    try {
      const response = await fetch(`${API_URL}/api/mcps/${mcpId}/install`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('0711_token')}`,
        },
      });

      if (!response.ok) throw new Error('Installation failed');

      alert('MCP successfully installed!');
      router.push('/dashboard');
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Installation failed');
    } finally {
      setInstalling(false);
    }
  };

  if (loading) {
    return (
      <>
        <Navigation />
        <div style={{ padding: '4rem', textAlign: 'center' }}>Loading...</div>
      </>
    );
  }

  if (!mcp) {
    return (
      <>
        <Navigation />
        <div style={{ padding: '4rem', textAlign: 'center' }}>
          <h2>MCP not found</h2>
          <Link href="/marketplace">← Back to Marketplace</Link>
        </div>
      </>
    );
  }

  return (
    <>
      <Navigation />

      <div className={styles.container}>
        <div className={styles.content}>
          {/* Breadcrumb */}
          <div className={styles.breadcrumb}>
            <Link href="/marketplace">Marketplace</Link> / {mcp.display_name || mcp.name}
          </div>

          {/* Header */}
          <div className={styles.header}>
            <div>
              <h1>{mcp.display_name || mcp.name}</h1>
              <p className={styles.description}>{mcp.description}</p>

              <div className={styles.meta}>
                <span className={styles.category}>{mcp.category}</span>
                <span className={styles.rating}>⭐ {mcp.rating?.toFixed(1) || 'New'}</span>
                <span className={styles.installs}>{mcp.install_count || 0} installs</span>
              </div>
            </div>

            <div className={styles.pricing}>
              <div className={styles.price}>
                €{mcp.price_monthly || 0}<span>/Monat</span>
              </div>
              <button
                onClick={handleInstall}
                disabled={installing}
                className={styles.installButton}
              >
                {installing ? 'Installing...' : 'Install MCP'}
              </button>
              <p className={styles.priceNote}>
                Jederzeit kündbar • Keine Setup-Gebühr
              </p>
            </div>
          </div>

          {/* Features */}
          <div className={styles.section}>
            <h2>Features</h2>
            <ul className={styles.featureList}>
              <li>Spezialisiertes Training für {mcp.category}</li>
              <li>Integration mit Lakehouse</li>
              <li>Custom LoRA-Adapter</li>
              <li>Real-time processing</li>
              <li>API & WebSocket access</li>
            </ul>
          </div>

          {/* Technical Details */}
          <div className={styles.section}>
            <h2>Technical Specifications</h2>
            <div className={styles.specs}>
              <div className={styles.spec}>
                <strong>Version:</strong> {mcp.version || '1.0.0'}
              </div>
              <div className={styles.spec}>
                <strong>Category:</strong> {mcp.category}
              </div>
              <div className={styles.spec}>
                <strong>Model Size:</strong> {mcp.model_size_gb || 2} GB
              </div>
              <div className={styles.spec}>
                <strong>Response Time:</strong> &lt; 3s average
              </div>
            </div>
          </div>

          {/* Use Cases */}
          <div className={styles.section}>
            <h2>Use Cases</h2>
            <p>Coming soon - examples and use cases for this MCP</p>
          </div>

          {/* Support */}
          <div className={styles.supportSection}>
            <h3>Need Help?</h3>
            <p>
              <a href="mailto:support@0711.io">Contact Support</a> |{' '}
              <Link href="/docs">Documentation</Link>
            </p>
          </div>
        </div>
      </div>

      <Footer />
    </>
  );
}
