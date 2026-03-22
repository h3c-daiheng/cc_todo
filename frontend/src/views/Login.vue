<template>
  <div class="login-wrap">
    <el-card class="login-card">
      <h2 class="title">团队待办</h2>
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码"
                    prefix-icon="Lock" show-password />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" class="btn-login">
          登录
        </el-button>
        <p v-if="error" class="error">{{ error }}</p>
      </el-form>
    </el-card>
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
.login-wrap { min-height: 100vh; display: flex; align-items: center; justify-content: center; }
.login-card { width: 360px; border-radius: 12px; }
.title { text-align: center; margin-bottom: 24px; font-size: 22px; color: #E8572A; }
.btn-login { width: 100%; background: #E8572A; border-color: #E8572A; }
.btn-login:hover { background: #F4A259; border-color: #F4A259; }
.error { color: #E8572A; margin-top: 8px; font-size: 13px; }
</style>
