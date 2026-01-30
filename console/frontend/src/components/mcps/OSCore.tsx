'use client';

import { Database, Cpu, Network, ArrowRight } from 'lucide-react';
import MCPConnectionBadge from './MCPConnectionBadge';
import { colors, fonts } from './theme';

interface MCP {
  id: string;
  name: string;
  display_name: string;
  icon: string;
  icon_color: string;
  connected: boolean;
}

interface OSCoreProps {
  inputMcps: MCP[];
  outputMcps: MCP[];
  dragging: MCP | null;
  dropZone: 'input' | 'output' | null;
  onDrop: (zone: 'input' | 'output') => void;
  onDropZoneEnter: (zone: 'input' | 'output') => void;
  onDropZoneLeave: () => void;
}

export default function OSCore({ inputMcps, outputMcps, dragging, dropZone, onDrop, onDropZoneEnter, onDropZoneLeave }: OSCoreProps) {
  return (
    <div className="border rounded-xl overflow-hidden" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
      {/* Header */}
      <div className="p-6 border-b" style={{ backgroundColor: colors.dark, borderColor: colors.dark }}>
        <div className="flex items-center justify-center gap-2">
          <Cpu className="w-5 h-5" style={{ color: colors.light }} />
          <h2 className="text-xl font-semibold" style={{ color: colors.light, fontFamily: fonts.heading }}>
            0711-OS
          </h2>
        </div>
        <p className="text-center text-xs mt-1" style={{ color: colors.midGray, fontFamily: fonts.body }}>
          Intelligence Operating System
        </p>
      </div>

      {/* Drop Zones */}
      <div className="p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {/* Input Drop Zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); onDropZoneEnter('input'); }}
            onDragLeave={onDropZoneLeave}
            onDrop={(e) => { e.preventDefault(); onDrop('input'); }}
            className="p-6 rounded-lg border-2 border-dashed transition-all"
            style={{
              borderColor: dropZone === 'input' ? colors.orange : colors.lightGray,
              backgroundColor: dropZone === 'input' ? colors.orange + '08' : colors.dark + '03'
            }}
          >
            <div className="text-center mb-4">
              <div className="inline-flex w-10 h-10 rounded-lg border items-center justify-center mb-2" style={{ backgroundColor: colors.dark + '05', borderColor: colors.lightGray }}>
                <ArrowRight className="w-5 h-5" style={{ color: colors.midGray }} />
              </div>
              <h4 className="font-semibold text-xs mb-1" style={{ color: colors.dark, fontFamily: fonts.heading }}>Input Zone</h4>
              <p className="text-xs" style={{ color: colors.midGray, fontFamily: fonts.body }}>Drop sources here</p>
            </div>

            <div className="space-y-2">
              {inputMcps.length === 0 ? (
                <p className="text-center text-xs py-4" style={{ color: colors.midGray }}>No inputs</p>
              ) : (
                inputMcps.map((mcp) => <MCPConnectionBadge key={mcp.id} mcp={mcp} type="input" />)
              )}
            </div>
          </div>

          {/* Output Drop Zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); onDropZoneEnter('output'); }}
            onDragLeave={onDropZoneLeave}
            onDrop={(e) => { e.preventDefault(); onDrop('output'); }}
            className="p-6 rounded-lg border-2 border-dashed transition-all"
            style={{
              borderColor: dropZone === 'output' ? colors.orange : colors.lightGray,
              backgroundColor: dropZone === 'output' ? colors.orange + '08' : colors.dark + '03'
            }}
          >
            <div className="text-center mb-4">
              <div className="inline-flex w-10 h-10 rounded-lg border items-center justify-center mb-2" style={{ backgroundColor: colors.dark + '05', borderColor: colors.lightGray }}>
                <Network className="w-5 h-5" style={{ color: colors.midGray }} />
              </div>
              <h4 className="font-semibold text-xs mb-1" style={{ color: colors.dark, fontFamily: fonts.heading }}>Output Zone</h4>
              <p className="text-xs" style={{ color: colors.midGray, fontFamily: fonts.body }}>Drop services here</p>
            </div>

            <div className="space-y-2">
              {outputMcps.length === 0 ? (
                <p className="text-center text-xs py-4" style={{ color: colors.midGray }}>No outputs</p>
              ) : (
                outputMcps.map((mcp) => <MCPConnectionBadge key={mcp.id} mcp={mcp} type="output" />)
              )}
            </div>
          </div>
        </div>

        {/* Lakehouse Status */}
        <div className="border rounded-lg p-4" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
          <div className="flex items-center gap-2 mb-3">
            <Database className="w-4 h-4" style={{ color: colors.midGray }} />
            <h4 className="font-semibold text-xs" style={{ color: colors.dark, fontFamily: fonts.heading }}>Lakehouse</h4>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs" style={{ color: colors.midGray, fontFamily: fonts.body }}>
            <div>Vector: Ready</div>
            <div>SQL: Ready</div>
            <div>Graph: Ready</div>
          </div>
        </div>
      </div>
    </div>
  );
}
