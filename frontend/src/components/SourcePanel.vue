<template>
  <el-divider content-position="left">溯源来源（{{ sources.length }}）</el-divider>
  <div class="source-list">
    <el-collapse v-if="sources.length">
      <el-collapse-item v-for="(s, i) in sources" :key="i">
        <template #title>
          <span class="src-title">
            #{{ i + 1 }}
            <el-tag size="small" v-if="s.fault_code">{{ s.fault_code }}</el-tag>
            <el-tag size="small" v-if="s.chapter_title">{{ s.chapter_title }}</el-tag>
            <span class="score" :class="scoreClass(s.score)">
              {{ s.score != null ? s.score.toFixed(3) : '' }}
            </span>
          </span>
        </template>
        <p class="src-preview">{{ s.preview || s.text || '无预览' }}</p>
      </el-collapse-item>
    </el-collapse>
    <el-empty v-else description="无来源信息" :image-size="40" />
  </div>
</template>

<script setup>
defineProps({
  sources: { type: Array, default: () => [] },
})

function scoreClass(score) {
  if (score == null) return 'score-none'
  if (score >= 0.7) return 'score-high'
  if (score >= 0.4) return 'score-mid'
  return 'score-low'
}
</script>

<style scoped>
.source-list { max-height: 240px; overflow: auto; }
.src-title { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; }
.src-preview { font-size: 12px; color: #606266; margin: 4px 0; line-height: 1.6; white-space: pre-wrap; }
.score { font-size: 12px; }
.score-high { color: #67c23a; }
.score-mid { color: #e6a23c; }
.score-low { color: #f56c6c; }
.score-none { color: #909399; }
</style>