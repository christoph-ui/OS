'use client';

import { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, ArrowRight } from 'lucide-react';
import { colors, fonts, mcpIconLabels } from './mcps/theme';

interface Tool {
  id: string;
  name: string;
  description: string;
  example: string;
  icon: string;
}

interface MCP {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  tools: Tool[];
  tool_count: number;
}

interface MCPsViewProps {
  onQuestionClick: (question: string) => void;
  onSwitchToChat: () => void;
}

export default function MCPsView({ onQuestionClick, onSwitchToChat }: MCPsViewProps) {
  const [mcps, setMcps] = useState<MCP[]>([]);
  const [expandedMcp, setExpandedMcp] = useState<string | null>('market');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMCPs();
  }, []);

  const loadMCPs = async () => {
    try {
      const response = await fetch('http://localhost:4010/api/mcps/capabilities');
      const data = await response.json();
      setMcps(data.mcps || []);
    } catch (error) {
      console.error('Error loading MCPs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToolClick = (tool: Tool) => {
    onQuestionClick(tool.example);
    onSwitchToChat();
  };

  const toggleMcp = (mcpId: string) => {
    setExpandedMcp(expandedMcp === mcpId ? null : mcpId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: '500px', backgroundColor: colors.light }}>
        <div className="text-center">
          <div className="w-10 h-10 border-3 rounded-full animate-spin mx-auto mb-4" style={{ borderColor: colors.lightGray, borderTopColor: colors.orange }}></div>
          <p style={{ color: colors.midGray, fontFamily: fonts.body }}>Loading tools...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: colors.light, padding: '40px' }}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-10">
          <h1 className="text-3xl font-semibold mb-2" style={{ color: colors.dark, fontFamily: fonts.heading, margin: 0 }}>
            MCP Tools
          </h1>
          <p style={{ color: colors.midGray, fontFamily: fonts.body, fontSize: '15px' }}>
            {mcps.length} MCPs • {mcps.reduce((sum, m) => sum + m.tool_count, 0)} tools available
          </p>
          <p className="mt-2" style={{ color: colors.midGray, fontFamily: fonts.body, fontSize: '14px' }}>
            Expand any MCP to see its tools. Click a tool to try it in chat.
          </p>
        </div>

        {/* MCP Cards */}
        <div className="space-y-4">
          {mcps.map((mcp) => {
            const iconLabel = mcpIconLabels[mcp.id] || mcp.name.substring(0, 2).toUpperCase();

            return (
              <div
                key={mcp.id}
                className="border rounded-lg overflow-hidden"
                style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}
              >
                {/* MCP Header - Dark */}
                <div
                  onClick={() => toggleMcp(mcp.id)}
                  className="flex items-center gap-4 p-6 cursor-pointer transition-all"
                  style={{ backgroundColor: colors.dark }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = colors.dark + 'f5'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = colors.dark}
                >
                  {/* Icon - 2-letter code */}
                  <div
                    className="w-14 h-14 rounded-lg flex items-center justify-center border flex-shrink-0"
                    style={{ backgroundColor: colors.light + '15', borderColor: colors.light + '20' }}
                  >
                    <span className="font-semibold text-lg" style={{ color: colors.light, fontFamily: fonts.heading }}>
                      {iconLabel}
                    </span>
                  </div>

                  {/* Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="text-xl font-semibold" style={{ color: colors.light, fontFamily: fonts.heading }}>
                        {mcp.name}
                      </h3>
                      <span
                        className="px-2 py-0.5 text-xs rounded"
                        style={{
                          backgroundColor: colors.orange + '20',
                          color: colors.orange,
                          fontFamily: fonts.heading,
                          fontWeight: 600
                        }}
                      >
                        Active
                      </span>
                    </div>
                    <p style={{ color: colors.midGray, fontFamily: fonts.body, fontSize: '14px' }}>
                      {mcp.description}
                    </p>
                    <p className="mt-2 text-sm" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                      {mcp.tool_count} {mcp.tool_count === 1 ? 'tool' : 'tools'} available
                    </p>
                  </div>

                  {/* Expand Icon */}
                  <div>
                    {expandedMcp === mcp.id ? (
                      <ChevronDown className="w-6 h-6" style={{ color: colors.midGray }} />
                    ) : (
                      <ChevronRight className="w-6 h-6" style={{ color: colors.midGray }} />
                    )}
                  </div>
                </div>

                {/* Tools Grid (Expanded) */}
                {expandedMcp === mcp.id && (
                  <div className="p-6 border-t" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {mcp.tools.map((tool) => (
                        <div
                          key={tool.id}
                          onClick={() => handleToolClick(tool)}
                          className="p-4 rounded-lg border cursor-pointer group transition-all"
                          style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}
                          onMouseEnter={(e) => e.currentTarget.style.borderColor = colors.orange + '66'}
                          onMouseLeave={(e) => e.currentTarget.style.borderColor = colors.lightGray}
                        >
                          {/* Tool Name */}
                          <h4
                            className="font-semibold mb-2 group-hover:text-[#d97757] transition-colors"
                            style={{
                              color: colors.dark,
                              fontFamily: fonts.heading,
                              fontSize: '15px'
                            }}
                          >
                            {tool.name}
                          </h4>

                          {/* Description */}
                          <p
                            className="text-sm line-clamp-2 mb-3"
                            style={{
                              color: colors.midGray,
                              fontFamily: fonts.body,
                              lineHeight: '1.5'
                            }}
                          >
                            {tool.description}
                          </p>

                          {/* Example */}
                          <div className="p-3 rounded-lg mb-3" style={{ backgroundColor: colors.dark + '05' }}>
                            <p className="text-xs mb-1" style={{ color: colors.midGray, fontFamily: fonts.heading, fontWeight: 600 }}>
                              Example:
                            </p>
                            <p className="text-xs italic line-clamp-2" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                              "{tool.example}"
                            </p>
                          </div>

                          {/* Try in Chat Button */}
                          <button
                            className="flex items-center gap-1 text-sm font-semibold"
                            style={{
                              color: colors.orange,
                              fontFamily: fonts.heading
                            }}
                          >
                            Try in Chat
                            <ArrowRight className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Help Section */}
        <div className="mt-10 p-6 border rounded-lg" style={{ backgroundColor: colors.dark, borderColor: colors.dark }}>
          <h3 className="font-semibold mb-2" style={{ color: colors.light, fontFamily: fonts.heading }}>
            How to Use
          </h3>
          <p style={{ color: colors.midGray, fontFamily: fonts.body, fontSize: '14px', lineHeight: '1.6' }}>
            Each MCP provides specialized tools for specific domains. Click a tool card to pre-fill the chat with an example query.
            MCPs work together - you can chain them in conversations for complex workflows.
          </p>
        </div>
      </div>
    </div>
  );
}
