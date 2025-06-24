const fs = require('fs');
const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: process.env.BASE_URL || '/',
  devServer: {
    port: 8080,
    allowedHosts: ["rtsys-lab.de", "www.rtsys-lab.de"],
    server: {
      type: 'https'
    }
  }
});
