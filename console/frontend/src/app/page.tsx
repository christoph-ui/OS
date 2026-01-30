'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ChatProV2 from '../components/ChatProV2';
import MCPsContainer from '../components/MCPsContainer';
import ProductWorkspace from '../components/ProductWorkspace';
import SyndicationWorkspace from '../components/SyndicationWorkspace';
import TenderWorkspace from '../components/TenderWorkspace';
import IngestWorkspace from '../components/IngestWorkspace';
import MCPMarketplace from '../components/connections/MCPMarketplace';
import ConnectionDashboard from '../components/connections/ConnectionDashboard';
import { CustomerProvider, useCustomer } from '../context/CustomerContext';

// Anthropic Brand Colors
const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
};

const Platform0711Content = () => {
  const router = useRouter();
  const { customerId, impersonated, impersonatedCustomer } = useCustomer();

  const [activeNav, setActiveNav] = useState('data');
  const [activeFilter, setActiveFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeMcp, setActiveMcp] = useState('auto');
  const [minioFiles, setMinioFiles] = useState<any>(null);
  const [ingestionStatus, setIngestionStatus] = useState<string>('');
  const [isIngesting, setIsIngesting] = useState(false);
  const [claudeAnalysis, setClaudeAnalysis] = useState<any>(null);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [categories, setCategories] = useState<any[]>([]);  // Dynamic categories from API
  const [documents, setDocuments] = useState<any[]>([]);  // Documents from lakehouse
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [currentUser, setCurrentUser] = useState<any>(null);

  // Load current user on mount
  useEffect(() => {
    const userStr = localStorage.getItem('0711_user');
    if (userStr) {
      try {
        setCurrentUser(JSON.parse(userStr));
      } catch (e) {}
    }
  }, []);

  const navItems = [
    { id: 'chat', label: 'Chat', icon: 'chat' },
    { id: 'products', label: 'Products', icon: 'products' },
    { id: 'data', label: 'Data', icon: 'data' },
    { id: 'tender', label: 'Tender', icon: 'tender' },
    { id: 'syndicate', label: 'Syndicate', icon: 'syndicate' },
    { id: 'mcps', label: 'MCPs', icon: 'mcps' },
    { id: 'marketplace', label: 'Marketplace', icon: 'marketplace' },
    { id: 'connections', label: 'Connections', icon: 'connections' },
    { id: 'ingest', label: 'Ingest', icon: 'ingest' },
    { id: 'settings', label: 'Settings', icon: 'settings' },
  ];

  // Filters built from dynamic categories (no hardcoded categories!)
  const filters = [
    { id: 'all', label: 'All', count: null },
    ...categories.map(cat => ({
      id: cat.key || cat.name.toLowerCase().replace(/\s+/g, '_'),
      label: cat.name,
      count: cat.count,
      icon: cat.icon,
      color: cat.color
    }))
  ];

  const mcpOptions = [
    { id: 'auto', label: 'Auto (detect from query)' },
    { id: 'ctax', label: 'CTAX (Tax)' },
    { id: 'law', label: 'LAW (Legal)' },
    { id: 'tender', label: 'TENDER (RFP)' },
    { id: 'market', label: 'MARKET (Intelligence)' },
    { id: 'publish', label: 'PUBLISH (Content)' },
  ];

  // Load data when customer ID changes (from Context)
  useEffect(() => {
    if (customerId) {
      console.log('Loading data for customer:', customerId);
      loadMinioFiles();
      loadCategories();
      loadDocuments();
    }
  }, [customerId]);

  useEffect(() => {
    loadDocuments();  // Reload when filter changes
  }, [activeFilter]);

  const loadCategories = async () => {
    try {
      // Get customer_id from token
      const token = localStorage.getItem('0711_token');
      let currentCustomerId = customerId;

      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          currentCustomerId = payload.customer_id || customerId;
        } catch (e) {}
      }

      console.log('Loading categories for customer:', currentCustomerId);

      const response = await fetch(`http://localhost:4010/api/data/categories?customer_id=${currentCustomerId}&_=${Date.now()}`, {
        cache: 'no-store'
      });
      const data = await response.json();
      setCategories(data.categories || []);
    } catch (error) {
      console.error('Error loading categories:', error);
      setCategories([]);
    }
  };

  const loadDocuments = async () => {
    setLoadingDocs(true);
    try {
      // Get customer_id from token
      const token = localStorage.getItem('0711_token');
      let currentCustomerId = customerId;

      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          currentCustomerId = payload.customer_id || customerId;
        } catch (e) {}
      }

      console.log('Loading documents for customer:', currentCustomerId, 'filter:', activeFilter);

      const params = new URLSearchParams({
        page: '1',
        page_size: '50',
        customer_id: currentCustomerId,  // CRITICAL: Add customer_id!
        _: Date.now().toString()  // Cache busting
      });

      if (activeFilter && activeFilter !== 'all') {
        params.append('category', activeFilter);
      }

      const response = await fetch(`http://localhost:4010/api/data/browse?${params}`, {
        cache: 'no-store'  // Force bypass cache
      });
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error loading documents:', error);
      setDocuments([]);
    } finally {
      setLoadingDocs(false);
    }
  };

  const loadMinioFiles = async () => {
    try {
      // Get customer_id directly from token (more reliable than waiting for state)
      const token = localStorage.getItem('0711_token');
      let currentCustomerId = customerId;

      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          currentCustomerId = payload.customer_id || customerId;
        } catch (e) {
          console.error('Token decode failed:', e);
        }
      }

      console.log('Loading MinIO files for customer:', currentCustomerId);

      // Use Control Plane API for MinIO (port 4080)
      const apiUrl = 'http://localhost:4080';
      const response = await fetch(`${apiUrl}/api/minio/browse/customer-${currentCustomerId}?_=${Date.now()}`, {
        cache: 'no-store'  // Bypass browser cache
      });
      const data = await response.json();
      if (data.success) {
        setMinioFiles(data);
      }
    } catch (error) {
      console.error('Error loading MinIO files:', error);
    }
  };

  const handleSemanticSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoadingDocs(true);
    try {
      const token = localStorage.getItem('0711_token');

      const response = await fetch('http://localhost:4010/api/data/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          query: searchQuery,
          limit: 20,
          mcp: null
        })
      });

      const data = await response.json();
      console.log('Search results:', data);

      if (data.results) {
        // Convert search results to document format
        const searchDocs = data.results.map((r: any) => ({
          filename: r.metadata?.filename || 'Unknown',
          text: r.text || r.chunk_text || '',
          score: r.score || r.distance,
          mcp: r.metadata?.mcp || 'general',
          size_bytes: r.text?.length || 0
        }));
        setDocuments(searchDocs);
      }
    } catch (error) {
      console.error('Semantic search error:', error);
    } finally {
      setLoadingDocs(false);
    }
  };

  const loadClaudeAnalysis = async () => {
    setLoadingAnalysis(true);
    try {
      // Get customer_id directly from token
      const token = localStorage.getItem('0711_token');
      let currentCustomerId = customerId;

      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          currentCustomerId = payload.customer_id || customerId;
        } catch (e) {}
      }

      // Use Control Plane API for Claude analysis (port 4080)
      const apiUrl = 'http://localhost:4080';
      const response = await fetch(`${apiUrl}/api/claude-analysis/result/${currentCustomerId}`);
      const data = await response.json();
      if (data.success && data.analysis) {
        setClaudeAnalysis(data);
        setShowAnalysis(true);
      }
    } catch (error) {
      console.error('Error loading analysis:', error);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const startIngestion = async () => {
    setIsIngesting(true);
    setIngestionStatus('Starting ingestion...');

    try {
      // Get customer_id directly from token
      const token = localStorage.getItem('0711_token');
      let currentCustomerId = customerId;

      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          currentCustomerId = payload.customer_id || customerId;
        } catch (e) {}
      }

      const response = await fetch('http://localhost:4080/api/ingestion/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: currentCustomerId,
          minio_bucket: `customer-${currentCustomerId}`,
          target_mcp: 'general'
        })
      });

      const result = await response.json();

      if (result.success) {
        setIngestionStatus('✓ Ingestion started! Processing files...');

        // Poll for status
        const pollInterval = setInterval(async () => {
          const statusRes = await fetch(`http://localhost:4080/api/ingestion/status/${currentCustomerId}`);
          const status = await statusRes.json();

          if (status.status === 'in_progress') {
            setIngestionStatus(`Processing: ${status.progress || 0}% - ${status.message || ''}`);
          } else if (status.status === 'complete') {
            setIngestionStatus('✓ Ingestion complete!');
            clearInterval(pollInterval);
            setIsIngesting(false);
          } else if (status.status === 'failed') {
            setIngestionStatus(`❌ Ingestion failed: ${status.error}`);
            clearInterval(pollInterval);
            setIsIngesting(false);
          }
        }, 2000);

        // Stop polling after 5 minutes
        setTimeout(() => clearInterval(pollInterval), 300000);
      }
    } catch (error) {
      console.error('Error starting ingestion:', error);
      setIngestionStatus(`❌ Error: ${error}`);
      setIsIngesting(false);
    }
  };

  const NavIcon = ({ type }: { type: string }) => {
    const iconStyle = { width: 20, height: 20 };

    switch (type) {
      case 'chat':
        return (
          <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        );
      case 'data':
        return (
          <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <ellipse cx="12" cy="5" rx="9" ry="3" />
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
          </svg>
        );
      case 'mcps':
        return (
          <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        );
      case 'products':
        return (
          <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
          </svg>
        );
      case 'ingest':
        return (
          <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17,8 12,3 7,8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        );
      case 'syndicate':
        return (
          <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M12 1v6m0 6v6M5.93 5.93l4.24 4.24m5.66 5.66l4.24 4.24M1 12h6m6 0h6M5.93 18.07l4.24-4.24m5.66-5.66l4.24-4.24" />
          </svg>
        );
      case 'marketplace':
        return (
          <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="9" cy="21" r="1" />
            <circle cx="20" cy="21" r="1" />
            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
          </svg>
        );
      case 'connections':
        return (
          <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M17 11l4-4m0 0l-4-4m4 4H9a4 4 0 0 0 0 8h.01M7 13l-4 4m0 0l4 4m-4-4h8a4 4 0 0 0 0-8H15" />
          </svg>
        );
      case 'tender':
        return (
          <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14,2 14,8 20,8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10,9 9,9 8,9" />
          </svg>
        );
      case 'settings':
        return (
          <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M12 1v6m0 6v6M5.93 5.93l4.24 4.24m5.66 5.66l4.24 4.24M1 12h6m6 0h6M5.93 18.07l4.24-4.24m5.66-5.66l4.24-4.24" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      fontFamily: "'Lora', Georgia, serif",
      backgroundColor: colors.light,
      color: colors.dark,
    }}>
      {/* Impersonation Warning Banner */}
      {impersonated && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 10000,
          backgroundColor: '#d75757',
          color: '#fff',
          padding: '12px 20px',
          textAlign: 'center',
          fontSize: 14,
          fontWeight: 600,
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        }}>
          ⚠️ IMPERSONATE MODE: Sie sehen Daten von "{impersonatedCustomer}" • Alle Aktionen werden protokolliert
          <button
            onClick={() => {
              localStorage.removeItem('0711_impersonated');
              localStorage.removeItem('0711_impersonated_customer');
              localStorage.removeItem('0711_token');
              window.location.href = 'http://localhost:4020/partner-login';
            }}
            style={{
              marginLeft: 20,
              padding: '4px 12px',
              backgroundColor: '#fff',
              color: '#d75757',
              border: 'none',
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Exit Impersonate
          </button>
        </div>
      )}

      {/* Sidebar */}
      <aside style={{
        marginTop: impersonated ? 45 : 0,
        width: 260,
        backgroundColor: colors.dark,
        color: colors.light,
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 0',
      }}>
        {/* Logo */}
        <div style={{
          padding: '0 24px 32px',
          borderBottom: `1px solid ${colors.midGray}33`,
        }}>
          <h1 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 28,
            fontWeight: 600,
            margin: 0,
            letterSpacing: '-0.5px',
          }}>
            <span style={{ color: colors.orange }}>0711</span>
          </h1>
          <p style={{
            fontSize: 13,
            color: colors.midGray,
            margin: '4px 0 0',
            letterSpacing: '0.5px',
          }}>
            Intelligence Platform
          </p>
        </div>

        {/* Navigation */}
        <nav style={{ padding: '24px 16px', flex: 1 }}>
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                if (item.id === 'settings') {
                  router.push('/settings');
                } else {
                  setActiveNav(item.id);
                }
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 16px',
                marginBottom: 4,
                border: 'none',
                borderRadius: 10,
                cursor: 'pointer',
                fontSize: 15,
                fontFamily: "'Lora', Georgia, serif",
                backgroundColor: activeNav === item.id ? `${colors.orange}15` : 'transparent',
                color: activeNav === item.id ? colors.orange : colors.midGray,
                transition: 'all 0.2s ease',
              }}
            >
              <NavIcon type={item.icon} />
              <span style={{ fontWeight: activeNav === item.id ? 500 : 400 }}>
                {item.label}
              </span>
            </button>
          ))}
        </nav>

        {/* Active MCP Section */}
        <div style={{
          padding: '16px 20px',
          borderTop: `1px solid ${colors.midGray}33`,
        }}>
          <p style={{
            fontSize: 10,
            textTransform: 'uppercase',
            letterSpacing: '1.5px',
            color: colors.midGray,
            margin: '0 0 12px',
            fontWeight: 600,
          }}>
            Active MCP
          </p>
          <select
            value={activeMcp}
            onChange={(e) => setActiveMcp(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: 8,
              border: `1px solid ${colors.midGray}55`,
              backgroundColor: `${colors.light}08`,
              color: colors.light,
              fontSize: 13,
              fontFamily: "'Lora', Georgia, serif",
              cursor: 'pointer',
              outline: 'none',
              appearance: 'none',
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23b0aea5' stroke-width='2'%3E%3Cpolyline points='6,9 12,15 18,9'%3E%3C/polyline%3E%3C/svg%3E")`,
              backgroundRepeat: 'no-repeat',
              backgroundPosition: 'right 12px center',
            }}
          >
            {mcpOptions.map((opt) => (
              <option key={opt.id} value={opt.id} style={{ backgroundColor: colors.dark }}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* User Menu */}
        <div style={{
          padding: '16px 20px',
          borderTop: `1px solid ${colors.midGray}33`,
          position: 'relative',
        }}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px',
              border: 'none',
              borderRadius: 10,
              cursor: 'pointer',
              backgroundColor: showUserMenu ? `${colors.orange}15` : 'transparent',
              transition: 'all 0.2s ease',
            }}
            onMouseOver={(e) => {
              if (!showUserMenu) e.currentTarget.style.backgroundColor = `${colors.midGray}22`;
            }}
            onMouseOut={(e) => {
              if (!showUserMenu) e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            <div style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              backgroundColor: `${colors.orange}25`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}>
              <svg style={{ width: 16, height: 16, color: colors.orange }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
            <div style={{ flex: 1, textAlign: 'left' }}>
              <div style={{
                fontSize: 13,
                color: colors.light,
                fontWeight: 500,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}>
                {currentUser ? `${currentUser.first_name} ${currentUser.last_name}` : 'User'}
              </div>
              <div style={{
                fontSize: 11,
                color: colors.midGray,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}>
                {currentUser?.email || ''}
              </div>
            </div>
            <svg
              style={{
                width: 16,
                height: 16,
                color: colors.midGray,
                transform: showUserMenu ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s',
              }}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <polyline points="6,9 12,15 18,9" />
            </svg>
          </button>

          {/* Dropdown Menu */}
          {showUserMenu && (
            <div style={{
              position: 'absolute',
              bottom: '100%',
              left: 20,
              right: 20,
              marginBottom: 8,
              backgroundColor: colors.dark,
              border: `1px solid ${colors.midGray}55`,
              borderRadius: 12,
              overflow: 'hidden',
              boxShadow: '0 -4px 20px rgba(0,0,0,0.3)',
            }}>
              <button
                onClick={() => {
                  setShowUserMenu(false);
                  router.push('/settings/profile');
                }}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '12px 16px',
                  border: 'none',
                  borderBottom: `1px solid ${colors.midGray}33`,
                  backgroundColor: 'transparent',
                  color: colors.light,
                  fontSize: 14,
                  cursor: 'pointer',
                  textAlign: 'left',
                  fontFamily: "'Lora', Georgia, serif",
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = `${colors.midGray}22`}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <svg style={{ width: 16, height: 16 }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                Profile
              </button>

              <button
                onClick={() => {
                  setShowUserMenu(false);
                  router.push('/settings');
                }}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '12px 16px',
                  border: 'none',
                  borderBottom: `1px solid ${colors.midGray}33`,
                  backgroundColor: 'transparent',
                  color: colors.light,
                  fontSize: 14,
                  cursor: 'pointer',
                  textAlign: 'left',
                  fontFamily: "'Lora', Georgia, serif",
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = `${colors.midGray}22`}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <svg style={{ width: 16, height: 16 }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 1v6m0 6v6M5.93 5.93l4.24 4.24m5.66 5.66l4.24 4.24M1 12h6m6 0h6M5.93 18.07l4.24-4.24m5.66-5.66l4.24-4.24" />
                </svg>
                Settings
              </button>

              <button
                onClick={() => {
                  localStorage.removeItem('0711_token');
                  localStorage.removeItem('0711_user');
                  localStorage.removeItem('0711_customer');
                  router.push('/login');
                }}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '12px 16px',
                  border: 'none',
                  backgroundColor: 'transparent',
                  color: colors.red,
                  fontSize: 14,
                  cursor: 'pointer',
                  textAlign: 'left',
                  fontFamily: "'Lora', Georgia, serif",
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = `${colors.red}15`}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <svg style={{ width: 16, height: 16 }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16,17 21,12 16,7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                Logout
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main style={{
        flex: 1,
        padding: (activeNav === 'chat' || activeNav === 'products') ? 0 : 40,
        overflowY: 'auto',
      }}>
        {/* Chat View */}
        {activeNav === 'chat' && (
          <ChatProV2 activeMCP={activeMcp} />
        )}

        {/* Products View */}
        {activeNav === 'products' && (
          <ProductWorkspace />
        )}

        {/* Tender View */}
        {activeNav === 'tender' && (
          <TenderWorkspace />
        )}

        {/* Syndication View */}
        {activeNav === 'syndicate' && (
          <SyndicationWorkspace />
        )}

        {/* Data View */}
        {activeNav === 'data' && (
          <>
            {/* Header */}
            <header style={{ marginBottom: 32, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h2 style={{
                  fontFamily: "'Poppins', Arial, sans-serif",
                  fontSize: 28,
                  fontWeight: 600,
                  margin: 0,
                  color: colors.dark,
                }}>
                  Data Browser
                </h2>
                <p style={{
                  fontSize: 15,
                  color: colors.midGray,
                  margin: '8px 0 0',
                }}>
                  Browse and search lakehouse documents
                </p>
              </div>

        </header>

        {/* Search Bar */}
        <div style={{
          display: 'flex',
          gap: 12,
          marginBottom: 24,
        }}>
          <div style={{
            flex: 1,
            position: 'relative',
          }}>
            <svg
              style={{
                position: 'absolute',
                left: 16,
                top: '50%',
                transform: 'translateY(-50%)',
                width: 20,
                height: 20,
                color: colors.midGray,
              }}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              placeholder="Semantic search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '16px 20px 16px 48px',
                border: `1.5px solid ${colors.lightGray}`,
                borderRadius: 12,
                fontSize: 15,
                fontFamily: "'Lora', Georgia, serif",
                backgroundColor: '#fff',
                outline: 'none',
                transition: 'all 0.2s ease',
                boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = colors.orange;
                e.currentTarget.style.boxShadow = `0 2px 16px ${colors.orange}15`;
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = colors.lightGray;
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)';
              }}
            />
          </div>
          <button
            onClick={handleSemanticSearch}
            disabled={loadingDocs || !searchQuery.trim()}
            style={{
              padding: '16px 32px',
              backgroundColor: loadingDocs ? colors.midGray : colors.orange,
              color: '#fff',
              border: 'none',
              borderRadius: 12,
              fontSize: 15,
              fontFamily: "'Poppins', Arial, sans-serif",
              fontWeight: 500,
              cursor: loadingDocs || !searchQuery.trim() ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: `0 4px 12px ${colors.orange}40`,
            }}
            onMouseOver={(e) => {
              if (!loadingDocs) {
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = `0 6px 20px ${colors.orange}50`;
              }
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = `0 4px 12px ${colors.orange}40`;
            }}
          >
            {loadingDocs ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Filters */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 40,
          flexWrap: 'wrap',
        }}>
          <svg
            style={{ width: 18, height: 18, color: colors.midGray, marginRight: 4 }}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polygon points="22,3 2,3 10,12.46 10,19 14,21 14,12.46" />
          </svg>
          {filters.map((filter) => (
            <button
              key={filter.id}
              onClick={() => setActiveFilter(filter.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 16px',
                border: 'none',
                borderRadius: 20,
                fontSize: 13,
                fontFamily: "'Lora', Georgia, serif",
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                backgroundColor: activeFilter === filter.id ? colors.orange : colors.lightGray,
                color: activeFilter === filter.id ? '#fff' : colors.dark,
                fontWeight: activeFilter === filter.id ? 500 : 400,
              }}
            >
              {filter.id === 'all' ? 'All' : filter.label}
              {filter.count !== null && (
                <span style={{
                  opacity: 0.7,
                  fontSize: 12,
                }}>
                  ({filter.count})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Documents List or Empty State */}
        {loadingDocs ? (
          <div style={{ textAlign: 'center', padding: 60, color: colors.midGray }}>
            <div style={{ fontSize: 32, marginBottom: 16 }}>⟳</div>
            <div>Loading documents...</div>
          </div>
        ) : documents.length > 0 ? (
          <div style={{
            backgroundColor: '#fff',
            borderRadius: 16,
            border: `1.5px solid ${colors.lightGray}`,
            overflow: 'hidden',
          }}>
            {documents.map((doc, idx) => (
              <div
                key={doc.id || idx}
                style={{
                  padding: '20px 24px',
                  borderBottom: idx < documents.length - 1 ? `1px solid ${colors.lightGray}` : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  transition: 'background 0.15s ease',
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = colors.lightGray}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <svg style={{ width: 20, height: 20, color: colors.midGray, flexShrink: 0 }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14,2 14,8 20,8" />
                </svg>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontFamily: "'SF Mono', 'Monaco', monospace",
                    fontSize: 14,
                    color: colors.dark,
                    marginBottom: 4,
                  }}>
                    {doc.filename}
                  </div>
                  {doc.snippet && (
                    <div style={{
                      fontSize: 12,
                      color: colors.midGray,
                      lineHeight: 1.4,
                    }}>
                      {doc.snippet.substring(0, 120)}...
                    </div>
                  )}
                </div>
                <div style={{
                  padding: '4px 12px',
                  backgroundColor: `${colors.blue}15`,
                  borderRadius: 6,
                  fontSize: 11,
                  color: colors.blue,
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                }}>
                  {doc.category || 'general'}
                </div>
                <div style={{
                  fontSize: 12,
                  color: colors.midGray,
                  whiteSpace: 'nowrap',
                }}>
                  {(doc.size_bytes / 1024).toFixed(1)} KB
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '80px 20px',
            backgroundColor: '#fff',
            borderRadius: 16,
            border: `1.5px dashed ${colors.lightGray}`,
          }}>
            <div style={{
              width: 80,
              height: 80,
              borderRadius: 20,
              backgroundColor: colors.lightGray,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 24,
            }}>
              <svg
                style={{ width: 36, height: 36, color: colors.midGray }}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14,2 14,8 20,8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <line x1="10" y1="9" x2="8" y2="9" />
              </svg>
            </div>
            <h3 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 18,
              fontWeight: 500,
              margin: '0 0 8px',
              color: colors.dark,
            }}>
              No documents found
            </h3>
            <p style={{
              fontSize: 14,
              color: colors.midGray,
              margin: 0,
              textAlign: 'center',
              maxWidth: 300,
              lineHeight: 1.6,
            }}>
              Click ▶ Ingest above to process your {minioFiles?.file_count || 0} MinIO files
            </p>
          </div>
        )}

        {/* Claude Analysis Modal */}
        {showAnalysis && claudeAnalysis && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(20, 20, 19, 0.8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
              padding: 20,
            }}
            onClick={() => setShowAnalysis(false)}
          >
            <div
              style={{
                backgroundColor: colors.light,
                borderRadius: 16,
                maxWidth: 900,
                maxHeight: '90vh',
                overflow: 'auto',
                padding: 40,
                boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: 24,
              }}>
                <div>
                  <h3 style={{
                    fontFamily: "'Poppins', Arial, sans-serif",
                    fontSize: 24,
                    fontWeight: 600,
                    color: colors.dark,
                    margin: 0,
                  }}>
                    🧠 Claude Data Analysis
                  </h3>
                  <p style={{
                    fontSize: 13,
                    color: colors.midGray,
                    margin: '8px 0 0',
                  }}>
                    {claudeAnalysis.files_analyzed}/{claudeAnalysis.total_files} files analyzed • {claudeAnalysis.model}
                  </p>
                </div>
                <button
                  onClick={() => setShowAnalysis(false)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: colors.lightGray,
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 14,
                    cursor: 'pointer',
                    fontFamily: "'Poppins', Arial, sans-serif",
                  }}
                >
                  Close
                </button>
              </div>

              <div style={{
                fontFamily: "'Lora', Georgia, serif",
                fontSize: 15,
                lineHeight: 1.8,
                color: colors.dark,
                whiteSpace: 'pre-wrap',
              }}>
                {claudeAnalysis.analysis}
              </div>
            </div>
          </div>
        )}
          </>
        )}

        {/* MCPs View */}
        {activeNav === 'mcps' && (
          <MCPsContainer
            onQuestionClick={(q) => {
              setActiveNav('chat');
            }}
            onSwitchToChat={() => setActiveNav('chat')}
          />
        )}

        {/* Marketplace View */}
        {activeNav === 'marketplace' && (
          <MCPMarketplace />
        )}

        {/* Connections View */}
        {activeNav === 'connections' && (
          <ConnectionDashboard />
        )}

        {/* Ingest View - Professional Workflow */}
        {activeNav === 'ingest' && (
          <IngestWorkspace />
        )}
      </main>
    </div>
  );
};

export default function Platform0711() {
  return (
    <CustomerProvider>
      <Platform0711Content />
    </CustomerProvider>
  );
}
