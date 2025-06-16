const fs = require('fs');
const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: process.env.BASE_URL || '/',
  devServer: {
    port: 8080,
    server: {
      type: 'https',
      options: {
        key: fs.readFileSync('/etc/ssl/quic_conf/certificate.key'),
        cert: fs.readFileSync('/etc/ssl/quic_conf/certificate.pem'),
      }
    }
  }
});
