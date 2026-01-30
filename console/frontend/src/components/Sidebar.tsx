'use client';

import {
  MessageSquare,
  Database,
  Puzzle,
  Upload,
  ChevronDown,
} from 'lucide-react';

type View = 'chat' | 'data' | 'mcps' | 'ingest';

interface SidebarProps {
  currentView: View;
  onViewChange: (view: View) => void;
  activeMCP: string | null;
  onMCPChange: (mcp: string | null) => void;
}

const CORE_MCPS = [
  { id: 'ctax', name: 'CTAX', description: 'German Tax' },
  { id: 'law', name: 'LAW', description: 'Legal Analysis' },
  { id: 'tender', name: 'TENDER', description: 'RFP Processing' },
];

export default function Sidebar({
  currentView,
  onViewChange,
  activeMCP,
  onMCPChange,
}: SidebarProps) {
  const navItems = [
    { id: 'chat' as View, icon: MessageSquare, label: 'Chat' },
    { id: 'data' as View, icon: Database, label: 'Data' },
    { id: 'mcps' as View, icon: Puzzle, label: 'MCPs' },
    { id: 'ingest' as View, icon: Upload, label: 'Ingest' },
  ];

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-800">0711</h1>
        <p className="text-xs text-gray-500">Intelligence Platform</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onViewChange(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                  currentView === item.id
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            </li>
          ))}
        </ul>

        {/* MCP Selector */}
        <div className="mt-6">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3 mb-2">
            Active MCP
          </h3>
          <div className="relative">
            <select
              value={activeMCP || ''}
              onChange={(e) => onMCPChange(e.target.value || null)}
              className="w-full appearance-none bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">Auto (detect from query)</option>
              {CORE_MCPS.map((mcp) => (
                <option key={mcp.id} value={mcp.id}>
                  {mcp.name} - {mcp.description}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-400">
          <p>Core MCPs: CTAX, LAW, TENDER</p>
          <p className="mt-1">vLLM + Mixtral 8x7B</p>
        </div>
      </div>
    </aside>
  );
}
