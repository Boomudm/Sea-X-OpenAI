/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: '#EE4D2D',
        ink: '#211A18',
        canvas: '#FAF8F6',
        peach: '#FFF4EE',
        line: '#EAE3DF',
        muted: '#78716C',
      },
      boxShadow: {
        soft: '0 10px 30px rgba(71, 42, 32, 0.07)',
        float: '0 16px 40px rgba(71, 42, 32, 0.13)',
      },
      fontFamily: {
        sans: ['Manrope', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['Manrope', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      transitionTimingFunction: {
        weighted: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
    },
  },
  plugins: [],
}
