// Theme configuration for CloudCommerce
export const theme = {
  colors: {
    // Primary purple shades
    primary: {
      50: '#f5f0ff',
      100: '#e9d8ff',
      200: '#d6b9ff',
      300: '#b98bf2',
      400: '#9f5ce6',
      500: '#8b3dff',  // Main brand purple
      600: '#7b2cff',  // Hover state
      700: '#6a1bff',  // Active state
      800: '#4a00b3',  // Darker shade
      900: '#2d0066',  // Darkest shade
    },
    // Secondary colors
    secondary: {
      teal: '#00e6cc',
      pink: '#ff4d9e',
      yellow: '#ffd700',
      blue: '#4d9eff',
    },
    // Background colors
    background: {
      light: '#ffffff',
      dark: '#0f0c1d',
      card: '#1a1625',
      cardLight: '#f8f7ff',
    },
    // Text colors
    text: {
      primary: '#1a0d2e',
      secondary: '#4a4a6a',
      light: '#ffffff',
      muted: '#8c8ca1',
    },
    // Status colors
    status: {
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6',
    },
  },
  fonts: {
    sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: 'JetBrains Mono, Menlo, Monaco, Consolas, "Liberation Mono", monospace',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
    none: 'none',
  },
  borderRadius: {
    none: '0',
    sm: '0.25rem',
    DEFAULT: '0.5rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    '2xl': '1.5rem',
    '3xl': '2rem',
    full: '9999px',
  },
  // Octopus mascot colors
  octopus: {
    primary: '#8b3dff',
    secondary: '#b98bf2',
    highlight: '#00e6cc',
    eye: '#ffd700',
  },
} as const;

export type Theme = typeof theme;

export default theme;
