'use client';

import { useState } from 'react';
import { X, Star, Download, Check, ArrowRight } from 'lucide-react';
import SubscribeButton from './SubscribeButton';
import { colors, fonts, mcpIconLabels, directionStyles } from './theme';

interface MCP {
  id: string;
  name: string;
  display_name: string;
  description: string;
  icon: string;
  icon_color: string;
  direction: string;
  category: string;
  pricing_model: string;
  price_per_month_cents?: number;
  price_per_query_cents?: number;
  rating: number;
  review_count: number;
  install_count: number;
  featured: boolean;
  verified: boolean;
  capabilities?: any;
  supported_languages?: string[];
  model_type?: string;
  base_model?: string;
}

interface MCPDetailModalProps {
  mcp: MCP;
  isSubscribed: boolean;
  onClose: () => void;
  onSubscribe: (mcpName: string) => Promise<void>;
}

export default function MCPDetailModal({ mcp, isSubscribed, onClose, onSubscribe }: MCPDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'tools' | 'pricing'>('overview');

  const formatPrice = () => {
    if (mcp.pricing_model === 'free') return 'Free';
    if (mcp.price_per_month_cents) {
      return `€${(mcp.price_per_month_cents / 100).toFixed(0)}/month`;
    }
    if (mcp.price_per_query_cents) {
      return `€${(mcp.price_per_query_cents / 100).toFixed(2)}/query`;
    }
    return 'Custom pricing';
  };

  const directionStyle = directionStyles[mcp.direction as keyof typeof directionStyles] || directionStyles.output;
  const iconLabel = mcpIconLabels[mcp.name] || mcp.name.substring(0, 2).toUpperCase();
  const tools = mcp.capabilities ? Object.keys(mcp.capabilities).map(key => ({
    name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    enabled: mcp.capabilities[key]
  })) : [];

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50 p-4"
      style={{ backgroundColor: 'rgba(20, 20, 19, 0.50)' }}
      onClick={onClose}
    >
      <div
        className="max-w-3xl w-full max-h-[85vh] overflow-hidden rounded-xl border"
        style={{ backgroundColor: colors.light, borderColor: colors.lightGray, boxShadow: '0 20px 50px rgba(20, 20, 19, 0.20)' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-8 border-b" style={{ backgroundColor: colors.dark, borderColor: colors.dark }}>
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-8 h-8 rounded-lg flex items-center justify-center border transition-all hover:bg-[#faf9f5]/10"
            style={{ borderColor: colors.light + '20', color: colors.light }}
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-start gap-5">
            {/* Icon */}
            <div
              className="w-16 h-16 rounded-lg flex items-center justify-center border"
              style={{ backgroundColor: colors.light + '15', borderColor: colors.light + '20' }}
            >
              <span className="font-semibold text-2xl" style={{ color: colors.light, fontFamily: fonts.heading }}>
                {iconLabel}
              </span>
            </div>

            {/* Info */}
            <div className="flex-1">
              <h2 className="text-2xl font-semibold mb-3" style={{ color: colors.light, fontFamily: fonts.heading }}>
                {mcp.display_name}
              </h2>

              <div className="flex items-center gap-4 mb-3 text-sm">
                <div className="flex items-center gap-1" style={{ color: colors.light + 'cc' }}>
                  <Star className="w-4 h-4" />
                  <span>{Number(mcp.rating).toFixed(1)}</span>
                  <span style={{ color: colors.midGray }}>({mcp.review_count})</span>
                </div>
                <span style={{ color: colors.midGray }}>•</span>
                <div className="flex items-center gap-1" style={{ color: colors.light + 'cc' }}>
                  <Download className="w-4 h-4" />
                  <span>{mcp.install_count.toLocaleString()} installs</span>
                </div>
                {mcp.verified && (
                  <>
                    <span style={{ color: colors.midGray }}>•</span>
                    <div className="flex items-center gap-1" style={{ color: colors.light + 'cc' }}>
                      <Check className="w-4 h-4" />
                      <span>Verified</span>
                    </div>
                  </>
                )}
              </div>

              <span
                className={`inline-block px-2 py-1 ${directionStyle.bg} border ${directionStyle.border} text-xs rounded`}
                style={{
                  color: colors.light,
                  backgroundColor: colors.light + '15',
                  borderColor: colors.light + '20',
                  fontFamily: fonts.heading,
                  fontWeight: 600
                }}
              >
                {directionStyle.label}
              </span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b px-8" style={{ borderColor: colors.lightGray }}>
          {(['overview', 'tools', 'pricing'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className="px-6 py-4 text-sm font-semibold capitalize transition-all"
              style={{
                color: activeTab === tab ? colors.orange : colors.midGray,
                borderBottom: activeTab === tab ? `2px solid ${colors.orange}` : '2px solid transparent',
                fontFamily: fonts.heading
              }}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-8 overflow-y-auto max-h-[45vh]">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <h3 className="font-semibold mb-2" style={{ color: colors.dark, fontFamily: fonts.heading }}>About</h3>
                <p className="leading-relaxed" style={{ color: colors.midGray, fontFamily: fonts.body, fontSize: '15px' }}>
                  {mcp.description}
                </p>
              </div>

              {mcp.supported_languages && mcp.supported_languages.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm mb-2" style={{ color: colors.dark, fontFamily: fonts.heading }}>Languages</h4>
                  <div className="flex gap-2">
                    {mcp.supported_languages.map((lang) => (
                      <span key={lang} className="px-2 py-1 border text-xs rounded" style={{ backgroundColor: colors.dark + '05', borderColor: colors.lightGray, color: colors.dark, fontFamily: fonts.heading }}>
                        {lang.toUpperCase()}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'tools' && (
            <div>
              <h3 className="font-semibold mb-4" style={{ color: colors.dark, fontFamily: fonts.heading }}>
                Available Tools ({tools.length})
              </h3>
              {tools.length > 0 ? (
                <div className="space-y-2">
                  {tools.filter(t => t.enabled).map((tool, idx) => (
                    <div key={idx} className="p-3 rounded border" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
                      <h4 className="font-semibold text-sm" style={{ color: colors.dark, fontFamily: fonts.heading }}>{tool.name}</h4>
                      <p className="text-xs mt-1" style={{ color: colors.midGray, fontFamily: fonts.body }}>Available after subscription</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-8" style={{ color: colors.midGray, fontFamily: fonts.body }}>Tool details available after subscription</p>
              )}
            </div>
          )}

          {activeTab === 'pricing' && (
            <div className="space-y-6">
              <div className="text-center py-8 border rounded-lg" style={{ backgroundColor: colors.dark + '03', borderColor: colors.lightGray }}>
                <div className="text-4xl font-semibold mb-2" style={{ color: colors.dark, fontFamily: fonts.heading }}>{formatPrice()}</div>
                <div style={{ color: colors.midGray, fontFamily: fonts.body, fontSize: '14px' }}>
                  {mcp.pricing_model === 'subscription' ? 'Monthly subscription' :
                   mcp.pricing_model === 'usage_based' ? 'Pay per use' : 'Free forever'}
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-3 text-sm" style={{ color: colors.dark, fontFamily: fonts.heading }}>Included</h4>
                <div className="space-y-2 text-sm" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4" style={{ color: colors.dark }} />
                    <span>All {tools.length} tools included</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4" style={{ color: colors.dark }} />
                    <span>24/7 availability</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4" style={{ color: colors.dark }} />
                    <span>Cancel anytime</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs mb-1" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                {mcp.direction === 'input' ? 'Start ingesting data' : 'Enable AI services'}
              </div>
              <div className="text-2xl font-semibold" style={{ color: colors.dark, fontFamily: fonts.heading }}>{formatPrice()}</div>
            </div>
            <div className="w-64">
              <SubscribeButton
                mcpName={mcp.name}
                isSubscribed={isSubscribed}
                onSubscribe={onSubscribe}
                price={formatPrice()}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
