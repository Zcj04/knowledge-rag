<template>
  <div class="kb-detail" v-loading="store.loading">
    <div class="kb-header">
      <div>
        <el-page-header @back="$router.push('/')" :content="store.currentKb?.name" />
      </div>
      <div class="kb-header-actions">
        <el-button @click="showUpload = true">
          <el-icon><Upload /></el-icon> 上传文档
        </el-button>
        <el-button @click="$router.push(`/qa?kb=${$route.params.id}`)" type="primary">
          <el-icon><ChatDotRound /></el-icon> 开始提问
        </el-button>
      </div>
    </div>

    <div class="kb-body">
      <div class="categories-panel">
        <div class="panel-header">
          <span>分类管理</span>
          <el-button text size="small" @click="showAddCategory(null)">
            <el-icon><Plus /></el-icon>
          </el-button>
        </div>
        <div class="category-list">
          <div v-for="cat in store.categories" :key="cat.id">
            <div class="category-item" :class="{ active: selectedCategoryId === cat.id }" @click="selectCategory(cat.id)">
              <el-icon><Folder /></el-icon>
              <span>{{ cat.name }}</span>
              <span class="category-count">{{ catDocCount(cat.id) }}</span>
              <div class="cat-actions">
                <el-button text size="small" @click.stop="showAddCategory(cat.id)"><el-icon><Plus /></el-icon></el-button>
                <el-button text size="small" @click.stop="editCategory(cat)"><el-icon><Edit /></el-icon></el-button>
                <el-button text size="small" @click.stop="removeCategory(cat)"><el-icon><Delete /></el-icon></el-button>
              </div>
            </div>
            <div v-for="child in cat.children" :key="child.id" class="category-item sub" :class="{ active: selectedCategoryId === child.id }" @click="selectCategory(child.id)">
              <el-icon><FolderOpened /></el-icon>
              <span>{{ child.name }}</span>
              <span class="category-count">{{ catDocCount(child.id) }}</span>
              <div class="cat-actions">
                <el-button text size="small" @click.stop="removeCategory(child)"><el-icon><Delete /></el-icon></el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="documents-panel">
        <div class="panel-header">
          <el-input v-model="searchText" placeholder="搜索文档..." clearable size="small" style="width: 240px" prefix-icon="Search" @input="loadDocuments" />
          <el-select v-model="filterStatus" placeholder="状态筛选" clearable size="small" style="width: 120px" @change="loadDocuments">
            <el-option label="已完成" value="completed" />
            <el-option label="处理中" value="processing" />
            <el-option label="失败" value="failed" />
          </el-select>
        </div>

        <el-table :data="store.documents" style="width: 100%" v-loading="store.loading" empty-text="暂无文档">
          <el-table-column prop="title" label="文档名称" min-width="200">
            <template #default="{ row }">
              <div class="doc-title">
                <el-icon :size="18"><Document /></el-icon>
                <span>{{ row.title }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="file_type" label="类型" width="80">
            <template #default="{ row }">
              <el-tag size="small">{{ row.file_type.toUpperCase() }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag size="small" :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="分类" width="140">
            <template #default="{ row }">
              <el-select
                v-model="row._categoryId"
                placeholder="未分类"
                size="small"
                clearable
                @change="(val: number | null) => handleRecategorize(row, val)"
                @visible-change="(visible: boolean) => { if (visible) row._categoryId = row.category_id }"
              >
                <el-option
                  v-for="cat in flatCategories"
                  :key="cat.id"
                  :label="cat._label"
                  :value="cat.id"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column prop="chunk_count" label="分块" width="70" />
          <el-table-column label="标签" min-width="120">
            <template #default="{ row }">
              <el-tag v-for="t in row.tags" :key="t" size="small" class="doc-tag" effect="plain">{{ t }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button text size="small" @click="showTagDialog(row)">标签</el-button>
              <el-popconfirm title="确定删除此文档？" @confirm="store.deleteDocument(kbId, row.id)">
                <template #reference>
                  <el-button text size="small" type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrap" v-if="store.totalDocs > 20">
          <el-pagination v-model:current-page="page" :page-size="20" :total="store.totalDocs" layout="total, prev, pager, next" @current-change="loadDocuments" />
        </div>
      </div>
    </div>

    <el-dialog v-model="showUpload" title="上传文档" width="500px">
      <el-upload ref="uploadRef" drag :action="`/api/kb/${kbId}/documents/upload`" :headers="uploadHeaders" :data="uploadData" :on-success="onUploadSuccess" :on-error="onUploadError" multiple :limit="20">
        <el-icon :size="48" color="#c0c4cc"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF / DOCX / TXT / MD / 图片，单文件最大 50MB</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="showUpload = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCatDialog" :title="editingCat ? '编辑分类' : '新建分类'" width="400px">
      <el-form label-position="top">
        <el-form-item label="名称">
          <el-input v-model="catForm.name" placeholder="分类名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCatDialog = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showTagDlg" title="编辑标签" width="450px">
      <el-select v-model="selectedTagIds" multiple placeholder="选择标签" style="width: 100%" filterable allow-create @create="handleCreateTag">
        <el-option v-for="t in store.tags" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <template #footer>
        <el-button @click="showTagDlg = false">取消</el-button>
        <el-button type="primary" @click="saveTags">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useKbStore } from '../stores/kb'
import { ElMessage } from 'element-plus'
import { Upload, ChatDotRound, Plus, Folder, FolderOpened, Edit, Delete, Document, UploadFilled } from '@element-plus/icons-vue'
import type { Category, Document as DocType } from '../stores/kb'

const route = useRoute()
const store = useKbStore()

const kbId = computed(() => Number(route.params.id))
const searchText = ref('')
const filterStatus = ref('')
const page = ref(1)
const selectedCategoryId = ref<number | null>(null)
const showUpload = ref(false)
const showCatDialog = ref(false)
const editingCat = ref<Category | null>(null)
const catForm = ref({ name: '' })
const parentCatId = ref<number | null>(null)

const showTagDlg = ref(false)
const selectedTagIds = ref<number[]>([])
const taggingDoc = ref<DocType | null>(null)

const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`,
}))

const uploadData = computed(() => {
  const data: Record<string, any> = {}
  if (selectedCategoryId.value != null) {
    data.category_id = String(selectedCategoryId.value)
  }
  return data
})

// Flatten category tree for dropdown display
const flatCategories = computed(() => {
  const result: (Category & { _label: string })[] = []
  function walk(cats: Category[], prefix: string) {
    for (const c of cats) {
      result.push({ ...c, _label: prefix + c.name })
      if (c.children?.length) {
        walk(c.children, prefix + '  ')
      }
    }
  }
  walk(store.categories, '')
  return result
})

// Count docs per category (approximate from current page)
function catDocCount(_catId: number): string {
  return ''
}

onMounted(async () => {
  await store.fetchKbDetail(kbId.value)
  await store.fetchTags()
  loadDocuments()
})

function loadDocuments() {
  store.fetchDocuments(kbId.value, {
    category_id: selectedCategoryId.value || undefined,
    status: filterStatus.value || undefined,
    search: searchText.value || undefined,
    offset: (page.value - 1) * 20,
    limit: 20,
  })
}

function selectCategory(catId: number) {
  selectedCategoryId.value = selectedCategoryId.value === catId ? null : catId
  page.value = 1
  loadDocuments()
}

function showAddCategory(parentId: number | null) {
  parentCatId.value = parentId
  editingCat.value = null
  catForm.value.name = ''
  showCatDialog.value = true
}

function editCategory(cat: Category) {
  editingCat.value = cat
  catForm.value.name = cat.name
  parentCatId.value = null
  showCatDialog.value = true
}

async function saveCategory() {
  if (!catForm.value.name.trim()) return
  try {
    if (editingCat.value) {
      await store.updateCategory(kbId.value, editingCat.value.id, { name: catForm.value.name })
    } else {
      await store.createCategory(kbId.value, { name: catForm.value.name, parent_id: parentCatId.value })
    }
    showCatDialog.value = false
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  }
}

async function removeCategory(cat: Category) {
  try {
    await store.deleteCategory(kbId.value, cat.id)
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

function onUploadSuccess() {
  ElMessage.success('上传成功，正在处理...')
  setTimeout(loadDocuments, 2000)
}

function onUploadError(err: any) {
  ElMessage.error('上传失败: ' + (err.message || '未知错误'))
}

function statusType(s: string) {
  const map: Record<string, string> = { completed: 'success', processing: 'warning', failed: 'danger', pending: 'info' }
  return map[s] || 'info'
}

function statusLabel(s: string) {
  const map: Record<string, string> = { completed: '已完成', processing: '处理中', failed: '失败', pending: '等待中' }
  return map[s] || s
}

async function handleRecategorize(doc: any, categoryId: number | null) {
  try {
    await store.updateDocCategory(kbId.value, doc.id, categoryId)
    ElMessage.success('分类已更新')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '更新分类失败')
  }
}

function showTagDialog(doc: DocType) {
  taggingDoc.value = doc
  selectedTagIds.value = doc.tags.map((t: string) => store.tags.find((tag) => tag.name === t)?.id).filter(Boolean) as number[]
  showTagDlg.value = true
}

async function saveTags() {
  if (!taggingDoc.value) return
  await store.updateDocTags(kbId.value, taggingDoc.value.id, selectedTagIds.value)
  showTagDlg.value = false
}

async function handleCreateTag(val: string) {
  const tag = await store.createTag(val)
  selectedTagIds.value.push(tag.id)
}
</script>

<style scoped>
.kb-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; background: #fff; padding: 16px 20px; border-radius: 8px; border: 1px solid #ebeef5; }
.kb-header-actions { display: flex; gap: 8px; }
.kb-body { display: flex; gap: 16px; }
.categories-panel { width: 240px; flex-shrink: 0; background: #fff; border-radius: 8px; border: 1px solid #ebeef5; padding: 12px 0; max-height: calc(100vh - 200px); overflow-y: auto; }
.categories-panel .panel-header { display: flex; align-items: center; justify-content: space-between; padding: 0 12px 8px; font-weight: 600; font-size: 14px; color: #303133; border-bottom: 1px solid #ebeef5; margin-bottom: 4px; }
.category-item { display: flex; align-items: center; gap: 6px; padding: 8px 12px; cursor: pointer; font-size: 13px; color: #606266; transition: background .15s; }
.category-item:hover { background: #f5f7fa; }
.category-item.active { background: #ecf5ff; color: #409EFF; }
.category-item.sub { padding-left: 32px; }
.category-item span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.category-count { flex: 0 !important; font-size: 11px; color: #c0c4cc; margin-left: auto; padding-right: 4px; }
.cat-actions { display: none; flex-shrink: 0; }
.category-item:hover .cat-actions { display: flex; }
.category-item:hover .category-count { display: none; }
.documents-panel { flex: 1; background: #fff; border-radius: 8px; border: 1px solid #ebeef5; padding: 16px; min-width: 0; }
.documents-panel .panel-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.doc-title { display: flex; align-items: center; gap: 6px; }
.doc-tag { margin-right: 4px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
