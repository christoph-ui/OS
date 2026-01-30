'use client';

import { useState, useEffect } from 'react';
import { Database, Cpu, Network } from 'lucide-react';
import MCPConnectPanel from './MCPConnectPanel';
import OSCore from './OSCore';
import { colors, fonts } from './theme';

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
  connected_direction?: string;
}

interface ConnectionData {
  input: MCP[];
  output: MCP[];
  summary: {
    total_subscribed: number;
    total_connected: number;
    input_connected: number;
    output_connected: number;
  };
}

export default function MCPConnectionDashboard() {
  const [connections, setConnections] = useState<ConnectionData>({
    input: [],
    output: [],
    summary: { total_subscribed: 0, total_connected: 0, input_connected: 0, output_connected: 0 }
  });
  const [loading, setLoading] = useState(true);
  const [dragging, setDragging] = useState<MCP | null>(null);
  const [dropZone, setDropZone] = useState<'input' | 'output' | null>(null);

  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      const response = await fetch('http://localhost:4010/api/mcp/marketplace/connections', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('0711_token')}` }
      });
      const data = await response.json();
      if (data.success) setConnections(data);
    } catch (error) {
      console.error('Error loading connections:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = async (zone: 'input' | 'output') => {
    if (!dragging) return;
    try {
      const params = new URLSearchParams({ mcp_name: dragging.name, direction: zone });
      const response = await fetch(`http://localhost:4010/api/mcp/marketplace/connect?${params}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('0711_token')}` }
      });
      if ((await response.json()).success) await loadConnections();
    } catch (error) {
      console.error('Error connecting MCP:', error);
    } finally {
      setDragging(null);
      setDropZone(null);
    }
  };

  const handleDisconnect = async (mcpName: string) => {
    try {
      const response = await fetch(`http://localhost:4010/api/mcp/marketplace/disconnect/${mcpName}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('0711_token')}` }
      });
      if ((await response.json()).success) await loadConnections();
    } catch (error) {
      console.error('Error disconnecting:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full" style={{ minHeight: '500px', backgroundColor: colors.light }}>
        <div className="text-center">
          <div className="w-10 h-10 border-3 rounded-full animate-spin mx-auto mb-4" style={{ borderColor: colors.lightGray, borderTopColor: colors.orange }}></div>
          <p style={{ color: colors.midGray, fontFamily: fonts.body }}>Loading connections...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: colors.light, padding: '40px', minHeight: '100%' }}>
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-10">
        <h1 className="text-3xl font-semibold mb-2" style={{ color: colors.dark, fontFamily: fonts.heading }}>
          MCP Connections
        </h1>
        <p style={{ color: colors.midGray, fontFamily: fonts.body, fontSize: '15px' }}>
          {connections.summary.total_connected} of {connections.summary.total_subscribed} MCPs connected
        </p>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mt-8">
          {[
            { label: 'Input MCPs', value: connections.summary.input_connected, icon: Database },
            { label: 'Output MCPs', value: connections.summary.output_connected, icon: Network },
            { label: 'Total Active', value: connections.summary.total_connected, icon: Cpu }
          ].map((stat, idx) => (
            <div key={idx} className="border rounded-lg p-4" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
              <div className="flex items-center gap-2 mb-2">
                <stat.icon className="w-4 h-4" style={{ color: colors.midGray }} />
                <span className="text-xs" style={{ color: colors.midGray, fontFamily: fonts.heading }}>{stat.label}</span>
              </div>
              <div className="text-2xl font-semibold" style={{ color: colors.dark, fontFamily: fonts.heading }}>{stat.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 3-Column Layout */}
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-3">
            <MCPConnectPanel
              type="input"
              mcps={connections.input}
              onDragStart={setDragging}
              onDragEnd={() => { setDragging(null); setDropZone(null); }}
              onDisconnect={handleDisconnect}
            />
          </div>

          <div className="col-span-6">
            <OSCore
              inputMcps={connections.input.filter(m => m.connected)}
              outputMcps={connections.output.filter(m => m.connected)}
              dragging={dragging}
              dropZone={dropZone}
              onDrop={handleDrop}
              onDropZoneEnter={setDropZone}
              onDropZoneLeave={() => setDropZone(null)}
            />
          </div>

          <div className="col-span-3">
            <MCPConnectPanel
              type="output"
              mcps={connections.output}
              onDragStart={setDragging}
              onDragEnd={() => { setDragging(null); setDropZone(null); }}
              onDisconnect={handleDisconnect}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
