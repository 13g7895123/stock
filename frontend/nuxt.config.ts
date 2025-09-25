export default defineNuxtConfig({
  devtools: { enabled: true },
  devServer: {
    port: 3302,
    host: '0.0.0.0'
  },
  ssr: true,
  modules: [
    '@nuxt/ui',
    '@pinia/nuxt'
  ],
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      apiUrl: process.env.API_URL || 'http://localhost:9127/api/v1'
    }
  },
  nitro: {
    devProxy: {
      '/api': {
        target: 'http://localhost:9127',
        changeOrigin: true,
        prependPath: true
      }
    }
  },
  vite: {
    plugins: [
      // Disable vue-inspector plugin to fix "Invalid end tag" errors
      {
        name: 'disable-vue-inspector',
        configureServer(server) {
          const plugin = server.config.plugins.find(p => p?.name === 'vite-plugin-vue-inspector')
          if (plugin) {
            plugin.buildStart = () => {}
            plugin.transform = () => null
          }
        }
      }
    ]
  },
  colorMode: {
    preference: 'system',
    fallback: 'light',
    hid: 'nuxt-color-mode-script',
    globalName: '__NUXT_COLOR_MODE__',
    componentName: 'ColorScheme',
    classPrefix: '',
    classSuffix: '',
    storageKey: 'nuxt-color-mode'
  }
})