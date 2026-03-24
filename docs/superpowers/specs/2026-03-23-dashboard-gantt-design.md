# Dashboard & Gantt Chart Design

**Date:** 2026-03-23
**Status:** Approved

## Overview

Add a personal dashboard, team dashboard, and Gantt chart to the existing todo application. All statistics are computed on the frontend from task API responses. Charts are rendered with ECharts via the `vue-echarts` wrapper.

## Scope

- **Personal Dashboard** (`/dashboard`): task status counts, overdue tasks, priority breakdown, completion trend
- **Team Dashboard** (`/team/:id/dashboard`): same as personal dashboard plus team member workload
- **Gantt Chart** (`/gantt`): timeline view of tasks with personal/team view toggle

Out of scope: real-time updates, task dependency arrows, drag-to-reschedule.

## Backend Changes

### 1. Add `start_date` to Task model

```python
# backend/models.py — Task class
start_date: Mapped[date | None] = mapped_column(Date)
```

- Optional field; existing tasks remain valid with `start_date = null`
- Add `start_date` to `TaskCreate` and `TaskUpdate` schemas in `routers/tasks.py`
- Include `start_date` in the task response dict (alongside existing `due_date`)

**Migration:** The project has no Alembic setup. Add the column via a startup check in `database.py` (similar to how WAL mode is enabled), or run manually:

```sql
ALTER TABLE tasks ADD COLUMN start_date DATE;
```

### 2. Add `team_id` filter to task list endpoint

The existing `GET /api/v1/tasks` endpoint does not support `team_id` filtering. Add it as an optional query parameter to `list_tasks` in `routers/tasks.py`:

```python
team_id: int | None = None
```

When provided, filter results to tasks where `task.team_id == team_id`. Explicitly check that the current user is a member of that team (or is an admin); raise HTTP 403 if not. Do not rely on the base query silently returning empty results, as that would mislead the client.

### 3. Fetch all tasks (pagination)

The task list endpoint is paginated (default `size=20`, response shape: `{ total, page, size, items }`). Dashboard and Gantt pages must fetch all relevant tasks, not just the first page. Implement a helper in `src/api/tasks.js`:

```js
// fetchAllTasks(params) — loops GET /api/v1/tasks until all pages are fetched
// Returns flat array of all task objects
async function fetchAllTasks(params = {}) {
  const allTasks = []
  let page = 1
  const size = 100
  while (true) {
    const { data } = await api.get('/tasks', { params: { ...params, page, size } })
    allTasks.push(...data.data.items)
    if (data.data.items.length < size) break
    page++
  }
  return allTasks
}
```

## Frontend Architecture

### Dependencies

```
echarts
vue-echarts
```

### New Files

| File | Purpose |
|------|---------|
| `src/views/Dashboard.vue` | Personal dashboard page |
| `src/views/TeamDashboard.vue` | Team dashboard page |
| `src/views/Gantt.vue` | Gantt chart page |
| `src/composables/useTaskStats.js` | Shared stat computation (status counts, overdue, priority, trend) |
| `src/api/tasks.js` | `fetchAllTasks(params)` — paginated fetch helper that loops until all tasks are retrieved |

### Routes

```js
{ path: '/dashboard', component: Dashboard }
{ path: '/team/:id/dashboard', component: TeamDashboard }
{ path: '/gantt', component: Gantt }
```

Routes follow the existing convention: no `meta` key needed; the router guard blocks unauthenticated access to all routes that lack `meta.public`.

Add sidebar navigation links for Dashboard and Gantt in `AppLayout.vue`.

### Composable: `useTaskStats.js`

Accepts a reactive array of tasks and returns computed properties:

- `statusCounts` — `{ pending, in_progress, done }`
- `overdueCount` — tasks where `due_date < today` and `status !== 'done'`
- `overdueTasks` — filtered task list for the overdue panel
- `priorityCounts` — `{ low, medium, high }`
- `completionTrend(days = 14)` — array of `{ date, count }` for the last N days. Filter to tasks where `status === 'done'` first, then group by date. Truncate `updated_at` to a date string before grouping (`updated_at.slice(0, 10)`). Note: `updated_at` is a proxy — it reflects the last edit, not necessarily the status transition. For small datasets this is acceptable.
- `memberWorkload(members)` — map of `userId → openTaskCount` (tasks where `status !== 'done'`), team dashboard only

## Page Designs

### Personal Dashboard (`Dashboard.vue`)

Layout (top to bottom):

1. **Stat cards row** — 4 cards: 待处理 / 进行中 / 已完成 / 已逾期, colored orange / blue / green / red
2. **Charts row** — two equal-width panels:
   - Left: priority breakdown donut chart (ECharts pie with `radius: ['40%', '70%']`)
   - Right: 14-day completion trend line chart (ECharts line)
3. **Overdue task list** — el-table or simple list; shown only when `overdueCount > 0`

Data source: `fetchAllTasks()` with no filters. For non-admin users the backend already scopes results to tasks the user created or is assigned to. Admin users will see all tasks system-wide on their personal dashboard — this is acceptable.

### Team Dashboard (`TeamDashboard.vue`)

Identical to personal dashboard with two additions:

- Page title shows the team name
- **Member workload panel** at the bottom: horizontal bar chart (ECharts bar with `orient: 'horizontal'`), one bar per team member showing their open task count

Data sources:
- Tasks: `fetchAllTasks({ team_id: route.params.id })`
- Member list: `GET /api/v1/teams/:id` — response includes a `members` array with user info; fetch this on page mount to populate `memberWorkload`.

### Gantt Chart (`Gantt.vue`)

**Toolbar:**
- Toggle: 我的任务 / 团队视图
- Team selector (el-select, visible only in team view)
- Time range selector: 本周 / 本月 / 自定义 (el-date-picker range)

**Chart:**
- Rendered with ECharts custom series (standard approach for Gantt in ECharts)
- Y-axis: task names
- X-axis: date range
- Bar color by status: blue=in_progress, orange=pending, green=done, red=overdue (overdue = `due_date < today && status !== 'done'`)
- Today marker: vertical line at current date
- Tasks without `start_date`: rendered as a 1-day bar at `due_date`
- Tasks without `due_date`: omitted from the chart
- Tooltip on hover: task title, assignee, status, start→due date

**Data sources:**
- Personal view: `fetchAllTasks()`
- Team view: `fetchAllTasks({ team_id: selectedTeamId })`
- Team selector options: `GET /api/v1/teams` — fetches the list of teams the current user belongs to; populate the el-select on page mount

## Task Form Changes

Add an optional **开始日期** date picker to the task create/edit form (after the existing **截止日期** field). Frontend validation: if both dates are set, `start_date` must be ≤ `due_date`.

## Error Handling

- If the tasks API call fails, show an el-alert error banner; charts render empty
- Team dashboard redirects to `/dashboard` if the user is not a member of the requested team (backend returns 403; frontend catches and redirects)

## Testing

- Unit tests for `useTaskStats.js` composable (pure functions, no DOM needed): test each computed property with a fixed task array
- Backend: add `start_date` field to existing task create/update test cases in `tests/test_tasks.py`; add a test for the new `team_id` query parameter on `list_tasks`
