import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import TrainView from './views/TrainView.vue' // <-- Add this import

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/:trainId',
    name: 'train',
    component: TrainView,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL || '/'),
  routes
})

export default router