<template>
  <div class="page">
    <div class="header">
      <h2>系统设置 — 邮件服务器</h2>
      <el-button type="primary" @click="saveSettings" :loading="saving">保存</el-button>
    </div>

    <el-card v-loading="loading">
      <el-form :model="form" label-width="130px" style="max-width: 560px">
        <el-form-item label="SMTP 主机">
          <el-input v-model="form.smtp_host" placeholder="如：smtp.example.com" />
        </el-form-item>
        <el-form-item label="SMTP 端口">
          <el-input-number v-model="form.smtp_port" :min="1" :max="65535" controls-position="right" style="width: 160px" />
        </el-form-item>
        <el-form-item label="发件人地址">
          <el-input v-model="form.smtp_from" placeholder="noreply@example.com" />
        </el-form-item>
        <el-form-item label="SMTP 用户名">
          <el-input v-model="form.smtp_username" placeholder="登录用户名" />
        </el-form-item>
        <el-form-item label="SMTP 密码">
          <el-input
            v-model="form.smtp_password"
            type="password"
            placeholder="留空表示不修改"
            show-password
          />
        </el-form-item>
        <el-form-item label="使用 TLS">
          <el-switch v-model="form.smtp_use_tls" />
        </el-form-item>
        <el-form-item label="邮件发送时间">
          <el-input-number
            v-model="form.email_send_hour"
            :min="0"
            :max="23"
            controls-position="right"
            style="width: 120px"
          />
          <span class="hint">时（0–23）</span>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api/index.js'

const loading = ref(false)
const saving = ref(false)
const form = reactive({
  smtp_host: '',
  smtp_port: 25,
  smtp_from: '',
  smtp_username: '',
  smtp_password: '',
  smtp_use_tls: false,
  email_send_hour: 8,
})

async function loadSettings() {
  loading.value = true
  try {
    const res = await api.get('/settings')
    const data = res.data || res
    Object.assign(form, {
      smtp_host: data.smtp_host || '',
      smtp_port: data.smtp_port ?? 25,
      smtp_from: data.smtp_from || '',
      smtp_username: data.smtp_username || '',
      smtp_password: '',
      smtp_use_tls: !!data.smtp_use_tls,
      email_send_hour: data.email_send_hour ?? 8,
    })
  } catch (e) {
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    const payload = {
      smtp_host: form.smtp_host,
      smtp_port: form.smtp_port,
      smtp_from: form.smtp_from,
      smtp_username: form.smtp_username,
      smtp_use_tls: form.smtp_use_tls,
      email_send_hour: form.email_send_hour,
    }
    if (form.smtp_password) {
      payload.smtp_password = form.smtp_password
    }
    await api.put('/settings', payload)
    form.smtp_password = ''
    ElMessage.success('设置已保存')
  } catch (e) {
    const msg = e.response?.data?.detail || '保存失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.page { padding: 24px; max-width: 800px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
h2 { color: #E8572A; font-size: 22px; font-weight: 700; margin: 0; }
.hint { margin-left: 8px; color: #888; font-size: 13px; }
</style>
