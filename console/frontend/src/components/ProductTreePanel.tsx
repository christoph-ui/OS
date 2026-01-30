'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { colors, fonts } from './mcps/theme';

interface Product {
  code: string;
  name: string;
  specs: any;
}

interface Subcategory {
  name: string;
  count: number;
  filters: any;
  products?: Product[];
}

interface Category {
  id?: string;
  name: string;
  icon?: string;
  count: number;
  subcategories?: Subcategory[];
  products?: Product[];
  filters?: any;
}

interface ProductTreePanelProps {
  tree: { categories: Category[]; total_products: number } | null;
  selectedProduct: string | null;
  expandedCategories: string[];
  onProductSelect: (code: string) => void;
  onToggleCategory: (id: string) => void;
}

export default function ProductTreePanel({
  tree,
  selectedProduct,
  expandedCategories,
  onProductSelect,
  onToggleCategory
}: ProductTreePanelProps) {
  return (
    <div className="w-80 border-r overflow-y-auto" style={{ backgroundColor: colors.dark, borderColor: colors.dark }}>
      {/* Header */}
      <div className="p-4 border-b" style={{ borderColor: colors.midGray + '33' }}>
        <h3 className="font-semibold text-lg" style={{ color: colors.light, fontFamily: fonts.heading }}>Product Catalog</h3>
        <p className="text-xs mt-1" style={{ color: colors.midGray, fontFamily: fonts.body }}>
          {tree?.total_products || 0} products
        </p>
      </div>

      {/* Categories */}
      <div className="p-2">
        {!tree || !tree.categories || tree.categories.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm" style={{ color: colors.midGray, fontFamily: fonts.body }}>Loading products...</p>
          </div>
        ) : (
          tree.categories.map(category => (
            <CategoryNode
              key={category.id || category.name}
              category={category}
              expanded={expandedCategories.includes(category.id || category.name)}
              selectedProduct={selectedProduct}
              onToggle={() => onToggleCategory(category.id || category.name)}
              onProductSelect={onProductSelect}
            />
          ))
        )}
      </div>
    </div>
  );
}

function CategoryNode({
  category,
  expanded,
  selectedProduct,
  onToggle,
  onProductSelect
}: {
  category: Category;
  expanded: boolean;
  selectedProduct: string | null;
  onToggle: () => void;
  onProductSelect: (code: string) => void;
}) {
  return (
    <div className="mb-1">
      {/* Category Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors"
        style={{ backgroundColor: expanded ? colors.light + '10' : 'transparent' }}
        onMouseEnter={(e) => !expanded && (e.currentTarget.style.backgroundColor = colors.light + '08')}
        onMouseLeave={(e) => !expanded && (e.currentTarget.style.backgroundColor = 'transparent')}
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4" style={{ color: colors.midGray }} />
        ) : (
          <ChevronRight className="w-4 h-4" style={{ color: colors.midGray }} />
        )}
        <span className="text-sm font-medium flex-1 text-left" style={{ color: colors.light, fontFamily: fonts.heading }}>
          {category.name}
        </span>
        <span className="text-xs px-2 py-0.5 rounded-full" style={{ color: colors.midGray, backgroundColor: colors.light + '15', fontFamily: fonts.heading }}>
          {category.count}
        </span>
      </button>

      {/* Products (Top 10 pro Kategorie) */}
      {expanded && category.products && category.products.length > 0 && (
        <div className="ml-6 mt-1 space-y-0.5">
          {category.products.map(product => (
            <button
              key={product.code}
              onClick={() => onProductSelect(product.code)}
              className="w-full text-left px-3 py-2 rounded-lg text-sm transition-all"
              style={{
                backgroundColor: selectedProduct === product.code ? colors.orange + '20' : 'transparent',
                color: selectedProduct === product.code ? colors.orange : colors.midGray,
                borderLeft: selectedProduct === product.code ? `2px solid ${colors.orange}` : '2px solid transparent',
                fontFamily: fonts.body
              }}
              onMouseEnter={(e) => selectedProduct !== product.code && (e.currentTarget.style.backgroundColor = colors.light + '08')}
              onMouseLeave={(e) => selectedProduct !== product.code && (e.currentTarget.style.backgroundColor = 'transparent')}
            >
              <div className="font-medium text-xs" style={{ color: selectedProduct === product.code ? colors.orange : colors.light, fontFamily: fonts.heading }}>{product.code}</div>
              <div className="text-xs mt-0.5 truncate" style={{ color: colors.midGray }}>{product.name}</div>
              {product.price && <div className="text-xs mt-0.5" style={{ color: colors.orange }}>{product.price} EUR</div>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
