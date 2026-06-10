<template>
  <div class="dashboard">
    <div class="page-header">
      <h2>知识库列表</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 新建知识库
      </el-button>
    </div>

    <!-- KB Cards Grid -->
    <div v-loading="store.loading" class="kb-grid">
      <div v-for="kb in store.kbs" :key="kb.id" class="kb-card" @click="$router.push(`/kb/${kb.id}`)">
        <div class="kb-card-header">
          <el-icon :size="28" color="#409EFF"><Folder /></el-icon>
          <el-tag size="small" :type="kb.visibility === 'public' ? 'success' : 'info'">
            {{ kb.visibility === 'public' ? '公开' : '私有' }}
          </el-tag>
        </div>
        <h3>{{ kb.name }}</h3>
        <p class="desc">{{ kb.description || '暂无描述' }}</p>
        <div class="kb-card-footer">
          <span><el-icon><Document /></el-icon> {{ kb.document_count }} 个文档</span>
          <el-dropdown trigger="click" @command="(cmd: string) => handleAction(cmd, kb)">
            <el-button text size="small" @click.stop>
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit">编辑</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="!store.loading && store.kbs.length === 0" class="empty-state">
        <el-empty description="还没有知识库，点击右上角新建" />
      </div>
    </div>

    <!-- Create / Edit Dialog -->
    <el-dialog v-model="showCreateDialog" :title="editingKb ? '编辑知识库' : '新建知识库'" width="480px">
      <el-form label-position="top">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="知识库描述" />
        </el-form-item>
        <el-form-item label="可见性">
          <el-radio-group v-model="form.visibility">
            <el-radio value="private">私有</el-radio>
            <el-radio value="public">公开</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          {{ editingKb ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useKbStore } from '../stores/kb'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Folder, Document, MoreFilled } from '@element-plus/icons-vue'
import type { KnowledgeBase } from '../stores/kb'

const store = useKbStore()

const showCreateDialog = ref(false)
const editingKb = ref<KnowledgeBase | null>(null)
const saving = ref(false)
const form = reactive({ name: '', description: '', visibility: 'private' })

onMounted(() => store.fetchKbs())

function handleAction(cmd: string, kb: KnowledgeBase) {
  if (cmd === 'edit') {
    editingKb.value = kb
    form.name = kb.name
    form.description = kb.description
    form.visibility = kb.visibility
    showCreateDialog.value = true
  } else if (cmd === 'delete') {
    ElMessageBox.confirm(`确定要删除知识库「${kb.name}」吗？此操作不可恢复。`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
    }).then(async () => {
      await store.deleteKb(kb.id)
      ElMessage.success('已删除')
    }).catch(() => {})
  }
}

async function handleSave() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  saving.value = true
  try {
    if (editingKb.value) {
      await store.updateKb(editingKb.value.id, {
        name: form.name,
        description: form.description,
        visibility: form.visibility,
      } as any)
      ElMessage.success('已更新')
    } else {
      await store.createKb({ ...form })
      ElMessage.success('已创建')
    }
    showCreateDialog.value = false
    form.name = ''
    form.description = ''
    form.visibility = 'private'
    editingKb.value = null
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.dashboard { max-width: 1200px; }
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.page-header h2 { font-size: 20px; color: #303133; }
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.kb-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  border: 1px solid #ebeef5;
  transition: box-shadow .2s, transform .2s;
}
.kb-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  transform: translateY(-2px);
}
.kb-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.kb-card h3 { font-size: 16px; color: #303133; margin-bottom: 8px; }
.desc { font-size: 13px; color: #909399; margin-bottom: 16px; min-height: 20px; }
.kb-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #c0c4cc;
}
.kb-card-footer span { display: flex; align-items: center; gap: 4px; }
.empty-state { grid-column: 1 / -1; padding: 60px 0; }
</style>
