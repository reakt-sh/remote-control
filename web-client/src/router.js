import { createRouter, createWebHistory } from 'vue-router'
import ControlView from './views/ControlView.vue'

const routes = [
  {
    path: '/',
    name: 'control',
    component: ControlView
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL || '/'),
  routes
})

export default router