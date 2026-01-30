'use client';

import { ArrowRight, ArrowLeft, X, Check } from 'lucide-react';
import { colors, fonts, mcpIconLabels } from './theme';

interface MCP {
  id: string;
  name: string;
  display_name: string;
  description: string;
  icon: string;
  icon_color: string;
  direction: string;
  subscribed: boolean;
  connected: boolean;
  status: string;
}

interface MCPConnectPanelProps {
  type: 'input' | 'output';
  mcps: MCP[];
  onDragStart: (mcp: MCP) => void;
  onDragEnd: () => void;
  onDisconnect: (mcpName: string) => void;
}

export default function MCPConnectPanel({ type, mcps, onDragStart, onDragEnd, onDisconnect }: MCPConnectPanelProps) {
  const isInput = type === 'input';

  return (
    <div className="border rounded-xl overflow-hidden" style={{ backgroundColor: colors.dark, borderColor: colors.dark }}>
      {/* Header */}
      <div className="p-4 border-b" style={{ borderColor: colors.midGray + '33' }}>
        <div className="flex items-center gap-2 mb-1">
          {isInput ? <ArrowRight className="w-4 h-4" style={{ color: colors.light }} /> : <ArrowLeft className="w-4 h-4" style={{ color: colors.light }} />}
          <h3 className="font-semibold text-sm" style={{ color: colors.light, fontFamily: fonts.heading }}>
            {isInput ? 'Input MCPs' : 'Output MCPs'}
          </h3>
        </div>
        <p className="text-xs" style={{ color: colors.midGray, fontFamily: fonts.body }}>
          {isInput ? 'Data sources' : 'Services & outputs'}
        </p>
      </div>

      {/* MCP Cards */}
      <div className="p-3 space-y-2 max-h-[calc(100vh-350px)] overflow-y-auto">
        {mcps.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-xs" style={{ color: colors.midGray, fontFamily: fonts.body }}>
              No {isInput ? 'input' : 'output'} MCPs subscribed
            </p>
          </div>
        ) : (
          mcps.map((mcp) => {
            const iconLabel = mcpIconLabels[mcp.name] || mcp.name.substring(0, 2).toUpperCase();

            return (
              <div
                key={mcp.id}
                draggable={mcp.subscribed}
                onDragStart={() => onDragStart(mcp)}
                onDragEnd={onDragEnd}
                className="group relative p-3 rounded-lg border transition-all"
                style={{
                  backgroundColor: mcp.connected ? colors.light + '10' : colors.light + '05',
                  borderColor: mcp.connected ? colors.orange + '66' : colors.light + '15',
                  cursor: mcp.subscribed ? 'move' : 'not-allowed',
                  opacity: mcp.subscribed ? 1 : 0.5
                }}
              >
                <div className="flex items-center gap-3">
                  {/* Icon - Monochrome */}
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 border"
                    style={{ backgroundColor: colors.light + '15', borderColor: colors.light + '20' }}
                  >
                    <span className="font-semibold text-sm" style={{ color: colors.light + '99', fontFamily: fonts.heading }}>
                      {iconLabel}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-xs truncate" style={{ color: colors.light, fontFamily: fonts.heading }}>
                      {mcp.display_name || mcp.name.toUpperCase()}
                    </h4>
                    <p className="text-xs mt-0.5" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                      {mcp.connected ? 'Connected' : 'Drag to connect'}
                    </p>
                  </div>

                  {/* Disconnect Button */}
                  {mcp.connected && (
                    <button
                      onClick={(e) => { e.stopPropagation(); onDisconnect(mcp.name); }}
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-[#d97757]/20"
                      title="Disconnect"
                    >
                      <X className="w-3.5 h-3.5" style={{ color: colors.light }} />
                    </button>
                  )}
                </div>

                {/* Status Indicator */}
                {mcp.connected && (
                  <div className="absolute top-2 right-2">
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: colors.orange }}></div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
