/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0B1A3E',
          800: '#112455',
          700: '#162D60',
          600: '#1E3A7A',
        },
        teal: {
          500: '#00B496',
          600: '#009A80',
          700: '#007A65',
        },
        gold: {
          400: '#F5C542',
          500: '#E5B532',
        },
        muted: '#8A9BBB',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
