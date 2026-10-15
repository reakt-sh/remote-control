import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import LiveTrainView from './views/LiveTrainView.vue'
import RecordedTrainView from './views/RecordedTrainView.vue'
import { useAccessStore } from '@/stores/accessStore'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { requiresAccess: true }
  },
  {
    path: '/:trainId',
    name: 'train',
    component: LiveTrainView,
    props: true,
    meta: { requiresAccess: true }
  },
  {
    path: '/:trainId/record',
    name: 'recorded-train',
    component: RecordedTrainView,
    props: true,
    meta: { requiresAccess: true }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL || '/'),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAccess) {
    const accessStore = useAccessStore()
    if (!accessStore.isGranted) {
      next(false)
      return
    }
  }
  next()
})

export default router
