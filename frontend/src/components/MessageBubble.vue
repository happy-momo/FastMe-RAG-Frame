<template>
  <div class="bubble-row" :class="msg.role">
    <div class="avatar">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
    <div class="bubble">
      <div class="content">
        <span v-if="msg.streaming && !msg.content" class="thinking">思考中…</span>
        <span class="text">{{ msg.content }}</span>
        <span v-if="msg.streaming" class="cursor">▍</span>
      </div>
      <SourcePanel v-if="msg.sources && msg.sources.length" :sources="msg.sources" />
    </div>
  </div>
</template>

<script setup>
import SourcePanel from './SourcePanel.vue'

defineProps({ msg: { type: Object, required: true } })
</script>

<style scoped>
.bubble-row { display: flex; gap: 12px; margin-bottom: 18px; }
.bubble-row.user { flex-direction: row-reverse; }
.avatar {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; color: #fff; flex-shrink: 0;
}
.bubble-row.user .avatar { background: #409eff; }
.bubble-row.assistant .avatar { background: #67c23a; }
.bubble {
  max-width: 70%; background: #fff; border: 1px solid #ebeef5;
  border-radius: 8px; padding: 12px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.bubble-row.user .bubble { background: #ecf5ff; }
.content { font-size: 14px; line-height: 1.7; white-space: pre-wrap; word-break: break-word; }
.thinking { color: #909399; }
.cursor { color: #409eff; animation: blink 0.8s infinite; }
@keyframes blink { 50% { opacity: 0; } }
</style>