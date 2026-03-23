# UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the entire frontend from orange warm-tone to indigo purple modern minimalist style with a sidebar navigation layout.

**Architecture:** Add CSS variables to `App.vue` for the new color system. Create `AppLayout.vue` as a sidebar wrapper for authenticated pages. Update all views and components to use the new design tokens. Login/Register use a full-screen split-pane layout without the sidebar.

**Tech Stack:** Vue 3, Element Plus, Pinia, CSS custom properties

**Design spec:** `docs/superpowers/specs/2026-03-23-ui-redesign-design.md`

---

## Dependencies

```
Task 1 (backend login response) → Task 2 (user store)
Task 3 (CSS variables) → Task 4 (AppLayout) → Task 5 (App.vue wiring)
Task 5 → Tasks 6-12 (all view/component updates)
Tasks 6-12 are independent of each other
```

---

### Task 1: Add is_admin to login response

The login endpoint only returns `access_token`. The sidebar needs `is_admin` to show admin links. Add it to the response.

**Files:**
- Modify: `backend/routers/auth.py:44`

- [ ] **Step 1: Update login response**

In `backend/routers/auth.py`, change line 44 from:
```python
    return ok({"access_token": access_token, "token_type": "bearer"})
```
to:
```python
    return ok({"access_token": access_token, "token_type": "bearer", "is_admin": user.is_admin})
```

- [ ] **Step 2: Run tests**

Run: `cd /root/todo/backend && python3 -m pytest tests/test_auth.py -v`
Expected: All 11 tests PASS.

- [ ] **Step 3: Commit**

```bash
cd /root/todo && git add backend/routers/auth.py
git commit -m "feat: include is_admin in login response"
```

---

### Task 2: Extend user store to persist is_admin

**Files:**
- Modify: `frontend/src/stores/user.js`

**Current content:**
```javascript
import { defineStore } from 'pinia'
import api, { setToken } from '../api/index.js'

export const useUserStore = defineStore('user', {
  state: () => ({ user: null }),
  getters: {
    isLoggedIn: s => !!s.user,
    isAdmin: s => s.user?.is_admin
  },
  actions: {
    async login(username, password) {
      const res = await api.post('/auth/login', { username, password })
      setToken(res.data.access_token)
      this.user = { username }
      return res
    },
    async logout() {
      await api.post('/auth/logout')
      setToken(null)
      this.user = null
    }
  }
})
```

- [ ] **Step 1: Update login action to store is_admin**

Change `this.user = { username }` to:
```javascript
      this.user = { username, is_admin: !!res.data.is_admin }
```

- [ ] **Step 2: Verify build**

Run: `cd /root/todo/frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
cd /root/todo && git add frontend/src/stores/user.js
git commit -m "feat: persist is_admin in user store from login response"
```

---

### Task 3: CSS variables and global styles

Delete the unused Vite scaffold `style.css`. Define all design tokens as CSS variables in `App.vue`'s non-scoped `<style>` block. Update `body` styles for new color scheme.

**Files:**
- Delete: `frontend/src/style.css`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Delete style.css**

```bash
rm /root/todo/frontend/src/style.css
```

This file is a Vite scaffold leftover and is not imported anywhere.

- [ ] **Step 2: Rewrite App.vue**

Replace the entire content of `frontend/src/App.vue` with:

```vue
<template>
  <app-layout v-if="showLayout">
    <router-view />
  </app-layout>
  <router-view v-else />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from './stores/user.js'
import AppLayout from './components/AppLayout.vue'

const route = useRoute()
const store = useUserStore()

const showLayout = computed(() => {
  return store.isLoggedIn && !route.meta.public
})
</script>

<style>
:root {
  --primary: #6366F1;
  --primary-hover: #4F46E5;
  --primary-light: #EEF2FF;
  --primary-border: #C7D2FE;
  --sidebar-bg: #1E1B4B;
  --sidebar-active: rgba(99,102,241,0.3);
  --page-bg: #F8FAFC;
  --card-bg: #FFFFFF;
  --card-inner-bg: #FAFAFA;
  --border: #E2E8F0;
  --text-primary: #1E1B4B;
  --text-secondary: #64748B;
  --text-muted: #94A3B8;
  --success: #10B981;
  --warning: #F59E0B;
  --danger: #EF4444;

  /* Override Element Plus primary color to match design system */
  --el-color-primary: #6366F1;
  --el-color-primary-light-3: #818CF8;
  --el-color-primary-light-5: #A5B4FC;
  --el-color-primary-light-7: #C7D2FE;
  --el-color-primary-light-8: #E0E7FF;
  --el-color-primary-light-9: #EEF2FF;
  --el-color-primary-dark-2: #4F46E5;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: var(--page-bg);
  font-family: 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  color: var(--text-primary);
}
</style>
```

Note: `AppLayout` doesn't exist yet — that's Task 4. The build will fail until Task 4 is done. Do NOT run build yet.

- [ ] **Step 3: Commit**

```bash
cd /root/todo && git add -u frontend/src/style.css frontend/src/App.vue
git commit -m "feat: add CSS design tokens and conditional layout in App.vue"
```

---

### Task 4: Create AppLayout sidebar component

**Files:**
- Create: `frontend/src/components/AppLayout.vue`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/AppLayout.vue`:

```vue
<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="brand">待办</div>

      <nav class="nav-menu">
        <router-link to="/my-tasks" class="nav-item" active-class="active">
          <el-icon><List /></el-icon>
          <span>我的任务</span>
        </router-link>

        <div class="nav-section">团队</div>
        <router-link
          v-for="t in teams"
          :key="t.id"
          :to="`/team/${t.id}`"
          class="nav-item"
          active-class="active"
        >
          <el-icon><UserFilled /></el-icon>
          <span>{{ t.name }}</span>
        </router-link>
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
.main-content {
  flex: 1;
  margin-left: 200px;
  min-height: 100vh;
}
</style>
```

- [ ] **Step 2: Verify build**

Run: `cd /root/todo/frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
cd /root/todo && git add frontend/src/components/AppLayout.vue
git commit -m "feat: add AppLayout sidebar navigation component"
```

---

### Task 5: Login and Register pages — split-pane layout

**Files:**
- Modify: `frontend/src/views/Login.vue`
- Modify: `frontend/src/views/Register.vue`

- [ ] **Step 1: Rewrite Login.vue**

Replace the entire content of `frontend/src/views/Login.vue`:

```vue
<template>
  <div class="auth-wrap">
    <div class="auth-brand">
      <h1>团队待办</h1>
      <p>高效协作，轻松管理</p>
    </div>
    <div class="auth-form-side">
      <div class="auth-form">
        <h2>欢迎回来</h2>
        <p class="subtitle">请登录你的账号</p>
        <el-form :model="form" @submit.prevent="handleLogin">
          <el-form-item>
            <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="form.password" type="password" placeholder="密码"
                      prefix-icon="Lock" show-password />
          </el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="btn-submit">
            登 录
          </el-button>
          <p v-if="error" class="error">{{ error }}</p>
          <p class="switch-link">没有账号？<router-link to="/register">立即注册</router-link></p>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user.js'

const router = useRouter()
const store = useUserStore()
const form = reactive({ username: '', password: '' })
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await store.login(form.username, form.password)
    router.push('/my-tasks')
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrap {
  display: flex;
  min-height: 100vh;
}
.auth-brand {
  flex: 1;
  background: linear-gradient(135deg, #1E1B4B 0%, #4338CA 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
}
.auth-brand h1 {
  font-size: 36px;
  font-weight: 800;
  color: #fff;
}
.auth-brand p {
  font-size: 14px;
  color: rgba(255,255,255,0.6);
  margin-top: 8px;
}
.auth-form-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  padding: 40px;
}
.auth-form {
  width: 100%;
  max-width: 360px;
}
.auth-form h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.subtitle {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 24px;
}
.btn-submit {
  width: 100%;
  background: var(--primary);
  border-color: var(--primary);
  border-radius: 10px;
  font-weight: 600;
}
.btn-submit:hover {
  background: var(--primary-hover);
  border-color: var(--primary-hover);
}
.error {
  color: var(--danger);
  margin-top: 8px;
  font-size: 13px;
}
.switch-link {
  text-align: center;
  margin-top: 16px;
  font-size: 13px;
  color: var(--text-muted);
}
.switch-link a {
  color: var(--primary);
  text-decoration: none;
}
.switch-link a:hover {
  color: var(--primary-hover);
}
:deep(.el-input__wrapper) {
  background: #F8FAFC;
  border-radius: 10px;
  box-shadow: 0 0 0 1px var(--border);
}
</style>
```

- [ ] **Step 2: Rewrite Register.vue**

Replace the entire content of `frontend/src/views/Register.vue`:

```vue
<template>
  <div class="auth-wrap">
    <div class="auth-brand">
      <h1>团队待办</h1>
      <p>高效协作，轻松管理</p>
    </div>
    <div class="auth-form-side">
      <div class="auth-form">
        <h2>注册账号</h2>
        <p class="subtitle">创建一个新账号</p>
        <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleRegister">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="form.email" placeholder="邮箱" prefix-icon="Message" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码"
                      prefix-icon="Lock" show-password />
          </el-form-item>
          <el-form-item prop="confirmPassword">
            <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码"
                      prefix-icon="Lock" show-password />
          </el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="btn-submit">
            注 册
          </el-button>
          <p v-if="error" class="error">{{ error }}</p>
          <p class="switch-link">已有账号？<router-link to="/login">去登录</router-link></p>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

const router = useRouter()
const formRef = ref(null)
const form = reactive({ username: '', email: '', password: '', confirmPassword: '' })
const loading = ref(false)
const error = ref('')

const usernameValidator = (rule, value, callback) => {
  if (!/^[a-zA-Z0-9_]{2,64}$/.test(value)) {
    callback(new Error('用户名须为 2-64 位字母、数字或下划线'))
  } else {
    callback()
  }
}

const confirmValidator = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { validator: usernameValidator, trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少需要 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: confirmValidator, trigger: 'blur' },
  ],
}

async function handleRegister() {
  try {
    await formRef.value.validate()
  } catch { return }
  loading.value = true
  error.value = ''
  try {
    await api.post('/auth/register', {
      username: form.username,
      email: form.email,
      password: form.password,
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (e) {
    error.value = e.response?.data?.detail || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrap {
  display: flex;
  min-height: 100vh;
}
.auth-brand {
  flex: 1;
  background: linear-gradient(135deg, #1E1B4B 0%, #4338CA 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
}
.auth-brand h1 {
  font-size: 36px;
  font-weight: 800;
  color: #fff;
}
.auth-brand p {
  font-size: 14px;
  color: rgba(255,255,255,0.6);
  margin-top: 8px;
}
.auth-form-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  padding: 40px;
}
.auth-form {
  width: 100%;
  max-width: 360px;
}
.auth-form h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.subtitle {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 24px;
}
.btn-submit {
  width: 100%;
  background: var(--primary);
  border-color: var(--primary);
  border-radius: 10px;
  font-weight: 600;
}
.btn-submit:hover {
  background: var(--primary-hover);
  border-color: var(--primary-hover);
}
.error {
  color: var(--danger);
  margin-top: 8px;
  font-size: 13px;
}
.switch-link {
  text-align: center;
  margin-top: 16px;
  font-size: 13px;
  color: var(--text-muted);
}
.switch-link a {
  color: var(--primary);
  text-decoration: none;
}
.switch-link a:hover {
  color: var(--primary-hover);
}
:deep(.el-input__wrapper) {
  background: #F8FAFC;
  border-radius: 10px;
  box-shadow: 0 0 0 1px var(--border);
}
</style>
```

- [ ] **Step 3: Verify build**

Run: `cd /root/todo/frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
cd /root/todo && git add frontend/src/views/Login.vue frontend/src/views/Register.vue
git commit -m "feat: redesign Login and Register with split-pane layout"
```

---

### Task 6: TaskCard and TaskBoard components

**Files:**
- Modify: `frontend/src/components/TaskCard.vue`
- Modify: `frontend/src/components/TaskBoard.vue`

- [ ] **Step 1: Rewrite TaskCard.vue**

Replace the entire content of `frontend/src/components/TaskCard.vue`:

```vue
<template>
  <div class="task-card" :class="borderClass">
    <div class="card-title">{{ task.title }}</div>
    <div class="card-footer">
      <span class="priority-tag" :class="priorityClass">{{ priorityLabel }}</span>
      <span v-if="task.due_date" class="due">{{ task.due_date }}</span>
    </div>
    <div v-if="task.labels?.length" class="labels">
      <span v-for="l in task.labels" :key="l" class="label-tag">{{ l }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ task: Object })

const priorityMap = {
  high: { cls: 'high', label: '高' },
  medium: { cls: 'medium', label: '中' },
  low: { cls: 'low', label: '低' },
}
const priorityClass = computed(() => priorityMap[props.task.priority]?.cls || 'low')
const priorityLabel = computed(() => priorityMap[props.task.priority]?.label || props.task.priority)

const borderClass = computed(() => {
  if (props.task.status === 'done') return 'border-success'
  if (props.task.status === 'in_progress') return 'border-primary'
  if (props.task.priority === 'high') return 'border-danger'
  if (props.task.priority === 'medium') return 'border-warning'
  return 'border-default'
})
</script>

<style scoped>
.task-card {
  background: var(--card-inner-bg);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 8px;
  border-left: 3px solid #CBD5E1;
  cursor: grab;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  transition: box-shadow 0.2s ease;
}
.task-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.border-danger { border-left-color: var(--danger); }
.border-warning { border-left-color: var(--warning); }
.border-primary { border-left-color: var(--primary); }
.border-success { border-left-color: var(--success); }
.border-default { border-left-color: #CBD5E1; }

.card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.priority-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 9999px;
}
.priority-tag.high { background: #FEE2E2; color: #991B1B; }
.priority-tag.medium { background: #FEF3C7; color: #92400E; }
.priority-tag.low { background: #E0E7FF; color: #3730A3; }

.due { font-size: 11px; color: var(--text-muted); }

.labels { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
.label-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--primary-light);
  color: var(--primary);
}
</style>
```

- [ ] **Step 2: Rewrite TaskBoard.vue**

Replace the entire content of `frontend/src/components/TaskBoard.vue`:

```vue
<template>
  <div class="board">
    <div v-for="col in columns" :key="col.status" class="column">
      <div class="col-header">
        <div class="col-title">
          <span class="dot" :style="{ background: col.color }"></span>
          <span>{{ col.label }}</span>
        </div>
        <span class="col-count">{{ (groupedTasks[col.status] || []).length }}</span>
      </div>
      <draggable
        :list="groupedTasks[col.status] || []"
        group="tasks"
        item-key="id"
        @change="(evt) => onChange(col.status, evt)"
        ghost-class="dragging-ghost"
      >
        <template #item="{ element }">
          <task-card :task="element" @click="$emit('task-click', element)" />
        </template>
      </draggable>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import draggable from 'vuedraggable'
import TaskCard from './TaskCard.vue'

const props = defineProps({ tasks: Array })
const emit = defineEmits(['update-status', 'task-click'])

const columns = [
  { status: 'pending', label: '待处理', color: '#94A3B8' },
  { status: 'in_progress', label: '进行中', color: '#6366F1' },
  { status: 'done', label: '已完成', color: '#10B981' },
]

const groupedTasks = computed(() => {
  const map = { pending: [], in_progress: [], done: [] }
  for (const t of props.tasks || []) {
    if (map[t.status]) map[t.status].push(t)
  }
  return map
})

function onChange(toStatus, evt) {
  if (evt.added) {
    emit('update-status', { taskId: evt.added.element.id, status: toStatus })
  }
}
</script>

<style scoped>
.board { display: flex; gap: 16px; align-items: flex-start; min-height: 60vh; }
.column {
  flex: 1;
  background: var(--card-bg);
  border-radius: 12px;
  padding: 12px;
  min-height: 200px;
  border: 1px solid var(--border);
}
.col-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.col-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.col-count {
  font-size: 12px;
  color: var(--text-muted);
}
.dragging-ghost { opacity: 0.4; }
</style>
```

- [ ] **Step 3: Verify build**

Run: `cd /root/todo/frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
cd /root/todo && git add frontend/src/components/TaskCard.vue frontend/src/components/TaskBoard.vue
git commit -m "feat: redesign TaskCard and TaskBoard with indigo theme"
```

---

### Task 7: MyTasks and TeamTasks pages

**Files:**
- Modify: `frontend/src/views/MyTasks.vue`
- Modify: `frontend/src/views/TeamTasks.vue`

- [ ] **Step 1: Rewrite MyTasks.vue template and styles**

The existing template already has the correct `<div class="header">` structure with `h2` and `el-button`. Add a task count line after the header. Replace the `<template>` section:

```html
<template>
  <div class="page">
    <div class="header">
      <div>
        <h2>我的任务</h2>
        <div class="task-count">共 {{ tasks.length }} 个任务</div>
      </div>
      <el-button type="primary" @click="showCreate = true" class="btn-new">+ 新建任务</el-button>
    </div>

    <div class="filters">
      <el-select v-model="filter.priority" placeholder="优先级" clearable @change="loadTasks" style="width:120px">
        <el-option value="high" label="高" />
        <el-option value="medium" label="中" />
        <el-option value="low" label="低" />
      </el-select>
      <el-select v-model="filter.status" placeholder="状态" clearable @change="loadTasks" style="width:120px">
        <el-option value="pending" label="待处理" />
        <el-option value="in_progress" label="进行中" />
        <el-option value="done" label="已完成" />
      </el-select>
    </div>

    <task-board :tasks="tasks" @update-status="updateStatus" @task-click="goDetail" />

    <el-dialog v-model="showCreate" title="新建任务" width="500px">
      <el-form :model="newTask" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="newTask.title" placeholder="任务标题" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="newTask.priority">
            <el-option value="high" label="高" />
            <el-option value="medium" label="中" />
            <el-option value="low" label="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="newTask.due_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="newTask.labelsInput" placeholder="逗号分隔，如：bug,紧急" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createTask" :disabled="!newTask.title">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

Replace the `<style scoped>` block:

```css
<style scoped>
.page { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.header h2 { font-size: 20px; font-weight: 700; color: var(--text-primary); margin: 0; }
.task-count { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.btn-new { border-radius: 10px; font-weight: 600; }
.filters { display: flex; gap: 8px; margin-bottom: 16px; }
</style>
```

Note: No inline color styles needed on `el-button type="primary"` — Element Plus's `--el-color-primary` is already overridden globally in Task 3.

- [ ] **Step 2: Rewrite TeamTasks.vue styles**

Replace the `<style scoped>` block in `frontend/src/views/TeamTasks.vue`:

```css
<style scoped>
.page { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.header h2 { font-size: 20px; font-weight: 700; color: var(--text-primary); margin: 0; }
.header-actions { display: flex; gap: 8px; }
</style>
```

All `el-button type="primary"` elements will automatically use the new indigo color via the global Element Plus override.

- [ ] **Step 3: Verify build**

Run: `cd /root/todo/frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
cd /root/todo && git add frontend/src/views/MyTasks.vue frontend/src/views/TeamTasks.vue
git commit -m "feat: redesign MyTasks and TeamTasks with new theme"
```

---

### Task 8: TaskDetail page

**Files:**
- Modify: `frontend/src/views/TaskDetail.vue`

- [ ] **Step 1: Update styles**

Replace the `<style scoped>` block in `frontend/src/views/TaskDetail.vue`:

```css
.page { padding: 24px; max-width: 900px; }
.detail-card { margin-top: 20px; border-radius: 12px; border: 1px solid var(--border); }
.section-card { margin-top: 16px; border-radius: 12px; border: 1px solid var(--border); }
.section-title { font-weight: 600; color: var(--text-primary); }
.urgent { color: var(--danger); font-weight: 600; }
.loading { padding-top: 60px; }
```

Remove `margin: 0 auto` from `.page` since the sidebar already positions the content.

- [ ] **Step 2: Verify build**

Run: `cd /root/todo/frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
cd /root/todo && git add frontend/src/views/TaskDetail.vue
git commit -m "feat: redesign TaskDetail with new theme"
```

---

### Task 9: CommentList and FileUpload components

**Files:**
- Modify: `frontend/src/components/CommentList.vue`
- Modify: `frontend/src/components/FileUpload.vue`

- [ ] **Step 1: Update CommentList.vue styles**

Replace the `<style scoped>` block in `frontend/src/components/CommentList.vue`:

```css
.comment-section { display: flex; flex-direction: column; gap: 12px; }
.empty { color: var(--text-muted); text-align: center; padding: 16px; }
.comment { background: var(--card-inner-bg); border-radius: 8px; padding: 10px 14px; }
.comment-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
.author { font-weight: 600; color: var(--primary); font-size: 13px; }
.time { font-size: 12px; color: var(--text-muted); }
.content { color: var(--text-primary); font-size: 14px; }
.comment-input { margin-top: 8px; }
```

- [ ] **Step 2: Update FileUpload.vue styles**

Replace the `<style scoped>` block in `frontend/src/components/FileUpload.vue`:

```css
.att-list { margin-top: 12px; display: flex; flex-direction: column; gap: 6px; }
.att-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.att-name { color: var(--primary); text-decoration: none; }
.att-name:hover { text-decoration: underline; color: var(--primary-hover); }
.att-size { color: var(--text-muted); font-size: 12px; }
.empty { color: var(--text-muted); font-size: 13px; padding: 8px 0; }
```

- [ ] **Step 3: Verify build**

Run: `cd /root/todo/frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
cd /root/todo && git add frontend/src/components/CommentList.vue frontend/src/components/FileUpload.vue
git commit -m "feat: redesign CommentList and FileUpload with new theme"
```

---

### Task 10: TeamManage page

**Files:**
- Modify: `frontend/src/views/TeamManage.vue`

- [ ] **Step 1: Update styles**

Replace the `<style scoped>` block in `frontend/src/views/TeamManage.vue`:

```css
.page { padding: 24px; max-width: 900px; }
.card { margin-top: 24px; border-radius: 12px; border: 1px solid var(--border); }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.add-member { display: flex; gap: 8px; align-items: center; }
```

- [ ] **Step 2: Verify build**

Run: `cd /root/todo/frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
cd /root/todo && git add frontend/src/views/TeamManage.vue
git commit -m "feat: redesign TeamManage with new theme"
```

---

### Task 11: Admin pages (UserManage + SystemSettings)

**Files:**
- Modify: `frontend/src/views/admin/UserManage.vue`
- Modify: `frontend/src/views/admin/SystemSettings.vue`

- [ ] **Step 1: Update UserManage.vue styles**

Replace the `<style scoped>` block in `frontend/src/views/admin/UserManage.vue`:

```css
.page { padding: 24px; max-width: 1000px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
h2 { color: var(--text-primary); font-size: 20px; font-weight: 700; margin: 0; }
```

- [ ] **Step 2: Update SystemSettings.vue styles**

Replace the `<style scoped>` block in `frontend/src/views/admin/SystemSettings.vue`:

```css
.page { padding: 24px; max-width: 800px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
h2 { color: var(--text-primary); font-size: 20px; font-weight: 700; margin: 0; }
.hint { margin-left: 8px; color: var(--text-muted); font-size: 13px; }
```

- [ ] **Step 3: Verify build**

Run: `cd /root/todo/frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
cd /root/todo && git add frontend/src/views/admin/UserManage.vue frontend/src/views/admin/SystemSettings.vue
git commit -m "feat: redesign admin pages with new theme"
```

---

### Task 12: Final verification

- [ ] **Step 1: Run full backend tests**

Run: `cd /root/todo/backend && python3 -m pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 2: Run frontend build**

Run: `cd /root/todo/frontend && npm run build`
Expected: Build succeeds with no errors.

- [ ] **Step 3: Commit any remaining changes**

If there are uncommitted changes, commit them.
