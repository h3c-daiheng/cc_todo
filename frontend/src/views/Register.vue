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
