"use client";

import { useState, useEffect } from "react";
import { Search, Filter, ArrowUpRight, ExternalLink } from "lucide-react";
import ConnectionWizard from "./ConnectionWizard";

interface MCP {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: string;
  subcategory: string;
  tags: string[];
  icon: string;
  icon_color: string;
  logo_url?: string;
  connection_type: "oauth2" | "api_key" | "database" | "service_account";
  featured: boolean;
  verified: boolean;
  pricing_model: string;
  oauth_config?: {
    provider: string;
    scopes: string[];
  };
  api_docs_url: string;
  setup_instructions: string;
  install_count?: number;
  rating?: number;
}

const CATEGORIES = [
  { id: "all", label: "All", icon: "🌐" },
  { id: "crm", label: "CRM", icon: "💼" },
  { id: "finance", label: "Finance", icon: "💰" },
  { id: "communication", label: "Communication", icon: "💬" },
  { id: "devops", label: "DevOps", icon: "🔧" },
  { id: "ecommerce", label: "E-commerce", icon: "🛍️" },
  { id: "database", label: "Databases", icon: "🗄️" },
  { id: "data", label: "Data", icon: "📊" },
  { id: "design", label: "Design", icon: "🎨" },
  { id: "ai", label: "AI", icon: "🤖" },
];

export default function MCPMarketplace() {
  const [mcps, setMcps] = useState<MCP[]>([]);
  const [filteredMcps, setFilteredMcps] = useState<MCP[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedMcp, setSelectedMcp] = useState<MCP | null>(null);
  const [showWizard, setShowWizard] = useState(false);

  useEffect(() => {
    fetchMcps();
  }, []);

  useEffect(() => {
    filterMcps();
  }, [mcps, searchQuery, selectedCategory]);

  const fetchMcps = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("0711_token");
      // Use Control Plane API (port 4080) for marketplace, not Console Backend (4010)
      const apiUrl = "http://localhost:4080";

      const response = await fetch(`${apiUrl}/api/mcps/?page_size=100`, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });

      if (response.ok) {
        const data = await response.json();
        // API returns {mcps: [], total, page, page_size}
        setMcps(data.mcps || data);
      }
    } catch (error) {
      console.error("Failed to fetch MCPs:", error);
    } finally {
      setLoading(false);
    }
  };

  const filterMcps = () => {
    // Only show MCPs that have connection_type (integration MCPs)
    let filtered = mcps.filter((mcp) => mcp.connection_type);

    if (selectedCategory !== "all") {
      filtered = filtered.filter((mcp) => mcp.category === selectedCategory);
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (mcp) =>
          mcp.display_name.toLowerCase().includes(query) ||
          mcp.description.toLowerCase().includes(query) ||
          (mcp.tags && mcp.tags.some((tag) => tag.toLowerCase().includes(query)))
      );
    }

    setFilteredMcps(filtered);
  };

  const handleConnect = (mcp: MCP) => {
    setSelectedMcp(mcp);
    setShowWizard(true);
  };

  const handleConnectionSuccess = (connectionId: string) => {
    console.log("Connection successful:", connectionId);
    setShowWizard(false);
  };

  const getConnectionTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      oauth2: "OAuth 2.0",
      api_key: "API Key",
      database: "Database",
      service_account: "Service Account",
    };
    return labels[type] || type;
  };

  const getConnectionTypeBadgeColor = (type: string) => {
    const colors: Record<string, string> = {
      oauth2: "bg-blue-100 text-blue-800",
      api_key: "bg-green-100 text-green-800",
      database: "bg-purple-100 text-purple-800",
      service_account: "bg-orange-100 text-orange-800",
    };
    return colors[type] || "bg-gray-100 text-gray-800";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading marketplace...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col space-y-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">MCP Marketplace</h1>
          <p className="text-gray-500 mt-2">
            Connect to your favorite tools and services in seconds
          </p>
        </div>

        {/* Search */}
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search MCPs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Categories */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {CATEGORIES.map((category) => (
          <button
            key={category.id}
            onClick={() => setSelectedCategory(category.id)}
            className={`px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap transition-colors ${
              selectedCategory === category.id
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <span className="mr-2">{category.icon}</span>
            {category.label}
          </button>
        ))}
      </div>

      {/* Featured MCPs */}
      {selectedCategory === "all" && searchQuery === "" && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">⭐ Featured Integrations</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {mcps
              .filter((mcp) => mcp.featured)
              .slice(0, 6)
              .map((mcp) => (
                <MCPCard
                  key={mcp.id}
                  mcp={mcp}
                  onConnect={handleConnect}
                  getConnectionTypeLabel={getConnectionTypeLabel}
                  getConnectionTypeBadgeColor={getConnectionTypeBadgeColor}
                />
              ))}
          </div>
        </div>
      )}

      {/* All MCPs */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            {selectedCategory === "all"
              ? "All Integrations"
              : `${CATEGORIES.find((c) => c.id === selectedCategory)?.label} Integrations`}
          </h2>
          <span className="text-sm text-gray-500">
            {filteredMcps.length} result{filteredMcps.length !== 1 ? "s" : ""}
          </span>
        </div>

        {filteredMcps.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No MCPs found matching your criteria</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredMcps.map((mcp) => (
              <MCPCard
                key={mcp.id}
                mcp={mcp}
                onConnect={handleConnect}
                getConnectionTypeLabel={getConnectionTypeLabel}
                getConnectionTypeBadgeColor={getConnectionTypeBadgeColor}
              />
            ))}
          </div>
        )}
      </div>

      {/* Connection Wizard */}
      {selectedMcp && (
        <ConnectionWizard
          mcp={selectedMcp}
          isOpen={showWizard}
          onClose={() => setShowWizard(false)}
          onSuccess={handleConnectionSuccess}
        />
      )}
    </div>
  );
}

interface MCPCardProps {
  mcp: MCP;
  onConnect: (mcp: MCP) => void;
  getConnectionTypeLabel: (type: string) => string;
  getConnectionTypeBadgeColor: (type: string) => string;
}

function MCPCard({
  mcp,
  onConnect,
  getConnectionTypeLabel,
  getConnectionTypeBadgeColor,
}: MCPCardProps) {
  return (
    <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow bg-white">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 flex items-center justify-center">
            {mcp.logo_url ? (
              <img
                src={mcp.logo_url}
                alt={mcp.display_name}
                className="w-12 h-12 object-contain"
                onError={(e) => {
                  // Fallback to emoji if logo fails to load
                  e.currentTarget.style.display = 'none';
                  e.currentTarget.nextElementSibling!.style.display = 'block';
                }}
              />
            ) : null}
            <div className={`text-4xl ${mcp.logo_url ? 'hidden' : ''}`}>{mcp.icon}</div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-900">{mcp.display_name}</h3>
              {mcp.verified && (
                <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                  ✓ Verified
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500 mt-0.5">{mcp.subcategory}</p>
          </div>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-600 mb-4 line-clamp-2">{mcp.description}</p>

      {/* Badges */}
      <div className="flex flex-wrap gap-2 mb-4">
        <span className={`px-2 py-1 text-xs font-medium rounded ${getConnectionTypeBadgeColor(mcp.connection_type)}`}>
          {getConnectionTypeLabel(mcp.connection_type)}
        </span>
        {mcp.pricing_model === "free" && (
          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
            Free
          </span>
        )}
        {mcp.tags && mcp.tags.slice(0, 2).map((tag, i) => (
          <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
            {tag}
          </span>
        ))}
      </div>

      {/* Stats */}
      {mcp.install_count && mcp.install_count > 0 && (
        <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
          <span>{mcp.install_count.toLocaleString()} installs</span>
          {mcp.rating && <span>⭐ {mcp.rating.toFixed(1)}</span>}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => onConnect(mcp)}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
        >
          Connect
        </button>
        <a
          href={mcp.api_docs_url}
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <ExternalLink className="h-5 w-5 text-gray-600" />
        </a>
      </div>
    </div>
  );
}
