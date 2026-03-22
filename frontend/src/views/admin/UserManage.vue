<template>
  <div class="page">
    <div class="header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showCreate = true">+ 创建用户</el-button>
    </div>

    <el-table :data="users" v-loading="loading" style="width: 100%">
      <el-table-column label="用户名" prop="username" />
      <el-table-column label="邮箱" prop="email" />
      <el-table-column label="角色" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.is_admin" type="danger" size="small">管理员</el-tag>
          <el-tag v-else type="info" size="small">普通用户</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'warning'" size="small">
            {{ row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" align="center">
        <template #default="{ row }">
          <el-button
            :type="row.is_active ? 'warning' : 'success'"
            size="small"
            @click="toggleActive(row)"
          >{{ row.is_active ? '停用' : '启用' }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" title="创建用户" width="460px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="form.email" placeholder="邮箱地址" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="form.password" type="password" placeholder="登录密码" show-password />
        </el-form-item>
        <el-form-item label="管理员">
          <el-switch v-model="form.is_admin" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createUser" :disabled="!form.username || !form.email || !form.password">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api/index.js'

const users = ref([])
const loading = ref(false)
const showCreate = ref(false)
const form = reactive({ username: '', email: '', password: '', is_admin: false })

async function loadUsers() {
  loading.value = true
  try {
    const res = await api.get('/users')
    users.value = res.data || res
  } catch (e) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

async function toggleActive(user) {
  try {
    const res = await api.put(`/users/${user.id}`, { is_active: !user.is_active })
    const updated = res.data || res
    const idx = users.value.findIndex(u => u.id === user.id)
    if (idx !== -1) users.value[idx] = updated
    ElMessage.success(updated.is_active ? '用户已启用' : '用户已停用')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function createUser() {
  try {
    await api.post('/users', {
      username: form.username,
      email: form.email,
      password: form.password,
      is_admin: form.is_admin,
    })
    showCreate.value = false
    Object.assign(form, { username: '', email: '', password: '', is_admin: false })
    await loadUsers()
    ElMessage.success('用户已创建')
  } catch (e) {
    const msg = e.response?.data?.detail || '创建失败'
    ElMessage.error(msg)
  }
}

onMounted(loadUsers)
</script>

<style scoped>
.page { padding: 24px; max-width: 1000px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
h2 { color: #E8572A; font-size: 22px; font-weight: 700; margin: 0; }
</style>
