import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      injectRegister: null,
      registerType: 'autoUpdate',
      includeAssets: ['vite.svg', 'icons/icon-192.png', 'icons/icon-512.png'],
      devOptions: {
        enabled: false,
      },
      manifest: {
        id: '/',
        name: 'Portex',
        short_name: 'Portex',
        description: 'Multi-user AI agent workspace for web, chat, and operator workflows.',
        theme_color: '#1565c0',
        background_color: '#f3f5f8',
        display: 'standalone',
        display_override: ['standalone'],
        scope: '/',
        start_url: '/chat',
        icons: [
          {
            src: '/icons/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/icons/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
          },
        ],
      },
      workbox: {
        navigateFallback: 'index.html',
        navigateFallbackDenylist: [/^\/api\//, /^\/ws\//],
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
      },
    }),
  ],
})
