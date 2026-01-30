'use client';

import React, { useState, useEffect } from 'react';
import { colors } from '@/lib/theme';

interface Product {
  product_id: string;
  product_name: string;
  product_type: string;
  etim_class: string;
}

export default function SyndicationWorkspace() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const [selectedFormats, setSelectedFormats] = useState<string[]>(['bmecat']);
  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  const formats = [
    { id: 'bmecat', name: 'BMEcat XML', desc: 'European (ECLASS/ETIM)', iconLabel: 'BM', languages: ['en', 'de'] },
    { id: 'amazon', name: 'Amazon Vendor', desc: 'B2B bulk upload', iconLabel: 'AZ', languages: ['en'] },
    { id: 'cnet', name: 'CNET Feed', desc: 'Content syndication', iconLabel: 'CN', languages: ['en'] },
    { id: 'fabdis', name: 'FAB-DIS France', desc: 'ROTH distributor', iconLabel: 'FD', languages: ['fr'] },
    { id: 'td_synnex', name: 'TD Synnex', desc: 'IT distribution', iconLabel: 'TD', languages: ['en'] },
    { id: '1worldsync', name: '1WorldSync', desc: 'GS1 GDSN', iconLabel: '1W', languages: ['en', 'de', 'fr'] },
    { id: 'etim_json', name: 'ETIM JSON', desc: 'ETIM xChange', iconLabel: 'EJ', languages: ['multi'] },
    { id: 'amer_xml', name: 'AMER XML', desc: 'US distributors', iconLabel: 'AM', languages: ['en'] },
  ];

  // Load products on mount
  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      // Use console backend API (handles CORS and routing)
      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4010/api/syndicate/products?limit=10000', {
        headers: token ? {
          'Authorization': `Bearer ${token}`
        } : {}
      });

      if (!response.ok) {
        console.error('Failed to load products:', response.status);
        setProducts([]);
        return;
      }

      const data = await response.json();
      console.log('✓ Loaded products:', data.products?.length || 0);
      setProducts(data.products || []);
    } catch (error) {
      console.error('Error loading products:', error);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  // Get categories from products
  const categories = React.useMemo(() => {
    const categoryMap: Record<string, number> = {};
    products.forEach(p => {
      const type = p.product_type || 'Other';
      categoryMap[type] = (categoryMap[type] || 0) + 1;
    });
    return Object.entries(categoryMap)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }, [products]);

  // Filtered products based on category
  const filteredProducts = React.useMemo(() => {
    if (categoryFilter === 'all') return products;
    return products.filter(p => p.product_type === categoryFilter);
  }, [products, categoryFilter]);

  // Toggle product selection
  const toggleProduct = (productId: string) => {
    setSelectedProducts(prev =>
      prev.includes(productId)
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    );
  };

  // Select all products
  const selectAll = () => {
    setSelectedProducts(filteredProducts.map(p => p.product_id));
  };

  // Clear selection
  const clearSelection = () => {
    setSelectedProducts([]);
  };

  // Toggle format selection
  const toggleFormat = (formatId: string) => {
    setSelectedFormats(prev =>
      prev.includes(formatId)
        ? prev.filter(id => id !== formatId)
        : [...prev, formatId]
    );
  };

  // Generate exports
  const generateExports = async () => {
    if (selectedProducts.length === 0 || selectedFormats.length === 0) return;

    setGenerating(true);
    setResults([]);

    try {
      // Generate each format
      const token = localStorage.getItem('0711_token');
      for (const formatId of selectedFormats) {
        const response = await fetch('http://localhost:4010/api/syndicate/generate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
          },
          body: JSON.stringify({
            format: formatId,
            product_ids: selectedProducts,
            language: language
          })
        });

        const result = await response.json();

        setResults(prev => [...prev, {
          format: formatId,
          success: result.success,
          filename: result.filename,
          output: result.output,
          products_count: result.products_count,
          validation: result.validation
        }]);
      }
    } catch (error) {
      console.error('Error generating exports:', error);
    } finally {
      setGenerating(false);
    }
  };

  // Download result
  const downloadResult = (result: any) => {
    let blob;

    // Determine file type and create appropriate blob
    const format = result.format;
    const isExcel = ['amazon', 'fabdis', 'td_synnex', '1worldsync'].includes(format);

    if (isExcel) {
      // Excel formats: Decode base64 to binary
      try {
        const binaryString = atob(result.output);  // Decode base64
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }

        blob = new Blob([bytes], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        });
      } catch (error) {
        console.error('Error decoding XLSX:', error);
        // Fallback: treat as text
        blob = new Blob([result.output], { type: 'text/plain' });
      }
    } else if (format === 'etim_json') {
      // JSON format
      blob = new Blob([result.output], { type: 'application/json' });
    } else {
      // XML formats (BMEcat, CNET, AMER)
      blob = new Blob([result.output], { type: 'text/xml' });
    }

    // Trigger download
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = result.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>⟳</div>
          <div style={{ color: colors.midGray }}>Loading products...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: 40 }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h2 style={{
          fontFamily: "'Poppins', Arial, sans-serif",
          fontSize: 32,
          fontWeight: 600,
          margin: 0,
          color: colors.dark,
        }}>
          📡 Content Syndication
        </h2>
        <p style={{ fontSize: 16, color: colors.midGray, margin: '8px 0 0' }}>
          Transform PIM data into {formats.length} distributor-ready formats
        </p>
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 16,
        marginBottom: 32,
      }}>
        <div style={{
          background: `linear-gradient(135deg, ${colors.blue}15 0%, ${colors.blue}08 100%)`,
          padding: 20,
          borderRadius: 12,
          border: `1.5px solid ${colors.blue}40`,
        }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: colors.blue }}>{products.length}</div>
          <div style={{ fontSize: 13, color: colors.midGray }}>Products Ready</div>
        </div>
        <div style={{
          background: `linear-gradient(135deg, ${colors.orange}15 0%, ${colors.orange}08 100%)`,
          padding: 20,
          borderRadius: 12,
          border: `1.5px solid ${colors.orange}40`,
        }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: colors.orange }}>{selectedProducts.length}</div>
          <div style={{ fontSize: 13, color: colors.midGray }}>Products Selected</div>
        </div>
        <div style={{
          background: `linear-gradient(135deg, ${colors.green}15 0%, ${colors.green}08 100%)`,
          padding: 20,
          borderRadius: 12,
          border: `1.5px solid ${colors.green}40`,
        }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: colors.green }}>{selectedFormats.length}</div>
          <div style={{ fontSize: 13, color: colors.midGray }}>Formats Selected</div>
        </div>
        <div style={{
          background: `linear-gradient(135deg, ${colors.midGray}15 0%, ${colors.midGray}08 100%)`,
          padding: 20,
          borderRadius: 12,
          border: `1.5px solid ${colors.midGray}40`,
        }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: colors.midGray }}>{results.length}</div>
          <div style={{ fontSize: 13, color: colors.midGray }}>Files Generated</div>
        </div>
      </div>

      {/* Main Content: 3 Columns */}
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr 250px', gap: 24, marginBottom: 32 }}>
        {/* Column 1: Product Selection */}
        <div style={{
          backgroundColor: '#fff',
          padding: 24,
          borderRadius: 16,
          border: `1.5px solid ${colors.lightGray}`,
          maxHeight: 600,
          overflow: 'auto',
        }}>
          <h3 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 18,
            fontWeight: 600,
            marginBottom: 16,
          }}>
            📦 Select Products
          </h3>

          {/* Selection Actions */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <button onClick={selectAll} style={{
              flex: 1,
              padding: '8px 12px',
              backgroundColor: colors.blue,
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              fontSize: 12,
              fontWeight: 500,
              cursor: 'pointer',
            }}>
              Select All ({filteredProducts.length})
            </button>
            <button onClick={clearSelection} style={{
              flex: 1,
              padding: '8px 12px',
              backgroundColor: colors.lightGray,
              color: colors.dark,
              border: 'none',
              borderRadius: 8,
              fontSize: 12,
              fontWeight: 500,
              cursor: 'pointer',
            }}>
              Clear
            </button>
          </div>

          {/* Category Filter */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 12, fontWeight: 500, color: colors.midGray, display: 'block', marginBottom: 8 }}>
              Filter by Category:
            </label>
            <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} style={{
              width: '100%',
              padding: '8px 12px',
              border: `1px solid ${colors.lightGray}`,
              borderRadius: 8,
              fontSize: 13,
            }}>
              <option value="all">All Categories ({products.length})</option>
              {categories.map(cat => (
                <option key={cat.name} value={cat.name}>{cat.name} ({cat.count})</option>
              ))}
            </select>
          </div>

          {/* Product List with Checkboxes */}
          <div style={{ maxHeight: 350, overflow: 'auto' }}>
            {filteredProducts.slice(0, 50).map(product => (
              <label key={product.product_id} style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 12px',
                marginBottom: 4,
                backgroundColor: selectedProducts.includes(product.product_id) ? `${colors.orange}10` : 'transparent',
                borderRadius: 8,
                cursor: 'pointer',
                fontSize: 13,
              }}>
                <input
                  type="checkbox"
                  checked={selectedProducts.includes(product.product_id)}
                  onChange={() => toggleProduct(product.product_id)}
                  style={{ cursor: 'pointer' }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: 13 }}>{product.product_id}</div>
                  <div style={{ fontSize: 11, color: colors.midGray }}>{product.product_name?.substring(0, 40)}...</div>
                </div>
              </label>
            ))}
            {filteredProducts.length > 50 && (
              <div style={{ padding: 12, textAlign: 'center', fontSize: 12, color: colors.midGray }}>
                + {filteredProducts.length - 50} more products
              </div>
            )}
          </div>
        </div>

        {/* Column 2: Format Selection */}
        <div style={{
          backgroundColor: '#fff',
          padding: 24,
          borderRadius: 16,
          border: `1.5px solid ${colors.lightGray}`,
        }}>
          <h3 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 18,
            fontWeight: 600,
            marginBottom: 16,
          }}>
            📤 Export Formats
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
            {formats.map(format => (
              <label key={format.id} style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: 16,
                backgroundColor: selectedFormats.includes(format.id) ? `${colors.green}15` : colors.lightGray,
                border: selectedFormats.includes(format.id) ? `2px solid ${colors.green}` : `1px solid ${colors.lightGray}`,
                borderRadius: 12,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}>
                <input
                  type="checkbox"
                  checked={selectedFormats.includes(format.id)}
                  onChange={() => toggleFormat(format.id)}
                  style={{ cursor: 'pointer' }}
                />
                <div
                  style={{
                    width: '40px',
                    height: '40px',
                    backgroundColor: colors.dark + '08',
                    border: `1px solid ${colors.lightGray}`,
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: colors.dark,
                    fontFamily: colors.dark,
                    fontSize: '14px',
                    fontWeight: 600
                  }}
                >
                  {format.iconLabel}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: 13 }}>{format.name}</div>
                  <div style={{ fontSize: 11, color: colors.midGray }}>{format.desc}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Column 3: Options */}
        <div style={{
          backgroundColor: '#fff',
          padding: 24,
          borderRadius: 16,
          border: `1.5px solid ${colors.lightGray}`,
        }}>
          <h3 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 18,
            fontWeight: 600,
            marginBottom: 16,
          }}>
            ⚙️ Options
          </h3>

          {/* Language Selector */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 12, fontWeight: 500, color: colors.midGray, display: 'block', marginBottom: 8 }}>
              Language:
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              {['en', 'de', 'fr'].map(lang => (
                <button
                  key={lang}
                  onClick={() => setLanguage(lang)}
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    backgroundColor: language === lang ? colors.orange : colors.lightGray,
                    color: language === lang ? '#fff' : colors.dark,
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 13,
                    fontWeight: 500,
                    cursor: 'pointer',
                    textTransform: 'uppercase',
                  }}
                >
                  {lang}
                </button>
              ))}
            </div>
          </div>

          {/* Info Box */}
          <div style={{
            padding: 16,
            backgroundColor: `${colors.blue}10`,
            borderRadius: 8,
            fontSize: 12,
            color: colors.midGray,
          }}>
            <div style={{ fontWeight: 500, marginBottom: 8 }}>💡 Quick Tip</div>
            <div>Select products by category for faster batch exports. All generated files include validation reports.</div>
          </div>
        </div>
      </div>

      {/* Generate Button */}
      <div style={{ marginBottom: 32 }}>
        <button
          onClick={generateExports}
          disabled={selectedProducts.length === 0 || selectedFormats.length === 0 || generating}
          style={{
            width: '100%',
            padding: '16px 24px',
            backgroundColor: (selectedProducts.length === 0 || selectedFormats.length === 0 || generating) ? colors.midGray : colors.orange,
            color: '#fff',
            border: 'none',
            borderRadius: 12,
            fontSize: 16,
            fontWeight: 600,
            cursor: (selectedProducts.length === 0 || selectedFormats.length === 0 || generating) ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: `0 4px 12px ${colors.orange}30`,
          }}
        >
          {generating ? '⟳ Generating...' : `Generate ${selectedFormats.length} Format${selectedFormats.length > 1 ? 's' : ''} for ${selectedProducts.length} Product${selectedProducts.length > 1 ? 's' : ''}`}
        </button>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div style={{
          backgroundColor: '#fff',
          padding: 24,
          borderRadius: 16,
          border: `1.5px solid ${colors.lightGray}`,
        }}>
          <h3 style={{
            fontFamily: "'Poppins', Arial, sans-serif",
            fontSize: 18,
            fontWeight: 600,
            marginBottom: 16,
          }}>
            ✓ Generated Files
          </h3>

          {results.map((result, idx) => (
            <div key={idx} style={{
              padding: 16,
              marginBottom: 12,
              backgroundColor: result.success ? `${colors.green}10` : `${colors.orange}10`,
              borderRadius: 12,
              border: `1px solid ${result.success ? colors.green : colors.orange}40`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ fontSize: 24 }}>{result.success ? '✓' : '⚠'}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: 14 }}>{result.filename}</div>
                  <div style={{ fontSize: 12, color: colors.midGray }}>
                    {result.products_count} products • {(result.output?.length / 1024).toFixed(1)} KB
                  </div>
                </div>
                {result.success && (
                  <button onClick={() => downloadResult(result)} style={{
                    padding: '8px 16px',
                    backgroundColor: colors.green,
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 13,
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}>
                    Download
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
