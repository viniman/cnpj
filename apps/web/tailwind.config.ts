import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef4ff',
          100: '#dfe8ff',
          200: '#c2d3ff',
          300: '#9bb5ff',
          400: '#6d8dff',
          500: '#4763f5',
          600: '#3444dc',
          700: '#2a34b3',
          800: '#252f8f',
          900: '#232c72',
        },
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
