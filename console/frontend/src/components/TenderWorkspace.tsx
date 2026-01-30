'use client';

import React, { useState, useEffect } from 'react';
import { useCustomer } from '../context/CustomerContext';

// Anthropic Brand Colors
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

interface RFP {
  id: string;
  filename: string;
  status: 'uploading' | 'uploaded' | 'analyzing' | 'analyzed' | 'generating_quote' | 'quoted' | 'error';
  uploadedAt: string;
  analysis?: {
    vergabestelle: string;
    gegenstand: string;
    eignungskriterien: string[];
    zuschlagskriterien: string[];
    fristen: { angebotsfrist: string; bindefrist: string };
    vergabeverfahren: string;
  };
  requirements?: {
    muss: string[];
    soll: string[];
    kann: string[];
  };
  matchedProducts?: Array<{
    product_id: string;
    product_name: string;
    confidence: number;
    price_eur: number;
    etim_class: string;
  }>;
  quote?: {
    lineItems: Array<{ name: string; quantity: number; unitPrice: number; total: number }>;
    subtotal: number;
    overhead: number;
    margin: number;
    total: number;
  };
  error?: string;
}

export default function TenderWorkspace() {
  const { customerId } = useCustomer();
  const [rfps, setRfps] = useState<RFP[]>([]);
  const [selectedRfp, setSelectedRfp] = useState<RFP | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // Load RFPs on mount
  useEffect(() => {
    loadRfps();
  }, [customerId]);

  const loadRfps = async () => {
    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch(`http://localhost:4010/api/tender/list?customer_id=${customerId}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });

      if (response.ok) {
        const data = await response.json();
        setRfps(data.rfps || []);
      }
    } catch (error) {
      console.error('Error loading RFPs:', error);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Please upload a PDF file');
      return;
    }

    setUploading(true);

    try {
      // Upload file
      const formData = new FormData();
      formData.append('file', file);
      formData.append('customer_id', customerId);

      const token = localStorage.getItem('0711_token');
      const uploadResponse = await fetch('http://localhost:4010/api/tender/upload', {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData
      });

      if (!uploadResponse.ok) throw new Error('Upload failed');

      const uploadData = await uploadResponse.json();
      const newRfp: RFP = {
        id: uploadData.rfp_id,
        filename: file.name,
        status: 'uploaded',
        uploadedAt: new Date().toISOString(),
      };

      setRfps(prev => [newRfp, ...prev]);
      setSelectedRfp(newRfp);

      // Auto-analyze
      await analyzeRfp(newRfp.id);
    } catch (error) {
      console.error('Error uploading RFP:', error);
      alert('Failed to upload RFP');
    } finally {
      setUploading(false);
    }
  };

  const analyzeRfp = async (rfpId: string) => {
    setProcessing(true);
    updateRfpStatus(rfpId, 'analyzing');

    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4010/api/tender/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ rfp_id: rfpId, customer_id: customerId })
      });

      if (!response.ok) throw new Error('Analysis failed');

      const data = await response.json();

      setRfps(prev => prev.map(rfp =>
        rfp.id === rfpId
          ? {
              ...rfp,
              status: 'analyzed',
              analysis: data.analysis,
              requirements: data.requirements
            }
          : rfp
      ));

      setSelectedRfp(prev => prev?.id === rfpId ? {
        ...prev,
        status: 'analyzed',
        analysis: data.analysis,
        requirements: data.requirements
      } : prev);

      // Auto-match products
      await matchProducts(rfpId);
    } catch (error) {
      console.error('Error analyzing RFP:', error);
      updateRfpStatus(rfpId, 'error', 'Analysis failed');
    } finally {
      setProcessing(false);
    }
  };

  const matchProducts = async (rfpId: string) => {
    updateRfpStatus(rfpId, 'analyzing');

    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4010/api/tender/match-products', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ rfp_id: rfpId, customer_id: customerId })
      });

      if (!response.ok) throw new Error('Product matching failed');

      const data = await response.json();

      setRfps(prev => prev.map(rfp =>
        rfp.id === rfpId
          ? { ...rfp, matchedProducts: data.matched_products }
          : rfp
      ));

      setSelectedRfp(prev => prev?.id === rfpId ? {
        ...prev,
        matchedProducts: data.matched_products
      } : prev);
    } catch (error) {
      console.error('Error matching products:', error);
    }
  };

  const generateQuote = async (rfpId: string) => {
    setProcessing(true);
    updateRfpStatus(rfpId, 'generating_quote');

    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4010/api/tender/generate-quote', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ rfp_id: rfpId, customer_id: customerId })
      });

      if (!response.ok) throw new Error('Quote generation failed');

      const data = await response.json();

      setRfps(prev => prev.map(rfp =>
        rfp.id === rfpId
          ? { ...rfp, status: 'quoted', quote: data.quote }
          : rfp
      ));

      setSelectedRfp(prev => prev?.id === rfpId ? {
        ...prev,
        status: 'quoted',
        quote: data.quote
      } : prev);
    } catch (error) {
      console.error('Error generating quote:', error);
      updateRfpStatus(rfpId, 'error', 'Quote generation failed');
    } finally {
      setProcessing(false);
    }
  };

  const updateRfpStatus = (rfpId: string, status: RFP['status'], error?: string) => {
    setRfps(prev => prev.map(rfp =>
      rfp.id === rfpId ? { ...rfp, status, error } : rfp
    ));
    setSelectedRfp(prev => prev?.id === rfpId ? { ...prev, status, error } : prev);
  };

  const StatusBadge = ({ status }: { status: RFP['status'] }) => {
    const statusConfig = {
      uploading: { label: 'Uploading...', color: colors.midGray },
      uploaded: { label: 'Uploaded', color: colors.blue },
      analyzing: { label: 'Analyzing...', color: colors.orange },
      analyzed: { label: 'Analyzed', color: colors.green },
      generating_quote: { label: 'Generating Quote...', color: colors.orange },
      quoted: { label: 'Quote Ready', color: colors.green },
      error: { label: 'Error', color: colors.red },
    };

    const config = statusConfig[status];

    return (
      <span style={{
        padding: '4px 12px',
        backgroundColor: `${config.color}20`,
        color: config.color,
        borderRadius: 6,
        fontSize: 12,
        fontWeight: 600,
      }}>
        {config.label}
      </span>
    );
  };

  return (
    <div style={{
      display: 'flex',
      height: '100%',
      gap: 24,
    }}>
      {/* Left Sidebar - RFP List */}
      <aside style={{
        width: 320,
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}>
        <div>
          <h2 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 20,
            fontWeight: 600,
            margin: '0 0 8px',
            color: colors.dark,
          }}>
            RFPs & Tenders
          </h2>
          <p style={{
            fontSize: 13,
            color: colors.midGray,
            margin: 0,
          }}>
            Upload and analyze tender documents
          </p>
        </div>

        {/* Upload Zone */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${dragActive ? colors.orange : colors.lightGray}`,
            borderRadius: 12,
            padding: 32,
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            backgroundColor: dragActive ? `${colors.orange}10` : '#fff',
          }}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <div style={{
            fontSize: 40,
            marginBottom: 12,
            opacity: 0.5,
          }}>
            📄
          </div>
          <p style={{
            fontSize: 14,
            fontWeight: 500,
            color: colors.dark,
            margin: '0 0 6px',
          }}>
            {uploading ? 'Uploading...' : 'Drop RFP PDF here'}
          </p>
          <p style={{
            fontSize: 12,
            color: colors.midGray,
            margin: 0,
          }}>
            or click to browse
          </p>
          <input
            id="file-input"
            type="file"
            accept=".pdf"
            onChange={handleFileInput}
            style={{ display: 'none' }}
            disabled={uploading}
          />
        </div>

        {/* RFP List */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}>
          {rfps.length === 0 ? (
            <div style={{
              padding: 40,
              textAlign: 'center',
              color: colors.midGray,
              fontSize: 13,
            }}>
              No RFPs uploaded yet
            </div>
          ) : (
            rfps.map(rfp => (
              <div
                key={rfp.id}
                onClick={() => setSelectedRfp(rfp)}
                style={{
                  padding: 16,
                  backgroundColor: selectedRfp?.id === rfp.id ? `${colors.orange}15` : '#fff',
                  border: `1px solid ${selectedRfp?.id === rfp.id ? colors.orange : colors.lightGray}`,
                  borderRadius: 10,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: 8,
                }}>
                  <div style={{
                    fontSize: 13,
                    fontWeight: 500,
                    color: colors.dark,
                    wordBreak: 'break-word',
                  }}>
                    {rfp.filename}
                  </div>
                  <StatusBadge status={rfp.status} />
                </div>
                <div style={{
                  fontSize: 11,
                  color: colors.midGray,
                }}>
                  {new Date(rfp.uploadedAt).toLocaleDateString('de-DE')}
                </div>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* Main Content - RFP Details */}
      <main style={{
        flex: 1,
        backgroundColor: '#fff',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 32,
        overflowY: 'auto',
      }}>
        {!selectedRfp ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: colors.midGray,
          }}>
            <div style={{ fontSize: 60, marginBottom: 16, opacity: 0.3 }}>📋</div>
            <div style={{ fontSize: 16, fontWeight: 500 }}>Select an RFP to view details</div>
            <div style={{ fontSize: 13, marginTop: 8 }}>or upload a new tender document</div>
          </div>
        ) : (
          <>
            {/* Header */}
            <div style={{ marginBottom: 32, borderBottom: `1px solid ${colors.lightGray}`, paddingBottom: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <h2 style={{
                    fontFamily: "'Poppins', Arial, sans-serif",
                    fontSize: 24,
                    fontWeight: 600,
                    margin: '0 0 8px',
                    color: colors.dark,
                  }}>
                    {selectedRfp.filename}
                  </h2>
                  <div style={{ fontSize: 13, color: colors.midGray }}>
                    Uploaded {new Date(selectedRfp.uploadedAt).toLocaleString('de-DE')}
                  </div>
                </div>
                <StatusBadge status={selectedRfp.status} />
              </div>

              {/* Action Buttons */}
              {selectedRfp.status === 'uploaded' && (
                <button
                  onClick={() => analyzeRfp(selectedRfp.id)}
                  disabled={processing}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: colors.orange,
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: processing ? 'not-allowed' : 'pointer',
                    marginTop: 16,
                  }}
                >
                  {processing ? 'Analyzing...' : 'Analyze RFP'}
                </button>
              )}

              {selectedRfp.status === 'analyzed' && !selectedRfp.quote && (
                <button
                  onClick={() => generateQuote(selectedRfp.id)}
                  disabled={processing}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: colors.green,
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: processing ? 'not-allowed' : 'pointer',
                    marginTop: 16,
                  }}
                >
                  {processing ? 'Generating Quote...' : 'Generate Quote'}
                </button>
              )}
            </div>

            {/* Analysis Results */}
            {selectedRfp.analysis && (
              <section style={{ marginBottom: 32 }}>
                <h3 style={{
                  fontFamily: "'Poppins', Arial, sans-serif",
                  fontSize: 18,
                  fontWeight: 600,
                  margin: '0 0 16px',
                  color: colors.dark,
                }}>
                  📊 RFP Analysis
                </h3>
                <div style={{
                  display: 'grid',
                  gap: 16,
                  gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                }}>
                  <InfoCard title="Vergabestelle" value={selectedRfp.analysis.vergabestelle} />
                  <InfoCard title="Gegenstand" value={selectedRfp.analysis.gegenstand} />
                  <InfoCard title="Vergabeverfahren" value={selectedRfp.analysis.vergabeverfahren} />
                  <InfoCard title="Angebotsfrist" value={selectedRfp.analysis.fristen?.angebotsfrist} />
                </div>
              </section>
            )}

            {/* Requirements */}
            {selectedRfp.requirements && (
              <section style={{ marginBottom: 32 }}>
                <h3 style={{
                  fontFamily: "'Poppins', Arial, sans-serif",
                  fontSize: 18,
                  fontWeight: 600,
                  margin: '0 0 16px',
                  color: colors.dark,
                }}>
                  📋 Requirements
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <RequirementCard type="Muss" items={selectedRfp.requirements.muss} color={colors.red} />
                  <RequirementCard type="Soll" items={selectedRfp.requirements.soll} color={colors.orange} />
                  <RequirementCard type="Kann" items={selectedRfp.requirements.kann} color={colors.blue} />
                </div>
              </section>
            )}

            {/* Matched Products */}
            {selectedRfp.matchedProducts && selectedRfp.matchedProducts.length > 0 && (
              <section style={{ marginBottom: 32 }}>
                <h3 style={{
                  fontFamily: "'Poppins', Arial, sans-serif",
                  fontSize: 18,
                  fontWeight: 600,
                  margin: '0 0 16px',
                  color: colors.dark,
                }}>
                  🔗 Matched Products ({selectedRfp.matchedProducts.length})
                </h3>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                  backgroundColor: colors.lightGray,
                  padding: 16,
                  borderRadius: 8,
                }}>
                  {selectedRfp.matchedProducts.map((product, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: 12,
                        backgroundColor: '#fff',
                        borderRadius: 6,
                      }}
                    >
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 500, color: colors.dark }}>
                          {product.product_name}
                        </div>
                        <div style={{ fontSize: 12, color: colors.midGray, marginTop: 4 }}>
                          ETIM: {product.etim_class} • Confidence: {Math.round(product.confidence * 100)}%
                        </div>
                      </div>
                      <div style={{ fontSize: 14, fontWeight: 600, color: colors.green }}>
                        €{product.price_eur.toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Quote */}
            {selectedRfp.quote && (
              <section>
                <h3 style={{
                  fontFamily: "'Poppins', Arial, sans-serif",
                  fontSize: 18,
                  fontWeight: 600,
                  margin: '0 0 16px',
                  color: colors.dark,
                }}>
                  💰 Quote
                </h3>
                <div style={{
                  backgroundColor: colors.lightGray,
                  padding: 24,
                  borderRadius: 12,
                }}>
                  <div style={{ marginBottom: 16 }}>
                    {selectedRfp.quote.lineItems.map((item, idx) => (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          padding: '8px 0',
                          borderBottom: idx < selectedRfp.quote!.lineItems.length - 1 ? `1px solid ${colors.lightGray}` : 'none',
                        }}
                      >
                        <div>
                          <div style={{ fontSize: 14, fontWeight: 500 }}>{item.name}</div>
                          <div style={{ fontSize: 12, color: colors.midGray }}>
                            {item.quantity} × €{item.unitPrice.toFixed(2)}
                          </div>
                        </div>
                        <div style={{ fontSize: 14, fontWeight: 600 }}>
                          €{item.total.toFixed(2)}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div style={{
                    borderTop: `2px solid ${colors.midGray}`,
                    paddingTop: 16,
                    fontSize: 14,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span>Subtotal:</span>
                      <span>€{selectedRfp.quote.subtotal.toFixed(2)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span>Overhead & Admin:</span>
                      <span>€{selectedRfp.quote.overhead.toFixed(2)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
                      <span>Margin:</span>
                      <span>€{selectedRfp.quote.margin.toFixed(2)}</span>
                    </div>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: 18,
                      fontWeight: 700,
                      color: colors.green,
                    }}>
                      <span>Total:</span>
                      <span>€{selectedRfp.quote.total.toFixed(2)}</span>
                    </div>
                  </div>
                  <button
                    style={{
                      width: '100%',
                      padding: '12px',
                      marginTop: 16,
                      backgroundColor: colors.green,
                      color: '#fff',
                      border: 'none',
                      borderRadius: 8,
                      fontSize: 14,
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    📄 Export PDF Quote
                  </button>
                </div>
              </section>
            )}

            {/* Error State */}
            {selectedRfp.status === 'error' && (
              <div style={{
                padding: 20,
                backgroundColor: `${colors.red}15`,
                border: `1px solid ${colors.red}`,
                borderRadius: 8,
                color: colors.red,
                fontSize: 14,
              }}>
                ⚠️ {selectedRfp.error || 'An error occurred processing this RFP'}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

// Helper Components

const InfoCard = ({ title, value }: { title: string; value?: string }) => (
  <div style={{
    padding: 16,
    backgroundColor: colors.lightGray,
    borderRadius: 8,
  }}>
    <div style={{
      fontSize: 11,
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
      color: colors.midGray,
      marginBottom: 8,
      fontWeight: 600,
    }}>
      {title}
    </div>
    <div style={{
      fontSize: 14,
      color: colors.dark,
      lineHeight: 1.4,
    }}>
      {value || 'N/A'}
    </div>
  </div>
);

const RequirementCard = ({ type, items, color }: { type: string; items: string[]; color: string }) => (
  <div style={{
    padding: 16,
    backgroundColor: `${color}10`,
    border: `1px solid ${color}40`,
    borderRadius: 8,
  }}>
    <div style={{
      fontSize: 13,
      fontWeight: 600,
      color,
      marginBottom: 12,
    }}>
      {type}-Anforderungen ({items?.length || 0})
    </div>
    <ul style={{
      margin: 0,
      paddingLeft: 20,
      fontSize: 13,
      lineHeight: 1.6,
      color: colors.dark,
    }}>
      {items?.map((item, idx) => (
        <li key={idx}>{item}</li>
      )) || <li>None</li>}
    </ul>
  </div>
);
