<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="brand">待办</div>

      <nav class="nav-menu">
        <router-link to="/my-tasks" class="nav-item" active-class="active">
          <el-icon><List /></el-icon>
          <span>我的任务</span>
        </router-link>

        <router-link to="/dashboard" class="nav-item" active-class="active">
          <el-icon><DataAnalysis /></el-icon>
          <span>我的仪表盘</span>
        </router-link>

        <router-link to="/gantt" class="nav-item" active-class="active">
          <el-icon><Calendar /></el-icon>
          <span>甘特图</span>
        </router-link>

        <div class="nav-section">团队</div>
        <template v-for="t in teams" :key="t.id">
          <router-link
            :to="`/team/${t.id}`"
            class="nav-item"
            active-class="active"
          >
            <el-icon><UserFilled /></el-icon>
            <span>{{ t.name }}</span>
          </router-link>
          <router-link
            :to="`/team/${t.id}/dashboard`"
            class="nav-item nav-item-sub"
            active-class="active"
          >
            <el-icon><DataAnalysis /></el-icon>
            <span>仪表盘</span>
          </router-link>
        </template>
      </nav>

      <div class="nav-bottom">
        <template v-if="store.isAdmin">
          <router-link to="/admin/users" class="nav-item" active-class="active">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </router-link>
          <router-link to="/admin/settings" class="nav-item" active-class="active">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </router-link>
        </template>
        <div class="nav-item logout" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user.js'
import api from '../api/index.js'

const router = useRouter()
const store = useUserStore()
const teams = ref([])

async function loadTeams() {
  try {
    const res = await api.get('/teams')
    teams.value = res.data || res || []
  } catch {
    teams.value = []
  }
}

async function handleLogout() {
  await store.logout()
  router.push('/login')
}

onMounted(loadTeams)
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: 200px;
  background: var(--sidebar-bg);
  padding: 20px 12px;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}
.brand {
  font-size: 18px;
  font-weight: 800;
  color: #fff;
  padding: 0 8px;
  margin-bottom: 24px;
}
.nav-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-section {
  font-size: 11px;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 16px 8px 6px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: rgba(255,255,255,0.6);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.15s ease;
}
.nav-item:hover {
  color: #fff;
  background: rgba(255,255,255,0.08);
}
.nav-item.active {
  color: #fff;
  background: var(--sidebar-active);
}
.nav-bottom {
  border-top: 1px solid rgba(255,255,255,0.1);
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.logout:hover { color: #FCA5A5; }
.nav-item-sub { padding-left: 28px; font-size: 12px; }
.main-content {
  flex: 1;
  margin-left: 200px;
  min-height: 100vh;
}
</style>
