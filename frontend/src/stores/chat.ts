import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export interface Message {
  id: number
  role: string
  content: string
  citations: Citation[] | null
  confidence: number | null
  created_at: string
}

export interface Citation {
  document_title: string
  chunk_text: string
  similarity: number
}

export interface Conversation {
  id: number
  title: string
  kb_id: number | null
  created_at: string
  message_count: number
}

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([])
  const currentConvId = ref<number | null>(null)
  const messages = ref<Message[]>([])
  const selectedKbId = ref<number | null>(null)
  const asking = ref(false)

  async function fetchConversations(kbId?: number) {
    const params = kbId ? { kb_id: kbId } : {}
    const { data } = await api.get('/qa/conversations', { params })
    conversations.value = data
  }

  async function fetchConversation(convId: number) {
    const { data } = await api.get(`/qa/conversations/${convId}`)
    messages.value = data.messages
    currentConvId.value = convId
    selectedKbId.value = data.kb_id
  }

  async function askQuestion(question: string) {
    asking.value = true
    try {
      const payload: any = { question }
      if (currentConvId.value) payload.conversation_id = currentConvId.value
      if (selectedKbId.value) payload.kb_id = selectedKbId.value

      const { data } = await api.post('/qa/ask', payload)

      // Add user message locally
      messages.value.push({
        id: Date.now(),
        role: 'user',
        content: question,
        citations: null,
        confidence: null,
        created_at: new Date().toISOString(),
      })

      // Add assistant message
      messages.value.push({
        id: data.message_id,
        role: 'assistant',
        content: data.answer,
        citations: data.citations,
        confidence: data.confidence,
        created_at: new Date().toISOString(),
      })

      if (!currentConvId.value) {
        currentConvId.value = data.conversation_id
        await fetchConversations()
      }
      return data
    } finally {
      asking.value = false
    }
  }

  async function deleteConversation(convId: number) {
    await api.delete(`/qa/conversations/${convId}`)
    conversations.value = conversations.value.filter((c) => c.id !== convId)
    if (currentConvId.value === convId) {
      currentConvId.value = null
      messages.value = []
    }
  }

  async function exportConversation(convId: number) {
    const { data } = await api.get(`/qa/conversations/${convId}/export`, { responseType: 'text' })
    const blob = new Blob([data], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `conversation-${convId}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  function newConversation() {
    currentConvId.value = null
    messages.value = []
  }

  function setKbId(kbId: number | null) {
    selectedKbId.value = kbId
  }

  return {
    conversations, currentConvId, messages, selectedKbId, asking,
    fetchConversations, fetchConversation, askQuestion,
    deleteConversation, exportConversation, newConversation, setKbId,
  }
})
