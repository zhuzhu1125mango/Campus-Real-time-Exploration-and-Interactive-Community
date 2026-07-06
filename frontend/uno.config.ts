import { defineConfig, presetIcons, presetUno } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetIcons({
      scale: 1.2,
      extraProperties: {
        display: 'inline-block',
        'vertical-align': 'middle',
      },
    }),
  ],
  theme: {
    colors: {
      brand: {
        50: '#eff6ff',
        100: '#dbeafe',
        200: '#bfdbfe',
        300: '#93c5fd',
        400: '#60a5fa',
        500: '#3b82f6',
        600: '#2563eb',
        700: '#1d4ed8',
        800: '#1e40af',
        900: '#1e3a8a',
      },
      accent: {
        orange: '#f97316',
        'orange-light': '#fff7ed',
        green: '#10b981',
        'green-light': '#ecfdf5',
        red: '#ef4444',
        yellow: '#f59e0b',
      },
      surface: {
        light: '#f8fafc',
        dark: '#0f172a',
      },
    },
    borderRadius: {
      '2xl': '16px',
      '3xl': '24px',
    },
    boxShadow: {
      glass: '0 8px 32px rgba(31, 41, 55, 0.08)',
      float: '0 12px 40px rgba(0, 0, 0, 0.12)',
    },
  },
  rules: [
    [
      'glass',
      {
        background: 'rgba(255, 255, 255, 0.72)',
        'backdrop-filter': 'blur(12px) saturate(180%)',
        '-webkit-backdrop-filter': 'blur(12px) saturate(180%)',
      },
    ],
    [
      'glass-dark',
      {
        background: 'rgba(30, 41, 59, 0.72)',
        'backdrop-filter': 'blur(12px) saturate(180%)',
        '-webkit-backdrop-filter': 'blur(12px) saturate(180%)',
      },
    ],
    [
      'glass-border',
      {
        'border-color': 'rgba(255, 255, 255, 0.5)',
      },
    ],
    [
      'glass-border-dark',
      {
        'border-color': 'rgba(255, 255, 255, 0.1)',
      },
    ],
  ],
})
