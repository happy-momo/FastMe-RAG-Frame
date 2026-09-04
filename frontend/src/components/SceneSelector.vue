<template>
  <el-select :model-value="modelValue" placeholder="选择场景" @update:model-value="$emit('update:modelValue', $event)" style="width: 200px">
    <el-option
      v-for="s in scenes"
      :key="s.name"
      :label="s.description || s.name"
      :value="s.name"
    />
  </el-select>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: 'default' },
  scenes: { type: Array, default: () => [] },
})
defineEmits(['update:modelValue'])
</script>