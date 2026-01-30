'use client';

import { useState } from 'react';
import '../styles/admin.css';

type Screen = 'workspace' | 'admin';
type Client = {
  id: string;
  name: string;
  case: string;
  mcps: string[];
  active?: boolean;
};

type Message = {
  type: 'user' | 'ai' | 'system';
  content: string;
  time: string;
  mcp?: string;
};

export default function AdminConsole() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('workspace');
  const [selectedClient, setSelectedClient] = useState<Client>({
    id: '1',
    name: 'Müller GmbH',
    case: 'USt-Voranmeldung Q4',
    mcps: ['CTAX'],
    active: true,
  });

  const clients: Client[] = [
    {
      id: '1',
      name: 'Müller GmbH',
      case: 'USt-Voranmeldung Q4',
      mcps: ['CTAX'],
      active: true,
    },
    {
      id: '2',
      name: 'Schmidt AG',
      case: 'Jahresabschluss 2024',
      mcps: ['CTAX', 'LAW'],
    },
    {
      id: '3',
      name: 'TechStart UG',
      case: 'Gründungsberatung',
      mcps: ['CTAX', 'LAW'],
    },
    {
      id: '4',
      name: 'Bosch Thermotechnik',
      case: 'Produktdaten-Klassifikation',
      mcps: ['ETIM'],
    },
    {
      id: '5',
      name: 'DAX Consulting',
      case: 'Sanctions Screening',
      mcps: ['SANCTION', 'LAW'],
    },
  ];

  const messages: Message[] = [
    {
      type: 'system',
      content: 'CTAX verbunden • Mandantendaten geladen • Bereit für Bearbeitung',
      time: '',
    },
    {
      type: 'user',
      content:
        'Prüfe bitte die USt-Voranmeldung für Q4 2024. Besonders die Vorsteuerabzüge.',
      time: '14:23',
    },
    {
      type: 'ai',
      content: `Ich habe die Q4 Daten analysiert. Hier meine Erkenntnisse:

**Vorsteuerabzüge:** €12.847,32 aus 47 Rechnungen
**Auffälligkeit:** Rechnung #2024-089 (€2.340,00) – fehlende USt-IdNr des Lieferanten
**Empfehlung:** USt-IdNr anfordern vor Einreichung

Die restlichen Positionen sind korrekt. Soll ich den Entwurf erstellen?`,
      time: '14:24',
      mcp: 'CTAX',
    },
    {
      type: 'user',
      content:
        'Ja, erstelle den Entwurf. Die fehlende USt-IdNr wurde mittlerweile nachgereicht.',
      time: '14:26',
    },
    {
      type: 'ai',
      content: `USt-Voranmeldung Q4 2024 erstellt.

**Zusammenfassung:**
• Umsatzsteuer: €24.156,84
• Vorsteuer: €12.847,32
• Zahllast: €11.309,52
• Fälligkeit: 10.02.2025

Das Dokument ist bereit zur Übermittlung an ELSTER.`,
      time: '14:27',
      mcp: 'CTAX',
    },
  ];

  const mcps = [
    { name: 'CTAX Core', port: '9010', status: 'active' },
    { name: 'Law Analysis', port: '9014', status: 'idle' },
    { name: 'ETIM', port: '9013', status: 'idle' },
    { name: 'Sanctions', port: '9015', status: 'idle' },
  ];

  return (
    <div className="app">
      {/* Navigation */}
      <nav className="nav-tabs">
        <div className="nav-logo">
          0711 <span>Expert</span>
        </div>
        <div
          className={`nav-tab ${currentScreen === 'workspace' ? 'active' : ''}`}
          onClick={() => setCurrentScreen('workspace')}
        >
          Arbeitsbereich
        </div>
        <div
          className={`nav-tab ${currentScreen === 'admin' ? 'active' : ''}`}
          onClick={() => setCurrentScreen('admin')}
        >
          Verwaltung
        </div>
        <div className="nav-user">
          <div className="nav-avatar">MS</div>
        </div>
      </nav>

      {/* Workspace Screen */}
      {currentScreen === 'workspace' && (
        <div className="screen active">
          <div className="agent-workspace">
            {/* Client Sidebar */}
            <aside className="client-sidebar">
              <div className="sidebar-header">
                <div className="sidebar-title">Meine Mandanten</div>
                <div className="search-box">
                  <span className="search-icon">🔍</span>
                  <input type="text" placeholder="Suchen..." />
                </div>
              </div>
              <div className="client-list">
                {clients.map((client) => (
                  <div
                    key={client.id}
                    className={`client-item ${client.active ? 'active' : ''}`}
                    onClick={() => setSelectedClient(client)}
                  >
                    <div className="client-name">{client.name}</div>
                    <div className="client-case">{client.case}</div>
                    <div className="client-mcps">
                      {client.mcps.map((mcp) => (
                        <span
                          key={mcp}
                          className={`mcp-tag ${mcp.toLowerCase()}`}
                        >
                          {mcp}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </aside>

            {/* Chat Area */}
            <main className="chat-area">
              <header className="chat-header">
                <div className="chat-client-info">
                  <h2>{selectedClient.name}</h2>
                  <p>{selectedClient.case}</p>
                </div>
                <div className="chat-actions">
                  <button className="btn btn-secondary">Dokumente</button>
                  <button className="btn btn-primary">Abschließen</button>
                </div>
              </header>

              <div className="chat-messages">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`message message-${msg.type}`}>
                    <div className="message-bubble">
                      {msg.content.split('\n').map((line, i) => (
                        <span key={i}>
                          {line}
                          {i < msg.content.split('\n').length - 1 && <br />}
                        </span>
                      ))}
                    </div>
                    {msg.time && (
                      <div className="message-meta">
                        {msg.time}
                        {msg.mcp && (
                          <span className="mcp-used">● {msg.mcp}</span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="chat-input-area">
                <div className="chat-input-wrapper">
                  <textarea
                    className="chat-input"
                    placeholder="Nachricht eingeben..."
                    rows={1}
                  />
                  <button className="send-btn">→</button>
                </div>
              </div>
            </main>

            {/* MCP Status Panel */}
            <aside className="mcp-panel">
              <div className="mcp-panel-header">
                <h3>Verbundene MCPs</h3>
              </div>
              <div className="mcp-list">
                {mcps.map((mcp, idx) => (
                  <div
                    key={idx}
                    className="mcp-item"
                    style={{ opacity: mcp.status === 'idle' ? 0.5 : 1 }}
                  >
                    <div className="mcp-name">
                      <span
                        className={`status-dot status-${mcp.status}`}
                      ></span>
                      {mcp.name}
                    </div>
                    <span className="mcp-port">:{mcp.port}</span>
                  </div>
                ))}
              </div>

              <div className="context-section">
                <div className="context-title">Mandanten-Kontext</div>
                <div className="context-card">
                  <div className="context-label">Rechtsform</div>
                  <div className="context-value">GmbH</div>
                </div>
                <div className="context-card">
                  <div className="context-label">Umsatz 2024</div>
                  <div className="context-value positive">€847K</div>
                </div>
                <div className="context-card">
                  <div className="context-label">Offene Vorgänge</div>
                  <div className="context-value">3</div>
                </div>
              </div>
            </aside>
          </div>
        </div>
      )}

      {/* Admin Screen */}
      {currentScreen === 'admin' && (
        <div className="screen active">
          <div className="admin-panel">
            <header className="admin-header">
              <div>
                <h1>Systemverwaltung</h1>
                <p className="admin-subtitle">
                  MCPs, Benutzer und Mandanten verwalten
                </p>
              </div>
            </header>

            {/* Stats */}
            <div className="stats-row">
              <div className="stat-card">
                <div className="stat-label">Aktive MCPs</div>
                <div className="stat-value">6</div>
                <div className="stat-change positive">Alle online</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Agenten</div>
                <div className="stat-value">4</div>
                <div className="stat-change">3 online</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Mandanten</div>
                <div className="stat-value">127</div>
                <div className="stat-change positive">+5 diese Woche</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Vorgänge/Tag</div>
                <div className="stat-value">342</div>
                <div className="stat-change positive">↑ 12%</div>
              </div>
            </div>

            {/* MCP Management */}
            <div className="admin-sections">
              <div className="admin-section full-width">
                <div className="section-header">
                  <h2>MCP Server</h2>
                  <button className="btn btn-primary">+ MCP hinzufügen</button>
                </div>
                <div className="section-content">
                  <div className="mcp-row header">
                    <div>Port</div>
                    <div>Name / Beschreibung</div>
                    <div>Status</div>
                    <div>Aktionen</div>
                  </div>
                  {[
                    {
                      port: '9010',
                      name: 'CTAX Core',
                      desc: 'Einkommensteuer, Umsatzsteuer, Voranmeldungen',
                      status: 'active',
                    },
                    {
                      port: '9011',
                      name: 'CTAX Business',
                      desc: 'Gewerbesteuer, Körperschaftsteuer',
                      status: 'active',
                    },
                    {
                      port: '9013',
                      name: 'ETIM Classification',
                      desc: 'Produktklassifikation ETIM/ECLASS',
                      status: 'busy',
                    },
                    {
                      port: '9014',
                      name: 'Law Analysis',
                      desc: 'Verträge, Compliance, Rechtsprüfung',
                      status: 'active',
                    },
                    {
                      port: '9015',
                      name: 'Sanctions Screening',
                      desc: 'OFAC, EU, UK Sanktionslisten',
                      status: 'active',
                    },
                  ].map((mcp, idx) => (
                    <div key={idx} className="mcp-row">
                      <div className="mcp-row-port">{mcp.port}</div>
                      <div>
                        <div className="mcp-row-name">{mcp.name}</div>
                        <div className="mcp-row-desc">{mcp.desc}</div>
                      </div>
                      <div className="mcp-row-status">
                        <span
                          className={`status-dot status-${mcp.status}`}
                        ></span>{' '}
                        {mcp.status === 'active'
                          ? 'Online'
                          : mcp.status === 'busy'
                          ? 'Busy'
                          : 'Idle'}
                      </div>
                      <div className="mcp-row-actions">
                        <button className="icon-btn">⚙️</button>
                        <button className="icon-btn">📊</button>
                        <button className="icon-btn">⏸️</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
