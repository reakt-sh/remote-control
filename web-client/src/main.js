import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import '@fortawesome/fontawesome-free/css/all.css'
import './styles/main.css'

// Disable all console logs in production
// console.log = function () {};
console.info = function () {};
console.warn = function () {};
console.error = function () {};
console.debug = function () {};

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')