'use client';

import React, { useState, useEffect } from 'react';
import ProductTreePanel from './ProductTreePanel';
import ProductCard from './ProductCard';
import ToolPalettePanel from './ToolPalettePanel';
import ToolResultsTimeline from './ToolResultsTimeline';

export default function ProductWorkspace() {
  const [productTree, setProductTree] = useState<any>(null);
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [expandedCategories, setExpandedCategories] = useState<string[]>(['industrial_protection']);
  const [toolResults, setToolResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [availableTools, setAvailableTools] = useState<any[]>([]);
  const [runningTools, setRunningTools] = useState<Set<string>>(new Set());

  // Load product tree and tools on mount
  useEffect(() => {
    loadProductTree();
    loadTools();
  }, []);

  const loadProductTree = async () => {
    try {
      console.log('🔄 Loading product tree from API...');
      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4010/api/products/tree', {
        headers: token ? {
          'Authorization': `Bearer ${token}`
        } : {}
      });
      console.log('📡 API response status:', response.status);
      const data = await response.json();
      console.log('✅ Product tree loaded:', data);
      console.log('   Categories:', data.categories?.length);
      console.log('   Total products:', data.total_products);
      setProductTree(data);
    } catch (error) {
      console.error('❌ Error loading product tree:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTools = async () => {
    try {
      console.log('🔄 Loading tools from API...');
      const response = await fetch('http://localhost:4010/api/mcps/capabilities');
      const data = await response.json();

      // Flatten tools from all MCPs
      const allTools: any[] = [];
      data.mcps?.forEach((mcp: any) => {
        mcp.tools?.forEach((tool: any) => {
          allTools.push({
            ...tool,
            mcp: mcp.id,
            mcp_name: mcp.name,
            query_template: tool.example || `Analyze using ${tool.name}`
          });
        });
      });

      console.log('✅ Loaded', allTools.length, 'tools');
      setAvailableTools(allTools);
    } catch (error) {
      console.error('❌ Error loading tools:', error);
    }
  };

  const handleProductSelect = async (productCode: string) => {
    try {
      const token = localStorage.getItem('0711_token');
      const response = await fetch(`http://localhost:4010/api/products/${encodeURIComponent(productCode)}`, {
        headers: token ? {
          'Authorization': `Bearer ${token}`
        } : {}
      });

      if (!response.ok) {
        console.error(`Product ${productCode} not found (${response.status})`);
        setSelectedProduct(null);
        return;
      }

      const details = await response.json();
      // Add all available tools to the product
      setSelectedProduct({
        ...details,
        applicable_tools: availableTools
      });
    } catch (error) {
      console.error('Error loading product details:', error);
      setSelectedProduct(null);
    }
  };

  const findProductInTree = (code: string) => {
    if (!productTree?.categories) return null;
    for (const category of productTree.categories) {
      const product = category.products?.find((p: any) => p.code === code);
      if (product) return product;
    }
    return null;
  };

  const runTool = async (tool: any) => {
    if (!selectedProduct) return;

    // Mark tool as running
    setRunningTools(prev => new Set(prev).add(tool.id));

    try {
      const response = await fetch('http://localhost:4010/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: tool.query_template,
          mcp: tool.mcp
        })
      });

      const result = await response.json();

      setToolResults(prev => [...prev, {
        tool_name: tool.name,
        tool_icon: tool.icon,
        mcp_used: tool.mcp,
        answer: result.answer || result.response || 'No response',
        sources: result.sources || [],
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      console.error('Error running tool:', error);
    } finally {
      // Remove tool from running state
      setRunningTools(prev => {
        const newSet = new Set(prev);
        newSet.delete(tool.id);
        return newSet;
      });
    }
  };

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories(prev =>
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading products...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full bg-gray-50">
      {/* Left: Product Tree */}
      <ProductTreePanel
        tree={productTree}
        selectedProduct={selectedProduct?.product_code}
        expandedCategories={expandedCategories}
        onProductSelect={handleProductSelect}
        onToggleCategory={toggleCategory}
      />

      {/* Center: Product Details + Results */}
      <div className="flex-1 overflow-y-auto p-6">
        {selectedProduct ? (
          <>
            <ProductCard product={selectedProduct} />
            {toolResults.length > 0 && (
              <ToolResultsTimeline results={toolResults} />
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center mb-6">
              <span className="text-5xl">📦</span>
            </div>
            <h3 className="text-2xl font-semibold text-gray-800 mb-2">
              Select a Product
            </h3>
            <p className="text-gray-600 max-w-md">
              Choose a product from the tree on the left to see details and run AI tools
            </p>
          </div>
        )}
      </div>

      {/* Right: AI Tools */}
      <ToolPalettePanel
        selectedProduct={selectedProduct}
        onToolClick={runTool}
        runningTools={runningTools}
      />
    </div>
  );
}
