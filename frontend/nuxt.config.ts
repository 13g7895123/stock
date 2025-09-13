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
        changeOrigin: true
      }
    }
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