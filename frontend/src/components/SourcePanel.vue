<template>
  <div class="source-panel" v-if="sources && sources.length">
    <div class="source-panel__header">
      <div class="source-panel__title">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 4h12v12H4z" />
          <path d="M8 8h4M8 11h6M8 14h3" />
        </svg>
        <span>溯源来源</span>
        <span class="source-panel__count">{{ sources.length }} 条</span>
      </div>
      <button class="source-panel__toggle" @click="expanded = !expanded">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :style="{ transform: expanded ? 'rotate(180deg)' : '' }">
          <path d="M5 8l5 5 5-5" />
        </svg>
      </button>
    </div>

    <transition name="expand">
      <div v-show="expanded" class="source-panel__body">
        <div class="source-cards">
          <div
            v-for="(s, i) in sources"
            :key="i"
            class="source-card"
            :class="{ 'source-card--active': activeIndex === i }"
            @click="activeIndex = activeIndex === i ? -1 : i"
          >
            <div class="source-card__header">
              <div class="source-card__index">#{{ i + 1 }}</div>
              <div class="source-card__tags">
                <span v-if="s.doc_type" class="src-tag src-tag--type">{{ docTypeLabel(s.doc_type) }}</span>
                <span v-if="s.fault_code" class="src-tag src-tag--fault">{{ s.fault_code }}</span>
                <span v-if="s.chapter_title" class="src-tag src-tag--chapter">{{ s.chapter_title }}</span>
                <span v-if="s.device_id" class="src-tag src-tag--device">{{ s.device_id }}</span>
              </div>
              <div class="source-card__score" :class="scoreClass(s.score)">
                <span class="score-bar"><span class="score-bar__fill" :style="{ width: scoreWidth(s.score) }"></span></span>
                <span class="score-value">{{ s.score != null ? (s.score * 100).toFixed(1) + '%' : '—' }}</span>
              </div>
            </div>

            <transition name="slide">
              <div v-show="activeIndex === i" class="source-card__content">
                <div class="source-card__text">{{ s.preview || s.text || '无预览内容' }}</div>
                <div v-if="s.metadata && Object.keys(s.metadata).length" class="source-card__meta">
                  <div v-for="(val, key) in displayMeta(s.metadata)" :key="key" class="meta-item">
                    <span class="meta-key">{{ metaLabel(key) }}</span>
                    <span class="meta-val">{{ String(val) }}</span>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  sources: { type: Array, default: () => [] },
})

const expanded = ref(true)
const activeIndex = ref(0)

function scoreClass(score) {
  if (score == null) return 'score-none'
  if (score >= 0.7) return 'score-high'
  if (score >= 0.4) return 'score-mid'
  return 'score-low'
}

function scoreWidth(score) {
  if (score == null) return '0%'
  return Math.max(2, Math.min(100, score * 100)) + '%'
}

function docTypeLabel(type) {
  const map = {
    log: '运维日志',
    manual: '设备手册',
    business: '工单记录',
    sop: '工艺SOP',
  }
  return map[type] || type
}

function metaLabel(key) {
  const map = {
    doc_id: '文档ID',
    chunk_id: '片段ID',
    doc_type: '类型',
    device_id: '设备',
    line_id: '产线',
    fault_code: '故障码',
    chapter_title: '章节',
    timestamp: '时间',
    source: '来源',
    page: '页码',
  }
  return map[key] || key
}

function displayMeta(metadata) {
  // 只展示有意义的元数据，不展示过长文本
  const showKeys = ['doc_id', 'doc_type', 'device_id', 'line_id', 'fault_code', 'chapter_title', 'timestamp', 'source', 'page']
  const result = {}
  for (const k of showKeys) {
    if (metadata[k] != null && metadata[k] !== '' && String(metadata[k]).length < 80) {
      result[k] = metadata[k]
    }
  }
  return result
}
</script>

<style scoped>
.source-panel {
  margin-top: 12px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.8) 0%, rgba(241, 245, 249, 0.6) 100%);
  border: 1px solid var(--fm-border);
  border-radius: var(--fm-radius-md);
  overflow: hidden;
}

.source-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid var(--fm-border-light);
}

.source-panel__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--fm-text-secondary);
}

.source-panel__title svg {
  width: 16px;
  height: 16px;
  color: var(--fm-primary);
}

.source-panel__count {
  padding: 2px 8px;
  background: var(--fm-primary-50);
  color: var(--fm-primary);
  border-radius: var(--fm-radius-full);
  font-size: 11px;
  font-weight: 600;
  margin-left: 2px;
}

.source-panel__toggle {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fm-text-tertiary);
  border-radius: var(--fm-radius-sm);
  transition: all var(--fm-transition);
}

.source-panel__toggle:hover {
  background: var(--fm-border-light);
  color: var(--fm-text-secondary);
}

.source-panel__toggle svg {
  width: 16px;
  height: 16px;
  transition: transform 0.25s ease;
}

.source-panel__body {
  padding: 12px;
}

.source-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-card {
  background: #fff;
  border: 1px solid var(--fm-border-light);
  border-radius: var(--fm-radius-sm);
  transition: all var(--fm-transition);
  overflow: hidden;
}

.source-card:hover {
  border-color: var(--fm-border-dark);
  box-shadow: var(--fm-shadow-sm);
}

.source-card--active {
  border-color: var(--fm-primary-100);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.08);
}

.source-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  user-select: none;
}

.source-card__index {
  font-size: 11px;
  font-weight: 700;
  color: var(--fm-primary);
  background: var(--fm-primary-50);
  padding: 2px 6px;
  border-radius: 4px;
  min-width: 26px;
  text-align: center;
  flex-shrink: 0;
}

.source-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.src-tag {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 7px;
  border-radius: var(--fm-radius-full);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.src-tag--type {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(6, 182, 212, 0.1));
  color: var(--fm-primary-dark);
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.src-tag--fault {
  background: rgba(239, 68, 68, 0.08);
  color: #dc2626;
  border: 1px solid rgba(239, 68, 68, 0.15);
}

.src-tag--chapter {
  background: rgba(16, 185, 129, 0.08);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.15);
}

.src-tag--device {
  background: rgba(245, 158, 11, 0.08);
  color: #d97706;
  border: 1px solid rgba(245, 158, 11, 0.15);
}

.source-card__score {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.score-bar {
  width: 40px;
  height: 5px;
  background: var(--fm-border-light);
  border-radius: var(--fm-radius-full);
  overflow: hidden;
}

.score-bar__fill {
  height: 100%;
  border-radius: var(--fm-radius-full);
  transition: width 0.5s ease;
}

.score-high .score-bar__fill {
  background: linear-gradient(90deg, var(--fm-success-light), var(--fm-success));
}

.score-mid .score-bar__fill {
  background: linear-gradient(90deg, #fbbf24, var(--fm-warning));
}

.score-low .score-bar__fill {
  background: linear-gradient(90deg, #f87171, var(--fm-error));
}

.score-value {
  font-size: 11px;
  font-weight: 600;
  min-width: 34px;
  text-align: right;
}

.score-high .score-value { color: var(--fm-success); }
.score-mid .score-value { color: var(--fm-warning); }
.score-low .score-value { color: var(--fm-error); }
.score-none .score-value { color: var(--fm-text-muted); }

.source-card__content {
  padding: 0 12px 12px;
  border-top: 1px solid var(--fm-border-light);
}

.source-card__text {
  font-size: 12.5px;
  line-height: 1.75;
  color: var(--fm-text-secondary);
  padding: 10px 0;
  white-space: pre-wrap;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 8;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.source-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  padding: 8px 0 0;
  border-top: 1px dashed var(--fm-border-light);
  margin-top: 4px;
  padding-top: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

.meta-key {
  color: var(--fm-text-muted);
}

.meta-val {
  color: var(--fm-text-secondary);
  font-weight: 500;
  font-family: var(--fm-font-mono);
  font-size: 10.5px;
  background: var(--fm-border-light);
  padding: 1px 6px;
  border-radius: 4px;
}

/* Animations */
.expand-enter-active,
.expand-leave-active {
  overflow: hidden;
  transition: max-height 0.3s ease, opacity 0.25s ease;
  max-height: 800px;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
  max-height: 0;
}
</style>
