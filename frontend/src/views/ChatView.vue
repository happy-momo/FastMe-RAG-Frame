<template>
  <div class="chat-view">
    <!-- 顶部：会话 + 场景 + 新增 -->
    <div class="chat-header">
      <el-dropdown trigger="click" @command="handleSessionCommand">
        <el-button>
          {{ currentSession || '选择/新建会话' }} <el-icon><arrow-down /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="new">＋ 新建会话</el-dropdown-item>
            <el-dropdown-item
              v-for="s in store.sortedSessions"
              :key="s.id"
              :command="s.id"
              divided
            >
              会话 · {{ formatTime(s.created_at) }}（{{ s.message_count }}）
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <SceneSelector v-model="scene" :scenes="store.scenes" />

      <div class="spacer" />

      <el-button-group>
        <el-button :icon="Delete" circle @click="clearAllMessage" title="清空当前对话" />
        <el-button :icon="DocumentAdd" circle @click="$router.push('/upload')" title="入库文档" />
      </el-button-group>
    </div>

    <!-- 消息区 -->
    <div class="messages" ref="msgBox">
      <el-empty
        v-if="!store.currentMessages.length"
        description="上传文档后，在这里提问"
        :image-size="90"
      />
      <MessageBubble v-for="m in store.currentMessages" :key="m.id" :msg="m" />
      <div class="gap" />
    </div>

    <!-- 输入区 -->
    <div class="input-bar">
      <el-input
        v-model="input"
        type="textarea"
        :rows="2"
        placeholder="输入你的问题，Enter 发送，Shift+Enter 换行"
        resize="none"
        @keydown.enter.exact.prevent="send"
      />
      <el-button
        type="primary"
        :loading="sending"
        :disabled="sending"
        @click="send"
        :icon="Promotion"
      >
        {{ sending ? '生成中' : '发送' }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Delete, DocumentAdd, Promotion } from '@element-plus/icons-vue'
import { streamChat } from '../api/chat'
import { useChatStore } from '../store/chat'
import MessageBubble from '../components/MessageBubble.vue'
import SceneSelector from '../components/SceneSelector.vue'

const store = useChatStore()
const input = ref('')
const scene = ref('default')
const sending = ref(false)
const msgBox = ref(null)

const currentSession = computed(() => store.currentSession)

function formatTime(ms) {
  const d = new Date(Number(ms))
  return `${d.getMonth() + 1}-${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function scrollBottom() {
  requestAnimationFrame(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}

async function handleSessionCommand(cmd) {
  if (cmd === 'new') {
    await store.addSession()
  } else if (!store.messages[cmd]) {
    await store.loadSessions()
  }
  store.switchSession(cmd)
}

function clearAllMessage() {
  if (!store.currentSession) return
  store.messages[store.currentSession] = []
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
  scrollBottom()

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
    store.appendToLast(sessionId, `\n[错误] ${err.message}`)
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
</script>

<style scoped>
.chat-view { display: flex; flex-direction: column; height: 100vh; }
.chat-header { display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-bottom: 1px solid #ebeef5; }
.spacer { flex: 1; }
.messages { flex: 1; overflow-y: auto; padding: 24px 20px 8px; }
.gap { height: 8px; }
.input-bar { display: flex; align-items: flex-end; gap: 12px; padding: 14px 20px 20px; border-top: 1px solid #ebeef5; }
.input-bar .el-textarea { flex: 1; }
</style>