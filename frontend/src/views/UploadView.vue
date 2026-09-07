<template>
  <div class="upload-view">
    <div class="upload-container">
      <!-- 左侧：上传主区域 -->
      <div class="upload-main">
        <div class="upload-main__header">
          <h2>文档入库</h2>
          <p>上传文档，系统将自动完成文本提取、切片、向量化并存入知识库</p>
        </div>

        <!-- 文档类型选择 -->
        <div class="upload-section">
          <div class="section-label">
            <span class="section-num">1</span>
            选择文档类型
          </div>
          <div class="doc-type-grid">
            <div
              v-for="dt in docTypes"
              :key="dt.value"
              class="doc-type-card"
              :class="{ active: docType === dt.value }"
              @click="docType = dt.value"
            >
              <div class="doc-type-card__icon">{{ dt.icon }}</div>
              <div class="doc-type-card__info">
                <div class="doc-type-card__title">{{ dt.label }}</div>
                <div class="doc-type-card__desc">{{ dt.desc }}</div>
              </div>
              <div class="doc-type-card__check" v-if="docType === dt.value">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 10l4 4 8-8" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- 文件上传 -->
        <div class="upload-section">
          <div class="section-label">
            <span class="section-num">2</span>
            上传文档
          </div>

          <!-- 拖拽区 -->
          <div
            v-if="!currentFile"
            class="drop-zone"
            :class="{ 'drop-zone--dragover': isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
            @click="triggerFileInput"
          >
            <div class="drop-zone__icon">
              <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M24 4v22m0-22l-8 8m8-8l8 8" />
                <path d="M6 38v4a2 2 0 0 0 2 2h32a2 2 0 0 0 2-2v-4" />
              </svg>
            </div>
            <div class="drop-zone__title">
              将文件拖到此处，或 <span class="drop-zone__link">点击选择</span>
            </div>
            <div class="drop-zone__formats">
              支持格式：PDF · DOCX · TXT · LOG · MD
            </div>
            <div class="drop-zone__hint">最大 50MB · 建议文档结构清晰、内容完整</div>
            <input
              ref="fileInput"
              type="file"
              accept=".pdf,.docx,.txt,.log,.md"
              style="display: none"
              @change="handleFileSelect"
            />
          </div>

          <!-- 已选文件 -->
          <div v-else class="file-preview">
            <div class="file-preview__icon">
              <svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 4H8a2 2 0 0 0-2 2v28a2 2 0 0 0 2 2h24a2 2 0 0 0 2-2V14L22 2h-8z" />
                <path d="M22 2v12h12" />
              </svg>
            </div>
            <div class="file-preview__info">
              <div class="file-preview__name">{{ currentFile.name }}</div>
              <div class="file-preview__meta">
                <span>{{ formatSize(currentFile.size) }}</span>
                <span class="dot">·</span>
                <span>{{ fileTypeLabel }}</span>
              </div>
              <div v-if="uploading" class="file-preview__progress">
                <div class="progress-bar">
                  <div class="progress-bar__fill" :style="{ width: progressPercent + '%' }"></div>
                </div>
                <span class="progress-text">{{ progressPercent }}%</span>
              </div>
              <div v-else class="file-preview__ready">
                <span class="ready-dot"></span>
                准备就绪，等待入库
              </div>
            </div>
            <button class="file-preview__remove" @click="removeFile" :disabled="uploading">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 4l12 12M16 4L4 16" />
              </svg>
            </button>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="upload-actions">
          <button
            class="btn btn--primary"
            :class="{ 'btn--loading': uploading, 'btn--disabled': !canUpload }"
            :disabled="!canUpload"
            @click="doUpload"
          >
            <span v-if="!uploading" class="btn__icon">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10 3v10m0-10l-3 3m3-3l3 3" />
                <path d="M3 17h14" />
              </svg>
            </span>
            <svg v-else class="btn__spinner" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="22 22" />
            </svg>
            <span class="btn__text">{{ uploading ? '正在入库...' : '开始入库' }}</span>
          </button>

          <button
            v-if="result?.success"
            class="btn btn--ghost"
            @click="$router.push('/chat')"
          >
            <span class="btn__icon">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 4h12v8H9l-5 4V4z" />
              </svg>
            </span>
            <span class="btn__text">去对话</span>
          </button>
        </div>
      </div>

      <!-- 右侧：状态与结果 -->
      <div class="upload-side">
        <!-- 入库进度/结果卡片 -->
        <div class="side-card" :class="{ 'side-card--success': result?.success, 'side-card--error': result?.failed }">
          <div class="side-card__header">
            <div class="side-card__icon" :class="sideStatusClass">
              <template v-if="uploading">
                <svg class="spinner" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="28 28" />
                </svg>
              </template>
              <template v-else-if="result?.success">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M5 12l5 5L20 7" />
                </svg>
              </template>
              <template v-else-if="result?.failed">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="9" />
                  <path d="M12 8v5M12 16v.5" />
                </svg>
              </template>
              <template v-else>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="4" width="18" height="16" rx="2" />
                  <path d="M3 10h18M8 4v4M16 4v4" />
                </svg>
              </template>
            </div>
            <div class="side-card__title">{{ sideStatusTitle }}</div>
            <div class="side-card__subtitle">{{ sideStatusSubtitle }}</div>
          </div>

          <!-- 成功后的统计 -->
          <div v-if="result?.success" class="result-stats">
            <div class="stat-item">
              <div class="stat-item__value">{{ result.chunks_count }}</div>
              <div class="stat-item__label">切片数量</div>
            </div>
            <div class="stat-item">
              <div class="stat-item__value">{{ result.vector_count.toLocaleString() }}</div>
              <div class="stat-item__label">向量总数</div>
            </div>
          </div>

          <!-- 步骤指示器 -->
          <div class="steps-list">
            <div
              v-for="(step, i) in steps"
              :key="step.key"
              class="step-item"
              :class="step.status"
            >
              <div class="step-item__dot">
                <span v-if="step.status === 'done'">✓</span>
                <span v-else-if="step.status === 'active'">{{ i + 1 }}</span>
                <span v-else>{{ i + 1 }}</span>
              </div>
              <div class="step-item__text">
                <span class="step-item__label">{{ step.label }}</span>
                <span v-if="step.status === 'active'" class="step-item__hint">处理中...</span>
              </div>
            </div>
          </div>

          <!-- 错误信息 -->
          <div v-if="result?.failed" class="error-msg">
            {{ result.error }}
          </div>
        </div>

        <!-- 提示卡片 -->
        <div class="info-card">
          <div class="info-card__header">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="10" cy="10" r="8" />
              <path d="M10 7v.01M10 10v4" />
            </svg>
            <span>入库说明</span>
          </div>
          <ul class="info-card__list">
            <li>系统会自动提取文本并按语义切片</li>
            <li>Embedding 模型：BAAI/bge-m3（本地优先）</li>
            <li>向量库：Chroma（本地持久化）</li>
            <li>支持中英双语文档检索</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadDocument } from '../api/ingest'

const docType = ref('manual')
const isDragging = ref(false)
const currentFile = ref(null)
const uploading = ref(false)
const result = ref(null)
const progressPercent = ref(0)
const fileInput = ref(null)

const docTypes = [
  { value: 'manual', label: '设备手册', icon: '📖', desc: '操作说明、技术参数、维护指南' },
  { value: 'log', label: '运维日志', icon: '📊', desc: '设备运行日志、故障记录、告警信息' },
  { value: 'business', label: '工单记录', icon: '📋', desc: '生产工单、质检记录、异常报告' },
  { value: 'sop', label: '工艺 SOP', icon: '📐', desc: '标准作业流程、工艺规范、检验标准' },
]

const canUpload = computed(() => currentFile.value && !uploading.value)

const fileTypeLabel = computed(() => {
  if (!currentFile.value) return ''
  const ext = currentFile.value.name.split('.').pop()?.toLowerCase()
  return ext.toUpperCase() + ' 文件'
})

const steps = computed(() => {
  const base = [
    { key: 'parse', label: '解析文档' },
    { key: 'chunk', label: '文本切片' },
    { key: 'embed', label: '向量化' },
    { key: 'store', label: '存入向量库' },
  ]
  if (!uploading.value && !result.value) {
    return base.map(s => ({ ...s, status: 'pending' }))
  }
  if (result.value?.success) {
    return base.map(s => ({ ...s, status: 'done' }))
  }
  if (result.value?.failed) {
    return base.map((s, i) => ({ ...s, status: i === 0 ? 'error' : 'pending' }))
  }
  // 上传中：模拟进度
  const activeIdx = Math.min(3, Math.floor(progressPercent.value / 26))
  return base.map((s, i) => ({
    ...s,
    status: i < activeIdx ? 'done' : i === activeIdx ? 'active' : 'pending',
  }))
})

const sideStatusClass = computed(() => {
  if (uploading.value) return 'loading'
  if (result.value?.success) return 'success'
  if (result.value?.failed) return 'error'
  return 'idle'
})

const sideStatusTitle = computed(() => {
  if (uploading.value) return '正在入库'
  if (result.value?.success) return '入库完成'
  if (result.value?.failed) return '入库失败'
  return '等待上传'
})

const sideStatusSubtitle = computed(() => {
  if (uploading.value) return '文档处理中，请稍候...'
  if (result.value?.success) return '文档已成功加入知识库'
  if (result.value?.failed) return '请检查文件或重试'
  return '选择文档类型并上传文件'
})

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(e) {
  const file = e.target.files?.[0]
  if (file) addFile(file)
  e.target.value = '' // 重置以允许重复选择同一文件
}

function handleDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (!file) return
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  if (!['.pdf', '.docx', '.txt', '.log', '.md'].includes(ext)) {
    ElMessage.error('不支持的文件格式')
    return
  }
  addFile(file)
}

function addFile(file) {
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 50MB')
    return
  }
  currentFile.value = file
  result.value = null
  progressPercent.value = 0
}

function removeFile() {
  currentFile.value = null
  result.value = null
  progressPercent.value = 0
}

let progressTimer = null

function startProgressSim() {
  progressPercent.value = 0
  progressTimer = setInterval(() => {
    const increment = Math.random() * 8 + 2
    progressPercent.value = Math.min(95, progressPercent.value + increment)
  }, 400)
}

function stopProgressSim() {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
  progressPercent.value = 100
}

async function doUpload() {
  if (!currentFile.value || uploading.value) return
  uploading.value = true
  result.value = null
  startProgressSim()

  try {
    const res = await uploadDocument(currentFile.value, docType.value, null)
    result.value = { success: true, ...res }
    stopProgressSim()
    ElMessage.success('入库成功')
  } catch (e) {
    stopProgressSim()
    result.value = {
      success: false,
      failed: true,
      error: e.response?.data?.detail || e.message || '入库失败',
    }
    ElMessage.error('入库失败')
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.upload-view {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
}

.upload-container {
  max-width: 1100px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
  align-items: start;
}

/* Main column */
.upload-main {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.upload-main__header h2 {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 6px;
  color: var(--fm-text-primary);
  letter-spacing: -0.01em;
}

.upload-main__header p {
  font-size: 13.5px;
  color: var(--fm-text-tertiary);
  margin: 0;
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--fm-text-primary);
}

.section-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--fm-primary), var(--fm-accent));
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Document type cards */
.doc-type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.doc-type-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--fm-bg-card);
  border: 2px solid var(--fm-border);
  border-radius: var(--fm-radius-md);
  cursor: pointer;
  transition: all var(--fm-transition);
  position: relative;
}

.doc-type-card:hover {
  border-color: var(--fm-primary-light);
  background: var(--fm-primary-50);
}

.doc-type-card.active {
  border-color: var(--fm-primary);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.06), rgba(6, 182, 212, 0.04));
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
}

.doc-type-card__icon {
  font-size: 28px;
  flex-shrink: 0;
}

.doc-type-card__info {
  flex: 1;
  min-width: 0;
}

.doc-type-card__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--fm-text-primary);
  margin-bottom: 2px;
}

.doc-type-card__desc {
  font-size: 11.5px;
  color: var(--fm-text-tertiary);
  line-height: 1.4;
}

.doc-type-card__check {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--fm-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.doc-type-card__check svg {
  width: 14px;
  height: 14px;
}

/* Drop zone */
.drop-zone {
  background: var(--fm-bg-card);
  border: 2px dashed var(--fm-border-dark);
  border-radius: var(--fm-radius-lg);
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all var(--fm-transition);
}

.drop-zone:hover,
.drop-zone--dragover {
  border-color: var(--fm-primary);
  background: var(--fm-primary-50);
}

.drop-zone--dragover {
  transform: scale(1.01);
}

.drop-zone__icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  color: var(--fm-primary);
  background: var(--fm-primary-50);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drop-zone__icon svg {
  width: 36px;
  height: 36px;
}

.drop-zone__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--fm-text-primary);
  margin-bottom: 6px;
}

.drop-zone__link {
  color: var(--fm-primary);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.drop-zone__formats {
  font-size: 13px;
  color: var(--fm-text-secondary);
  margin-bottom: 6px;
}

.drop-zone__hint {
  font-size: 12px;
  color: var(--fm-text-muted);
}

/* File preview */
.file-preview {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  background: var(--fm-bg-card);
  border: 1px solid var(--fm-border);
  border-radius: var(--fm-radius-lg);
  box-shadow: var(--fm-shadow-sm);
}

.file-preview__icon {
  width: 48px;
  height: 48px;
  border-radius: var(--fm-radius-md);
  background: linear-gradient(135deg, var(--fm-primary-50), var(--fm-accent-50));
  color: var(--fm-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.file-preview__icon svg {
  width: 26px;
  height: 26px;
}

.file-preview__info {
  flex: 1;
  min-width: 0;
}

.file-preview__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--fm-text-primary);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-preview__meta {
  font-size: 12px;
  color: var(--fm-text-tertiary);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.file-preview__meta .dot {
  color: var(--fm-text-muted);
}

.file-preview__progress {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-bar {
  flex: 1;
  height: 5px;
  background: var(--fm-border-light);
  border-radius: var(--fm-radius-full);
  overflow: hidden;
}

.progress-bar__fill {
  height: 100%;
  background: linear-gradient(90deg, var(--fm-primary), var(--fm-accent));
  border-radius: var(--fm-radius-full);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 11px;
  font-weight: 600;
  color: var(--fm-primary);
  min-width: 36px;
  text-align: right;
}

.file-preview__ready {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--fm-success);
  font-weight: 500;
}

.ready-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--fm-success);
  animation: fm-pulse-dot 2s ease-in-out infinite;
}

.file-preview__remove {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--fm-border-light);
  color: var(--fm-text-tertiary);
  border-radius: var(--fm-radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--fm-transition);
  flex-shrink: 0;
}

.file-preview__remove:hover {
  background: #fef2f2;
  color: var(--fm-error);
}

.file-preview__remove:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.file-preview__remove svg {
  width: 16px;
  height: 16px;
}

/* Actions */
.upload-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 22px;
  border: none;
  border-radius: var(--fm-radius-md);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--fm-transition);
  font-family: inherit;
}

.btn--primary {
  background: linear-gradient(135deg, var(--fm-primary), var(--fm-primary-dark));
  color: #fff;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.btn--primary:hover:not(.btn--disabled):not(.btn--loading) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
}

.btn--primary:active:not(.btn--disabled):not(.btn--loading) {
  transform: translateY(0);
}

.btn--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn__icon {
  display: flex;
}

.btn__icon svg {
  width: 18px;
  height: 18px;
}

.btn__spinner {
  width: 18px;
  height: 18px;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn--ghost {
  background: var(--fm-bg-card);
  color: var(--fm-text-secondary);
  border: 1px solid var(--fm-border);
}

.btn--ghost:hover {
  border-color: var(--fm-primary-light);
  color: var(--fm-primary);
  background: var(--fm-primary-50);
}

.btn--ghost .btn__icon svg {
  width: 17px;
  height: 17px;
}

/* Side column */
.upload-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 0;
}

.side-card {
  background: var(--fm-bg-card);
  border: 1px solid var(--fm-border);
  border-radius: var(--fm-radius-lg);
  padding: 20px;
  box-shadow: var(--fm-shadow-sm);
  transition: all var(--fm-transition);
}

.side-card--success {
  border-color: rgba(16, 185, 129, 0.3);
  background: linear-gradient(180deg, rgba(16, 185, 129, 0.04), #fff 40%);
}

.side-card--error {
  border-color: rgba(239, 68, 68, 0.3);
  background: linear-gradient(180deg, rgba(239, 68, 68, 0.04), #fff 40%);
}

.side-card__header {
  text-align: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--fm-border-light);
}

.side-card__icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 10px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.side-card__icon.loading {
  background: var(--fm-primary-50);
  color: var(--fm-primary);
}

.side-card__icon.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--fm-success);
}

.side-card__icon.error {
  background: rgba(239, 68, 68, 0.1);
  color: var(--fm-error);
}

.side-card__icon.idle {
  background: var(--fm-border-light);
  color: var(--fm-text-tertiary);
}

.side-card__icon svg {
  width: 24px;
  height: 24px;
}

.spinner {
  animation: spin 0.8s linear infinite;
}

.side-card__title {
  font-size: 16px;
  font-weight: 700;
  color: var(--fm-text-primary);
  margin-bottom: 4px;
}

.side-card__subtitle {
  font-size: 12px;
  color: var(--fm-text-tertiary);
}

/* Result stats */
.result-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--fm-border-light);
}

.stat-item {
  text-align: center;
  padding: 10px 6px;
  background: var(--fm-bg);
  border-radius: var(--fm-radius-sm);
}

.stat-item__value {
  font-size: 20px;
  font-weight: 700;
  color: var(--fm-primary);
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-item__label {
  font-size: 11px;
  color: var(--fm-text-tertiary);
}

/* Steps */
.steps-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.step-item__dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
  transition: all var(--fm-transition);
}

.step-item.pending .step-item__dot {
  background: var(--fm-border-light);
  color: var(--fm-text-muted);
}

.step-item.active .step-item__dot {
  background: linear-gradient(135deg, var(--fm-primary), var(--fm-accent));
  color: #fff;
  animation: fm-pulse-dot 2s ease-in-out infinite;
}

.step-item.done .step-item__dot {
  background: var(--fm-success);
  color: #fff;
  font-size: 12px;
}

.step-item.error .step-item__dot {
  background: var(--fm-error);
  color: #fff;
}

.step-item__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.step-item__label {
  font-size: 13px;
  font-weight: 500;
  color: var(--fm-text-secondary);
}

.step-item.active .step-item__label {
  color: var(--fm-text-primary);
  font-weight: 600;
}

.step-item.done .step-item__label {
  color: var(--fm-text-secondary);
}

.step-item__hint {
  font-size: 11px;
  color: var(--fm-primary);
  font-weight: 500;
}

.error-msg {
  margin-top: 12px;
  padding: 10px 12px;
  background: rgba(239, 68, 68, 0.06);
  border-radius: var(--fm-radius-sm);
  font-size: 12px;
  color: var(--fm-error);
  line-height: 1.5;
  word-break: break-all;
}

/* Info card */
.info-card {
  background: var(--fm-bg-card);
  border: 1px solid var(--fm-border);
  border-radius: var(--fm-radius-lg);
  padding: 16px;
}

.info-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--fm-text-primary);
  margin-bottom: 10px;
}

.info-card__header svg {
  width: 18px;
  height: 18px;
  color: var(--fm-accent);
}

.info-card__list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-card__list li {
  font-size: 12px;
  color: var(--fm-text-tertiary);
  padding-left: 14px;
  position: relative;
  line-height: 1.5;
}

.info-card__list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 4px;
  height: 4px;
  background: var(--fm-primary);
  border-radius: 50%;
  opacity: 0.6;
}

/* Responsive */
@media (max-width: 960px) {
  .upload-container {
    grid-template-columns: 1fr;
  }
  .upload-side {
    position: static;
  }
}

@media (max-width: 600px) {
  .doc-type-grid {
    grid-template-columns: 1fr;
  }
}
</style>
