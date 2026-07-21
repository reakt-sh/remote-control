// vue.config.js
const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: process.env.BASE_URL || '/',
  devServer: {
    port: 8080,
    allowedHosts: ['rtsys-lab.de', 'www.rtsys-lab.de'],
    server: {
      type: 'https',
    },
  },
  configureWebpack: {
    resolve: {
      fallback: {
        https: require.resolve('https-browserify'),
        http: require.resolve('stream-http'),
      },
    },
  },
  pwa: {
    name: 'Remote Control Interface',
    themeColor: '#000000',
    msTileColor: '#000000',

    manifestOptions: {
      short_name: 'Remote Control',
      display: 'fullscreen',
      orientation: 'landscape',
      background_color: '#000000',
      theme_color: '#000000'
    }
  }
});