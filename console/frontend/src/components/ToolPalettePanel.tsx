'use client';

import React from 'react';

interface ToolPalettePanelProps {
  selectedProduct: any | null;
  onToolClick: (tool: any) => void;
  runningTools: Set<string>;
}

export default function ToolPalettePanel({ selectedProduct, onToolClick, runningTools }: ToolPalettePanelProps) {
  const tools = selectedProduct?.applicable_tools || [];

  // Group tools by MCP
  const toolsByMCP = tools.reduce((acc: any, tool: any) => {
    const mcpName = tool.mcp.toUpperCase();
    if (!acc[mcpName]) {
      acc[mcpName] = [];
    }
    acc[mcpName].push(tool);
    return acc;
  }, {});

  return (
    <div className="w-80 border-l bg-white overflow-y-auto">
      {/* Header */}
      <div className="p-4 border-b bg-gradient-to-r from-blue-50 to-purple-50">
        <h3 className="font-semibold text-gray-900">
          {selectedProduct ? '🔧 Tools for This Product' : '🔧 All Tools'}
        </h3>
        <p className="text-xs text-gray-600 mt-1">
          {selectedProduct
            ? `${tools.length} tools available`
            : 'Select a product to see applicable tools'}
        </p>
      </div>

      {/* Tools grouped by MCP */}
      <div className="p-3">
        {Object.keys(toolsByMCP).length > 0 ? (
          Object.keys(toolsByMCP).map(mcpName => (
            <div key={mcpName} className="mb-4">
              <div className="flex items-center gap-2 mb-2 px-2">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {mcpName === 'MARKET' ? '🎯' : mcpName === 'PUBLISH' ? '📢' : '⚡'} {mcpName} MCP
                </span>
                <div className="flex-1 h-px bg-gray-200"></div>
              </div>
              <div className="space-y-2">
                {toolsByMCP[mcpName].map((tool: any) => (
                  <ToolButton
                    key={tool.id}
                    tool={tool}
                    onClick={() => onToolClick(tool)}
                    disabled={!selectedProduct}
                    isRunning={runningTools.has(tool.id)}
                  />
                ))}
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-gray-400">
            <div className="text-4xl mb-2">🔧</div>
            <p className="text-sm">Select a product to see tools</p>
          </div>
        )}
      </div>
    </div>
  );
}

function ToolButton({ tool, onClick, disabled, isRunning }: any) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || isRunning}
      className="w-full text-left p-3 border border-gray-200 rounded-lg hover:border-blue-400 hover:shadow-md transition-all group disabled:opacity-50 disabled:cursor-not-allowed bg-white relative overflow-hidden"
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{tool.icon}</span>
        <span className="font-medium text-sm text-gray-900 group-hover:text-blue-600 flex-1">
          {tool.name}
        </span>
        {isRunning && (
          <svg className="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        )}
      </div>
      <p className="text-xs text-gray-600">{tool.description}</p>

      {/* Animated progress bar */}
      {isRunning && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-100 overflow-hidden">
          <div className="h-full bg-gradient-to-r from-blue-400 via-blue-500 to-blue-400 animate-pulse-slow"></div>
        </div>
      )}
    </button>
  );
}
