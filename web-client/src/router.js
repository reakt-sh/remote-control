import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import LiveTrainView from './views/LiveTrainView.vue'
import RecordedTrainView from './views/RecordedTrainView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/:trainId',
    name: 'train',
    component: LiveTrainView,
    props: true
  },
  {
    path: '/:trainId/record',
    name: 'recorded-train',
    component: RecordedTrainView,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL || '/'),
  routes
})

export default router