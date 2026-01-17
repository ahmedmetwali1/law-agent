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
                obsidian: {
                    900: '#09090b',
                    800: '#18181b',
                    700: '#27272a',
                    600: '#3f3f46',
                },
                cobalt: {
                    600: '#2563eb',
                    500: '#3b82f6',
                    400: '#60a5fa',
                },
                gold: {
                    500: '#d4af37',
                    400: '#e4bf47',
                    300: '#f4cf57',
                },
                success: '#10b981',
                warning: '#f59e0b',
                error: '#ef4444',
                info: '#3b82f6',
            },
            fontFamily: {
                sans: ['Cairo', 'sans-serif'],
                mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
            },
            backdropBlur: {
                xs: '2px',
            },
            animation: {
                'spin-slow': 'spin 3s linear infinite',
            },
        },
    },
    plugins: [
        require('tailwindcss-animate'),
    ],
}
