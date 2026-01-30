'use client';

import { useState } from 'react';
import MCPsView from './MCPsView';
import MCPConnectionDashboard from './mcps/MCPConnectionDashboard';
import MCPMarketplace from './mcps/MCPMarketplace';

interface MCPsContainerProps {
  onQuestionClick: (question: string) => void;
  onSwitchToChat: () => void;
}

// Anthropic Brand Colors (matching page.tsx)
const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
};

export default function MCPsContainer({ onQuestionClick, onSwitchToChat }: MCPsContainerProps) {
  const [activeTab, setActiveTab] = useState<'marketplace' | 'connections' | 'tools'>('marketplace');

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Sub-Navigation Tabs */}
      <div style={{
        display: 'flex',
        gap: 8,
        padding: '24px 40px 0',
        backgroundColor: colors.light,
      }}>
        <button
          onClick={() => setActiveTab('marketplace')}
          style={{
            padding: '14px 28px',
            border: 'none',
            borderRadius: '12px 12px 0 0',
            fontSize: 15,
            fontWeight: 500,
            fontFamily: "'Lora', Georgia, serif",
            cursor: 'pointer',
            backgroundColor: activeTab === 'marketplace' ? colors.orange : 'transparent',
            color: activeTab === 'marketplace' ? '#fff' : colors.midGray,
            transition: 'all 0.2s ease',
            position: 'relative',
            borderBottom: activeTab === 'marketplace' ? `3px solid ${colors.orange}` : '3px solid transparent',
          }}
          onMouseEnter={(e) => {
            if (activeTab !== 'marketplace') {
              e.currentTarget.style.backgroundColor = `${colors.orange}15`;
              e.currentTarget.style.color = colors.orange;
            }
          }}
          onMouseLeave={(e) => {
            if (activeTab !== 'marketplace') {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = colors.midGray;
            }
          }}
        >
          🏪 Marketplace
        </button>
        <button
          onClick={() => setActiveTab('connections')}
          style={{
            padding: '14px 28px',
            border: 'none',
            borderRadius: '12px 12px 0 0',
            fontSize: 15,
            fontWeight: 500,
            fontFamily: "'Lora', Georgia, serif",
            cursor: 'pointer',
            backgroundColor: activeTab === 'connections' ? colors.orange : 'transparent',
            color: activeTab === 'connections' ? '#fff' : colors.midGray,
            transition: 'all 0.2s ease',
            position: 'relative',
            borderBottom: activeTab === 'connections' ? `3px solid ${colors.orange}` : '3px solid transparent',
          }}
          onMouseEnter={(e) => {
            if (activeTab !== 'connections') {
              e.currentTarget.style.backgroundColor = `${colors.orange}15`;
              e.currentTarget.style.color = colors.orange;
            }
          }}
          onMouseLeave={(e) => {
            if (activeTab !== 'connections') {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = colors.midGray;
            }
          }}
        >
          🔌 Connections
        </button>
        <button
          onClick={() => setActiveTab('tools')}
          style={{
            padding: '14px 28px',
            border: 'none',
            borderRadius: '12px 12px 0 0',
            fontSize: 15,
            fontWeight: 500,
            fontFamily: "'Lora', Georgia, serif",
            cursor: 'pointer',
            backgroundColor: activeTab === 'tools' ? colors.orange : 'transparent',
            color: activeTab === 'tools' ? '#fff' : colors.midGray,
            transition: 'all 0.2s ease',
            position: 'relative',
            borderBottom: activeTab === 'tools' ? `3px solid ${colors.orange}` : '3px solid transparent',
          }}
          onMouseEnter={(e) => {
            if (activeTab !== 'tools') {
              e.currentTarget.style.backgroundColor = `${colors.orange}15`;
              e.currentTarget.style.color = colors.orange;
            }
          }}
          onMouseLeave={(e) => {
            if (activeTab !== 'tools') {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = colors.midGray;
            }
          }}
        >
          🛠️ Tools
        </button>
      </div>

      {/* Subtle Border Below Tabs */}
      <div style={{
        height: 2,
        backgroundColor: colors.lightGray,
        marginBottom: 0,
      }} />

      {/* Content Area */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {activeTab === 'marketplace' && (
          <MCPMarketplace />
        )}

        {activeTab === 'connections' && (
          <MCPConnectionDashboard />
        )}

        {activeTab === 'tools' && (
          <div style={{ backgroundColor: colors.light }}>
            <MCPsView
              onQuestionClick={onQuestionClick}
              onSwitchToChat={onSwitchToChat}
            />
          </div>
        )}
      </div>
    </div>
  );
}
