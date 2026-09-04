import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/chat' },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('../views/ChatView.vue'),
    meta: { title: '对话' },
  },
  {
    path: '/upload',
    name: 'upload',
    component: () => import('../views/UploadView.vue'),
    meta: { title: '文档入库' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  document.title = to.meta?.title ? `${to.meta.title} · FastMe RAG` : 'FastMe RAG Chatbot'
})

export default router