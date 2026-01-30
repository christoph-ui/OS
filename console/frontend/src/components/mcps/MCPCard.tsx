'use client';

import { Star, TrendingUp, Download, ArrowRight } from 'lucide-react';
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
}

interface MCPCardProps {
  mcp: MCP;
  isSubscribed: boolean;
  onSubscribe: (mcpName: string) => Promise<void>;
  onCardClick: (mcp: MCP) => void;
}

export default function MCPCard({ mcp, isSubscribed, onSubscribe, onCardClick }: MCPCardProps) {
  const formatPrice = () => {
    if (mcp.pricing_model === 'free') return 'Free';
    if (mcp.price_per_month_cents) {
      return `€${(mcp.price_per_month_cents / 100).toFixed(0)}/mo`;
    }
    if (mcp.price_per_query_cents) {
      return `€${(mcp.price_per_query_cents / 100).toFixed(2)}/query`;
    }
    return 'Custom';
  };

  const directionStyle = directionStyles[mcp.direction as keyof typeof directionStyles] || directionStyles.output;
  const iconLabel = mcpIconLabels[mcp.name] || mcp.name.substring(0, 2).toUpperCase();

  return (
    <div
      className="group bg-[#faf9f5] border border-[#e8e6dc] rounded-lg overflow-hidden hover:border-[#d97757]/40 transition-all duration-300 cursor-pointer flex flex-col"
      style={{ boxShadow: '0 1px 3px rgba(20, 20, 19, 0.08)', minHeight: '440px' }}
      onClick={() => onCardClick(mcp)}
    >
      {/* Header Section - Fixed Height */}
      <div className="p-6 border-b border-[#e8e6dc] flex-shrink-0">
        <div className="flex items-start gap-4">
          {/* Icon - Monochrome geometric */}
          <div
            className="w-14 h-14 rounded-lg flex items-center justify-center border border-[#e8e6dc] flex-shrink-0"
            style={{ backgroundColor: '#1e293b' + '08' }}
          >
            <span
              className="font-semibold text-lg"
              style={{
                color: '#1e293b' + '99',
                fontFamily: fonts.heading,
                letterSpacing: '-0.5px'
              }}
            >
              {iconLabel}
            </span>
          </div>

          <div className="flex-1 min-w-0">
            {/* Direction Badge - Subtle */}
            <div className="mb-2">
              <span
                className={`inline-block px-2 py-0.5 ${directionStyle.bg} border ${directionStyle.border} ${directionStyle.text} text-xs rounded`}
                style={{ fontFamily: fonts.heading, letterSpacing: '0.5px', fontWeight: 600 }}
              >
                {directionStyle.label}
              </span>
            </div>

            {/* Title */}
            <h3
              className="font-semibold text-lg mb-1.5 group-hover:text-[#d97757] transition-colors"
              style={{
                color: colors.dark,
                fontFamily: fonts.heading,
                lineHeight: '1.3'
              }}
            >
              {mcp.display_name}
            </h3>

            {/* Stats - Subtle */}
            <div className="flex items-center gap-3 text-xs" style={{ color: colors.midGray }}>
              <div className="flex items-center gap-1">
                <Star className="w-3.5 h-3.5" style={{ color: colors.midGray }} />
                <span>{Number(mcp.rating).toFixed(1)}</span>
              </div>
              <span>•</span>
              <div className="flex items-center gap-1">
                <Download className="w-3.5 h-3.5" />
                <span>{mcp.install_count.toLocaleString()}</span>
              </div>
              {mcp.verified && (
                <>
                  <span>•</span>
                  <span style={{ color: colors.dark + '99' }}>Verified</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Content Section - Grows to fill space */}
      <div className="p-6 flex flex-col flex-1">
        {/* Description - Fixed 2 lines */}
        <p
          className="text-sm line-clamp-2 mb-4 leading-relaxed"
          style={{
            color: colors.midGray,
            fontFamily: fonts.body,
            height: '40px' // Fixed height for 2 lines
          }}
        >
          {mcp.description}
        </p>

        {/* Category Tag - Fixed height */}
        <div className="mb-4" style={{ height: '28px' }}>
          <span
            className="inline-block px-2 py-1 border text-xs rounded"
            style={{
              backgroundColor: colors.dark + '05',
              borderColor: colors.lightGray,
              color: colors.midGray,
              fontFamily: fonts.heading
            }}
          >
            {mcp.category}
          </span>
        </div>

        {/* Spacer - Pushes pricing and button to bottom */}
        <div className="flex-1"></div>

        {/* Pricing - Fixed height */}
        <div className="flex items-baseline justify-between mb-5 pb-5 border-b" style={{ borderColor: colors.lightGray, minHeight: '60px' }}>
          <div>
            <div
              className="text-2xl font-semibold"
              style={{
                color: colors.dark,
                fontFamily: fonts.heading
              }}
            >
              {formatPrice()}
            </div>
            {mcp.pricing_model !== 'free' && (
              <div className="text-xs mt-0.5" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                {mcp.pricing_model === 'subscription' ? 'Monthly' : 'Per use'}
              </div>
            )}
          </div>

          {mcp.featured && (
            <span
              className="px-2 py-1 text-xs rounded"
              style={{
                backgroundColor: colors.orange + '15',
                color: colors.orange,
                fontFamily: fonts.heading,
                fontWeight: 600
              }}
            >
              Featured
            </span>
          )}
        </div>

        {/* Subscribe Button - Always at bottom */}
        <div className="flex-shrink-0">
          <SubscribeButton
            mcpName={mcp.name}
            isSubscribed={isSubscribed}
            onSubscribe={onSubscribe}
            price={formatPrice()}
          />
        </div>
      </div>
    </div>
  );
}
