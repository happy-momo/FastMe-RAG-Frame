<template>
  <div class="msg-row" :class="msg.role">
    <div class="msg-avatar">
      <template v-if="msg.role === 'user'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1" />
        </svg>
      </template>
      <template v-else>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="5" width="18" height="14" rx="3" />
          <circle cx="8.5" cy="12" r="1.5" fill="currentColor" />
          <circle cx="15.5" cy="12" r="1.5" fill="currentColor" />
          <path d="M12 3v2M12 19v2M5 9V5M19 9V5M5 15v4M19 15v4" />
        </svg>
      </template>
    </div>

    <div class="msg-body">
      <div class="msg-meta">
        <span class="msg-role">{{ msg.role === 'user' ? '你' : 'FastMe RAG' }}</span>
        <span v-if="msg.role === 'assistant' && msg.sources && msg.sources.length" class="msg-meta-tag">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8l2-2 2 2 4-4 4 4" />
          </svg>
          已检索 {{ msg.sources.length }} 条来源
        </span>
      </div>

      <div class="msg-bubble" :class="{ 'msg-bubble--streaming': msg.streaming }">
        <div class="msg-content">
          <template v-if="msg.streaming && !msg.content">
            <div class="msg-thinking">
              <span class="thinking-dots">
                <span></span><span></span><span></span>
              </span>
              <span class="thinking-text">正在思考中...</span>
            </div>
          </template>
          <template v-else>
            <div class="msg-text" :class="{ 'msg-text--user': msg.role === 'user' }">{{ msg.content }}</div>
            <span v-if="msg.streaming" class="msg-cursor"></span>
          </template>
        </div>
      </div>

      <SourcePanel v-if="msg.role === 'assistant' && msg.sources && msg.sources.length" :sources="msg.sources" />
    </div>
  </div>
</template>

<script setup>
import SourcePanel from './SourcePanel.vue'

defineProps({
  msg: { type: Object, required: true },
})
</script>

<style scoped>
.msg-row {
  display: flex;
  gap: 14px;
  margin-bottom: 24px;
  animation: msg-appear 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes msg-appear {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.msg-row.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}

.msg-avatar svg {
  width: 20px;
  height: 20px;
}

.msg-row.user .msg-avatar {
  background: linear-gradient(135deg, var(--fm-primary), var(--fm-primary-dark));
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.msg-row.assistant .msg-avatar {
  background: linear-gradient(135deg, var(--fm-accent), #0891b2);
  box-shadow: 0 4px 12px rgba(6, 182, 212, 0.35);
}

.msg-body {
  max-width: min(72%, 720px);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
}

.msg-row.user .msg-body {
  align-items: flex-end;
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  padding: 0 6px;
}

.msg-row.user .msg-meta {
  flex-direction: row-reverse;
}

.msg-role {
  font-size: 12px;
  font-weight: 600;
  color: var(--fm-text-tertiary);
}

.msg-meta-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--fm-primary);
  background: var(--fm-primary-50);
  padding: 2px 8px;
  border-radius: var(--fm-radius-full);
}

.msg-meta-tag svg {
  width: 12px;
  height: 12px;
}

.msg-bubble {
  position: relative;
  padding: 14px 18px;
  border-radius: 18px;
  line-height: 1.75;
  font-size: 14.5px;
  word-break: break-word;
  transition: all var(--fm-transition);
}

.msg-row.assistant .msg-bubble {
  background: var(--fm-bg-card);
  border: 1px solid var(--fm-border);
  box-shadow: var(--fm-shadow-md);
  border-top-left-radius: 4px;
}

.msg-row.user .msg-bubble {
  background: linear-gradient(135deg, var(--fm-primary), var(--fm-primary-dark));
  color: #fff;
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.3);
  border-top-right-radius: 4px;
}

.msg-bubble--streaming {
  min-width: 120px;
}

.msg-content {
  position: relative;
}

.msg-text {
  white-space: pre-wrap;
  color: var(--fm-text-primary);
}

.msg-text--user {
  color: #fff;
}

.msg-thinking {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--fm-text-tertiary);
  font-size: 13.5px;
}

.thinking-dots {
  display: inline-flex;
  gap: 4px;
}

.thinking-dots span {
  width: 6px;
  height: 6px;
  background: var(--fm-primary);
  border-radius: 50%;
  animation: thinking-bounce 1.2s ease-in-out infinite;
}

.thinking-dots span:nth-child(2) {
  animation-delay: 0.15s;
}

.thinking-dots span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes thinking-bounce {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  40% {
    transform: translateY(-5px);
    opacity: 1;
  }
}

.thinking-text {
  font-size: 13px;
  color: var(--fm-text-tertiary);
}

.msg-cursor {
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background: var(--fm-primary);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursor-blink 1s step-end infinite;
  border-radius: 1px;
}

@keyframes cursor-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.msg-row.user .msg-cursor {
  background: rgba(255, 255, 255, 0.8);
}
</style>
