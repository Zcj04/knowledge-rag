<template>
  <div class="qa-view">
    <!-- Toolbar -->
    <div class="qa-toolbar">
      <div class="toolbar-left">
        <el-select v-model="chat.selectedKbId" placeholder="选择知识库" clearable size="small" style="width: 200px"
                   @change="onKbChange">
          <el-option v-for="kb in kbStore.kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
        </el-select>
        <el-divider direction="vertical" />
        <el-select v-model="selectedConvId" placeholder="历史对话" clearable size="small" style="width: 220px"
                   @change="onConvChange" @visible-change="onConvDropdownVisible">
          <el-option v-for="c in chat.conversations" :key="c.id" :label="c.title" :value="c.id">
            <span>{{ c.title }}</span>
            <span style="float:right;color:#909399;font-size:12px">{{ c.message_count }}条</span>
          </el-option>
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button size="small" @click="chat.newConversation(); selectedConvId = null">
          <el-icon><Plus /></el-icon> 新对话
        </el-button>
        <el-button size="small" @click="handleExport" :disabled="!chat.currentConvId">
          <el-icon><Download /></el-icon> 导出
        </el-button>
      </div>
    </div>

    <!-- Chat area -->
    <div class="qa-body">
      <div class="chat-area" ref="chatAreaRef">
        <!-- Welcome -->
        <div v-if="chat.messages.length === 0" class="welcome">
          <el-icon :size="56" color="#c0c4cc"><ChatDotRound /></el-icon>
          <h3>智能知识问答</h3>
          <p>选择一个知识库，开始提问吧</p>
        </div>

        <!-- Messages -->
        <div v-for="(msg, idx) in chat.messages" :key="msg.id || idx" class="message-wrap"
             :class="msg.role">
          <div class="message-bubble">
            <div class="msg-role">
              <el-icon v-if="msg.role === 'user'" :size="16"><UserFilled /></el-icon>
              <el-icon v-else :size="16" color="#409EFF"><Cpu /></el-icon>
              <span>{{ msg.role === 'user' ? '你' : '助手' }}</span>
              <span v-if="msg.confidence != null" class="confidence-badge"
                    :class="{ high: msg.confidence >= 0.7, low: msg.confidence < 0.5 }">
                置信度 {{ (msg.confidence * 100).toFixed(0) }}%
              </span>
            </div>
            <div class="msg-content" v-html="renderMarkdown(msg.content)" @click="onMsgClick(msg, idx)" />
            <!-- Citation chips -->
            <div v-if="msg.citations && msg.citations.length" class="citation-chips">
              <el-tag v-for="(c, i) in msg.citations" :key="i" size="small" effect="plain"
                      @click="showCitation(i)">
                {{ c.document_title }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="chat.asking" class="message-wrap assistant">
          <div class="message-bubble">
            <el-icon :size="16" color="#409EFF"><Cpu /></el-icon>
            <span class="typing">思考中...</span>
          </div>
        </div>
      </div>

      <!-- Citation Panel -->
      <div v-if="activeCitation != null" class="citation-panel">
        <div class="citation-header">
          <span>来源引用</span>
          <el-button text size="small" @click="activeCitation = null">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <div class="citation-body">
          <p class="citation-doc">{{ activeCitation.document_title }}</p>
          <el-progress
            :percentage="Math.round(activeCitation.similarity * 100)"
            :color="progressColor(activeCitation.similarity)"
            :stroke-width="6"
          />
          <p class="citation-text">{{ activeCitation.chunk_text }}</p>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="qa-input">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="2"
        placeholder="输入您的问题... (Ctrl+Enter 发送)"
        resize="none"
        @keydown.enter.ctrl="handleAsk"
      />
      <el-button type="primary" :loading="chat.asking" :disabled="!inputText.trim()" @click="handleAsk">
        <el-icon><Position /></el-icon> 发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useKbStore } from '../stores/kb'
import { ElMessage } from 'element-plus'
import { Plus, Download, ChatDotRound, UserFilled, Cpu, Close, Position } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'

const route = useRoute()
const chat = useChatStore()
const kbStore = useKbStore()

const md = new MarkdownIt({ breaks: true, linkify: true })

const inputText = ref('')
const chatAreaRef = ref<HTMLElement | null>(null)
const selectedConvId = ref<number | null>(null)
const activeCitation = ref<any>(null)

onMounted(async () => {
  await kbStore.fetchKbs()
  await chat.fetchConversations()

  // If navigated from kb detail with kb param, select that kb
  const kbParam = route.query.kb
  if (kbParam) {
    chat.setKbId(Number(kbParam))
  }

  const convId = route.params.convId
  if (convId) {
    selectedConvId.value = Number(convId)
    await chat.fetchConversation(Number(convId))
  }

  await nextTick()
  scrollToBottom()
})

watch(() => chat.messages.length, () => {
  nextTick(() => scrollToBottom())
})

function scrollToBottom() {
  if (chatAreaRef.value) {
    chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
  }
}

function onKbChange(kbId: number | null) {
  chat.setKbId(kbId)
  chat.fetchConversations(kbId || undefined)
}

function onConvChange(convId: number | null) {
  if (convId) {
    chat.fetchConversation(convId)
  } else {
    chat.newConversation()
  }
}

function onConvDropdownVisible(visible: boolean) {
  if (visible) {
    chat.fetchConversations(chat.selectedKbId || undefined)
  }
}

async function handleAsk() {
  const q = inputText.value.trim()
  if (!q || chat.asking) return
  inputText.value = ''
  try {
    const result = await chat.askQuestion(q)
    if (!selectedConvId.value) {
      selectedConvId.value = result.conversation_id
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '提问失败')
  }
}

function renderMarkdown(text: string) {
  return md.render(text)
}

function showCitation(index: number) {
  const msg = chat.messages.filter(m => m.role === 'assistant' && m.citations)
  let allCitations: any[] = []
  for (const m of msg) {
    if (m.citations) allCitations = allCitations.concat(m.citations)
  }
  activeCitation.value = allCitations[index] || null
}

function onMsgClick(_msg: any, _index: number) {
  // Could expand to show citations for that specific message
}

function progressColor(similarity: number) {
  if (similarity >= 0.7) return '#67c23a'
  if (similarity >= 0.5) return '#e6a23c'
  return '#f56c6c'
}

async function handleExport() {
  if (!chat.currentConvId) return
  await chat.exportConversation(chat.currentConvId)
  ElMessage.success('已导出')
}
</script>

<style scoped>
.qa-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px);
  max-width: 1200px;
}
.qa-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #fff;
  border-radius: 8px 8px 0 0;
  border: 1px solid #ebeef5;
  border-bottom: none;
}
.toolbar-left, .toolbar-right { display: flex; align-items: center; gap: 8px; }
.qa-body {
  flex: 1;
  display: flex;
  border: 1px solid #ebeef5;
  background: #fff;
  min-height: 0;
}
.chat-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  min-width: 0;
}
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #c0c4cc;
}
.welcome h3 { font-size: 20px; margin: 16px 0 8px; color: #909399; }
.welcome p { font-size: 14px; }
.message-wrap { margin-bottom: 20px; }
.message-wrap.user { display: flex; justify-content: flex-end; }
.message-bubble {
  display: inline-block;
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 8px;
  position: relative;
}
.message-wrap.user .message-bubble { background: #409EFF; color: #fff; }
.message-wrap.assistant .message-bubble { background: #f5f7fa; color: #303133; }
.msg-role {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  margin-bottom: 6px;
  opacity: 0.8;
}
.confidence-badge {
  margin-left: 6px;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: #e6f7e6;
  color: #67c23a;
}
.confidence-badge.low { background: #fef0f0; color: #f56c6c; }
.confidence-badge.high { background: #e6f7e6; color: #67c23a; }
.msg-content { font-size: 14px; line-height: 1.7; }
.msg-content :deep(p) { margin-bottom: 8px; }
.msg-content :deep(pre) { background: #f0f0f0; padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 13px; }
.citation-chips { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px; }
.citation-chips :deep(.el-tag) { cursor: pointer; }
.typing { font-size: 14px; color: #909399; margin-left: 8px; }

/* Citation Panel */
.citation-panel {
  width: 300px;
  flex-shrink: 0;
  border-left: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.citation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  border-bottom: 1px solid #ebeef5;
}
.citation-body { padding: 16px; }
.citation-doc { font-size: 14px; color: #409EFF; margin-bottom: 12px; font-weight: 500; }
.citation-text {
  margin-top: 12px;
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
  background: #fafafa;
  padding: 10px;
  border-radius: 4px;
}

/* Input */
.qa-input {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 0 0 8px 8px;
  border: 1px solid #ebeef5;
  border-top: none;
  align-items: flex-end;
}
.qa-input :deep(.el-textarea__inner) { font-size: 14px; }
.qa-input .el-button { flex-shrink: 0; }
</style>
