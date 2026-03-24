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
import { getErrorMessage } from '../api/index.js'
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
    error.value = getErrorMessage(e, '登录失败')
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
