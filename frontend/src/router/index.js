import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user.js'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/my-tasks', component: () => import('../views/MyTasks.vue') },
  { path: '/team/:id', component: () => import('../views/TeamTasks.vue') },
  { path: '/task/:id', component: () => import('../views/TaskDetail.vue') },
  { path: '/team/:id/manage', component: () => import('../views/TeamManage.vue') },
  { path: '/admin/users', component: () => import('../views/admin/UserManage.vue'), meta: { requireAdmin: true } },
  { path: '/admin/settings', component: () => import('../views/admin/SystemSettings.vue'), meta: { requireAdmin: true } },
  { path: '/', redirect: '/my-tasks' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const store = useUserStore()
  if (!to.meta.public && !store.isLoggedIn) return '/login'
  if (to.meta.requireAdmin && !store.isAdmin) return '/my-tasks'
})

export default router
