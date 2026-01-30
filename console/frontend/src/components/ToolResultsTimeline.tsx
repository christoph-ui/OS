'use client';

import React from 'react';
import { Sparkles } from 'lucide-react';

interface ToolResultsTimelineProps {
  results: any[];
}

export default function ToolResultsTimeline({ results }: ToolResultsTimelineProps) {
  return (
    <div className="space-y-4 mt-6">
      <h3 className="font-semibold text-gray-900 flex items-center gap-2 text-lg">
        <Sparkles className="w-5 h-5 text-orange-500" />
        AI Analysis Results ({results.length})
      </h3>

      {results.map((result, idx) => (
        <div key={idx} className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          {/* Tool Badge */}
          <div className="flex items-center gap-2 mb-4">
            <span className="text-2xl">{result.tool_icon}</span>
            <div className="flex-1">
              <div className="font-medium text-gray-900">{result.tool_name}</div>
              <div className="text-xs text-gray-500">
                via {result.mcp_used.toUpperCase()} MCP
              </div>
            </div>
            <div className="text-xs text-gray-500">
              {new Date(result.timestamp).toLocaleTimeString()}
            </div>
          </div>

          {/* Result Content */}
          <div className="prose prose-sm max-w-none text-gray-700">
            {result.answer.split('\n').map((line: string, i: number) => (
              <p key={i} className="mb-2">{line}</p>
            ))}
          </div>

          {/* Sources */}
          {result.sources?.length > 0 && (
            <div className="mt-4 pt-4 border-t">
              <p className="text-xs text-gray-600 mb-2">
                Sources ({result.sources.length})
              </p>
              <div className="flex flex-wrap gap-2">
                {result.sources.map((source: any, i: number) => (
                  <div
                    key={i}
                    className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                  >
                    {source.filename || source}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
