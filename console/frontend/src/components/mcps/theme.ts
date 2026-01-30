/**
 * Anthropic Design Theme for MCP Dashboard
 *
 * Premium enterprise aesthetic:
 * - Monochromatic (dark/light/grays)
 * - Orange accent only (for CTAs and active states)
 * - No bright colors, no rainbows
 * - Subtle, professional, timeless
 */

// Anthropic Brand Colors (matching main console)
export const colors = {
  dark: '#1e293b',      // Almost black - primary text, dark backgrounds
  light: '#faf9f5',     // Warm off-white - light backgrounds
  midGray: '#94a3b8',   // Muted taupe - secondary text, icons
  lightGray: '#e8e6dc', // Warm light gray - borders, subtle backgrounds
  orange: '#d97757',    // Muted terracotta - ONLY for accents, CTAs, active states
  blue: '#6a9bcc',      // Muted blue - rare subtle accent
  green: '#788c5d',     // Muted olive - rare subtle accent
};

// Typography
export const fonts = {
  heading: "'Poppins', Arial, sans-serif",
  body: "'Lora', Georgia, serif",
};

// MCP Icon Mapping (using simple letters instead of emojis)
export const mcpIconLabels: Record<string, string> = {
  pim: 'PI',
  dam: 'DA',
  plm: 'PL',
  erp: 'ER',
  crm: 'CR',
  web: 'WB',
  etim: 'ET',
  channel: 'CH',
  syndicate: 'SY',
  tax: 'TX',
  compliance: 'CM',
  llm_chats: 'AI',
  market: 'MK',
  publish: 'PB',
};

// Direction badge styles (subtle, monochrome)
export const directionStyles = {
  input: {
    label: 'INPUT',
    bg: 'bg-dark/5',
    border: 'border-dark/10',
    text: 'text-dark/70',
  },
  output: {
    label: 'OUTPUT',
    bg: 'bg-dark/5',
    border: 'border-dark/10',
    text: 'text-dark/70',
  },
  bidirectional: {
    label: 'BOTH',
    bg: 'bg-dark/5',
    border: 'border-dark/10',
    text: 'text-dark/70',
  },
};

// Status indicator colors (minimal)
export const statusColors = {
  subscribed: 'bg-dark/60',
  connected: 'bg-orange',
  disconnected: 'bg-midGray/40',
};
