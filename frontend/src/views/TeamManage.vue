<template>
  <div class="page">
    <el-page-header @back="$router.back()" :content="team ? team.name + ' — 成员管理' : '成员管理'" />

    <el-card class="card">
      <template #header>
        <div class="card-header">
          <span>成员列表</span>
          <div class="add-member">
            <el-input-number
              v-model="newUserId"
              :min="1"
              placeholder="用户 ID"
              controls-position="right"
              style="width: 140px"
            />
            <el-button type="primary" @click="addMember" :disabled="!newUserId">添加成员</el-button>
          </div>
        </div>
      </template>

      <el-table :data="members" v-loading="loading" style="width: 100%">
        <el-table-column label="用户名" prop="username" />
        <el-table-column label="邮箱" prop="email" />
        <el-table-column label="加入时间" prop="joined_at">
          <template #default="{ row }">
            {{ row.joined_at ? row.joined_at.slice(0, 10) : '—' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              @click="removeMember(row.user_id)"
              :disabled="team && team.leader_id === row.user_id"
            >移除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'

const route = useRoute()
const router = useRouter()
const teamId = computed(() => Number(route.params.id))

const team = ref(null)
const members = ref([])
const loading = ref(false)
const newUserId = ref(null)

async function loadTeam() {
  try {
    const res = await api.get(`/teams/${teamId.value}`)
    const data = res.data || res
    team.value = data
    members.value = data.members || []
  } catch (e) {
    ElMessage.error('加载团队信息失败')
  }
}

async function addMember() {
  if (!newUserId.value) return
  try {
    await api.post(`/teams/${teamId.value}/members`, { user_id: newUserId.value })
    newUserId.value = null
    await loadTeam()
    ElMessage.success('成员已添加')
  } catch (e) {
    const msg = e.response?.data?.detail || '添加失败'
    ElMessage.error(msg)
  }
}

async function removeMember(userId) {
  try {
    await ElMessageBox.confirm('确定要移除该成员吗？', '确认', { type: 'warning' })
  } catch {
    return
  }
  try {
    await api.delete(`/teams/${teamId.value}/members/${userId}`)
    await loadTeam()
    ElMessage.success('成员已移除')
  } catch (e) {
    const msg = e.response?.data?.detail || '移除失败'
    ElMessage.error(msg)
  }
}

onMounted(loadTeam)
</script>

<style scoped>
.page { padding: 24px; max-width: 900px; }
.card { margin-top: 24px; border-radius: 12px; border: 1px solid var(--border); }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.add-member { display: flex; gap: 8px; align-items: center; }
</style>
