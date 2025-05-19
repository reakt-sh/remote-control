import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import '@fortawesome/fontawesome-free/css/all.css'
import './styles/main.css'

// disable console.log for production
// console.log = () => {};

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')