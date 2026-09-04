<template>
  <el-container class="app-shell">
    <el-aside width="260px" class="sidebar">
      <div class="brand">
        <h1>FastMe RAG</h1>
        <p>开箱即用 RAG Chatbot</p>
      </div>
      <el-menu :default-active="$route.path" router class="side-menu">
        <el-menu-item index="/chat">💬 对话</el-menu-item>
        <el-menu-item index="/upload">📄 文档入库</el-menu-item>
      </el-menu>
      <div class="health">
        <el-tag :type="health.llm_reachable ? 'success' : 'warning'" size="small">
          LLM {{ health.llm_reachable ? '可达' : '未连接' }}
        </el-tag>
        <el-tag size="small" type="info" class="vc">
          向量数 {{ health.vector_count }}
        </el-tag>
      </div>
    </el-aside>
    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { fetchHealth } from './api/ingest'

const health = reactive({ llm_reachable: null, vector_count: 0 })

onMounted(async () => {
  try {
    const h = await fetchHealth()
    Object.assign(health, h)
  } catch (e) {
    /* 后端未起时静默 */
  }
})
</script>

<style>
* { box-sizing: border-box; }
html, body, #app { height: 100%; margin: 0; font-family: system-ui, -apple-system, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; }
.app-shell { height: 100vh; }
.sidebar {
  background: #1f2d3d;
  color: #fff;
  display: flex;
  flex-direction: column;
}
.brand { padding: 20px 20px 12px; }
.brand h1 { margin: 0; font-size: 22px; }
.brand p { margin: 4px 0 0; font-size: 12px; opacity: 0.7; }
.side-menu { background: transparent; border-right: none; }
.side-menu .el-menu-item { color: #cfd8e3; }
.side-menu .el-menu-item.is-active { color: #fff; background: #2f3f52; }
.health { margin-top: auto; padding: 16px 20px; display: flex; flex-direction: column; gap: 8px; align-items: flex-start; }
.main { padding: 0; height: 100vh; overflow: hidden; }
</style>