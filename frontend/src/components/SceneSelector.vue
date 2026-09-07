<template>
  <el-select
    :model-value="modelValue"
    placeholder="选择场景"
    @update:model-value="$emit('update:modelValue', $event)"
    class="scene-selector"
    popper-class="scene-selector__popper"
  >
    <template #prefix>
      <span class="scene-selector__prefix">
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M8 1.5l6 3v7l-6 3-6-3v-7l6-3z" />
          <path d="M2 4.5l6 3 6-3M8 7.5v7" />
        </svg>
      </span>
    </template>
    <el-option
      v-for="s in scenes"
      :key="s.name"
      :label="s.description || s.name"
      :value="s.name"
    >
      <div class="scene-option">
        <span class="scene-option__icon">{{ sceneIcon(s.name) }}</span>
        <div class="scene-option__text">
          <span class="scene-option__title">{{ sceneTitle(s.description) }}</span>
          <span class="scene-option__desc">{{ sceneDesc(s.description) }}</span>
        </div>
      </div>
    </el-option>
  </el-select>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: 'default' },
  scenes: { type: Array, default: () => [] },
})
defineEmits(['update:modelValue'])

function sceneIcon(name) {
  const map = {
    fault_diagnosis: '🔧',
    manual_query: '📖',
    work_order_trace: '📋',
    default: '💬',
  }
  return map[name] || '💬'
}

function sceneTitle(desc) {
  if (!desc) return ''
  return desc.split(' - ')[0] || desc
}

function sceneDesc(desc) {
  if (!desc) return ''
  const parts = desc.split(' - ')
  return parts[1] || ''
}
</script>

<style scoped>
.scene-selector {
  width: 240px;
}

.scene-selector :deep(.el-select__wrapper) {
  border-radius: var(--fm-radius-md);
  background: var(--fm-bg);
  border-color: var(--fm-border);
  transition: all var(--fm-transition);
}

.scene-selector :deep(.el-select__wrapper:hover) {
  border-color: var(--fm-primary-light);
}

.scene-selector :deep(.el-select__wrapper.is-focused) {
  border-color: var(--fm-primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.scene-selector__prefix {
  display: flex;
  align-items: center;
  color: var(--fm-primary);
}

.scene-selector__prefix svg {
  width: 16px;
  height: 16px;
}

.scene-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
}

.scene-option__icon {
  font-size: 18px;
  flex-shrink: 0;
}

.scene-option__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.scene-option__title {
  font-size: 13px;
  font-weight: 500;
  color: var(--fm-text-primary);
  line-height: 1.3;
}

.scene-option__desc {
  font-size: 11px;
  color: var(--fm-text-muted);
  line-height: 1.3;
}
</style>

<style>
/* Popper dropdown styles */
.scene-selector__popper .el-select-dropdown__item {
  height: auto;
  padding: 8px 14px;
  line-height: normal;
}

.scene-selector__popper .el-select-dropdown__item.is-hovering {
  background: var(--fm-primary-50);
}

.scene-selector__popper .el-select-dropdown__item.selected {
  color: var(--fm-primary);
  font-weight: 500;
}
</style>
