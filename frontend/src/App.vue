<template>
  <div class="fm-layout">
    <!-- Sidebar -->
    <aside class="fm-sidebar">
      <div class="fm-sidebar__brand">
        <div class="fm-sidebar__logo">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M16 2L4 9v14l12 7 12-7V9L16 2z"
              fill="url(#logo-grad)"
            />
            <path
              d="M16 8l-8 4.5v7L16 24l8-4.5v-7L16 8z"
              fill="rgba(255,255,255,0.2)"
            />
            <path
              d="M16 12l-4 2.5v3L16 20l4-2.5v-3L16 12z"
              fill="rgba(255,255,255,0.35)"
            />
            <defs>
              <linearGradient id="logo-grad" x1="4" y1="2" x2="28" y2="30" gradientUnits="userSpaceOnUse">
                <stop stop-color="#6366f1" />
                <stop offset="1" stop-color="#06b6d4" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div class="fm-sidebar__brand-text">
          <h1>FastMe RAG</h1>
          <p>制造业 RAG 框架</p>
        </div>
      </div>

      <nav class="fm-sidebar__nav">
        <router-link to="/chat" class="fm-nav-item" :class="{ active: $route.path === '/chat' }">
          <span class="fm-nav-item__icon">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M2 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6l-4 4V4z" />
            </svg>
          </span>
          <span class="fm-nav-item__label">智能对话</span>
        </router-link>
        <router-link to="/upload" class="fm-nav-item" :class="{ active: $route.path === '/upload' }">
          <span class="fm-nav-item__icon">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 3v10m0-10l-3 3m3-3l3 3" />
              <path d="M3 17h14" />
            </svg>
          </span>
          <span class="fm-nav-item__label">文档入库</span>
        </router-link>
      </nav>

      <div class="fm-sidebar__footer">
        <div class="fm-status-card">
          <div class="fm-status-card__header">
            <span class="fm-status-card__title">系统状态</span>
          </div>
          <div class="fm-status-card__item">
            <span
              class="fm-status-dot"
              :class="health.llm_reachable === true ? 'ok' : health.llm_reachable === false ? 'warn' : 'loading'"
            ></span>
            <span class="fm-status-card__label">大模型</span>
            <span class="fm-status-card__value">
              {{ health.llm_reachable === true ? '已连接' : health.llm_reachable === false ? '未连接' : '检测中' }}
            </span>
          </div>
          <div class="fm-status-card__item">
            <span class="fm-status-dot ok"></span>
            <span class="fm-status-card__label">向量库</span>
            <span class="fm-status-card__value">{{ health.vector_count.toLocaleString() }} 条</span>
          </div>
        </div>

        <div class="fm-sidebar__version">v1.0.0 · chatbot-demo</div>
      </div>
    </aside>

    <!-- Main content area -->
    <div class="fm-main">
      <header class="fm-header">
        <div class="fm-header__left">
          <h2 class="fm-header__title">{{ pageTitle }}</h2>
          <span class="fm-header__subtitle">{{ pageSubtitle }}</span>
        </div>
        <div class="fm-header__right">
          <el-tooltip
            :content="health.llm_reachable ? '大模型服务已连接，可正常对话' : '大模型未连接，请检查 LLM 配置'"
            placement="bottom"
            :show-after="300"
          >
            <div class="fm-llm-indicator" :class="{ connected: health.llm_reachable, disconnected: health.llm_reachable === false }">
              <span class="fm-llm-indicator__dot"></span>
              <span class="fm-llm-indicator__text">
                {{ health.llm_reachable ? 'LLM 在线' : health.llm_reachable === false ? 'LLM 离线' : '检测中...' }}
              </span>
            </div>
          </el-tooltip>
        </div>
      </header>
      <main class="fm-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, computed } from 'vue'
import { fetchHealth } from './api/ingest'

const health = reactive({ llm_reachable: null, vector_count: 0, models_dir: '' })

const pageTitle = computed(() => {
  const map = { '/chat': '智能对话', '/upload': '文档入库' }
  return map[window.location.pathname] || '智能对话'
})

const pageSubtitle = computed(() => {
  const map = {
    '/chat': '基于制造业知识库的智能问答助手',
    '/upload': '上传文档并构建向量知识库'
  }
  return map[window.location.pathname] || ''
})

async function loadHealth() {
  try {
    const h = await fetchHealth()
    Object.assign(health, h)
  } catch (e) {
    health.llm_reachable = false
    health.vector_count = 0
  }
}

onMounted(() => {
  loadHealth()
  // 定期刷新 LLM 状态
  setInterval(loadHealth, 30000)
})
</script>

<style scoped>
.fm-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--fm-bg);
}

/* ===== Sidebar ===== */
.fm-sidebar {
  width: var(--fm-sidebar-width);
  min-width: var(--fm-sidebar-width);
  background: var(--fm-bg-sidebar);
  color: var(--fm-text-inverse);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.fm-sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 200px;
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.15) 0%, transparent 100%);
  pointer-events: none;
}

.fm-sidebar__brand {
  padding: 24px 20px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.fm-sidebar__logo {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.fm-sidebar__logo svg {
  width: 36px;
  height: 36px;
}

.fm-sidebar__brand-text h1 {
  font-size: 17px;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, #a5b4fc, #67e8f9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.01em;
}

.fm-sidebar__brand-text p {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  margin: 2px 0 0;
}

/* Navigation */
.fm-sidebar__nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
  z-index: 1;
}

.fm-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: var(--fm-radius-md);
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--fm-transition);
  position: relative;
}

.fm-nav-item:hover {
  color: rgba(255, 255, 255, 0.9);
  background: var(--fm-bg-sidebar-hover);
}

.fm-nav-item.active {
  color: #fff;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(6, 182, 212, 0.15));
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.fm-nav-item.active::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: linear-gradient(180deg, var(--fm-primary-light), var(--fm-accent));
  border-radius: 0 2px 2px 0;
}

.fm-nav-item__icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.fm-nav-item__icon svg {
  width: 18px;
  height: 18px;
}

/* Footer / Status */
.fm-sidebar__footer {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  position: relative;
  z-index: 1;
}

.fm-status-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--fm-radius-md);
  padding: 12px;
  margin-bottom: 12px;
}

.fm-status-card__header {
  margin-bottom: 10px;
}

.fm-status-card__title {
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.fm-status-card__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
}

.fm-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  position: relative;
}

.fm-status-dot.ok {
  background: var(--fm-success-light);
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
}

.fm-status-dot.ok::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: var(--fm-success-light);
  animation: fm-pulse-dot 2s ease-in-out infinite;
}

.fm-status-dot.warn {
  background: var(--fm-warning);
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.6);
}

.fm-status-dot.loading {
  background: var(--fm-text-muted);
  animation: fm-pulse-dot 1.5s ease-in-out infinite;
}

.fm-status-card__label {
  color: rgba(255, 255, 255, 0.5);
}

.fm-status-card__value {
  margin-left: auto;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 500;
}

.fm-sidebar__version {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.25);
  text-align: center;
  padding-top: 4px;
}

/* ===== Main area ===== */
.fm-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.fm-header {
  height: var(--fm-header-height);
  padding: 0 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--fm-bg-card);
  border-bottom: 1px solid var(--fm-border-light);
  flex-shrink: 0;
}

.fm-header__left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.fm-header__title {
  font-size: var(--fm-text-xl);
  font-weight: 700;
  color: var(--fm-text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.fm-header__subtitle {
  font-size: var(--fm-text-sm);
  color: var(--fm-text-tertiary);
}

.fm-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.fm-llm-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: var(--fm-radius-full);
  font-size: var(--fm-text-sm);
  font-weight: 500;
  transition: all var(--fm-transition);
  cursor: default;
  user-select: none;
}

.fm-llm-indicator.connected {
  background: rgba(16, 185, 129, 0.08);
  color: var(--fm-success);
  border: 1px solid rgba(16, 185, 129, 0.15);
}

.fm-llm-indicator.disconnected {
  background: rgba(245, 158, 11, 0.08);
  color: var(--fm-warning);
  border: 1px solid rgba(245, 158, 11, 0.15);
}

.fm-llm-indicator__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  position: relative;
}

.fm-llm-indicator.connected .fm-llm-indicator__dot {
  background: var(--fm-success);
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.7);
}

.fm-llm-indicator.connected .fm-llm-indicator__dot::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: var(--fm-success);
  animation: fm-pulse-dot 2s ease-in-out infinite;
}

.fm-llm-indicator.disconnected .fm-llm-indicator__dot {
  background: var(--fm-warning);
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.7);
}

.fm-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}
</style>
