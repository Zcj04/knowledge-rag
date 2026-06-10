<template>
  <div class="history-view">
    <div class="page-header">
      <h2>对话历史</h2>
      <el-button size="small" @click="chat.fetchConversations()">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <div class="conv-list" v-loading="loading">
      <div v-for="conv in chat.conversations" :key="conv.id" class="conv-card">
        <div class="conv-main" @click="$router.push(`/qa/${conv.id}`)">
          <h4>{{ conv.title }}</h4>
          <div class="conv-meta">
            <el-tag v-if="conv.kb_id" size="small" type="info">{{ getKbName(conv.kb_id) }}</el-tag>
            <span>{{ conv.message_count }} 条消息</span>
            <span>{{ formatDate(conv.created_at) }}</span>
          </div>
        </div>
        <div class="conv-actions">
          <el-button text size="small" @click="$router.push(`/qa/${conv.id}`)">
            <el-icon><ChatDotRound /></el-icon>
          </el-button>
          <el-button text size="small" @click="handleExport(conv.id)">
            <el-icon><Download /></el-icon>
          </el-button>
          <el-popconfirm title="确认删除此对话？" @confirm="handleDelete(conv.id)">
            <template #reference>
              <el-button text size="small" type="danger">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>

      <div v-if="!loading && chat.conversations.length === 0" class="empty-state">
        <el-empty description="暂无对话记录" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import { useKbStore } from '../stores/kb'
import { ElMessage } from 'element-plus'
import { Refresh, ChatDotRound, Download, Delete } from '@element-plus/icons-vue'

const chat = useChatStore()
const kbStore = useKbStore()
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  await kbStore.fetchKbs()
  await chat.fetchConversations()
  loading.value = false
})

function getKbName(kbId: number) {
  const kb = kbStore.kbs.find((k) => k.id === kbId)
  return kb?.name || `KB#${kbId}`
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN')
}

async function handleExport(convId: number) {
  await chat.exportConversation(convId)
  ElMessage.success('已导出')
}

async function handleDelete(convId: number) {
  await chat.deleteConversation(convId)
  ElMessage.success('已删除')
}
</script>

<style scoped>
.history-view { max-width: 900px; }
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-header h2 { font-size: 20px; color: #303133; }
.conv-list { display: flex; flex-direction: column; gap: 10px; }
.conv-card {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px 20px;
  transition: box-shadow .15s;
}
.conv-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.conv-main { flex: 1; cursor: pointer; min-width: 0; }
.conv-main h4 {
  font-size: 15px;
  color: #303133;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: #909399;
}
.conv-actions { display: flex; gap: 4px; flex-shrink: 0; }
.empty-state { padding: 60px 0; }
</style>
