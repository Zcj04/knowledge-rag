import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export interface KnowledgeBase {
  id: number
  name: string
  description: string
  visibility: string
  owner_id: number
  document_count: number
  created_at: string
}

export interface Category {
  id: number
  name: string
  parent_id: number | null
  kb_id: number
  sort_order: number
  children: Category[]
}

export interface Document {
  id: number
  title: string
  file_type: string
  kb_id: number
  category_id: number | null
  uploader_id: number
  status: string
  chunk_count: number
  error_message: string | null
  created_at: string
  tags: string[]
}

export interface Tag {
  id: number
  name: string
}

export const useKbStore = defineStore('kb', () => {
  const kbs = ref<KnowledgeBase[]>([])
  const currentKb = ref<KnowledgeBase | null>(null)
  const categories = ref<Category[]>([])
  const documents = ref<Document[]>([])
  const totalDocs = ref(0)
  const tags = ref<Tag[]>([])
  const loading = ref(false)

  async function fetchKbs() {
    loading.value = true
    try {
      const { data } = await api.get('/kb')
      kbs.value = data
    } catch (err: any) {
      console.error('Failed to fetch knowledge bases:', err)
      kbs.value = []
    } finally {
      loading.value = false
    }
  }

  async function createKb(payload: { name: string; description: string; visibility: string }) {
    const { data } = await api.post('/kb', payload)
    kbs.value.unshift(data)
    return data
  }

  async function updateKb(id: number, payload: Partial<KnowledgeBase>) {
    const { data } = await api.put(`/kb/${id}`, payload)
    const idx = kbs.value.findIndex((k) => k.id === id)
    if (idx >= 0) kbs.value[idx] = data
    currentKb.value = data
    return data
  }

  async function deleteKb(id: number) {
    await api.delete(`/kb/${id}`)
    kbs.value = kbs.value.filter((k) => k.id !== id)
  }

  async function fetchKbDetail(id: number) {
    loading.value = true
    try {
      const { data } = await api.get(`/kb/${id}`)
      currentKb.value = data
      categories.value = data.categories || []
    } finally {
      loading.value = false
    }
  }

  async function fetchCategories(kbId: number) {
    const { data } = await api.get(`/kb/${kbId}/categories`)
    categories.value = data
    return data
  }

  async function createCategory(kbId: number, payload: { name: string; parent_id?: number | null; sort_order?: number }) {
    const { data } = await api.post(`/kb/${kbId}/categories`, payload)
    await fetchCategories(kbId)
    return data
  }

  async function updateCategory(kbId: number, catId: number, payload: Partial<Category>) {
    const { data } = await api.put(`/kb/${kbId}/categories/${catId}`, payload)
    await fetchCategories(kbId)
    return data
  }

  async function deleteCategory(kbId: number, catId: number) {
    await api.delete(`/kb/${kbId}/categories/${catId}`)
    await fetchCategories(kbId)
  }

  async function fetchDocuments(kbId: number, params: Record<string, any> = {}) {
    const { data } = await api.get(`/kb/${kbId}/documents`, { params })
    documents.value = data.items
    totalDocs.value = data.total
    return data
  }

  async function uploadDocument(kbId: number, file: File, categoryId?: number) {
    const form = new FormData()
    form.append('file', file)
    if (categoryId) form.append('category_id', String(categoryId))
    const { data } = await api.post(`/kb/${kbId}/documents/upload`, form)
    return data
  }

  async function deleteDocument(kbId: number, docId: number) {
    await api.delete(`/kb/${kbId}/documents/${docId}`)
    documents.value = documents.value.filter((d) => d.id !== docId)
  }

  async function updateDocTags(kbId: number, docId: number, tagIds: number[]) {
    const { data } = await api.put(`/kb/${kbId}/documents/${docId}/tags`, { tag_ids: tagIds })
    const idx = documents.value.findIndex((d) => d.id === docId)
    if (idx >= 0) {
      documents.value[idx] = { ...documents.value[idx], tags: data.tags }
    }
    return data
  }

  async function updateDocCategory(kbId: number, docId: number, categoryId: number | null) {
    const { data } = await api.put(`/kb/${kbId}/documents/${docId}/category`, { category_id: categoryId })
    const idx = documents.value.findIndex((d) => d.id === docId)
    if (idx >= 0) {
      documents.value[idx] = { ...documents.value[idx], category_id: data.category_id }
    }
    return data
  }

  async function fetchTags() {
    const { data } = await api.get('/kb/tags')
    tags.value = data
    return data
  }

  async function createTag(name: string) {
    const { data } = await api.post('/kb/tags', { name })
    tags.value.push(data)
    return data
  }

  return {
    kbs, currentKb, categories, documents, totalDocs, tags, loading,
    fetchKbs, createKb, updateKb, deleteKb,
    fetchKbDetail, fetchCategories, createCategory, updateCategory, deleteCategory,
    fetchDocuments, uploadDocument, deleteDocument, updateDocTags, updateDocCategory,
    fetchTags, createTag,
  }
})
