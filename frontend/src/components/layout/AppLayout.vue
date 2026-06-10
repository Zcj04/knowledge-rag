<template>
  <el-container class="app-layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo" @click="$router.push('/')">
        <span class="logo-text">Knowledge RAG</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#1a1a2e"
        text-color="#a0aec0"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>知识库列表</span>
        </el-menu-item>
        <el-menu-item index="/qa">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能问答</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Clock /></el-icon>
          <span>对话历史</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <div class="user-info">
          <el-avatar :size="32" icon="UserFilled" />
          <span class="username">{{ auth.user?.username }}</span>
        </div>
        <el-button text size="small" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </div>
    </el-aside>
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { ElMessage } from 'element-plus'
import { HomeFilled, ChatDotRound, Clock, SwitchButton, UserFilled } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/kb')) return '/'
  if (path.startsWith('/qa')) return '/qa'
  if (path.startsWith('/history')) return '/history'
  return path
})

onMounted(async () => {
  if (auth.token) {
    try {
      await auth.fetchMe()
    } catch {
      // Token invalid, redirect to login
      auth.logout()
      router.push('/login')
    }
  }
})

function handleLogout() {
  auth.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.app-layout { height: 100vh; }
.sidebar {
  background: #1a1a2e;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.logo {
  padding: 20px 16px;
  cursor: pointer;
  border-bottom: 1px solid #2d2d44;
}
.logo-text {
  color: #409EFF;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.sidebar :deep(.el-menu) {
  border-right: none;
  flex: 1;
}
.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #2d2d44;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e2e8f0;
  font-size: 13px;
}
.main-content {
  background: #f5f7fa;
  padding: 24px;
  overflow-y: auto;
}
</style>
