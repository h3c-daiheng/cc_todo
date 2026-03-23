# UI Redesign — 现代简约风格

## 概述

将前端全部页面从当前的橙色暖调风格改造为靛蓝紫现代简约风格。新增全局侧边栏导航，替代当前基于路由的页面跳转方式。登录/注册页使用左右分栏布局。

## 设计决策

### D1: 配色系统

采用靛蓝紫（`#6366F1`）为主色，搭配深色侧边栏（`#1E1B4B`）和浅灰页面背景（`#F8FAFC`）。

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--primary` | `#6366F1` | 按钮、链接、高亮 |
| `--primary-hover` | `#4F46E5` | 按钮悬停 |
| `--primary-light` | `#EEF2FF` | 浅色标签背景 |
| `--primary-border` | `#C7D2FE` | 浅色标签边框 |
| `--sidebar-bg` | `#1E1B4B` | 侧边栏背景 |
| `--sidebar-active` | `rgba(99,102,241,0.3)` | 侧边栏当前项 |
| `--page-bg` | `#F8FAFC` | 页面背景 |
| `--card-bg` | `#FFFFFF` | 卡片背景 |
| `--card-inner-bg` | `#FAFAFA` | 卡片内部元素背景 |
| `--border` | `#E2E8F0` | 通用边框 |
| `--text-primary` | `#1E1B4B` | 主要文字 |
| `--text-secondary` | `#64748B` | 次要文字 |
| `--text-muted` | `#94A3B8` | 辅助文字 |
| `--success` | `#10B981` | 已完成状态 |
| `--warning` | `#F59E0B` | 中优先级 |
| `--danger` | `#EF4444` | 高优先级 |

### D2: 全局布局 — 侧边栏

新增 `AppLayout.vue` 组件作为已登录页面的外壳，包含：
- 左侧固定侧边栏（200px 宽，深色背景 `#1E1B4B`）
- 右侧内容区（`flex: 1`，背景 `#F8FAFC`）

侧边栏内容：
- 顶部：品牌名「待办」，白色，18px，font-weight 800
- 导航菜单：图标 + 文字，当前页高亮（`--sidebar-active` 背景，圆角 8px）
  - 我的任务 → `/my-tasks`
  - 各团队 → `/team/:id`（动态从 API 获取团队列表）
- 底部区域（管理员可见）：
  - 用户管理 → `/admin/users`
  - 系统设置 → `/admin/settings`

**管理员判断：** 当前 `useUserStore` 的 `login()` 只存储 `username`，未持久化 `is_admin`。需要扩展 user store：在 login 成功后从 JWT payload 或 `/auth/me` 接口获取 `is_admin` 并存入 store，供 AppLayout 判断管理员菜单可见性。这是本次改动对 Pinia store 的唯一修改。

登录/注册页面不使用 AppLayout，直接全屏渲染。

**路由结构不变**，仅在 `App.vue` 中根据是否登录及是否为 public 路由决定是否包裹 AppLayout。

### D3: 登录 / 注册页

左右分栏布局：
- **左侧（flex: 1）：** 渐变背景 `linear-gradient(135deg, #1E1B4B, #4338CA)`，居中显示品牌名（36px 白色粗体）和标语（14px 半透明白色）
- **右侧（flex: 1）：** 白色背景，居中表单（max-width 360px）
  - 标题：22px，`--text-primary`，font-weight 700
  - 副标题：13px，`--text-muted`
  - 输入框：背景 `#F8FAFC`，边框 `#E2E8F0`，圆角 10px
  - 按钮：背景 `--primary`，圆角 10px，font-weight 600
  - 链接：`--primary` 色

注册页与登录页结构一致，仅表单字段和标题不同。

### D4: 看板页面（MyTasks / TeamTasks）

**页面头部：**
- 标题：20px，`--text-primary`，font-weight 700
- 副标题：12px，`--text-muted`（任务总数）
- 右侧：筛选按钮（白底描边）+ 新建按钮（`--primary` 实色）

**看板列：**
- 白底卡片容器，圆角 12px，边框 `--border`
- 列头：圆点状态指示色（灰=待处理，紫=进行中，绿=已完成）+ 标题 + 计数标签

**任务卡片：**
- 背景 `--card-inner-bg`，圆角 10px
- 左边框 3px 色带：高优先级=`--danger`，中=`--warning`，进行中=`--primary`，已完成=`--success`，默认=`#CBD5E1`
- 微阴影 `0 1px 3px rgba(0,0,0,0.04)`
- 悬停阴影加深 `0 4px 12px rgba(0,0,0,0.08)`
- 标题 13px，font-weight 600
- 底部：优先级标签（圆角药丸形）+ 截止日期

### D5: 任务详情页

- 页面背景 `--page-bg`
- 内容区白底卡片，max-width 900px，圆角 12px，边框 `--border`
- 标题区：大号标题 + 状态/优先级彩色药丸标签
- 描述区：正常文字排版
- 评论区：`--card-inner-bg` 背景，8px 圆角
  - 作者名：`--primary` 色，13px，font-weight 600
  - 时间戳：`--text-muted`，12px
- 附件区：统一列表样式，链接 `--primary` 色

### D6: 团队管理页

- 白底卡片包裹成员列表
- 成员项：用户名 + 角色标签（药丸形）
- 添加成员：保留现有 `el-input-number`（用户 ID 输入），仅更新样式
- 移除按钮：`--danger` 色

### D7: 管理后台页面

- **用户管理：** 表格行白底，斑马纹 `#FAFBFC`，角色/状态用彩色标签
- **系统设置：** 表单项白底卡片，开关/输入统一样式

### D8: 全局样式基础

**CSS 变量：** 在 `App.vue` 的 `<style>`（非 scoped）中定义所有 CSS 变量（`:root { ... }`）。现有 `src/style.css` 是 Vite 脚手架遗留文件（未被导入），直接删除。不新建 `variables.css` 文件，保持简单。

**`#app` 布局：** 移除 `style.css` 中的旧 `#app` 宽度限制（`width: 1126px`），改为全宽布局以适配侧边栏。

**圆角规范：**
- 大容器（列、卡片）：12px
- 中元素（输入框、按钮）：10px
- 小元素（标签、badge）：圆角药丸 `9999px` 或 4-8px

**间距规范（8px 倍数）：**
- 页面 padding：24px
- 组件间距：16px
- 卡片内 padding：12px
- 紧凑间距：8px

**过渡动画：**
- 按钮/卡片悬停：`transition: all 0.2s ease`
- 阴影变化、背景色变化

## 不变的部分

- 后端 API 无任何改动
- Vue Router 路由路径不变
- Pinia store 仅扩展 `is_admin` 持久化（见 D2），其余不变
- 功能逻辑不变（看板拖拽、筛选、评论、附件等）
- Element Plus 组件库继续使用（按钮、表单、对话框、表格等）

## 新增文件

| 文件 | 职责 |
|------|------|
| `src/components/AppLayout.vue` | 全局布局：侧边栏 + 内容区 |

## 修改文件

| 文件 | 改动内容 |
|------|---------|
| `src/App.vue` | 定义 CSS 变量（`:root`），根据路由条件包裹 AppLayout，替换旧背景色 |
| `src/style.css` | 删除（Vite 脚手架遗留文件，未被导入，不再需要） |
| `src/stores/user.js` | 扩展 login action 持久化 `is_admin`，供 AppLayout 使用 |
| `src/views/Login.vue` | 左右分栏布局 + 新配色 |
| `src/views/Register.vue` | 左右分栏布局 + 新配色 |
| `src/views/MyTasks.vue` | 新看板样式 + 工具栏 |
| `src/views/TeamTasks.vue` | 同 MyTasks 看板样式 |
| `src/views/TaskDetail.vue` | 新卡片布局 + 评论/附件样式 |
| `src/views/TeamManage.vue` | 新卡片/列表样式 |
| `src/views/admin/UserManage.vue` | 新表格/标签样式 |
| `src/views/admin/SystemSettings.vue` | 新表单卡片样式 |
| `src/components/TaskBoard.vue` | 新列样式 + 列头圆点 |
| `src/components/TaskCard.vue` | 新卡片样式 + 左边框色带 |
| `src/components/CommentList.vue` | 新评论气泡样式 |
| `src/components/FileUpload.vue` | 统一链接/列表样式 |
