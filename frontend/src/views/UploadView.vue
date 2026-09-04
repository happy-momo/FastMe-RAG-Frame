<template>
  <div class="upload-view">
    <el-card shadow="never" class="card">
      <template #header>
        <div class="card-head">
          <span>文档入库</span>
          <el-tag size="small" type="info">A2：有本地模型则用，否则自动下载</el-tag>
        </div>
      </template>

      <el-form label-width="110px">
        <el-form-item label="文档类型">
          <el-radio-group v-model="docType">
            <el-radio-button label="manual">设备手册</el-radio-button>
            <el-radio-button label="log">运维日志</el-radio-button>
            <el-radio-button label="business">工单</el-radio-button>
            <el-radio-button label="sop">工艺 SOP</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="选择文件">
          <el-upload
            v-model:file-list="fileList"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".pdf,.docx,.txt,.log,.md"
            :on-exceed="onExceed"
            :disabled="uploading"
          >
            <div class="upload-inner">
              <el-icon size="60" color="#c0c4cc"><upload-filled /></el-icon>
              <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
              <div class="tip">支持 PDF / DOCX / TXT / LOG / MD</div>
            </div>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="uploading" :disabled="!canUpload" @click="doUpload">
            {{ uploading ? '入库中…' : '开始入库' }}
          </el-button>
          <el-button @click="$router.push('/chat')">去对话</el-button>
        </el-form-item>
      </el-form>

      <el-alert
        v-if="result"
        :title="successTip"
        :type="result.failed ? 'error' : 'success'"
        :closable="false"
        show-icon
        class="result"
      />
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { uploadDocument } from '../api/ingest'

const docType = ref('manual')
const fileList = ref([])
const uploading = ref(false)
const result = ref(null)

const canUpload = computed(() => fileList.value.length > 0 && !uploading.value)
const successTip = computed(() =>
  result.value?.success
    ? `入库成功：${result.value.file_name}（${result.value.chunks_count} chunks，向量 ${result.value.vector_count}）`
    : result.value?.error || '',
)

function onExceed() {
  ElMessage.warning('一次只能上传一个文件')
}

async function doUpload() {
  const file = fileList.value[0]
  if (!file) return
  uploading.value = true
  result.value = null
  try {
    const res = await uploadDocument(file.raw, docType.value, null)
    result.value = { success: true, ...res }
    ElMessage.success('入库成功')
  } catch (e) {
    result.value = { success: false, error: e.response?.data?.detail || e.message }
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.upload-view { padding: 24px; height: 100%; overflow-y: auto; }
.card { max-width: 720px; margin: 0 auto; }
.card-head { display: flex; align-items: center; gap: 12px; }
.upload-inner { padding: 12px 0; }
.tip { font-size: 12px; color: #909399; }
.result { margin-top: 16px; }
</style>