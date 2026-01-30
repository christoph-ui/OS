'use client';

import { colors, fonts, mcpIconLabels } from './theme';

interface MCP {
  id: string;
  name: string;
  display_name: string;
  icon: string;
  icon_color: string;
}

interface MCPConnectionBadgeProps {
  mcp: MCP;
  type: 'input' | 'output';
}

export default function MCPConnectionBadge({ mcp, type }: MCPConnectionBadgeProps) {
  const iconLabel = mcpIconLabels[mcp.name] || mcp.name.substring(0, 2).toUpperCase();

  return (
    <div className="flex items-center gap-2 p-2 rounded border" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
      {/* Icon */}
      <div
        className="w-7 h-7 rounded flex items-center justify-center flex-shrink-0 border"
        style={{ backgroundColor: colors.dark + '05', borderColor: colors.lightGray }}
      >
        <span className="font-semibold text-xs" style={{ color: colors.dark + '99', fontFamily: fonts.heading }}>
          {iconLabel}
        </span>
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <h5 className="font-medium text-xs truncate" style={{ color: colors.dark, fontFamily: fonts.heading }}>
          {mcp.display_name || mcp.name.toUpperCase()}
        </h5>
        <p className="text-xs" style={{ color: colors.midGray, fontFamily: fonts.body }}>
          {type === 'input' ? 'Ingesting' : 'Publishing'}
        </p>
      </div>

      {/* Status Indicator - Subtle orange dot */}
      <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: colors.orange }}></div>
    </div>
  );
}
