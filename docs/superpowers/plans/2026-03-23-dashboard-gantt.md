# Dashboard & Gantt Chart Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a personal dashboard, team dashboard, and Gantt chart page to the todo app, with frontend-computed statistics using ECharts.

**Architecture:** Backend gains a `start_date` field on Task and a `team_id` filter on the task list endpoint. The frontend fetches all tasks via a pagination-aware helper, computes stats in a shared composable, and renders charts with ECharts custom/pie/line/bar series.

**Tech Stack:** FastAPI + SQLAlchemy + SQLite (backend), Vue 3 + Element Plus + ECharts + vue-echarts + Vitest (frontend)

---

## File Map

**Backend — modified:**
- `backend/models.py` — add `start_date` field to `Task`
- `backend/database.py` — add `migrate_tables()` called on startup to add the column to existing DBs
- `backend/main.py` — call `migrate_tables()` in startup
- `backend/routers/tasks.py` — add `start_date` to `TaskCreatePayload`, `TaskUpdatePayload`, `serialize_task`; add `team_id` query param to `list_tasks` with 403 check
- `backend/tests/test_tasks.py` — new tests for `start_date` field and `team_id` filter

**Frontend — new files:**
- `frontend/src/api/tasks.js` — `fetchAllTasks(params)` paginated helper
- `frontend/src/composables/useTaskStats.js` — stat computation composable
- `frontend/src/views/Dashboard.vue` — personal dashboard page
- `frontend/src/views/TeamDashboard.vue` — team dashboard page
- `frontend/src/views/Gantt.vue` — Gantt chart page
- `frontend/src/composables/__tests__/useTaskStats.test.js` — Vitest unit tests

**Frontend — modified:**
- `frontend/package.json` — add `echarts`, `vue-echarts`; add `vitest`, `@vue/test-utils` as dev deps
- `frontend/vite.config.js` — add vitest config block
- `frontend/src/router/index.js` — add 3 new routes
- `frontend/src/components/AppLayout.vue` — add Dashboard + Gantt nav links
- `frontend/src/views/MyTasks.vue` — add `start_date` field to create dialog
- `frontend/src/views/TeamTasks.vue` — add `start_date` field to create dialog
- `frontend/src/views/TaskDetail.vue` — display `start_date` in descriptions

---

## Task 1: Add `start_date` to backend Task model

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/database.py`
- Modify: `backend/main.py`
- Modify: `backend/routers/tasks.py`
- Test: `backend/tests/test_tasks.py`

- [ ] **Step 1: Write the failing test for start_date in create and response**

Add to `backend/tests/test_tasks.py`:

```python
def test_create_task_with_start_date(client, auth_headers):
    response = client.post(
        "/api/v1/tasks",
        json={"title": "有开始日期", "start_date": "2026-03-20", "due_date": "2026-03-30"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["start_date"] == "2026-03-20"
    assert data["due_date"] == "2026-03-30"


def test_update_task_start_date(client, auth_headers):
    created = client.post("/api/v1/tasks", json={"title": "任务"}, headers=auth_headers)
    task_id = created.json()["data"]["id"]

    response = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"start_date": "2026-04-01"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["start_date"] == "2026-04-01"


def test_start_date_defaults_to_null(client, auth_headers):
    created = client.post("/api/v1/tasks", json={"title": "无日期任务"}, headers=auth_headers)
    assert created.status_code == 200
    assert created.json()["data"]["start_date"] is None
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && python3 -m pytest tests/test_tasks.py::test_create_task_with_start_date tests/test_tasks.py::test_update_task_start_date tests/test_tasks.py::test_start_date_defaults_to_null -v
```

Expected: FAIL (KeyError or field missing)

- [ ] **Step 3: Add `start_date` to the Task model**

In `backend/models.py`, after the `due_date` line (line 55):

```python
start_date: Mapped[date | None] = mapped_column(Date)
```

- [ ] **Step 4: Add startup migration to `database.py`**

Add this function after `create_tables()` in `backend/database.py`:

```python
def migrate_tables():
    """Add columns that were added after initial table creation."""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN start_date DATE"))
            conn.commit()
        except Exception:
            pass  # Column already exists — safe to ignore
```

- [ ] **Step 5: Call `migrate_tables()` in startup**

In `backend/main.py`, after `create_tables()` on startup:

```python
from database import create_tables, migrate_tables

@app.on_event("startup")
def startup():
    create_tables()
    migrate_tables()
    # ... rest unchanged
```

- [ ] **Step 6: Add `start_date` to payloads and serializer in `routers/tasks.py`**

Add to `TaskCreatePayload` (after `due_date`):
```python
start_date: date | None = None
```

Add to `TaskUpdatePayload` (after `due_date`):
```python
start_date: date | None = None
```

In `serialize_task`, add after the `due_date` line:
```python
"start_date": task.start_date.isoformat() if task.start_date else None,
```

In `create_task`, add `start_date=payload.start_date` to the `Task(...)` constructor (after `due_date=payload.due_date`).

In `update_task`, add handling after the `due_date` block:
```python
if "start_date" in payload.model_fields_set:
    task.start_date = payload.start_date
```

- [ ] **Step 7: Run tests to confirm they pass**

```bash
cd backend && python3 -m pytest tests/test_tasks.py::test_create_task_with_start_date tests/test_tasks.py::test_update_task_start_date tests/test_tasks.py::test_start_date_defaults_to_null -v
```

Expected: PASS

- [ ] **Step 8: Run full test suite to check no regressions**

```bash
cd backend && python3 -m pytest tests/ -v
```

Expected: all pass

- [ ] **Step 9: Commit**

```bash
git add backend/models.py backend/database.py backend/main.py backend/routers/tasks.py backend/tests/test_tasks.py
git commit -m "feat: add start_date field to Task model with startup migration"
```

---

## Task 2: Add `team_id` filter to task list endpoint

**Files:**
- Modify: `backend/routers/tasks.py`
- Test: `backend/tests/test_tasks.py`

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_tasks.py`:

```python
def test_list_tasks_filter_by_team_id(client, auth_headers, normal_user, db):
    """Team member can filter tasks by team_id and gets only that team's tasks."""
    other = create_user(db, "leader_t2", "leader_t2@test.com", "pass")
    team = create_team(db, "过滤测试组", other.id)
    db.add(TeamMember(team_id=team.id, user_id=normal_user.id))
    db.commit()

    # Create a team task
    client.post(
        "/api/v1/tasks",
        json={"title": "团队任务A", "team_id": team.id},
        headers=auth_headers,
    )
    # Create a personal task (no team)
    client.post("/api/v1/tasks", json={"title": "个人任务"}, headers=auth_headers)

    response = client.get(f"/api/v1/tasks?team_id={team.id}", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert all(t["team_id"] == team.id for t in items)
    assert any(t["title"] == "团队任务A" for t in items)


def test_list_tasks_team_id_filter_rejects_non_member(client, db):
    """Non-member gets 403 when filtering by a team they don't belong to."""
    outsider = create_user(db, "outsider_t2", "outsider_t2@test.com", "pass")
    leader = create_user(db, "leader_t3", "leader_t3@test.com", "pass")
    team = create_team(db, "私密组", leader.id)

    response = client.get(
        f"/api/v1/tasks?team_id={team.id}",
        headers=make_headers(outsider.id),
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && python3 -m pytest tests/test_tasks.py::test_list_tasks_filter_by_team_id tests/test_tasks.py::test_list_tasks_team_id_filter_rejects_non_member -v
```

Expected: FAIL

- [ ] **Step 3: Add `team_id` query parameter to `list_tasks`**

In `backend/routers/tasks.py`, add `TeamMember` to imports from models:
```python
from models import Task, TaskLabel, Team, TeamMember, User
```

Add `team_id: int | None = None` to the `list_tasks` signature (after `due_date`).

Add the filter logic after the existing filters block (after the `if due_date` block):

```python
if team_id is not None:
    # Permission check: admin or team member only
    if not current_user.is_admin and not is_team_member(db, team_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该团队任务")
    query = query.filter(Task.team_id == team_id)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend && python3 -m pytest tests/test_tasks.py::test_list_tasks_filter_by_team_id tests/test_tasks.py::test_list_tasks_team_id_filter_rejects_non_member -v
```

Expected: PASS

- [ ] **Step 5: Run full test suite**

```bash
cd backend && python3 -m pytest tests/ -v
```

Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add backend/routers/tasks.py backend/tests/test_tasks.py
git commit -m "feat: add team_id filter with permission check to task list endpoint"
```

---

## Task 3: Set up frontend test tooling and install chart dependencies

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/vite.config.js`

- [ ] **Step 1: Install echarts, vue-echarts, and vitest**

```bash
cd frontend && npm install echarts vue-echarts
cd frontend && npm install -D vitest @vue/test-utils jsdom
```

- [ ] **Step 2: Add vitest config to `vite.config.js`**

Replace the contents of `frontend/vite.config.js` with:

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true }
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
  }
})
```

- [ ] **Step 3: Add test script to `package.json`**

In `frontend/package.json`, add to `"scripts"`:
```json
"test": "vitest run"
```

- [ ] **Step 4: Verify vitest works with a smoke test**

Create `frontend/src/composables/__tests__/smoke.test.js`:
```js
import { describe, it, expect } from 'vitest'
describe('smoke', () => {
  it('works', () => expect(1 + 1).toBe(2))
})
```

Run:
```bash
cd frontend && npm test
```

Expected: PASS (1 test passing)

- [ ] **Step 5: Delete the smoke test file**

```bash
rm frontend/src/composables/__tests__/smoke.test.js
```

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/vite.config.js frontend/package-lock.json
git commit -m "chore: add echarts, vue-echarts, and vitest to frontend"
```

---

## Task 4: Build `useTaskStats` composable (TDD)

**Files:**
- Create: `frontend/src/composables/useTaskStats.js`
- Create: `frontend/src/composables/__tests__/useTaskStats.test.js`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/composables/__tests__/useTaskStats.test.js`:

```js
import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useTaskStats } from '../useTaskStats.js'

const TODAY = '2026-03-23'

function makeTasks(overrides = []) {
  return overrides
}

describe('useTaskStats', () => {
  it('statusCounts counts tasks by status', () => {
    const tasks = ref([
      { status: 'pending', due_date: null, priority: 'low', updated_at: '2026-03-20T10:00:00' },
      { status: 'in_progress', due_date: null, priority: 'medium', updated_at: '2026-03-21T10:00:00' },
      { status: 'in_progress', due_date: null, priority: 'high', updated_at: '2026-03-22T10:00:00' },
      { status: 'done', due_date: null, priority: 'low', updated_at: '2026-03-23T10:00:00' },
    ])
    const { statusCounts } = useTaskStats(tasks)
    expect(statusCounts.value).toEqual({ pending: 1, in_progress: 2, done: 1 })
  })

  it('overdueCount counts tasks past due_date that are not done', () => {
    const tasks = ref([
      { status: 'pending', due_date: '2026-03-20', priority: 'medium', updated_at: '' },   // overdue
      { status: 'in_progress', due_date: '2026-03-22', priority: 'medium', updated_at: '' }, // overdue
      { status: 'done', due_date: '2026-03-20', priority: 'medium', updated_at: '' },       // done, not overdue
      { status: 'pending', due_date: '2026-03-30', priority: 'medium', updated_at: '' },    // future
      { status: 'pending', due_date: null, priority: 'medium', updated_at: '' },            // no date
    ])
    const { overdueCount, overdueTasks } = useTaskStats(tasks, TODAY)
    expect(overdueCount.value).toBe(2)
    expect(overdueTasks.value).toHaveLength(2)
  })

  it('priorityCounts counts tasks by priority', () => {
    const tasks = ref([
      { status: 'pending', due_date: null, priority: 'high', updated_at: '' },
      { status: 'pending', due_date: null, priority: 'high', updated_at: '' },
      { status: 'pending', due_date: null, priority: 'medium', updated_at: '' },
      { status: 'done', due_date: null, priority: 'low', updated_at: '' },
    ])
    const { priorityCounts } = useTaskStats(tasks)
    expect(priorityCounts.value).toEqual({ low: 1, medium: 1, high: 2 })
  })

  it('completionTrend returns counts for done tasks grouped by updated_at date', () => {
    const tasks = ref([
      { status: 'done', due_date: null, priority: 'low', updated_at: '2026-03-22T09:00:00' },
      { status: 'done', due_date: null, priority: 'low', updated_at: '2026-03-22T14:00:00' },
      { status: 'done', due_date: null, priority: 'low', updated_at: '2026-03-23T10:00:00' },
      { status: 'pending', due_date: null, priority: 'low', updated_at: '2026-03-22T10:00:00' }, // not done, excluded
    ])
    const { completionTrend } = useTaskStats(tasks, TODAY)
    const trend = completionTrend(3) // last 3 days: 03-21, 03-22, 03-23
    expect(trend).toHaveLength(3)
    const march22 = trend.find(d => d.date === '2026-03-22')
    const march23 = trend.find(d => d.date === '2026-03-23')
    const march21 = trend.find(d => d.date === '2026-03-21')
    expect(march22.count).toBe(2)
    expect(march23.count).toBe(1)
    expect(march21.count).toBe(0)
  })

  it('memberWorkload maps userId to open task count', () => {
    const tasks = ref([
      { status: 'pending', assigned_to: 1, due_date: null, priority: 'low', updated_at: '' },
      { status: 'in_progress', assigned_to: 1, due_date: null, priority: 'low', updated_at: '' },
      { status: 'done', assigned_to: 1, due_date: null, priority: 'low', updated_at: '' }, // done, excluded
      { status: 'pending', assigned_to: 2, due_date: null, priority: 'low', updated_at: '' },
      { status: 'pending', assigned_to: null, due_date: null, priority: 'low', updated_at: '' }, // unassigned
    ])
    const { memberWorkload } = useTaskStats(tasks)
    const members = [{ user_id: 1 }, { user_id: 2 }, { user_id: 3 }]
    const workload = memberWorkload(members)
    expect(workload[1]).toBe(2)
    expect(workload[2]).toBe(1)
    expect(workload[3]).toBe(0)
  })
})
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd frontend && npm test
```

Expected: FAIL (module not found)

- [ ] **Step 3: Create the composable**

Create `frontend/src/composables/useTaskStats.js`:

```js
import { computed } from 'vue'

/**
 * @param {import('vue').Ref<Array>} tasks - reactive array of task objects
 * @param {string} today - ISO date string 'YYYY-MM-DD', defaults to current date
 */
export function useTaskStats(tasks, today = new Date().toISOString().slice(0, 10)) {
  const statusCounts = computed(() => {
    const counts = { pending: 0, in_progress: 0, done: 0 }
    for (const t of tasks.value) {
      if (t.status in counts) counts[t.status]++
    }
    return counts
  })

  const overdueTasks = computed(() =>
    tasks.value.filter(t => t.due_date && t.due_date < today && t.status !== 'done')
  )

  const overdueCount = computed(() => overdueTasks.value.length)

  const priorityCounts = computed(() => {
    const counts = { low: 0, medium: 0, high: 0 }
    for (const t of tasks.value) {
      if (t.priority in counts) counts[t.priority]++
    }
    return counts
  })

  function completionTrend(days = 14) {
    // Build a map of date → count for done tasks completed in last `days` days
    const doneTasks = tasks.value.filter(t => t.status === 'done' && t.updated_at)
    const countsByDate = {}
    for (const t of doneTasks) {
      const d = t.updated_at.slice(0, 10)
      countsByDate[d] = (countsByDate[d] || 0) + 1
    }

    // Generate the last `days` dates ending at today
    const result = []
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date(today)
      d.setDate(d.getDate() - i)
      const dateStr = d.toISOString().slice(0, 10)
      result.push({ date: dateStr, count: countsByDate[dateStr] || 0 })
    }
    return result
  }

  function memberWorkload(members) {
    const openTasks = tasks.value.filter(t => t.status !== 'done')
    const map = {}
    for (const m of members) map[m.user_id] = 0
    for (const t of openTasks) {
      if (t.assigned_to !== null && t.assigned_to in map) {
        map[t.assigned_to]++
      }
    }
    return map
  }

  return { statusCounts, overdueCount, overdueTasks, priorityCounts, completionTrend, memberWorkload }
}
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd frontend && npm test
```

Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/composables/useTaskStats.js frontend/src/composables/__tests__/useTaskStats.test.js
git commit -m "feat: add useTaskStats composable with unit tests"
```

---

## Task 5: Build `fetchAllTasks` helper

**Files:**
- Create: `frontend/src/api/tasks.js`

- [ ] **Step 1: Write the test**

Add to `frontend/src/composables/__tests__/useTaskStats.test.js` (or create a new file `frontend/src/api/__tests__/tasks.test.js`):

Create `frontend/src/api/__tests__/tasks.test.js`:

```js
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock the api module
vi.mock('../index.js', () => ({
  default: { get: vi.fn() }
}))

import api from '../index.js'
import { fetchAllTasks } from '../tasks.js'

beforeEach(() => vi.clearAllMocks())

describe('fetchAllTasks', () => {
  it('returns all items from a single page response', async () => {
    api.get.mockResolvedValueOnce({
      code: 0, message: 'ok',
      data: { total: 2, page: 1, size: 100, items: [{ id: 1 }, { id: 2 }] }
    })
    const result = await fetchAllTasks()
    expect(result).toHaveLength(2)
    expect(api.get).toHaveBeenCalledTimes(1)
  })

  it('loops through multiple pages until exhausted', async () => {
    // First page: full (100 items), second page: partial (3 items)
    const page1 = Array.from({ length: 100 }, (_, i) => ({ id: i + 1 }))
    const page2 = [{ id: 101 }, { id: 102 }, { id: 103 }]
    api.get
      .mockResolvedValueOnce({ code: 0, message: 'ok', data: { total: 103, page: 1, size: 100, items: page1 } })
      .mockResolvedValueOnce({ code: 0, message: 'ok', data: { total: 103, page: 2, size: 100, items: page2 } })
    const result = await fetchAllTasks()
    expect(result).toHaveLength(103)
    expect(api.get).toHaveBeenCalledTimes(2)
  })

  it('passes params to each request', async () => {
    api.get.mockResolvedValueOnce({
      code: 0, message: 'ok',
      data: { total: 1, page: 1, size: 100, items: [{ id: 1 }] }
    })
    await fetchAllTasks({ team_id: 5 })
    expect(api.get).toHaveBeenCalledWith('/tasks', { params: { team_id: 5, page: 1, size: 100 } })
  })
})
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd frontend && npm test
```

Expected: FAIL (module not found)

- [ ] **Step 3: Create `frontend/src/api/tasks.js`**

```js
import api from './index.js'

/**
 * Fetch all tasks by looping through pages.
 * @param {Object} params - query params (e.g. { team_id: 5 })
 * @returns {Promise<Array>} flat array of all task objects
 */
export async function fetchAllTasks(params = {}) {
  const allTasks = []
  let page = 1
  const size = 100
  while (true) {
    const res = await api.get('/tasks', { params: { ...params, page, size } })
    allTasks.push(...res.data.items)
    if (res.data.items.length < size) break
    page++
  }
  return allTasks
}
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd frontend && npm test
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/tasks.js frontend/src/api/__tests__/tasks.test.js
git commit -m "feat: add fetchAllTasks paginated helper with tests"
```

---

## Task 6: Build the Personal Dashboard page

**Files:**
- Create: `frontend/src/views/Dashboard.vue`

- [ ] **Step 1: Create `frontend/src/views/Dashboard.vue`**

```vue
<template>
  <div class="page">
    <div class="header">
      <h2>我的仪表盘</h2>
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon style="margin-bottom:16px" />

    <!-- Stat cards -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">待处理</div>
        <div class="stat-value pending">{{ stats.statusCounts.value.pending }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">进行中</div>
        <div class="stat-value in-progress">{{ stats.statusCounts.value.in_progress }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">已完成</div>
        <div class="stat-value done">{{ stats.statusCounts.value.done }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">已逾期</div>
        <div class="stat-value overdue">{{ stats.overdueCount.value }}</div>
      </div>
    </div>

    <!-- Charts row -->
    <div class="chart-row">
      <el-card class="chart-card">
        <template #header>优先级分布</template>
        <v-chart :option="priorityChartOption" style="height:200px" autoresize />
      </el-card>
      <el-card class="chart-card">
        <template #header>近 14 天完成趋势</template>
        <v-chart :option="trendChartOption" style="height:200px" autoresize />
      </el-card>
    </div>

    <!-- Overdue list -->
    <el-card v-if="stats.overdueCount.value > 0" style="margin-top:16px">
      <template #header>
        <span style="color:#f56c6c">逾期任务 ({{ stats.overdueCount.value }})</span>
      </template>
      <el-table :data="stats.overdueTasks.value" size="small">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="due_date" label="截止日期" width="120" />
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="{ high: 'danger', medium: 'warning', low: 'info' }[row.priority]" size="small">
              {{ { high: '高', medium: '中', low: '低' }[row.priority] }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import { fetchAllTasks } from '../api/tasks.js'
import { useTaskStats } from '../composables/useTaskStats.js'

use([CanvasRenderer, PieChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const tasks = ref([])
const error = ref(null)
const stats = useTaskStats(tasks)

const priorityChartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: [
      { value: stats.priorityCounts.value.high, name: '高', itemStyle: { color: '#f56c6c' } },
      { value: stats.priorityCounts.value.medium, name: '中', itemStyle: { color: '#e6a23c' } },
      { value: stats.priorityCounts.value.low, name: '低', itemStyle: { color: '#909399' } },
    ],
  }],
}))

const trendChartOption = computed(() => {
  const trend = stats.completionTrend(14)
  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 10, right: 10, bottom: 30, left: 40 },
    xAxis: { type: 'category', data: trend.map(d => d.date.slice(5)) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'line', data: trend.map(d => d.count), smooth: true, areaStyle: {} }],
  }
})

async function load() {
  try {
    tasks.value = await fetchAllTasks()
  } catch (e) {
    error.value = '加载任务数据失败'
  }
}

onMounted(load)
</script>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}
.stat-label { font-size: 13px; color: #909399; margin-bottom: 8px; }
.stat-value { font-size: 32px; font-weight: 700; }
.stat-value.pending { color: #e6a23c; }
.stat-value.in-progress { color: #409eff; }
.stat-value.done { color: #67c23a; }
.stat-value.overdue { color: #f56c6c; }
.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.chart-card { min-height: 260px; }
</style>
```

- [ ] **Step 2: Verify the page renders without errors**

Start the dev servers and navigate to `/dashboard`. Check browser console for errors.

```bash
# Terminal 1
cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2
cd frontend && npm run dev
```

Open http://localhost:5173/dashboard — should show stat cards and chart placeholders.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "feat: add personal dashboard page with ECharts stat cards and charts"
```

---

## Task 7: Build the Team Dashboard page

**Files:**
- Create: `frontend/src/views/TeamDashboard.vue`

- [ ] **Step 1: Create `frontend/src/views/TeamDashboard.vue`**

```vue
<template>
  <div class="page">
    <div class="header">
      <h2>{{ teamName }} — 团队仪表盘</h2>
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon style="margin-bottom:16px" />

    <!-- Stat cards (same as Dashboard) -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">待处理</div>
        <div class="stat-value pending">{{ stats.statusCounts.value.pending }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">进行中</div>
        <div class="stat-value in-progress">{{ stats.statusCounts.value.in_progress }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">已完成</div>
        <div class="stat-value done">{{ stats.statusCounts.value.done }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">已逾期</div>
        <div class="stat-value overdue">{{ stats.overdueCount.value }}</div>
      </div>
    </div>

    <!-- Charts row -->
    <div class="chart-row">
      <el-card class="chart-card">
        <template #header>优先级分布</template>
        <v-chart :option="priorityChartOption" style="height:200px" autoresize />
      </el-card>
      <el-card class="chart-card">
        <template #header>近 14 天完成趋势</template>
        <v-chart :option="trendChartOption" style="height:200px" autoresize />
      </el-card>
    </div>

    <!-- Overdue list -->
    <el-card v-if="stats.overdueCount.value > 0" style="margin-top:16px">
      <template #header>
        <span style="color:#f56c6c">逾期任务 ({{ stats.overdueCount.value }})</span>
      </template>
      <el-table :data="stats.overdueTasks.value" size="small">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="due_date" label="截止日期" width="120" />
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="{ high: 'danger', medium: 'warning', low: 'info' }[row.priority]" size="small">
              {{ { high: '高', medium: '中', low: '低' }[row.priority] }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Member workload -->
    <el-card v-if="members.length > 0" style="margin-top:16px">
      <template #header>成员工作量（未完成任务数）</template>
      <v-chart :option="workloadChartOption" :style="`height:${Math.max(members.length * 36 + 40, 120)}px`" autoresize />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, LineChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import api from '../api/index.js'
import { fetchAllTasks } from '../api/tasks.js'
import { useTaskStats } from '../composables/useTaskStats.js'

use([CanvasRenderer, PieChart, LineChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const route = useRoute()
const router = useRouter()
const teamId = computed(() => Number(route.params.id))
const teamName = ref('团队')
const members = ref([])
const tasks = ref([])
const error = ref(null)
const stats = useTaskStats(tasks)

const priorityChartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: [
      { value: stats.priorityCounts.value.high, name: '高', itemStyle: { color: '#f56c6c' } },
      { value: stats.priorityCounts.value.medium, name: '中', itemStyle: { color: '#e6a23c' } },
      { value: stats.priorityCounts.value.low, name: '低', itemStyle: { color: '#909399' } },
    ],
  }],
}))

const trendChartOption = computed(() => {
  const trend = stats.completionTrend(14)
  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 10, right: 10, bottom: 30, left: 40 },
    xAxis: { type: 'category', data: trend.map(d => d.date.slice(5)) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'line', data: trend.map(d => d.count), smooth: true, areaStyle: {} }],
  }
})

const workloadChartOption = computed(() => {
  const workload = stats.memberWorkload(members.value)
  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 10, right: 30, bottom: 10, left: 80, containLabel: true },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: { type: 'category', data: members.value.map(m => m.username) },
    series: [{
      type: 'bar',
      data: members.value.map(m => workload[m.user_id] || 0),
      itemStyle: { color: '#409eff' },
    }],
  }
})

async function load() {
  try {
    const teamRes = await api.get(`/teams/${teamId.value}`)
    teamName.value = teamRes.name || teamRes.data?.name || '团队'
    members.value = teamRes.members || teamRes.data?.members || []
    tasks.value = await fetchAllTasks({ team_id: teamId.value })
  } catch (e) {
    if (e.response?.status === 403) {
      router.push('/dashboard')
    } else {
      error.value = '加载团队数据失败'
    }
  }
}

onMounted(load)
</script>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}
.stat-label { font-size: 13px; color: #909399; margin-bottom: 8px; }
.stat-value { font-size: 32px; font-weight: 700; }
.stat-value.pending { color: #e6a23c; }
.stat-value.in-progress { color: #409eff; }
.stat-value.done { color: #67c23a; }
.stat-value.overdue { color: #f56c6c; }
.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.chart-card { min-height: 260px; }
</style>
```

- [ ] **Step 2: Verify the page renders**

Navigate to `/team/1/dashboard` (replace 1 with a real team id). Should show team name, stat cards, and member workload chart.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/TeamDashboard.vue
git commit -m "feat: add team dashboard page"
```

---

## Task 8: Build the Gantt chart page

**Files:**
- Create: `frontend/src/views/Gantt.vue`

- [ ] **Step 1: Create `frontend/src/views/Gantt.vue`**

```vue
<template>
  <div class="page">
    <div class="header">
      <h2>甘特图</h2>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <el-radio-group v-model="viewMode" @change="load">
        <el-radio-button value="personal">我的任务</el-radio-button>
        <el-radio-button value="team">团队视图</el-radio-button>
      </el-radio-group>

      <el-select
        v-if="viewMode === 'team'"
        v-model="selectedTeamId"
        placeholder="选择团队"
        style="width:160px"
        @change="load"
      >
        <el-option v-for="t in teams" :key="t.id" :value="t.id" :label="t.name" />
      </el-select>

      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始"
        end-placeholder="结束"
        value-format="YYYY-MM-DD"
        :shortcuts="dateShortcuts"
        style="width:260px"
        @change="load"
      />
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon style="margin-bottom:16px" />

    <el-card v-if="ganttTasks.length > 0">
      <v-chart :option="ganttOption" :style="`height:${Math.max(ganttTasks.length * 40 + 60, 200)}px`" autoresize />
    </el-card>
    <el-empty v-else-if="!loading" description="暂无可显示的任务（需要设置截止日期）" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { CustomChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, DataZoomComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import api from '../api/index.js'
import { fetchAllTasks } from '../api/tasks.js'

use([CanvasRenderer, CustomChart, TooltipComponent, GridComponent, DataZoomComponent])

const viewMode = ref('personal')
const selectedTeamId = ref(null)
const teams = ref([])
const allTasks = ref([])
const error = ref(null)
const loading = ref(false)
const today = new Date().toISOString().slice(0, 10)

// Default to current month
const monthStart = today.slice(0, 8) + '01'
const monthEnd = new Date(today.slice(0, 4), Number(today.slice(5, 7)), 0).toISOString().slice(0, 10)
const dateRange = ref([monthStart, monthEnd])

const dateShortcuts = [
  {
    text: '本周',
    value: () => {
      const now = new Date()
      const day = now.getDay() || 7
      const start = new Date(now); start.setDate(now.getDate() - day + 1)
      const end = new Date(start); end.setDate(start.getDate() + 6)
      return [start.toISOString().slice(0, 10), end.toISOString().slice(0, 10)]
    }
  },
  {
    text: '本月',
    value: () => [monthStart, monthEnd]
  }
]

// Filter to tasks that have a due_date and fall within the date range
const ganttTasks = computed(() => {
  const [rangeStart, rangeEnd] = dateRange.value || [null, null]
  return allTasks.value.filter(t => {
    if (!t.due_date) return false
    if (rangeEnd && t.due_date > rangeEnd) return false
    const taskStart = t.start_date || t.due_date
    if (rangeStart && taskStart < rangeStart) return false
    return true
  })
})

function taskStatus(t) {
  if (t.status === 'done') return 'done'
  if (t.due_date && t.due_date < today) return 'overdue'
  return t.status
}

const statusColors = {
  pending: '#e6a23c',
  in_progress: '#409eff',
  done: '#67c23a',
  overdue: '#f56c6c',
}

const ganttOption = computed(() => {
  const tasks = ganttTasks.value
  const [rangeStart, rangeEnd] = dateRange.value || [monthStart, monthEnd]

  return {
    tooltip: {
      formatter: (params) => {
        const t = tasks[params.dataIndex]
        return `<b>${t.title}</b><br/>状态: ${t.status}<br/>开始: ${t.start_date || '—'}<br/>截止: ${t.due_date}`
      }
    },
    grid: { top: 10, right: 20, bottom: 60, left: 160, containLabel: false },
    xAxis: {
      type: 'time',
      min: rangeStart,
      max: rangeEnd,
      axisLabel: { formatter: (val) => new Date(val).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) },
    },
    yAxis: {
      type: 'category',
      data: tasks.map(t => t.title.length > 12 ? t.title.slice(0, 12) + '…' : t.title),
      axisLabel: { fontSize: 12 },
    },
    dataZoom: [{ type: 'slider', bottom: 10 }],
    series: [{
      type: 'custom',
      renderItem(params, api) {
        const t = tasks[params.dataIndex]
        const start = t.start_date || t.due_date
        const end = t.due_date
        const x1 = api.coord([start, params.dataIndex])[0]
        const x2 = api.coord([end, params.dataIndex])[0]
        const y = api.coord([start, params.dataIndex])[1]
        const barHeight = 18
        const color = statusColors[taskStatus(t)]
        const width = Math.max(x2 - x1, 4)
        return {
          type: 'rect',
          shape: { x: x1, y: y - barHeight / 2, width, height: barHeight },
          style: { fill: color, borderRadius: 3 },
        }
      },
      data: tasks.map((_, i) => i),
      encode: { x: [0, 1], y: 2 },
    }],
  }
})

async function load() {
  loading.value = true
  error.value = null
  try {
    if (viewMode.value === 'team' && !selectedTeamId.value) {
      allTasks.value = []
      return
    }
    const params = viewMode.value === 'team' ? { team_id: selectedTeamId.value } : {}
    allTasks.value = await fetchAllTasks(params)
  } catch (e) {
    error.value = '加载任务失败'
    allTasks.value = []
  } finally {
    loading.value = false
  }
}

async function loadTeams() {
  try {
    const res = await api.get('/teams')
    teams.value = res.data || res || []
  } catch { teams.value = [] }
}

onMounted(async () => {
  await loadTeams()
  await load()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
</style>
```

- [ ] **Step 2: Verify the page renders**

Navigate to `/gantt`. Should show toolbar and either a chart or empty state.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/Gantt.vue
git commit -m "feat: add Gantt chart page with ECharts custom series"
```

---

## Task 9: Wire up routes and sidebar navigation

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/components/AppLayout.vue`

- [ ] **Step 1: Add routes to `frontend/src/router/index.js`**

Add the three new routes after the `/my-tasks` route:

```js
{ path: '/dashboard', component: () => import('../views/Dashboard.vue') },
{ path: '/team/:id/dashboard', component: () => import('../views/TeamDashboard.vue') },
{ path: '/gantt', component: () => import('../views/Gantt.vue') },
```

- [ ] **Step 2: Add nav links to `AppLayout.vue`**

In `frontend/src/components/AppLayout.vue`:

1. Add `PieChart` and `Calendar` to the icon imports. The script setup already imports from `@element-plus/icons-vue` — check the existing import line at the top and add `DataAnalysis, Calendar` to it.

2. In the template, add two nav items after the `/my-tasks` link (and before the 团队 section):

```html
<router-link to="/dashboard" class="nav-item" active-class="active">
  <el-icon><DataAnalysis /></el-icon>
  <span>仪表盘</span>
</router-link>
<router-link to="/gantt" class="nav-item" active-class="active">
  <el-icon><Calendar /></el-icon>
  <span>甘特图</span>
</router-link>
```

- [ ] **Step 3: Verify nav and routing works**

Open the app. Sidebar should show 仪表盘 and 甘特图 links. Clicking them should navigate correctly.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/router/index.js frontend/src/components/AppLayout.vue
git commit -m "feat: add dashboard and gantt routes and sidebar navigation links"
```

---

## Task 10: Add `start_date` to task create forms and detail view

**Files:**
- Modify: `frontend/src/views/MyTasks.vue`
- Modify: `frontend/src/views/TeamTasks.vue`
- Modify: `frontend/src/views/TaskDetail.vue`

- [ ] **Step 1: Add `start_date` field to `MyTasks.vue` create dialog**

In `frontend/src/views/MyTasks.vue`:

1. Add `start_date: null` to the `newTask` reactive object.

2. In the create dialog form, add a new `el-form-item` after the 截止日期 field:

```html
<el-form-item label="开始日期">
  <el-date-picker v-model="newTask.start_date" type="date" value-format="YYYY-MM-DD" />
</el-form-item>
```

3. In the `createTask` function, include `start_date: newTask.start_date` in the POST body.

4. In the reset logic (after create), reset `newTask.start_date = null`.

- [ ] **Step 2: Add `start_date` field to `TeamTasks.vue` create dialog**

Same changes as Step 1, applied to `frontend/src/views/TeamTasks.vue`.

- [ ] **Step 3: Display `start_date` in `TaskDetail.vue`**

In `frontend/src/views/TaskDetail.vue`, add a new `el-descriptions-item` after the 截止日期 row:

```html
<el-descriptions-item label="开始日期">{{ task.start_date || '—' }}</el-descriptions-item>
```

- [ ] **Step 4: Verify form works end-to-end**

1. Create a task with both start_date and due_date.
2. Open the task detail — should show both dates.
3. Navigate to `/gantt` — the task should appear as a bar spanning start→due.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/MyTasks.vue frontend/src/views/TeamTasks.vue frontend/src/views/TaskDetail.vue
git commit -m "feat: add start_date field to task create forms and detail view"
```

---

## Final Verification

- [ ] **Run full backend test suite**

```bash
cd backend && python3 -m pytest tests/ -v
```

Expected: all pass

- [ ] **Run frontend tests**

```bash
cd frontend && npm test
```

Expected: all pass

- [ ] **Manual smoke test**

1. Log in as a normal user
2. Create a task with start_date + due_date
3. Visit `/dashboard` — stat cards and charts render
4. Visit `/gantt` — task appears as a colored bar
5. If in a team, visit `/team/:id/dashboard` — team stats + member workload chart render
6. Visit `/gantt`, switch to team view, select team — team tasks appear
