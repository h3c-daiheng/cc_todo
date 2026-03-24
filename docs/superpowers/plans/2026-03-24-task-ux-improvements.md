# 任务管理系统用户体验优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 添加快速创建、搜索和视图切换功能，提升团队协作场景下的任务管理体验

**Architecture:** 在现有 Vue 3 + Element Plus 架构上渐进式增强，新增三个独立组件（QuickTaskInput、TaskList、TaskCalendar），修改 MyTasks 和 TeamTasks 页面集成这些功能。所有功能使用现有后端 API，无需后端改动。

**Tech Stack:** Vue 3, Element Plus, Vitest

---

## 文件结构

**新增组件**:
- `frontend/src/components/QuickTaskInput.vue` - 快速创建任务输入框
- `frontend/src/components/TaskList.vue` - 列表视图组件
- `frontend/src/components/TaskCalendar.vue` - 日历视图组件

**修改文件**:
- `frontend/src/views/MyTasks.vue` - 集成快速创建、搜索、视图切换
- `frontend/src/views/TeamTasks.vue` - 同上

**测试文件**:
- `frontend/src/components/__tests__/QuickTaskInput.spec.js`
- `frontend/src/components/__tests__/TaskList.spec.js`
- `frontend/src/components/__tests__/TaskCalendar.spec.js`

---

## Task 1: QuickTaskInput 组件

**Files:**
- Create: `frontend/src/components/QuickTaskInput.vue`
- Create: `frontend/src/components/__tests__/QuickTaskInput.spec.js`

- [ ] **Step 1: 编写测试 - 基本渲染**

```javascript
// frontend/src/components/__tests__/QuickTaskInput.spec.js
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import QuickTaskInput from '../QuickTaskInput.vue'

describe('QuickTaskInput', () => {
  it('renders input with placeholder', () => {
    const wrapper = mount(QuickTaskInput)
    const input = wrapper.find('input')
    expect(input.exists()).toBe(true)
    expect(input.attributes('placeholder')).toBe('快速添加任务...')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd frontend && npm test -- QuickTaskInput.spec.js
```

预期: FAIL - QuickTaskInput.vue 不存在

- [ ] **Step 3: 实现组件基本结构**

```vue
<!-- frontend/src/components/QuickTaskInput.vue -->
<template>
  <div class="quick-input">
    <input
      v-model="title"
      type="text"
      placeholder="快速添加任务..."
      @keyup.enter="handleCreate"
      class="input-field"
    />
    <el-button @click="showDetail = true" text>详细</el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  teamId: { type: Number, default: null }
})
const emit = defineEmits(['created'])

const title = ref('')
const showDetail = ref(false)

function handleCreate() {
  if (!title.value.trim()) return
  emit('created', { title: title.value.trim() })
  title.value = ''
}
</script>

<style scoped>
.quick-input {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 16px;
}
.input-field {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
}
.input-field:focus {
  outline: none;
  border-color: var(--primary);
}
</style>
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd frontend && npm test -- QuickTaskInput.spec.js
```

预期: PASS

- [ ] **Step 5: 添加回车创建测试**

```javascript
// 在 QuickTaskInput.spec.js 中添加
it('emits created event on enter', async () => {
  const wrapper = mount(QuickTaskInput)
  const input = wrapper.find('input')

  await input.setValue('新任务')
  await input.trigger('keyup.enter')

  expect(wrapper.emitted('created')).toBeTruthy()
  expect(wrapper.emitted('created')[0][0]).toEqual({ title: '新任务' })
  expect(input.element.value).toBe('')
})
```

- [ ] **Step 6: 运行测试确认通过**

```bash
cd frontend && npm test -- QuickTaskInput.spec.js
```

预期: PASS

- [ ] **Step 7: 提交**

```bash
git add frontend/src/components/QuickTaskInput.vue frontend/src/components/__tests__/QuickTaskInput.spec.js
git commit -m "feat: add QuickTaskInput component with tests

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: TaskList 组件

**Files:**
- Create: `frontend/src/components/TaskList.vue`
- Create: `frontend/src/components/__tests__/TaskList.spec.js`

- [ ] **Step 1: 编写测试 - 渲染任务列表**

```javascript
// frontend/src/components/__tests__/TaskList.spec.js
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskList from '../TaskList.vue'
import ElementPlus from 'element-plus'

describe('TaskList', () => {
  const tasks = [
    { id: 1, title: '任务1', status: 'pending', priority: 'high', due_date: '2026-03-25', assigned_to: 1 },
    { id: 2, title: '任务2', status: 'in_progress', priority: 'medium', due_date: null, assigned_to: null }
  ]

  it('renders table with tasks', () => {
    const wrapper = mount(TaskList, {
      props: { tasks },
      global: { plugins: [ElementPlus] }
    })
    expect(wrapper.text()).toContain('任务1')
    expect(wrapper.text()).toContain('任务2')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd frontend && npm test -- TaskList.spec.js
```

预期: FAIL - TaskList.vue 不存在

- [ ] **Step 3: 实现列表视图组件**

```vue
<!-- frontend/src/components/TaskList.vue -->
<template>
  <el-table :data="tasks" @row-click="handleRowClick" class="task-table">
    <el-table-column prop="title" label="标题" min-width="200" />
    <el-table-column label="状态" width="140">
      <template #default="{ row }">
        <el-select v-model="row.status" @change="handleStatusChange(row)" size="small">
          <el-option value="pending" label="待处理" />
          <el-option value="in_progress" label="进行中" />
          <el-option value="done" label="已完成" />
        </el-select>
      </template>
    </el-table-column>
    <el-table-column label="优先级" width="100">
      <template #default="{ row }">
        <el-tag :type="priorityType(row.priority)" size="small">
          {{ priorityLabel(row.priority) }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="assigned_to" label="负责人" width="100">
      <template #default="{ row }">
        {{ row.assigned_to ? `用户 #${row.assigned_to}` : '未分配' }}
      </template>
    </el-table-column>
    <el-table-column prop="due_date" label="截止日期" width="120">
      <template #default="{ row }">
        {{ row.due_date || '—' }}
      </template>
    </el-table-column>
    <el-table-column label="操作" width="100">
      <template #default="{ row }">
        <el-button @click.stop="handleRowClick(row)" size="small" text>查看</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
const props = defineProps({ tasks: Array })
const emit = defineEmits(['task-click', 'update-status'])

const priorityMap = {
  high: { type: 'danger', label: '高' },
  medium: { type: 'warning', label: '中' },
  low: { type: 'info', label: '低' }
}

function priorityType(p) { return priorityMap[p]?.type || 'info' }
function priorityLabel(p) { return priorityMap[p]?.label || p }
function handleRowClick(row) { emit('task-click', row) }
function handleStatusChange(row) { emit('update-status', { taskId: row.id, status: row.status }) }
</script>

<style scoped>
.task-table { width: 100%; }
</style>
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd frontend && npm test -- TaskList.spec.js
```

预期: PASS

- [ ] **Step 5: 添加状态更新测试**

```javascript
// 在 TaskList.spec.js 中添加
it('emits update-status on status change', async () => {
  const wrapper = mount(TaskList, {
    props: { tasks },
    global: { plugins: [ElementPlus] }
  })

  const select = wrapper.findAllComponents({ name: 'ElSelect' })[0]
  await select.setValue('done')

  expect(wrapper.emitted('update-status')).toBeTruthy()
  expect(wrapper.emitted('update-status')[0][0]).toEqual({ taskId: 1, status: 'done' })
})
```

- [ ] **Step 6: 运行测试确认通过**

```bash
cd frontend && npm test -- TaskList.spec.js
```

预期: PASS

- [ ] **Step 7: 提交**

```bash
git add frontend/src/components/TaskList.vue frontend/src/components/__tests__/TaskList.spec.js
git commit -m "feat: add TaskList component with tests

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: TaskCalendar 组件

**Files:**
- Create: `frontend/src/components/TaskCalendar.vue`
- Create: `frontend/src/components/__tests__/TaskCalendar.spec.js`

- [ ] **Step 1: 编写测试 - 渲染日历**

```javascript
// frontend/src/components/__tests__/TaskCalendar.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskCalendar from '../TaskCalendar.vue'

describe('TaskCalendar', () => {
  it('renders calendar grid', () => {
    const wrapper = mount(TaskCalendar, {
      props: { tasks: [] }
    })
    expect(wrapper.find('.calendar').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd frontend && npm test -- TaskCalendar.spec.js
```

预期: FAIL - TaskCalendar.vue 不存在

- [ ] **Step 3: 实现日历视图组件**

```vue
<!-- frontend/src/components/TaskCalendar.vue -->
<template>
  <div class="calendar-container">
    <div class="calendar-header">
      <el-button @click="prevMonth" icon="ArrowLeft" circle />
      <span class="month-label">{{ currentMonth }}</span>
      <el-button @click="nextMonth" icon="ArrowRight" circle />
    </div>
    <div class="calendar">
      <div class="weekdays">
        <div v-for="day in ['日', '一', '二', '三', '四', '五', '六']" :key="day" class="weekday">{{ day }}</div>
      </div>
      <div class="days">
        <div v-for="day in calendarDays" :key="day.date" class="day-cell" :class="{ 'other-month': !day.isCurrentMonth }">
          <div class="day-number">{{ day.day }}</div>
          <div class="day-tasks">
            <div v-for="task in day.tasks" :key="task.id" class="task-item" @click="$emit('task-click', task)">
              {{ task.title }}
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="unscheduled">
      <h4>未安排</h4>
      <div v-for="task in unscheduledTasks" :key="task.id" class="task-item" @click="$emit('task-click', task)">
        {{ task.title }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ tasks: Array })
const emit = defineEmits(['task-click'])

const currentDate = ref(new Date())

const currentMonth = computed(() => {
  const y = currentDate.value.getFullYear()
  const m = currentDate.value.getMonth() + 1
  return `${y}年${m}月`
})

const calendarDays = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startDay = firstDay.getDay()
  const days = []

  for (let i = 0; i < startDay; i++) {
    const d = new Date(year, month, -startDay + i + 1)
    days.push({ date: d.toISOString().split('T')[0], day: d.getDate(), isCurrentMonth: false, tasks: [] })
  }

  for (let i = 1; i <= lastDay.getDate(); i++) {
    const d = new Date(year, month, i)
    const dateStr = d.toISOString().split('T')[0]
    const dayTasks = props.tasks.filter(t => t.due_date === dateStr)
    days.push({ date: dateStr, day: i, isCurrentMonth: true, tasks: dayTasks })
  }

  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    const d = new Date(year, month + 1, i)
    days.push({ date: d.toISOString().split('T')[0], day: d.getDate(), isCurrentMonth: false, tasks: [] })
  }

  return days
})

const unscheduledTasks = computed(() => props.tasks.filter(t => !t.due_date))

function prevMonth() { currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1) }
function nextMonth() { currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1) }
</script>

<style scoped>
.calendar-container { display: flex; gap: 16px; }
.calendar { flex: 1; }
.calendar-header { display: flex; justify-content: center; align-items: center; gap: 16px; margin-bottom: 16px; }
.month-label { font-size: 16px; font-weight: 600; }
.weekdays { display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; background: var(--border); }
.weekday { background: var(--card-bg); padding: 8px; text-align: center; font-size: 12px; font-weight: 600; }
.days { display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; background: var(--border); }
.day-cell { background: var(--card-bg); min-height: 80px; padding: 4px; }
.day-cell.other-month { opacity: 0.3; }
.day-number { font-size: 12px; font-weight: 600; margin-bottom: 4px; }
.task-item { font-size: 11px; padding: 2px 4px; background: var(--primary-light); border-radius: 4px; margin-bottom: 2px; cursor: pointer; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.task-item:hover { background: var(--primary); color: white; }
.unscheduled { width: 200px; }
.unscheduled h4 { margin-bottom: 8px; }
</style>
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd frontend && npm test -- TaskCalendar.spec.js
```

预期: PASS

- [ ] **Step 5: 添加任务分组测试**

```javascript
// 在 TaskCalendar.spec.js 中添加
it('groups tasks by due date', () => {
  const tasks = [
    { id: 1, title: '任务1', due_date: '2026-03-25' },
    { id: 2, title: '任务2', due_date: '2026-03-25' },
    { id: 3, title: '任务3', due_date: null }
  ]
  const wrapper = mount(TaskCalendar, { props: { tasks } })
  expect(wrapper.text()).toContain('未安排')
  expect(wrapper.text()).toContain('任务3')
})
```

- [ ] **Step 6: 运行测试确认通过**

```bash
cd frontend && npm test -- TaskCalendar.spec.js
```

预期: PASS

- [ ] **Step 7: 提交**

```bash
git add frontend/src/components/TaskCalendar.vue frontend/src/components/__tests__/TaskCalendar.spec.js
git commit -m "feat: add TaskCalendar component with tests

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: 集成到 MyTasks 页面

**Files:**
- Modify: `frontend/src/views/MyTasks.vue`

- [ ] **Step 1: 添加搜索和视图切换 UI**

在 `MyTasks.vue` 的 `<div class="filters">` 后添加:

```vue
<div class="toolbar">
  <el-input v-model="searchQuery" placeholder="搜索任务..." clearable style="width:200px" />
  <el-radio-group v-model="currentView" size="small">
    <el-radio-button value="board">看板</el-radio-button>
    <el-radio-button value="list">列表</el-radio-button>
    <el-radio-button value="calendar">日历</el-radio-button>
  </el-radio-group>
</div>
```

在 `<script setup>` 中添加:

```javascript
import { ref, computed, watch, onMounted } from 'vue'
import QuickTaskInput from '../components/QuickTaskInput.vue'
import TaskList from '../components/TaskList.vue'
import TaskCalendar from '../components/TaskCalendar.vue'

const searchQuery = ref('')
const currentView = ref(localStorage.getItem('taskView') || 'board')

const filteredTasks = computed(() => {
  let result = tasks.value
  if (filter.priority) result = result.filter(t => t.priority === filter.priority)
  if (filter.status) result = result.filter(t => t.status === filter.status)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(t =>
      t.title.toLowerCase().includes(q) ||
      (t.description && t.description.toLowerCase().includes(q))
    )
  }
  return result
})

watch(currentView, (v) => localStorage.setItem('taskView', v))
```

- [ ] **Step 2: 添加快速创建组件**

在 `<div class="filters">` 和 `<div class="toolbar">` 之间添加:

```vue
<quick-task-input @created="handleQuickCreate" />
```

在 `<script setup>` 中添加:

```javascript
async function handleQuickCreate(data) {
  try {
    await api.post('/tasks', { title: data.title, priority: 'medium' })
    await loadTasks()
    ElMessage.success('任务已创建')
  } catch (e) {
    ElMessage.error('创建失败')
  }
}
```

- [ ] **Step 3: 替换看板为视图切换**

将原来的 `<task-board>` 替换为:

```vue
<task-board v-if="currentView === 'board'" :tasks="filteredTasks" @update-status="updateStatus" @task-click="goDetail" />
<task-list v-else-if="currentView === 'list'" :tasks="filteredTasks" @update-status="updateStatus" @task-click="goDetail" />
<task-calendar v-else :tasks="filteredTasks" @task-click="goDetail" />
```

- [ ] **Step 4: 添加样式**

在 `<style scoped>` 中添加:

```css
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
```

- [ ] **Step 5: 测试功能**

```bash
cd frontend && npm run dev
```

手动测试:
1. 访问 /my-tasks
2. 测试快速创建（输入标题按回车）
3. 测试搜索（输入关键词）
4. 测试视图切换（点击看板/列表/日历按钮）

- [ ] **Step 6: 提交**

```bash
git add frontend/src/views/MyTasks.vue
git commit -m "feat: integrate quick create, search, and view switching in MyTasks

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: 集成到 TeamTasks 页面

**Files:**
- Modify: `frontend/src/views/TeamTasks.vue`

- [ ] **Step 1: 读取 TeamTasks.vue 当前实现**

```bash
cat frontend/src/views/TeamTasks.vue
```

- [ ] **Step 2: 应用与 MyTasks 相同的改动**

参考 Task 4 的步骤，在 TeamTasks.vue 中:
1. 添加搜索和视图切换 UI
2. 添加 QuickTaskInput 组件（传递 `team-id` prop）
3. 实现 `handleQuickCreate` 时包含 `team_id: route.params.id`
4. 替换看板为视图切换
5. 添加样式

关键差异:

```javascript
async function handleQuickCreate(data) {
  try {
    await api.post('/tasks', {
      title: data.title,
      priority: 'medium',
      team_id: parseInt(route.params.id)
    })
    await loadTasks()
    ElMessage.success('任务已创建')
  } catch (e) {
    ElMessage.error('创建失败')
  }
}
```

- [ ] **Step 3: 测试功能**

```bash
cd frontend && npm run dev
```

手动测试:
1. 访问 /team/:id
2. 测试快速创建（确认 team_id 正确传递）
3. 测试搜索和视图切换

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/TeamTasks.vue
git commit -m "feat: integrate quick create, search, and view switching in TeamTasks

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: 端到端测试

**Files:**
- Test: 所有功能

- [ ] **Step 1: 运行所有单元测试**

```bash
cd frontend && npm test
```

预期: 所有测试通过

- [ ] **Step 2: 启动开发服务器**

```bash
cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
cd frontend && npm run dev
```

- [ ] **Step 3: 手动测试完整流程**

测试清单:
- [ ] MyTasks: 快速创建任务
- [ ] MyTasks: 搜索任务（标题和描述）
- [ ] MyTasks: 切换到列表视图，修改状态
- [ ] MyTasks: 切换到日历视图，点击任务
- [ ] MyTasks: 刷新页面，视图偏好保持
- [ ] TeamTasks: 快速创建任务（确认 team_id）
- [ ] TeamTasks: 搜索和视图切换
- [ ] 筛选器和搜索组合使用

- [ ] **Step 4: 修复发现的问题**

如果测试中发现问题，修复后重新测试

- [ ] **Step 5: 最终提交**

```bash
git add -A
git commit -m "test: verify all UX improvements work end-to-end

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 完成标准

- [ ] 所有单元测试通过
- [ ] 快速创建功能正常（MyTasks 和 TeamTasks）
- [ ] 搜索功能正常（标题和描述）
- [ ] 三种视图切换正常（看板、列表、日历）
- [ ] 视图偏好保存在 localStorage
- [ ] 代码已提交到 git
