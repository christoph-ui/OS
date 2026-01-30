'use client';

import { useState, useEffect } from 'react';
import { Puzzle, Check, AlertCircle, Play, Square } from 'lucide-react';

interface MCP {
  name: string;
  version: string;
  status: 'loaded' | 'available' | 'error';
  description: string;
  lora_adapter: string | null;
  is_core: boolean;
}

interface MCPManagerProps {
  onMCPSelect: (mcp: string | null) => void;
}

export default function MCPManager({ onMCPSelect }: MCPManagerProps) {
  const [mcps, setMCPs] = useState<MCP[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    loadMCPs();
  }, []);

  const loadMCPs = async () => {
    try {
      const response = await fetch('/api/mcps');
      const data = await response.json();
      setMCPs(data.mcps);
    } catch (error) {
      console.error('Error loading MCPs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadMCP = async (name: string) => {
    setActionLoading(name);
    try {
      const response = await fetch(`/api/mcps/${name}/load`, {
        method: 'POST',
      });
      if (response.ok) {
        await loadMCPs();
      }
    } catch (error) {
      console.error('Error loading MCP:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const unloadMCP = async (name: string) => {
    setActionLoading(name);
    try {
      const response = await fetch(`/api/mcps/${name}/unload`, {
        method: 'POST',
      });
      if (response.ok) {
        await loadMCPs();
      }
    } catch (error) {
      console.error('Error unloading MCP:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'loaded':
        return <Check className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Puzzle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'loaded':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const coreMCPs = mcps.filter((m) => m.is_core);
  const marketplaceMCPs = mcps.filter((m) => !m.is_core);

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <h2 className="text-lg font-semibold text-gray-800">MCP Manager</h2>
        <p className="text-sm text-gray-500">Manage Model Context Protocols</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <>
            {/* Core MCPs */}
            <section>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
                Core MCPs
              </h3>
              <div className="grid gap-4">
                {coreMCPs.map((mcp) => (
                  <div
                    key={mcp.name}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        {getStatusIcon(mcp.status)}
                        <div>
                          <h4 className="font-semibold text-gray-800">
                            {mcp.name.toUpperCase()}
                          </h4>
                          <p className="text-sm text-gray-500 mt-1">
                            {mcp.description}
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <span
                              className={`px-2 py-0.5 rounded text-xs ${getStatusColor(
                                mcp.status
                              )}`}
                            >
                              {mcp.status}
                            </span>
                            <span className="text-xs text-gray-400">
                              v{mcp.version}
                            </span>
                            {mcp.lora_adapter && (
                              <span className="text-xs text-primary-600">
                                LoRA: {mcp.lora_adapter}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        {mcp.status === 'loaded' ? (
                          <>
                            <button
                              onClick={() => onMCPSelect(mcp.name)}
                              className="px-3 py-1.5 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors"
                            >
                              Use
                            </button>
                            <button
                              onClick={() => unloadMCP(mcp.name)}
                              disabled={actionLoading === mcp.name}
                              className="p-1.5 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                              title="Unload"
                            >
                              <Square className="w-5 h-5" />
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => loadMCP(mcp.name)}
                            disabled={actionLoading === mcp.name}
                            className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
                          >
                            {actionLoading === mcp.name ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-700"></div>
                            ) : (
                              <Play className="w-4 h-4" />
                            )}
                            Load
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Marketplace MCPs */}
            {marketplaceMCPs.length > 0 && (
              <section>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
                  Marketplace MCPs
                </h3>
                <div className="grid gap-4">
                  {marketplaceMCPs.map((mcp) => (
                    <div
                      key={mcp.name}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          {getStatusIcon(mcp.status)}
                          <div>
                            <h4 className="font-semibold text-gray-800">
                              {mcp.name.toUpperCase()}
                            </h4>
                            <p className="text-sm text-gray-500 mt-1">
                              {mcp.description}
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                              <span
                                className={`px-2 py-0.5 rounded text-xs ${getStatusColor(
                                  mcp.status
                                )}`}
                              >
                                {mcp.status}
                              </span>
                              <span className="text-xs text-gray-400">
                                v{mcp.version}
                              </span>
                            </div>
                          </div>
                        </div>

                        <button
                          onClick={() =>
                            mcp.status === 'loaded'
                              ? unloadMCP(mcp.name)
                              : loadMCP(mcp.name)
                          }
                          disabled={actionLoading === mcp.name}
                          className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
                        >
                          {actionLoading === mcp.name
                            ? 'Loading...'
                            : mcp.status === 'loaded'
                            ? 'Unload'
                            : 'Install'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Info */}
            <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
              <p className="font-medium mb-2">About MCPs</p>
              <ul className="list-disc list-inside space-y-1 text-gray-500">
                <li>Core MCPs (CTAX, LAW, TENDER) are always available</li>
                <li>Each MCP can have a specialized LoRA adapter</li>
                <li>LoRA adapters swap in less than 1 second</li>
                <li>Marketplace MCPs can be installed on demand</li>
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
