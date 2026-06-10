import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      component: () => import('../components/layout/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('../views/DashboardView.vue'),
        },
        {
          path: 'kb/:id',
          name: 'kb-detail',
          component: () => import('../views/KnowledgeBaseView.vue'),
        },
        {
          path: 'qa',
          name: 'qa',
          component: () => import('../views/QAChatView.vue'),
        },
        {
          path: 'qa/:convId',
          name: 'qa-conversation',
          component: () => import('../views/QAChatView.vue'),
        },
        {
          path: 'history',
          name: 'history',
          component: () => import('../views/HistoryView.vue'),
        },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.guest) {
    if (token) return next('/')
    return next()
  }
  if (!token) return next('/login')
  next()
})

export default router
