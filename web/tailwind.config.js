/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Supabase.com exact color palette
        brand: {
          DEFAULT: '#3ECF8E',
          50: '#ECFDF5',
          100: '#D1FAE5',
          200: '#A7F3D0',
          300: '#6EE7B7',
          400: '#34D399',
          500: '#3ECF8E',
          600: '#10B981',
          700: '#059669',
          800: '#047857',
          900: '#065F46',
        },
        // Supabase gray scale (matching their exact colors)
        gray: {
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          300: '#D1D5DB',
          400: '#9CA3AF',
          500: '#6B7280',
          600: '#4B5563',
          700: '#374151',
          800: '#1F2937',
          900: '#111827',
          950: '#0A0F1A',
        },
        // Supabase dark mode colors
        dark: {
          DEFAULT: '#1F2937',
          bg: '#0A0F1A',
          surface: '#151920',
          border: '#1F2937',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      backgroundColor: {
        'supabase-light': '#FFFFFF',
        'supabase-dark': '#0A0F1A',
      },
      textColor: {
        'supabase-light': '#111827',
        'supabase-dark': '#F9FAFB',
      },
    },
  },
  plugins: [],
}

