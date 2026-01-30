/**
 * Anthropic Design Theme for MCP Dashboard
 *
 * Premium enterprise aesthetic:
 * - Monochromatic (dark/light/grays)
 * - Orange accent only (for CTAs and active states)
 * - No bright colors, no rainbows
 * - Subtle, professional, timeless
 */

// Import centralized colors
import { colors as centralColors } from '@/lib/theme';

// Re-export with alias for backward compatibility
export const colors = centralColors;

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
