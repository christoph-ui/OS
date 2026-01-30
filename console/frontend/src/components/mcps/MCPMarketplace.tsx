'use client';

import { useState, useEffect } from 'react';
import { Search, Filter, ShoppingBag } from 'lucide-react';
import MCPCard from './MCPCard';
import MCPDetailModal from './MCPDetailModal';
import { colors, fonts } from './theme';

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

export default function MCPMarketplace() {
  const [mcps, setMcps] = useState<MCP[]>([]);
  const [subscribedMcps, setSubscribedMcps] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [directionFilter, setDirectionFilter] = useState<'all' | 'input' | 'output'>('all');
  const [selectedMcp, setSelectedMcp] = useState<MCP | null>(null);

  useEffect(() => {
    loadMarketplace();
    loadSubscriptions();
  }, []);

  const loadMarketplace = async () => {
    try {
      const response = await fetch('http://localhost:4080/api/mcps/');
      const data = await response.json();
      setMcps(data.mcps || []);
    } catch (error) {
      console.error('Error loading marketplace:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSubscriptions = async () => {
    try {
      const response = await fetch('http://localhost:4010/api/mcp/marketplace/subscriptions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('0711_token')}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setSubscribedMcps(data.subscriptions || []);
      }
    } catch (error) {
      console.error('Error loading subscriptions:', error);
    }
  };

  const handleSubscribe = async (mcpName: string) => {
    try {
      const token = localStorage.getItem('0711_token');
      console.log('Subscribing to:', mcpName);
      console.log('Token exists:', !!token);
      console.log('Token length:', token?.length);

      const response = await fetch(`http://localhost:4010/api/mcp/marketplace/subscribe/${mcpName}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('Subscribe response status:', response.status);

      const data = await response.json();
      console.log('Subscribe response data:', data);

      if (!response.ok) {
        throw new Error(data.detail || `Subscription failed: ${response.status}`);
      }

      if (data.success) {
        // Add to local subscribed list
        setSubscribedMcps([...subscribedMcps, mcpName]);
        console.log('✅ Subscribed successfully to', mcpName);
      }
    } catch (error) {
      console.error('❌ Error subscribing:', error);
      throw error;
    }
  };

  // Filter MCPs
  const filteredMcps = mcps.filter(mcp => {
    if (directionFilter !== 'all' && mcp.direction !== directionFilter) {
      return false;
    }
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        mcp.display_name.toLowerCase().includes(query) ||
        mcp.description.toLowerCase().includes(query) ||
        mcp.category.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const featuredMcps = filteredMcps.filter(m => m.featured);
  const regularMcps = filteredMcps.filter(m => !m.featured);

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: '500px', backgroundColor: colors.light }}>
        <div className="text-center">
          <div className="w-10 h-10 border-3 rounded-full animate-spin mx-auto mb-4" style={{ borderColor: colors.lightGray, borderTopColor: colors.orange }}></div>
          <p style={{ color: colors.midGray, fontFamily: fonts.body }}>Loading marketplace...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: colors.light, padding: '40px' }}>
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-10">
        <div className="flex items-center gap-3 mb-2">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center border"
            style={{ backgroundColor: colors.dark, borderColor: colors.dark }}
          >
            <ShoppingBag className="w-5 h-5" style={{ color: colors.light }} />
          </div>
          <div>
            <h1 className="text-3xl font-semibold" style={{ color: colors.dark, fontFamily: fonts.heading, margin: 0 }}>
              MCP Marketplace
            </h1>
          </div>
        </div>
        <p style={{ color: colors.midGray, fontFamily: fonts.body, fontSize: '15px', margin: '8px 0 0' }}>
          {filteredMcps.length} MCPs available • {subscribedMcps.length} subscribed
        </p>

        {/* Search & Filters */}
        <div className="flex gap-4 mt-8">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: colors.midGray }} />
            <input
              type="text"
              placeholder="Search MCPs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 border rounded-lg focus:outline-none text-sm"
              style={{
                borderColor: colors.lightGray,
                backgroundColor: colors.light,
                color: colors.dark,
                fontFamily: fonts.body
              }}
              onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
              onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
            />
          </div>

          {/* Direction Filter */}
          <div className="flex gap-2 border rounded-lg p-1" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
            {(['all', 'input', 'output'] as const).map((filter) => (
              <button
                key={filter}
                onClick={() => setDirectionFilter(filter)}
                className="px-4 py-2 rounded text-sm font-medium capitalize transition-all"
                style={{
                  backgroundColor: directionFilter === filter ? colors.orange : 'transparent',
                  color: directionFilter === filter ? colors.light : colors.midGray,
                  fontFamily: fonts.heading
                }}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Featured MCPs */}
        {featuredMcps.length > 0 && (
          <section>
            <h2
              className="text-xl font-semibold mb-6"
              style={{ color: colors.dark, fontFamily: fonts.heading }}
            >
              Featured
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {featuredMcps.map((mcp) => (
                <MCPCard
                  key={mcp.id}
                  mcp={mcp}
                  isSubscribed={subscribedMcps.includes(mcp.name)}
                  onSubscribe={handleSubscribe}
                  onCardClick={setSelectedMcp}
                />
              ))}
            </div>
          </section>
        )}

        {/* All MCPs */}
        <section>
          <h2
            className="text-xl font-semibold mb-6"
            style={{ color: colors.dark, fontFamily: fonts.heading }}
          >
            All MCPs ({regularMcps.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {regularMcps.map((mcp) => (
              <MCPCard
                key={mcp.id}
                mcp={mcp}
                isSubscribed={subscribedMcps.includes(mcp.name)}
                onSubscribe={handleSubscribe}
                onCardClick={setSelectedMcp}
              />
            ))}
          </div>
        </section>

        {/* Empty State */}
        {filteredMcps.length === 0 && (
          <div className="text-center py-16">
            <div className="text-6xl mb-4" style={{ color: colors.midGray }}>
              <Search className="w-16 h-16 mx-auto" />
            </div>
            <h3 className="text-xl font-semibold mb-2" style={{ color: colors.dark, fontFamily: fonts.heading }}>
              No MCPs found
            </h3>
            <p style={{ color: colors.midGray, fontFamily: fonts.body }}>
              Try adjusting your search or filters
            </p>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedMcp && (
        <MCPDetailModal
          mcp={selectedMcp}
          isSubscribed={subscribedMcps.includes(selectedMcp.name)}
          onClose={() => setSelectedMcp(null)}
          onSubscribe={async (name) => {
            await handleSubscribe(name);
            setSelectedMcp(null);
          }}
        />
      )}
    </div>
  );
}
