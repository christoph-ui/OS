/**
 * 0711 OS Console Theme
 * Single source of truth for all colors
 */

export const colors = {
  dark: '#1e293b',      // slate-800 - primary dark backgrounds
  light: '#faf9f5',     // cream white - light backgrounds
  midGray: '#94a3b8',   // slate-400 - secondary text
  lightGray: '#e8e6dc', // light borders
  orange: '#d97757',    // primary accent
  red: '#d75757',       // error/danger
  blue: '#6a9bcc',      // info/links
  green: '#57d797',     // success
} as const;

export type ColorKey = keyof typeof colors;
export type Colors = typeof colors;

// For CSS-in-JS usage
export const theme = {
  colors,
} as const;

export default theme;
