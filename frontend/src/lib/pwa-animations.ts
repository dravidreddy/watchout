/**
 * Custom Tailwind animations for PWA Components
 * Add these to your tailwind.config.ts
 */

module.exports = {
    theme: {
        extend: {
            keyframes: {
                'slide-up': {
                    '0%': { transform: 'translateY(100%)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                'slide-down': {
                    '0%': { transform: 'translateY(-100%)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
            },
            animation: {
                'slide-up': 'slide-up 0.3s ease-out',
                'slide-down': 'slide-down 0.3s ease-out',
            },
        },
    },
};
