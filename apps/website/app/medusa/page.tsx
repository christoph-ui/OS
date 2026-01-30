'use client';

import { useState } from 'react';

// Get API URL from environment variable (production-safe)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4080';

export default function MedusaPage() {
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    company: '',
    phone: '',
    address: '',
    city: '',
    postal_code: '',
    country: 'DE'
  });
  const [downloadToken, setDownloadToken] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    try {
      const response = await fetch('/api/medusa/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setDownloadToken(data.download_token);
        window.location.href = `${API_URL}/api/medusa/download/${data.download_token}`;
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const tools = {
    terminal: [
      { name: 'bridge_read_terminal', desc: 'Read recent output from a Claude Code terminal. Essential for seeing what Claude Code is doing without switching apps.' },
      { name: 'bridge_send_text', desc: 'Send text input to a Claude Code terminal. Type text as if at the keyboard. Can optionally press Enter after.' },
      { name: 'bridge_send_key', desc: 'Send special keys like Enter, Ctrl+C, Escape, Tab, and arrow keys to the terminal.' },
      { name: 'bridge_search_output', desc: 'Search terminal output for patterns using regex. Find errors, warnings, or any text in recent output.' },
      { name: 'bridge_sync_remote', desc: 'Sync logs from remote SSH projects. Fetch latest terminal output from the server.' },
    ],
    projects: [
      { name: 'bridge_list_projects', desc: 'List all configured projects. Shows type (local/remote), path, and status. Indicates which is active.' },
      { name: 'bridge_add_project', desc: 'Add a new Claude Code project. Configure for local Mac terminal or remote SSH connection.' },
      { name: 'bridge_remove_project', desc: 'Remove a project from the bridge. Removes configuration only — does not delete actual files.' },
      { name: 'bridge_switch_project', desc: 'Switch to a different active project. Changes which project receives commands by default.' },
      { name: 'bridge_get_project_status', desc: 'Get detailed status including running state, recent activity, error counts, and pending approvals.' },
    ],
    approval: [
      { name: 'bridge_list_pending', desc: 'List all pending approval requests. Shows commands waiting for your review with context and risk levels.' },
      { name: 'bridge_request_approval', desc: 'Submit a command for approval. Typically called by Claude Code when it wants to run something risky.' },
      { name: 'bridge_approve', desc: 'Approve a pending request. Marks as approved and optionally sends \'y\' to the terminal to proceed.' },
      { name: 'bridge_deny', desc: 'Deny a pending request. Marks as denied and optionally sends \'n\' to the terminal.' },
    ],
    rules: [
      { name: 'bridge_list_rules', desc: 'List all auto-approve rules. Shows patterns that automatically approve matching commands.' },
      { name: 'bridge_add_rule', desc: 'Add an auto-approve rule. Commands matching the pattern are automatically approved (except critical risk).' },
      { name: 'bridge_remove_rule', desc: 'Remove an auto-approve rule. The rule will no longer match commands.' },
      { name: 'bridge_toggle_rule', desc: 'Enable or disable an auto-approve rule without removing it.' },
    ],
    alerts: [
      { name: 'bridge_watch_for', desc: 'Set up a pattern alert. Watch for specific regex patterns in terminal output and get notified.' },
      { name: 'bridge_stop_watching', desc: 'Remove a pattern alert. The pattern will no longer be monitored.' },
      { name: 'bridge_get_alerts', desc: 'Get all alerts or only triggered alerts. See which patterns have matched.' },
      { name: 'bridge_clear_alerts', desc: 'Reset triggered alerts so they can trigger again. Does not remove the alerts.' },
    ],
    watchdog: [
      { name: 'bridge_watchdog_status', desc: 'Get watchdog status. Shows enabled state, pattern count, violation count, and all detection patterns.' },
      { name: 'bridge_watchdog_enable', desc: 'Enable the watchdog. Starts monitoring all terminals every 2 seconds. Sends ESC on violations.' },
      { name: 'bridge_watchdog_disable', desc: 'Disable the watchdog. Stops monitoring. Existing violations remain in history.' },
      { name: 'bridge_watchdog_add_pattern', desc: 'Add a custom detection pattern. Define additional behaviors to monitor beyond defaults.' },
      { name: 'bridge_watchdog_remove_pattern', desc: 'Remove a custom pattern. Only custom patterns can be removed — defaults are protected.' },
      { name: 'bridge_watchdog_violations', desc: 'Get violation history. See what shortcuts were caught, when, and what text triggered them.' },
    ],
    taskbible: [
      { name: 'bridge_get_task_bible', desc: 'Get the active task bible. Returns current task list with progress for a project.' },
      { name: 'bridge_get_next_task', desc: 'Get the next task to work on. Respects dependencies and priorities to suggest what\'s next.' },
      { name: 'bridge_update_task_status', desc: 'Update a task\'s status. Mark as in_progress, completed, blocked, or cancelled.' },
      { name: 'bridge_add_task_note', desc: 'Add a progress note to a task. Document work done or issues encountered.' },
      { name: 'bridge_check_dependencies', desc: 'Check task dependencies. See what must be completed before a specific task can start.' },
    ],
    setup: [
      { name: 'setup_detect_folders', desc: 'Automatically detect project folders. Scans Desktop, Documents, Code for development folders.' },
      { name: 'setup_add_folder', desc: 'Add a project folder to Medusa configuration. Configure with custom name and terminal app.' },
      { name: 'setup_get_status', desc: 'Check overall setup status. See what\'s configured and what steps remain.' },
      { name: 'setup_run_complete', desc: 'Run automated setup process. Checks Claude Desktop, configures MCP server, restarts if needed.' },
      { name: 'setup_test_api_key', desc: 'Validate an API key before saving. Test OpenAI, Google AI, or Anthropic keys.' },
    ],
  };

  return (
    <div style={{ fontFamily: '"Crimson Pro", Georgia, serif', background: '#050505', color: '#F5F0E6', minHeight: '100vh' }}>
      {/* Navigation */}
      <nav style={{ position: 'fixed', top: 0, width: '100%', padding: '2rem 4%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', zIndex: 1000, background: 'linear-gradient(to bottom, #050505, transparent)' }}>
        <a href="/" style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '1.4rem', letterSpacing: '0.2em', color: '#F5F0E6', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: 32, height: 32, border: '2px solid currentColor', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem' }}>07</div>
          MEDUSA
        </a>
        <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.7rem', letterSpacing: '0.2em', textTransform: 'uppercase', color: '#C9A227' }}>
          39 MCP Tools
        </div>
      </nav>

      {/* Hero */}
      <section style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '8rem 6%' }}>
        <h1 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(4rem, 12vw, 9rem)', lineHeight: 0.9, marginBottom: '2rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
          <span style={{ color: '#C9A227' }}>0711</span> MEDUSA
        </h1>
        <p style={{ fontSize: 'clamp(1.4rem, 2.5vw, 1.8rem)', maxWidth: 700, marginBottom: '0.5rem', fontStyle: 'italic' }}>
          "Today, we're introducing something that changes the way you build software with AI."
        </p>
        <p style={{ fontSize: '1.1rem', color: '#A69F94', marginBottom: '3rem' }}>
          Claude Desktop. Claude Code. Finally, together.
        </p>
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'center' }}>
          <button
            onClick={() => setShowForm(true)}
            style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.9rem', letterSpacing: '0.2em', textTransform: 'uppercase', background: '#C9A227', color: '#050505', padding: '1.8rem 4rem', border: 'none', cursor: 'pointer', transition: 'all 0.4s' }}
          >
            Download for macOS
          </button>
        </div>
      </section>

      {/* Features Overview */}
      <section style={{ padding: '10rem 6%', background: '#1a1a1a' }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.7rem', letterSpacing: '0.3em', textTransform: 'uppercase', color: '#C9A227', marginBottom: '3rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ width: 40, height: 1, background: '#C9A227' }} />
            The Features
          </div>
          <h2 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(2.5rem, 5vw, 4rem)', marginBottom: '4rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            Six Breakthroughs.<br />One Application.
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2px', background: '#2a2a2a' }}>
            {[
              { num: '01', title: 'Bidirectional Bridge', desc: 'Claude Desktop can see and control Claude Code. Real-time terminal visibility. 39 MCP tools for complete control.' },
              { num: '02', title: 'Behavior Watchdog', desc: 'AI cuts corners. Medusa catches it. 20+ behavior patterns detect laziness, placeholders, and shortcuts.' },
              { num: '03', title: 'Approval Gates', desc: 'Risky operations queue for approval. Total control without constant interruption. Custom rules for trusted patterns.' },
              { num: '04', title: 'Task Bible', desc: 'Complex projects. Perfect memory forever. Claude knows what\'s done, what\'s next, what\'s blocked.' },
              { num: '05', title: 'Smart Alerts', desc: 'Regex-based pattern matching catches errors instantly. Never miss another failure. Configurable triggers.' },
              { num: '06', title: 'Native macOS', desc: 'Built with Electron. Professional DMG installer. First-class citizen on your Mac. Spotlight searchable.' },
            ].map((feature) => (
              <div key={feature.num} style={{ background: '#0d0d0d', padding: '4rem' }}>
                <div style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '4rem', color: '#2a2a2a', lineHeight: 1, marginBottom: '1.5rem' }}>{feature.num}</div>
                <h3 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '2rem', marginBottom: '1.5rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{feature.title}</h3>
                <p style={{ color: '#A69F94', fontSize: '1.1rem', lineHeight: 1.8 }}>{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tools Documentation */}
      <section style={{ padding: '10rem 6%', background: '#050505' }}>
        <div style={{ maxWidth: 1400, margin: '0 auto', textAlign: 'center', marginBottom: '6rem' }}>
          <h2 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(3rem, 8vw, 6rem)', lineHeight: 1, marginBottom: '1.5rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            <span style={{ color: '#C9A227' }}>39</span> MCP Tools
          </h2>
          <p style={{ fontSize: '1.3rem', color: '#A69F94', maxWidth: 600, margin: '0 auto' }}>
            Complete reference for every tool in 0711 Medusa. Terminal control, behavior monitoring, approval gates, task management, and more.
          </p>
        </div>

        {/* Terminal Operations */}
        <div style={{ maxWidth: 1400, margin: '0 auto', marginBottom: '8rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '2rem', alignItems: 'start', marginBottom: '4rem' }}>
            <div style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '6rem', color: '#2a2a2a', lineHeight: 0.8 }}>01</div>
            <div>
              <h3 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(2rem, 4vw, 3rem)', marginBottom: '1rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Terminal Operations</h3>
              <p style={{ fontSize: '1.1rem', color: '#A69F94', maxWidth: 600 }}>Control and monitor Claude Code terminals directly from Claude Desktop. Read output, send commands, search logs.</p>
              <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', color: '#C9A227', marginTop: '1rem', letterSpacing: '0.1em' }}>5 TOOLS</div>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '2px', background: '#2a2a2a' }}>
            {tools.terminal.map((tool) => (
              <div key={tool.name} style={{ background: '#0d0d0d', padding: '2.5rem' }}>
                <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '1rem', fontWeight: 600, color: '#C9A227', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#2a2a2a' }}>→</span> {tool.name}
                </div>
                <p style={{ color: '#F5F0E6', fontSize: '1rem', lineHeight: 1.7 }}>{tool.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Project Management */}
        <div style={{ maxWidth: 1400, margin: '0 auto', marginBottom: '8rem', padding: '6rem 0', background: '#1a1a1a', marginLeft: '-6%', marginRight: '-6%', paddingLeft: '6%', paddingRight: '6%' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '2rem', alignItems: 'start', marginBottom: '4rem' }}>
            <div style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '6rem', color: '#2a2a2a', lineHeight: 0.8 }}>02</div>
            <div>
              <h3 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(2rem, 4vw, 3rem)', marginBottom: '1rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Project Management</h3>
              <p style={{ fontSize: '1.1rem', color: '#A69F94', maxWidth: 600 }}>Manage multiple Claude Code projects across local and remote environments. Switch contexts, monitor status, add new projects.</p>
              <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', color: '#C9A227', marginTop: '1rem', letterSpacing: '0.1em' }}>5 TOOLS</div>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '2px', background: '#2a2a2a' }}>
            {tools.projects.map((tool) => (
              <div key={tool.name} style={{ background: '#050505', padding: '2.5rem' }}>
                <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '1rem', fontWeight: 600, color: '#C9A227', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#2a2a2a' }}>→</span> {tool.name}
                </div>
                <p style={{ color: '#F5F0E6', fontSize: '1rem', lineHeight: 1.7 }}>{tool.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Approval System */}
        <div style={{ maxWidth: 1400, margin: '0 auto', marginBottom: '8rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '2rem', alignItems: 'start', marginBottom: '4rem' }}>
            <div style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '6rem', color: '#2a2a2a', lineHeight: 0.8 }}>03</div>
            <div>
              <h3 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(2rem, 4vw, 3rem)', marginBottom: '1rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Approval System</h3>
              <p style={{ fontSize: '1.1rem', color: '#A69F94', maxWidth: 600 }}>Review and authorize risky operations before execution. Complete control over what Claude Code can run.</p>
              <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', color: '#C9A227', marginTop: '1rem', letterSpacing: '0.1em' }}>4 TOOLS</div>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '2px', background: '#2a2a2a' }}>
            {tools.approval.map((tool) => (
              <div key={tool.name} style={{ background: '#0d0d0d', padding: '2.5rem' }}>
                <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '1rem', fontWeight: 600, color: '#C9A227', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#2a2a2a' }}>→</span> {tool.name}
                </div>
                <p style={{ color: '#F5F0E6', fontSize: '1rem', lineHeight: 1.7 }}>{tool.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Auto-Approve Rules */}
        <div style={{ maxWidth: 1400, margin: '0 auto', marginBottom: '8rem', padding: '6rem 0', background: '#1a1a1a', marginLeft: '-6%', marginRight: '-6%', paddingLeft: '6%', paddingRight: '6%' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '2rem', alignItems: 'start', marginBottom: '4rem' }}>
            <div style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '6rem', color: '#2a2a2a', lineHeight: 0.8 }}>04</div>
            <div>
              <h3 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(2rem, 4vw, 3rem)', marginBottom: '1rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Auto-Approve Rules</h3>
              <p style={{ fontSize: '1.1rem', color: '#A69F94', maxWidth: 600 }}>Automatically approve trusted command patterns. Build rules for common operations to reduce interruptions.</p>
              <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', color: '#C9A227', marginTop: '1rem', letterSpacing: '0.1em' }}>4 TOOLS</div>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '2px', background: '#2a2a2a' }}>
            {tools.rules.map((tool) => (
              <div key={tool.name} style={{ background: '#050505', padding: '2.5rem' }}>
                <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '1rem', fontWeight: 600, color: '#C9A227', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#2a2a2a' }}>→</span> {tool.name}
                </div>
                <p style={{ color: '#F5F0E6', fontSize: '1rem', lineHeight: 1.7 }}>{tool.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Smart Alerts */}
        <div style={{ maxWidth: 1400, margin: '0 auto', marginBottom: '8rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '2rem', alignItems: 'start', marginBottom: '4rem' }}>
            <div style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '6rem', color: '#2a2a2a', lineHeight: 0.8 }}>05</div>
            <div>
              <h3 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(2rem, 4vw, 3rem)', marginBottom: '1rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Smart Alerts</h3>
              <p style={{ fontSize: '1.1rem', color: '#A69F94', maxWidth: 600 }}>Get notified when specific patterns appear in terminal output. Never miss another error or warning.</p>
              <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', color: '#C9A227', marginTop: '1rem', letterSpacing: '0.1em' }}>4 TOOLS</div>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '2px', background: '#2a2a2a' }}>
            {tools.alerts.map((tool) => (
              <div key={tool.name} style={{ background: '#0d0d0d', padding: '2.5rem' }}>
                <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '1rem', fontWeight: 600, color: '#C9A227', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#2a2a2a' }}>→</span> {tool.name}
                </div>
                <p style={{ color: '#F5F0E6', fontSize: '1rem', lineHeight: 1.7 }}>{tool.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Behavior Watchdog */}
        <div style={{ maxWidth: 1400, margin: '0 auto', marginBottom: '8rem', padding: '6rem 0', background: '#1a1a1a', marginLeft: '-6%', marginRight: '-6%', paddingLeft: '6%', paddingRight: '6%' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '2rem', alignItems: 'start', marginBottom: '4rem' }}>
            <div style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '6rem', color: '#2a2a2a', lineHeight: 0.8 }}>06</div>
            <div>
              <h3 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(2rem, 4vw, 3rem)', marginBottom: '1rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Behavior Watchdog</h3>
              <p style={{ fontSize: '1.1rem', color: '#A69F94', maxWidth: 600 }}>Detect and stop AI shortcuts, laziness, and placeholder code. 20+ patterns monitor for common AI mistakes.</p>
              <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', color: '#C9A227', marginTop: '1rem', letterSpacing: '0.1em' }}>6 TOOLS</div>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '2px', background: '#2a2a2a' }}>
            {tools.watchdog.map((tool) => (
              <div key={tool.name} style={{ background: '#050505', padding: '2.5rem' }}>
                <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '1rem', fontWeight: 600, color: '#C9A227', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#2a2a2a' }}>→</span> {tool.name}
                </div>
                <p style={{ color: '#F5F0E6', fontSize: '1rem', lineHeight: 1.7 }}>{tool.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Task Bible */}
        <div style={{ maxWidth: 1400, margin: '0 auto', marginBottom: '8rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '2rem', alignItems: 'start', marginBottom: '4rem' }}>
            <div style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '6rem', color: '#2a2a2a', lineHeight: 0.8 }}>07</div>
            <div>
              <h3 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(2rem, 4vw, 3rem)', marginBottom: '1rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Task Bible</h3>
              <p style={{ fontSize: '1.1rem', color: '#A69F94', maxWidth: 600 }}>Structured task management with persistence across sessions. Claude always knows what's done and what's next.</p>
              <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', color: '#C9A227', marginTop: '1rem', letterSpacing: '0.1em' }}>5 TOOLS</div>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '2px', background: '#2a2a2a' }}>
            {tools.taskbible.map((tool) => (
              <div key={tool.name} style={{ background: '#0d0d0d', padding: '2.5rem' }}>
                <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '1rem', fontWeight: 600, color: '#C9A227', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#2a2a2a' }}>→</span> {tool.name}
                </div>
                <p style={{ color: '#F5F0E6', fontSize: '1rem', lineHeight: 1.7 }}>{tool.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Setup Wizard */}
        <div style={{ maxWidth: 1400, margin: '0 auto', marginBottom: '8rem', padding: '6rem 0', background: '#1a1a1a', marginLeft: '-6%', marginRight: '-6%', paddingLeft: '6%', paddingRight: '6%' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '2rem', alignItems: 'start', marginBottom: '4rem' }}>
            <div style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '6rem', color: '#2a2a2a', lineHeight: 0.8 }}>08</div>
            <div>
              <h3 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(2rem, 4vw, 3rem)', marginBottom: '1rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Setup Wizard</h3>
              <p style={{ fontSize: '1.1rem', color: '#A69F94', maxWidth: 600 }}>Guide users through 0711 Medusa configuration. Auto-detect projects, test API keys, verify installation.</p>
              <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', color: '#C9A227', marginTop: '1rem', letterSpacing: '0.1em' }}>5 TOOLS</div>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '2px', background: '#2a2a2a' }}>
            {tools.setup.map((tool) => (
              <div key={tool.name} style={{ background: '#050505', padding: '2.5rem' }}>
                <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '1rem', fontWeight: 600, color: '#C9A227', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#2a2a2a' }}>→</span> {tool.name}
                </div>
                <p style={{ color: '#F5F0E6', fontSize: '1rem', lineHeight: 1.7 }}>{tool.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Free Section */}
      <section style={{ padding: '10rem 6%', textAlign: 'center', background: '#1a1a1a' }}>
        <h2 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(2rem, 4vw, 3rem)', color: '#A69F94', marginBottom: '2rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
          Oh, and <span style={{ color: '#C9A227' }}>one more thing</span>...
        </h2>
        <div style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: 'clamp(5rem, 12vw, 10rem)', color: '#C9A227', marginBottom: '2rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
          Completely Free.
        </div>
        <p style={{ fontSize: '1.3rem', color: '#A69F94', maxWidth: 700, margin: '0 auto 3rem' }}>
          <strong style={{ color: '#F5F0E6' }}>Open source.</strong> MIT licensed. No subscriptions. No premium tiers. No tricks. No catches.
        </p>
        <button
          onClick={() => setShowForm(true)}
          style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.9rem', letterSpacing: '0.2em', textTransform: 'uppercase', background: '#C9A227', color: '#050505', padding: '1.8rem 4rem', border: 'none', cursor: 'pointer', transition: 'all 0.4s' }}
        >
          Download for macOS
        </button>
      </section>

      {/* Registration Modal */}
      {showForm && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(5, 5, 5, 0.95)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000, padding: '2rem', overflowY: 'auto' }}>
          <div style={{ background: '#1a1a1a', padding: '3rem', maxWidth: 600, width: '100%', border: '1px solid #2a2a2a', position: 'relative', margin: 'auto' }}>
            <button
              onClick={() => setShowForm(false)}
              style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', color: '#A69F94', fontSize: '2rem', cursor: 'pointer', lineHeight: 1 }}
            >
              ×
            </button>
            <h2 style={{ fontFamily: '"Bebas Neue", sans-serif', fontSize: '3rem', marginBottom: '1rem', letterSpacing: '0.05em', textTransform: 'uppercase', color: '#C9A227' }}>
              Download Medusa
            </h2>
            <p style={{ color: '#A69F94', marginBottom: '2rem' }}>
              Fill out the form below to download 0711 Medusa for macOS
            </p>
            {error && (
              <div style={{ background: '#cc4444', color: '#F5F0E6', padding: '1rem', marginBottom: '1rem', fontSize: '0.9rem' }}>
                {error}
              </div>
            )}
            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Email *</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  style={{ width: '100%', padding: '1rem', background: '#0d0d0d', border: '1px solid #2a2a2a', color: '#F5F0E6', fontSize: '1rem', fontFamily: '"Crimson Pro", Georgia, serif' }}
                />
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Full Name *</label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  style={{ width: '100%', padding: '1rem', background: '#0d0d0d', border: '1px solid #2a2a2a', color: '#F5F0E6', fontSize: '1rem', fontFamily: '"Crimson Pro", Georgia, serif' }}
                />
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Company</label>
                <input
                  type="text"
                  value={formData.company}
                  onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  style={{ width: '100%', padding: '1rem', background: '#0d0d0d', border: '1px solid #2a2a2a', color: '#F5F0E6', fontSize: '1rem', fontFamily: '"Crimson Pro", Georgia, serif' }}
                />
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Phone *</label>
                <input
                  type="tel"
                  required
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  style={{ width: '100%', padding: '1rem', background: '#0d0d0d', border: '1px solid #2a2a2a', color: '#F5F0E6', fontSize: '1rem', fontFamily: '"Crimson Pro", Georgia, serif' }}
                />
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Address *</label>
                <input
                  type="text"
                  required
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  style={{ width: '100%', padding: '1rem', background: '#0d0d0d', border: '1px solid #2a2a2a', color: '#F5F0E6', fontSize: '1rem', fontFamily: '"Crimson Pro", Georgia, serif' }}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>City *</label>
                  <input
                    type="text"
                    required
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    style={{ width: '100%', padding: '1rem', background: '#0d0d0d', border: '1px solid #2a2a2a', color: '#F5F0E6', fontSize: '1rem', fontFamily: '"Crimson Pro", Georgia, serif' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Postal Code *</label>
                  <input
                    type="text"
                    required
                    value={formData.postal_code}
                    onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                    style={{ width: '100%', padding: '1rem', background: '#0d0d0d', border: '1px solid #2a2a2a', color: '#F5F0E6', fontSize: '1rem', fontFamily: '"Crimson Pro", Georgia, serif' }}
                  />
                </div>
              </div>
              <div style={{ marginBottom: '2rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Country *</label>
                <select
                  required
                  value={formData.country}
                  onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                  style={{ width: '100%', padding: '1rem', background: '#0d0d0d', border: '1px solid #2a2a2a', color: '#F5F0E6', fontSize: '1rem', fontFamily: '"Crimson Pro", Georgia, serif' }}
                >
                  <option value="DE">Germany</option>
                  <option value="AT">Austria</option>
                  <option value="CH">Switzerland</option>
                  <option value="US">United States</option>
                  <option value="GB">United Kingdom</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={isSubmitting}
                style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.9rem', letterSpacing: '0.2em', textTransform: 'uppercase', background: '#C9A227', color: '#050505', padding: '1.5rem 3rem', border: 'none', cursor: isSubmitting ? 'not-allowed' : 'pointer', width: '100%', opacity: isSubmitting ? 0.6 : 1 }}
              >
                {isSubmitting ? 'Registering...' : 'Download Now'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer style={{ padding: '4rem 6%', borderTop: '1px solid #2a2a2a', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '2rem' }}>
        <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', color: '#A69F94' }}>
          <strong style={{ color: '#C9A227', fontWeight: 500 }}>0711 Medusa</strong><br />
          Made in Stuttgart, Germany
        </div>
        <div style={{ display: 'flex', gap: '3rem' }}>
          <a href="https://github.com/0711-medusa" style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.7rem', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#A69F94', textDecoration: 'none' }}>GitHub</a>
          <a href="mailto:hello@0711medusa.dev" style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.7rem', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#A69F94', textDecoration: 'none' }}>Contact</a>
        </div>
      </footer>
    </div>
  );
}
