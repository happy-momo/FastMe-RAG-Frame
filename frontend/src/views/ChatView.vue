<template>
  <div class="chat-view">
    <!-- 工具栏 -->
    <div class="chat-toolbar">
      <div class="chat-toolbar__left">
        <el-dropdown trigger="click" @command="handleSessionCommand" class="session-dropdown">
          <button class="session-selector">
            <span class="session-selector__icon">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 5a2 2 0 0 1 2-2h8l4 4v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5z" />
              </svg>
            </span>
            <span class="session-selector__label">{{ currentSession || '新对话' }}</span>
            <svg class="session-selector__arrow" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 8l5 5 5-5" />
            </svg>
          </button>
          <template #dropdown>
            <el-dropdown-menu class="session-menu">
              <div class="session-menu__header">
                <span>对话会话</span>
                <el-button type="primary" link size="small" @click.stop="addNewSession">
                  + 新建
                </el-button>
              </div>
              <el-dropdown-item v-if="!store.sortedSessions.length" disabled>
                暂无会话
              </el-dropdown-item>
              <el-dropdown-item
                v-for="s in store.sortedSessions"
                :key="s.id"
                :command="s.id"
                :class="{ active: store.currentSession === s.id }"
              >
                <div class="session-item">
                  <div class="session-item__title">会话 · {{ formatTime(s.created_at) }}</div>
                  <div class="session-item__count">{{ s.message_count }} 条消息</div>
                </div>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <div class="chat-toolbar__center">
        <SceneSelector v-model="scene" :scenes="store.scenes" />
      </div>

      <div class="chat-toolbar__right">
        <el-tooltip content="清空当前对话" placement="bottom" :show-after="300">
          <button class="icon-btn" @click="clearAllMessage">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 6h14" />
              <path d="M8 6V4a2 2 0 0 1 2-2h0a2 2 0 0 1 2 2v2" />
              <path d="M5 6l1 10a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2l1-10" />
            </svg>
          </button>
        </el-tooltip>
        <el-tooltip content="文档入库" placement="bottom" :show-after="300">
          <button class="icon-btn" @click="$router.push('/upload')">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 3H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9" />
              <path d="M14 2v5h5" />
              <path d="M11 13l-3 3 3 3" />
            </svg>
          </button>
        </el-tooltip>
      </div>
    </div>

    <!-- 消息区 -->
    <div class="chat-messages" ref="msgBox">
      <div class="chat-messages__inner">
        <!-- 欢迎状态 -->
        <div v-if="!store.currentMessages.length" class="welcome-state">
          <div class="welcome-illustration">
            <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="welcome-grad" x1="0" y1="0" x2="120" y2="120" gradientUnits="userSpaceOnUse">
                  <stop stop-color="#6366f1" stop-opacity="0.2" />
                  <stop offset="1" stop-color="#06b6d4" stop-opacity="0.1" />
                </linearGradient>
              </defs>
              <circle cx="60" cy="60" r="55" fill="url(#welcome-grad)" />
              <circle cx="60" cy="60" r="42" fill="white" />
              <g transform="translate(36, 38)">
                <rect x="4" y="4" width="40" height="36" rx="4" fill="#6366f1" opacity="0.1" />
                <path d="M8 44V12a2 2 0 0 1 2-2h28a2 2 0 0 1 2 2v26l-8-6-8 6-8-6-8 6z" fill="#6366f1" opacity="0.7" />
                <circle cx="18" cy="20" r="2" fill="#6366f1" />
                <circle cx="30" cy="20" r="2" fill="#6366f1" />
              </g>
            </svg>
          </div>
          <h2 class="welcome-title">你好，我是 <span class="fm-text-gradient">FastMe RAG</span></h2>
          <p class="welcome-desc">基于制造业知识库的智能问答助手，支持多场景检索溯源</p>

          <div class="quick-prompts">
            <div class="quick-prompt" v-for="q in quickPrompts" :key="q" @click="sendQuick(q)">
              <span class="quick-prompt__icon">💡</span>
              <span>{{ q }}</span>
            </div>
          </div>
        </div>

        <template v-else>
          <MessageBubble v-for="m in store.currentMessages" :key="m.id" :msg="m" />
        </template>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="chat-input-wrapper">
      <div class="chat-input-card">
        <div class="chat-input-scene-tag">
          <span class="dot"></span>
          {{ currentSceneLabel }}
        </div>
        <textarea
          v-model="input"
          class="chat-input"
          :placeholder="inputPlaceholder"
          rows="1"
          ref="textareaRef"
          @keydown.enter.exact.prevent="send"
          @input="autoResize"
        ></textarea>
        <div class="chat-input-actions">
          <span class="chat-input-hint">Enter 发送 · Shift+Enter 换行</span>
          <button
            class="send-btn"
            :class="{ 'send-btn--active': canSend, 'send-btn--loading': sending }"
            :disabled="!canSend"
            @click="send"
          >
            <svg v-if="!sending" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 3v14M3 10h14" />
            </svg>
            <svg v-else class="spinner" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="22 22" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { streamChat } from '../api/chat'
import { useChatStore } from '../store/chat'
import MessageBubble from '../components/MessageBubble.vue'
import SceneSelector from '../components/SceneSelector.vue'

const store = useChatStore()
const input = ref('')
const scene = ref('default')
const sending = ref(false)
const msgBox = ref(null)
const textareaRef = ref(null)

const currentSession = computed(() => store.currentSession)

const canSend = computed(() => input.value.trim().length > 0 && !sending.value)

const currentSceneLabel = computed(() => {
  const s = store.scenes.find(x => x.name === scene.value)
  return s?.description?.split(' - ')[0] || '默认问答'
})

const inputPlaceholder = computed(() => {
  const sceneLabels = {
    fault_diagnosis: '描述设备故障现象，我来帮你分析原因和解决方案...',
    manual_query: '输入设备操作相关问题，我来查询设备手册...',
    work_order_trace: '输入工单编号或生产问题，我来追溯相关记录...',
    default: '输入你的问题，我会基于知识库为你解答...',
  }
  return sceneLabels[scene.value] || '输入你的问题...'
})

const quickPrompts = [
  '设备故障诊断的流程是怎样的？',
  '如何查询设备操作手册？',
  '工单追溯支持哪些信息查询？',
  '系统支持哪些文档格式？',
]

function formatTime(ms) {
  const d = new Date(Number(ms))
  return `${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function autoResize() {
  nextTick(() => {
    const el = textareaRef.value
    if (!el) return
    el.style.height = 'auto'
    const maxH = 180
    el.style.height = Math.min(el.scrollHeight, maxH) + 'px'
  })
}

function scrollBottom() {
  requestAnimationFrame(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}

async function handleSessionCommand(cmd) {
  if (cmd === 'new') {
    // 新建会话：addSession 内部已设置 currentSession，无需再 switch
    // Create new session: addSession already sets currentSession, no need to switch again
    await store.addSession()
  } else {
    // 切换到已有会话：先设置 currentSession，再从后端加载历史消息
    // Switch to existing session: set currentSession first, then load history from backend
    store.switchSession(cmd)
    await store.loadSessionHistory(cmd)
  }
  nextTick(scrollBottom)
}

async function addNewSession() {
  await store.addSession()
  ElMessage.success('已创建新会话')
  nextTick(scrollBottom)
}

async function clearAllMessage() {
  if (!store.currentMessages.length) return
  try {
    await ElMessageBox.confirm('确定要清空当前对话的所有消息吗？', '确认清空', {
      confirmButtonText: '清空',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    })
    store.messages[store.currentSession] = []
  } catch { /* 取消 */ }
}

async function sendQuick(text) {
  input.value = text
  await nextTick()
  send()
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return

  const sessionId = await store.ensureCurrentSession()
  store.pushMessage(sessionId, { role: 'user', content: text })
  store.pushMessage(sessionId, { role: 'assistant', content: '', sources: [], streaming: true })
  store.markLastStreaming(sessionId, true)
  input.value = ''
  sending.value = true
  nextTick(() => { autoResize(); scrollBottom() })

  try {
    for await (const frame of streamChat(
      { question: text, scene: scene.value, session_id: sessionId },
      (event, payload) => {
        if (event === 'meta' && payload.sources) store.setLastSources(sessionId, payload.sources)
      },
    )) {
      if (frame.event === 'delta' && typeof frame.data === 'string') {
        store.appendToLast(sessionId, frame.data)
        scrollBottom()
      }
      if (frame.event === 'error') throw new Error(frame.data?.message || '生成失败')
    }
  } catch (err) {
    store.appendToLast(sessionId, `\n\n⚠️ **错误**：${err.message}`)
    ElMessage.error(err.message || '对话请求失败')
  } finally {
    store.markLastStreaming(sessionId, false)
    sending.value = false
    store.loadSessions().catch(() => {})
    scrollBottom()
  }
}

onMounted(async () => {
  store.loadScenes().catch(() => {})
  store.loadSessions().catch(() => {})
})

// 场景变化时重置输入高度
watch(scene, () => {
  nextTick(autoResize)
})
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--fm-bg);
  position: relative;
}

/* Toolbar */
.chat-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: var(--fm-bg-card);
  border-bottom: 1px solid var(--fm-border-light);
  flex-shrink: 0;
  gap: 16px;
}

.chat-toolbar__left { flex: 0 0 auto; }
.chat-toolbar__center { flex: 0 0 auto; }
.chat-toolbar__right {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 6px;
}

.session-selector {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px 7px 10px;
  background: var(--fm-bg);
  border: 1px solid var(--fm-border);
  border-radius: var(--fm-radius-md);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--fm-text-secondary);
  transition: all var(--fm-transition);
}

.session-selector:hover {
  border-color: var(--fm-primary-light);
  background: var(--fm-primary-50);
  color: var(--fm-primary);
}

.session-selector__icon {
  display: flex;
  width: 18px;
  height: 18px;
}

.session-selector__icon svg { width: 100%; height: 100%; }

.session-selector__label {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-selector__arrow {
  width: 14px;
  height: 14px;
  transition: transform 0.2s;
}

.session-menu :deep(.el-dropdown-menu) {
  padding: 8px;
  border-radius: var(--fm-radius-md);
  box-shadow: var(--fm-shadow-xl);
  min-width: 240px;
  max-height: 320px;      /* 限制下拉最大高度 / limit dropdown max height */
  overflow-y: auto;       /* 超出滚动 / scroll when overflow */
}

.session-menu__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--fm-text-tertiary);
  border-bottom: 1px solid var(--fm-border-light);
  margin-bottom: 4px;
}

.session-item__title {
  font-size: 13px;
  font-weight: 500;
  color: var(--fm-text-primary);
}

.session-item__count {
  font-size: 11px;
  color: var(--fm-text-muted);
  margin-top: 2px;
}

.icon-btn {
  width: 34px;
  height: 34px;
  border: none;
  background: transparent;
  border-radius: var(--fm-radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fm-text-tertiary);
  transition: all var(--fm-transition);
}

.icon-btn:hover {
  background: var(--fm-primary-50);
  color: var(--fm-primary);
}

.icon-btn svg {
  width: 18px;
  height: 18px;
}

/* Messages area */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
}

.chat-messages__inner {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 28px;
}

/* Welcome state */
.welcome-state {
  text-align: center;
  padding: 40px 20px 20px;
}

.welcome-illustration {
  width: 120px;
  height: 120px;
  margin: 0 auto 20px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.welcome-illustration svg {
  width: 100%;
  height: 100%;
}

.welcome-title {
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 10px;
  color: var(--fm-text-primary);
  letter-spacing: -0.02em;
}

.welcome-desc {
  font-size: 14px;
  color: var(--fm-text-tertiary);
  margin: 0 0 32px;
}

.quick-prompts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  max-width: 600px;
  margin: 0 auto;
}

.quick-prompt {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--fm-bg-card);
  border: 1px solid var(--fm-border);
  border-radius: var(--fm-radius-md);
  font-size: 13px;
  color: var(--fm-text-secondary);
  cursor: pointer;
  transition: all var(--fm-transition);
  text-align: left;
}

.quick-prompt:hover {
  border-color: var(--fm-primary-light);
  background: var(--fm-primary-50);
  color: var(--fm-primary-dark);
  transform: translateY(-1px);
  box-shadow: var(--fm-shadow-md);
}

.quick-prompt__icon {
  font-size: 16px;
  flex-shrink: 0;
}

/* Input area */
.chat-input-wrapper {
  padding: 16px 24px 24px;
  flex-shrink: 0;
  background: linear-gradient(180deg, transparent 0%, var(--fm-bg) 30%);
}

.chat-input-card {
  max-width: 900px;
  margin: 0 auto;
  background: var(--fm-bg-card);
  border: 1px solid var(--fm-border);
  border-radius: var(--fm-radius-lg);
  box-shadow: var(--fm-shadow-md);
  padding: 14px 16px 12px;
  transition: all var(--fm-transition);
  position: relative;
}

.chat-input-card:focus-within {
  border-color: var(--fm-primary-light);
  box-shadow: var(--fm-shadow-glow);
}

.chat-input-scene-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--fm-primary);
  background: var(--fm-primary-50);
  padding: 3px 10px;
  border-radius: var(--fm-radius-full);
  margin-bottom: 8px;
}

.chat-input-scene-tag .dot {
  width: 6px;
  height: 6px;
  background: var(--fm-primary);
  border-radius: 50%;
}

.chat-input {
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  font-family: inherit;
  font-size: 14.5px;
  line-height: 1.6;
  color: var(--fm-text-primary);
  background: transparent;
  min-height: 24px;
  max-height: 180px;
  overflow-y: auto;
}

.chat-input::placeholder {
  color: var(--fm-text-muted);
}

.chat-input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--fm-border-light);
}

.chat-input-hint {
  font-size: 11.5px;
  color: var(--fm-text-muted);
}

.send-btn {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: var(--fm-radius-sm);
  background: var(--fm-border-light);
  color: var(--fm-text-muted);
  cursor: not-allowed;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--fm-transition);
}

.send-btn--active {
  background: linear-gradient(135deg, var(--fm-primary), var(--fm-primary-dark));
  color: #fff;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.send-btn--active:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.45);
}

.send-btn--active:active {
  transform: translateY(0);
}

.send-btn svg {
  width: 18px;
  height: 18px;
  transition: transform 0.2s;
}

.spinner {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
