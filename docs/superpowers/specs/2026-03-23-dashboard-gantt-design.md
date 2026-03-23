# Dashboard & Gantt Chart Design

**Date:** 2026-03-23
**Status:** Approved

## Overview

Add a personal dashboard, team dashboard, and Gantt chart to the existing todo application. All statistics are computed on the frontend from existing task API responses. Charts are rendered with ECharts via the `vue-echarts` wrapper.

## Scope

- **Personal Dashboard** (`/dashboard`): task status counts, overdue tasks, priority breakdown, completion trend
- **Team Dashboard** (`/teams/:id/dashboard`): same as personal dashboard plus team member workload
- **Gantt Chart** (`/gantt`): timeline view of tasks with personal/team view toggle

Out of scope: real-time updates, task dependency arrows, drag-to-reschedule.

## Data Model Changes

### Add `start_date` to Task

```python
# backend/models.py — Task class
start_date: Mapped[date | None] = mapped_column(Date)
```

- Optional field; existing tasks remain valid with `start_date = null`
- Gantt chart renders tasks without a start date as a single-day milestone at `due_date`
- Add `start_date` to `TaskCreate` and `TaskUpdate` schemas in `routers/tasks.py`
- Include `start_date` in the task response dict (alongside existing `due_date`)

No new API endpoints are needed. The existing task list endpoint (`GET /api/v1/tasks`) is used by all three new pages.

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

### Routes

```js
{ path: '/dashboard', component: Dashboard, meta: { requireAuth: true } }
{ path: '/teams/:id/dashboard', component: TeamDashboard, meta: { requireAuth: true } }
{ path: '/gantt', component: Gantt, meta: { requireAuth: true } }
```

Add sidebar navigation links for Dashboard and Gantt in `AppLayout.vue`.

### Composable: `useTaskStats.js`

Accepts a reactive array of tasks and returns computed properties:

- `statusCounts` — `{ pending, in_progress, done }`
- `overdueCount` — tasks where `due_date < today` and `status !== 'done'`
- `overdueTasks` — filtered task list for the overdue panel
- `priorityCounts` — `{ low, medium, high }`
- `completionTrend(days = 14)` — array of `{ date, count }` for tasks completed in last N days (uses `updated_at` as proxy for completion date)
- `memberWorkload(members)` — map of `userId → openTaskCount` (team dashboard only)

## Page Designs

### Personal Dashboard (`Dashboard.vue`)

Layout (top to bottom):

1. **Stat cards row** — 4 cards: 待处理 / 进行中 / 已完成 / 已逾期, colored orange / blue / green / red
2. **Charts row** — two equal-width panels:
   - Left: priority breakdown donut chart (ECharts pie with `radius: ['40%', '70%']`)
   - Right: 14-day completion trend line chart (ECharts line)
3. **Overdue task list** — el-table or simple list; shown only when `overdueCount > 0`

Data source: `GET /api/v1/tasks` (fetches all tasks assigned to or created by the current user).

### Team Dashboard (`TeamDashboard.vue`)

Identical to personal dashboard with two additions:

- Page title shows the team name
- **Member workload panel** at the bottom: horizontal bar chart (ECharts bar, `layout: 'horizontal'`), one bar per team member showing their open task count
- Data source: `GET /api/v1/tasks?team_id=:id`

### Gantt Chart (`Gantt.vue`)

**Toolbar:**
- Toggle: 我的任务 / 团队视图
- Team selector (el-select, visible only in team view)
- Time range selector: 本周 / 本月 / 自定义 (el-date-picker range)

**Chart:**
- Rendered with ECharts custom series (standard approach for Gantt in ECharts)
- Y-axis: task names
- X-axis: date range
- Bar color by status: blue=in_progress, orange=pending, green=done, red=overdue
- Today marker: vertical line at current date
- Tasks without `start_date`: rendered as a 1-day bar at `due_date`
- Tooltip on hover: task title, assignee, status, start→due date

**Data source:**
- Personal view: `GET /api/v1/tasks` (my tasks)
- Team view: `GET /api/v1/tasks?team_id=:id`
- Filter to tasks that have a `due_date` (tasks with neither date are omitted)

## Task Form Changes

Add an optional **开始日期** date picker to the task create/edit form (after the existing **截止日期** field). Validate that `start_date <= due_date` when both are set (frontend validation only).

## Error Handling

- If the tasks API call fails, show an el-alert error banner; charts render empty
- Team dashboard redirects to `/dashboard` if the user is not a member of the requested team (reuse existing permission enforcement on the backend)

## Testing

- Unit tests for `useTaskStats.js` composable (pure functions, no DOM needed)
- Backend: add `start_date` to existing task create/update test cases in `tests/test_tasks.py`
