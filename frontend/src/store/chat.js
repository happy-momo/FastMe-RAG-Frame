import { defineStore } from 'pinia'
import { createSession, deleteSession, fetchScenes, fetchSessions, fetchSessionMessages } from '../api/ingest'

const genId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`

// 一条消息 / a message
// { id, role: 'user'|'assistant', content, sources, streaming }

export const useChatStore = defineStore('chat', {
  state: () => ({
    scenes: [],                 // 场景列表 [{name, description}]
    sessions: [],               // 会话列表 [{id, message_count, created_at}]
    currentSession: null,       // 当前会话名（即 session_id）
    messages: {},               // sessionId -> Message[]
  }),

  getters: {
    sortedSessions: (s) =>
      [...s.sessions].sort((a, b) => (a.created_at < b.created_at ? 1 : -1)),
    currentMessages: (s) => (s.currentSession ? s.messages[s.currentSession] ?? [] : []),
  },

  actions: {
    async loadScenes() {
      if (!this.scenes.length) this.scenes = await fetchScenes()
      return this.scenes
    },

    async loadSessions() {
      // 后端返回 { sessions: [...] }，取数组部分
      // Backend returns { sessions: [...] }, extract the array
      const res = await fetchSessions()
      this.sessions = res?.sessions ?? res ?? []
    },

    async ensureCurrentSession() {
      if (this.currentSession) return this.currentSession
      return this.addSession()
    },

    async addSession() {
      const name = `会话-${Date.now()}`
      await createSession(name)
      if (!this.messages[name]) this.messages[name] = []
      await this.loadSessions()
      this.currentSession = name
      return name
    },

    switchSession(id) {
      this.currentSession = id
      if (!this.messages[id]) this.messages[id] = []
    },

    async loadSessionHistory(sessionId) {
      // 从后端拉取会话历史消息并转为前端消息结构
      // Fetch session history from backend and convert to frontend message structure
      try {
        const res = await fetchSessionMessages(sessionId)
        const list = res?.messages ?? []
        const history = list
          .filter((m) => m && m.content)
          .map((m, i) => ({
            id: `hist_${sessionId}_${i}`,
            role: m.role === 'user' ? 'user' : 'assistant',
            content: m.content,
            sources: [],
            streaming: false,
          }))
        this.messages[sessionId] = history
        return history
      } catch (e) {
        // 拉取失败时保留本地状态，静默降级
        // On failure keep local state, degrade silently
        if (!this.messages[sessionId]) this.messages[sessionId] = []
        return this.messages[sessionId]
      }
    },

    async removeSession(id) {
      await deleteSession(id)
      delete this.messages[id]
      await this.loadSessions()
      if (this.currentSession === id) this.currentSession = null
    },

    pushMessage(sessionId, msg) {
      if (!this.messages[sessionId]) this.messages[sessionId] = []
      this.messages[sessionId].push(msg)
    },

    appendToLast(sessionId, text) {
      const list = this.messages[sessionId] || []
      const last = list[list.length - 1]
      if (last) last.content += text
    },

    markLastStreaming(sessionId, streaming) {
      const list = this.messages[sessionId] || []
      const last = list[list.length - 1]
      if (last) last.streaming = streaming
    },

    setLastSources(sessionId, sources) {
      const list = this.messages[sessionId] || []
      const last = list[list.length - 1]
      if (last) last.sources = sources
    },
  },
})