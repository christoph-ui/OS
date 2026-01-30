"use client";

import { useState, useEffect } from "react";
import {
  MoreVertical,
  RefreshCw,
  Trash2,
  TestTube,
  AlertTriangle,
} from "lucide-react";

interface Connection {
  id: string;
  customer_id: string;
  mcp_id: string;
  connection_type: string;
  connection_name: string;
  oauth_provider?: string;
  oauth_scopes?: string[];
  connection_metadata?: any;
  status: "active" | "expired" | "invalid" | "revoked" | "pending" | "error";
  health_status: "healthy" | "warning" | "error" | "unknown";
  last_health_check?: string;
  last_successful_use?: string;
  error_count: number;
  last_error_message?: string;
  total_api_calls: number;
  created_at: string;
  token_expires_at?: string;
}

interface MCP {
  id: string;
  name: string;
  display_name: string;
  icon: string;
  icon_color: string;
  logo_url?: string;
  category: string;
}

export default function ConnectionDashboard() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [mcps, setMcps] = useState<Map<string, MCP>>(new Map());
  const [loading, setLoading] = useState(true);
  const [testingConnectionId, setTestingConnectionId] = useState<string | null>(null);
  const [refreshingConnectionId, setRefreshingConnectionId] = useState<string | null>(null);

  useEffect(() => {
    fetchConnections();
    fetchMcps();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchConnections();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const fetchConnections = async () => {
    try {
      const token = localStorage.getItem("0711_token");
      // Use Control Plane API (port 4080) for connections, not Console Backend (4010)
      const apiUrl = "http://localhost:4080";

      const response = await fetch(`${apiUrl}/api/connections/`, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConnections(data);
      }
    } catch (error) {
      console.error("Failed to fetch connections:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMcps = async () => {
    try {
      const token = localStorage.getItem("0711_token");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4080";

      const response = await fetch(`${apiUrl}/api/mcps/?page_size=100`, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });

      if (response.ok) {
        const data = await response.json();
        const mcpMap = new Map();
        const mcpList = data.mcps || data;
        mcpList.forEach((mcp: MCP) => {
          mcpMap.set(mcp.id, mcp);
        });
        setMcps(mcpMap);
      }
    } catch (error) {
      console.error("Failed to fetch MCPs:", error);
    }
  };

  const handleTestConnection = async (connectionId: string) => {
    setTestingConnectionId(connectionId);
    try {
      const token = localStorage.getItem("0711_token");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4080";

      const response = await fetch(`${apiUrl}/api/connections/${connectionId}/test`, {
        method: "POST",
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });

      if (response.ok) {
        const result = await response.json();
        alert(result.success ? "✅ Connection test successful!" : `❌ Connection test failed: ${result.error}`);
        await fetchConnections();
      }
    } catch (error) {
      alert(`❌ Connection test failed: ${error}`);
    } finally {
      setTestingConnectionId(null);
    }
  };

  const handleRefreshToken = async (connectionId: string) => {
    setRefreshingConnectionId(connectionId);
    try {
      const token = localStorage.getItem("0711_token");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4080";

      const response = await fetch(`${apiUrl}/api/connections/${connectionId}/refresh`, {
        method: "PATCH",
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });

      if (response.ok) {
        alert("✅ Token refreshed successfully!");
        await fetchConnections();
      } else {
        const error = await response.json();
        alert(`❌ Token refresh failed: ${error.detail}`);
      }
    } catch (error) {
      alert(`❌ Token refresh failed: ${error}`);
    } finally {
      setRefreshingConnectionId(null);
    }
  };

  const handleDeleteConnection = async (connectionId: string, connectionName: string) => {
    if (!confirm(`Are you sure you want to disconnect "${connectionName}"?`)) {
      return;
    }

    try {
      const token = localStorage.getItem("0711_token");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4080";

      const response = await fetch(`${apiUrl}/api/connections/${connectionId}`, {
        method: "DELETE",
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });

      if (response.ok) {
        alert("✅ Connection deleted successfully!");
        await fetchConnections();
      } else {
        alert("❌ Failed to delete connection");
      }
    } catch (error) {
      alert(`❌ Failed to delete connection: ${error}`);
    }
  };

  const getHealthIndicator = (connection: Connection) => {
    if (connection.status === "revoked") {
      return <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded">⚫ Revoked</span>;
    }

    const indicators: Record<string, JSX.Element> = {
      healthy: <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">🟢 Healthy</span>,
      warning: <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs font-medium rounded">🟡 Warning</span>,
      error: <span className="px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded">🔴 Error</span>,
    };

    return indicators[connection.health_status] || <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded">⚪ Unknown</span>;
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { label: string; className: string }> = {
      active: { label: "Active", className: "bg-blue-100 text-blue-800" },
      expired: { label: "Expired", className: "bg-red-100 text-red-800" },
      invalid: { label: "Invalid", className: "bg-red-100 text-red-800" },
      revoked: { label: "Revoked", className: "bg-gray-100 text-gray-600" },
      pending: { label: "Pending", className: "bg-yellow-100 text-yellow-800" },
      error: { label: "Error", className: "bg-red-100 text-red-800" },
    };

    const config = statusConfig[status] || { label: status, className: "bg-gray-100 text-gray-800" };
    return <span className={`px-2 py-1 text-xs font-medium rounded ${config.className}`}>{config.label}</span>;
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getTokenExpiry = (connection: Connection) => {
    if (!connection.token_expires_at) return null;

    const expiryDate = new Date(connection.token_expires_at);
    const now = new Date();
    const diffMs = expiryDate.getTime() - now.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);

    if (diffMs < 0) return <span className="text-red-500">Expired</span>;
    if (diffMins < 60) return <span className="text-yellow-600">Expires in {diffMins}m</span>;
    if (diffHours < 24) return <span className="text-yellow-600">Expires in {diffHours}h</span>;
    return <span className="text-gray-500">Valid</span>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading connections...</p>
        </div>
      </div>
    );
  }

  if (connections.length === 0) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <p className="text-blue-800">
          No connections yet. Visit the marketplace to connect your first integration.
        </p>
      </div>
    );
  }

  const healthyCount = connections.filter((c) => c.health_status === "healthy").length;
  const warningCount = connections.filter((c) => c.health_status === "warning").length;
  const errorCount = connections.filter((c) => c.health_status === "error").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Connections</h1>
          <p className="text-gray-500 mt-2">
            Manage your active integrations and monitor their health
          </p>
        </div>
        <button
          onClick={fetchConnections}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <p className="text-sm font-medium text-gray-500 mb-1">Total Connections</p>
          <p className="text-2xl font-bold text-gray-900">{connections.length}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <p className="text-sm font-medium text-gray-500 mb-1">Healthy</p>
          <p className="text-2xl font-bold text-green-500">{healthyCount}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <p className="text-sm font-medium text-gray-500 mb-1">Warnings</p>
          <p className="text-2xl font-bold text-yellow-500">{warningCount}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <p className="text-sm font-medium text-gray-500 mb-1">Errors</p>
          <p className="text-2xl font-bold text-red-500">{errorCount}</p>
        </div>
      </div>

      {/* Connection Cards */}
      <div className="grid grid-cols-1 gap-4">
        {connections.map((connection) => {
          const mcp = mcps.get(connection.mcp_id);
          const isOAuth = connection.connection_type === "oauth2";

          return (
            <div key={connection.id} className="bg-white border border-gray-200 rounded-lg p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {mcp && (
                    <div className="w-10 h-10 flex items-center justify-center">
                      {mcp.logo_url ? (
                        <img
                          src={mcp.logo_url}
                          alt={mcp.display_name}
                          className="w-10 h-10 object-contain"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                            e.currentTarget.nextElementSibling!.style.display = 'block';
                          }}
                        />
                      ) : null}
                      <div className={`text-3xl ${mcp.logo_url ? 'hidden' : ''}`}>{mcp.icon}</div>
                    </div>
                  )}
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-gray-900">{connection.connection_name}</h3>
                      {getHealthIndicator(connection)}
                      {getStatusBadge(connection.status)}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {mcp?.display_name} • {connection.connection_type}
                    </p>
                  </div>
                </div>

                {/* Actions Dropdown */}
                <div className="relative group">
                  <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                    <MoreVertical className="h-5 w-5 text-gray-600" />
                  </button>
                  <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                    <button
                      onClick={() => handleTestConnection(connection.id)}
                      disabled={testingConnectionId === connection.id}
                      className="w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-sm text-gray-700 disabled:opacity-50"
                    >
                      <TestTube className="h-4 w-4" />
                      Test Connection
                    </button>
                    {isOAuth && (
                      <button
                        onClick={() => handleRefreshToken(connection.id)}
                        disabled={refreshingConnectionId === connection.id}
                        className="w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 text-sm text-gray-700 disabled:opacity-50"
                      >
                        <RefreshCw className="h-4 w-4" />
                        Refresh Token
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteConnection(connection.id, connection.connection_name)}
                      className="w-full text-left px-4 py-2 hover:bg-red-50 flex items-center gap-2 text-sm text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                      Disconnect
                    </button>
                  </div>
                </div>
              </div>

              {/* Error Message */}
              {connection.last_error_message && connection.error_count > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-red-800">
                        Error ({connection.error_count}x):
                      </p>
                      <p className="text-sm text-red-700 mt-1">
                        {connection.last_error_message}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                <div>
                  <p className="text-gray-500">Last Health Check</p>
                  <p className="font-medium text-gray-900">{formatDate(connection.last_health_check)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Last Used</p>
                  <p className="font-medium text-gray-900">{formatDate(connection.last_successful_use)}</p>
                </div>
                <div>
                  <p className="text-gray-500">API Calls</p>
                  <p className="font-medium text-gray-900">{connection.total_api_calls.toLocaleString()}</p>
                </div>
                {isOAuth && (
                  <div>
                    <p className="text-gray-500">Token Status</p>
                    <p className="font-medium">{getTokenExpiry(connection)}</p>
                  </div>
                )}
              </div>

              {/* OAuth Scopes */}
              {isOAuth && connection.oauth_scopes && connection.oauth_scopes.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm text-gray-500 mb-2">Scopes:</p>
                  <div className="flex flex-wrap gap-2">
                    {connection.oauth_scopes.slice(0, 5).map((scope, i) => (
                      <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        {scope}
                      </span>
                    ))}
                    {connection.oauth_scopes.length > 5 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        +{connection.oauth_scopes.length - 5} more
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Connection Metadata */}
              {connection.connection_metadata && Object.keys(connection.connection_metadata).length > 0 && (
                <div className="mb-4">
                  <p className="text-sm text-gray-500 mb-2">Connection Info:</p>
                  <div className="bg-gray-50 rounded p-3 text-xs font-mono text-gray-700">
                    {Object.entries(connection.connection_metadata).slice(0, 3).map(([key, value]) => (
                      <div key={key}>
                        {key}: {String(value)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Footer */}
              <div className="text-xs text-gray-400 border-t border-gray-100 pt-4">
                Connected {formatDate(connection.created_at)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
