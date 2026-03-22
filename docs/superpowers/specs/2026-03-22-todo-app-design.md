# 待办应用设计文档

**日期：** 2026-03-22
**版本：** 1.0

---

## 1. 项目概述

开发一个前后端分离的待办应用，支持个人任务管理和团队协作，部署于公司局域网内。

### 目标用户

- 个人用户：管理自己的任务清单
- 团队成员：协作完成团队任务
- 团队负责人：统筹团队任务进度
- 系统管理员：管理用户账号和系统配置

---

## 2. 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端框架 | Python + FastAPI |
| ORM | SQLAlchemy |
| 数据库 | SQLite |
| 定时任务 | APScheduler |
| 后端服务器 | Uvicorn |
| 前端框架 | Vue 3 + Vite |
| UI 组件库 | Element Plus |
| 前端状态管理 | Pinia |
| 认证方式 | JWT Token（有效期 8 小时） |

**部署方式：** 单台服务器，前端打包后由 Nginx 反向代理托管，后端运行在 Uvicorn 进程中。

---

## 3. 目录结构

```
todo-app/
├── backend/
│   ├── main.py           # 程序入口，注册路由、启动服务
│   ├── database.py       # 数据库连接与 Session 管理
│   ├── models.py         # SQLAlchemy 数据库模型
│   ├── schemas.py        # Pydantic 数据校验模型
│   ├── dependencies.py   # 公共依赖（当前用户获取、权限校验）
│   ├── routers/
│   │   ├── auth.py       # 登录、Token 刷新
│   │   ├── users.py      # 用户管理（管理员）
│   │   ├── tasks.py      # 任务 CRUD
│   │   ├── teams.py      # 团队管理
│   │   ├── comments.py   # 评论
│   │   ├── attachments.py# 附件上传下载
│   │   └── settings.py   # 系统配置（SMTP 等）
│   ├── services/
│   │   ├── email.py      # 邮件发送逻辑
│   │   └── auth.py       # 密码哈希、Token 生成验证
│   └── scheduler.py      # APScheduler 定时任务配置
│
└── frontend/
    ├── src/
    │   ├── views/
    │   │   ├── Login.vue         # 登录页
    │   │   ├── MyTasks.vue       # 我的任务
    │   │   ├── TeamTasks.vue     # 团队任务
    │   │   ├── TaskDetail.vue    # 任务详情
    │   │   ├── TeamManage.vue    # 团队管理
    │   │   └── admin/
    │   │       ├── UserManage.vue   # 用户管理
    │   │       └── SystemSettings.vue # 系统设置
    │   ├── components/
    │   │   ├── TaskCard.vue      # 任务卡片
    │   │   ├── TaskBoard.vue     # 看板（拖拽）
    │   │   ├── CommentList.vue   # 评论列表
    │   │   └── FileUpload.vue    # 附件上传
    │   ├── api/
    │   │   └── index.js          # 统一 API 请求封装（axios）
    │   ├── stores/
    │   │   ├── user.js           # 当前用户状态
    │   │   └── task.js           # 任务状态
    │   └── router/
    │       └── index.js          # 前端路由（页面跳转规则）
    └── package.json
```

---

## 4. 数据库设计

### users（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| username | TEXT UNIQUE | 用户名，登录用 |
| password_hash | TEXT | bcrypt 加密密码 |
| email | TEXT | 邮箱，用于接收提醒 |
| is_admin | BOOLEAN | 是否系统管理员 |
| email_notify | BOOLEAN | 是否开启每日邮件提醒，默认 true |
| is_active | BOOLEAN | 账号是否启用，默认 true |
| created_at | DATETIME | 创建时间 |

### teams（团队表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| name | TEXT | 团队名称 |
| created_by | INTEGER FK | 创建人（即团队负责人） |
| created_at | DATETIME | 创建时间 |

### team_members（团队成员表）

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | INTEGER FK | 用户 ID |
| team_id | INTEGER FK | 团队 ID |
| joined_at | DATETIME | 加入时间 |

### tasks（任务表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| title | TEXT | 任务标题 |
| description | TEXT | 详细描述 |
| status | TEXT | 状态：pending / in_progress / done |
| priority | TEXT | 优先级：low / medium / high |
| due_date | DATE | 截止日期 |
| labels | TEXT | 标签（JSON 数组字符串） |
| created_by | INTEGER FK | 创建人 |
| assigned_to | INTEGER FK NULL | 负责人，为空表示个人任务 |
| team_id | INTEGER FK NULL | 所属团队，为空表示个人任务 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 最后更新时间 |

### comments（评论表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| task_id | INTEGER FK | 所属任务 |
| user_id | INTEGER FK | 评论人 |
| content | TEXT | 评论内容 |
| created_at | DATETIME | 创建时间 |

### attachments（附件表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| task_id | INTEGER FK | 所属任务 |
| uploaded_by | INTEGER FK | 上传人 |
| filename | TEXT | 原始文件名 |
| file_path | TEXT | 服务器存储路径 |
| file_size | INTEGER | 文件大小（字节） |
| created_at | DATETIME | 上传时间 |

### system_settings（系统配置表）

| 字段 | 类型 | 说明 |
|------|------|------|
| key | TEXT PK | 配置项名称 |
| value | TEXT | 配置值 |
| updated_at | DATETIME | 最后修改时间 |

SMTP 相关配置项：`smtp_host`、`smtp_port`、`smtp_user`、`smtp_password`、`smtp_from`、`email_send_hour`（默认 8）

---

## 5. 权限设计

| 角色 | 判断条件 | 权限范围 |
|------|---------|---------|
| 普通用户 | 默认 | 管理自己的任务；查看/评论所在团队的任务 |
| 团队负责人 | team.created_by == user.id | 额外：管理团队成员、查看团队所有任务 |
| 系统管理员 | user.is_admin == true | 额外：管理所有用户账号、配置 SMTP |

---

## 6. 核心功能说明

### 6.1 任务管理

- 创建、编辑、删除任务（仅创建人或管理员可删除）
- 任务状态流转：待处理 → 进行中 → 已完成（支持拖拽）
- 截止日期临近（≤ 1 天）时任务卡片高亮红色警示
- 支持按状态、优先级、负责人、标签筛选

### 6.2 团队协作

- 用户可创建团队，成为该团队负责人
- 负责人可添加/移除团队成员
- 团队任务可分配给任意团队成员

### 6.3 评论与附件

- 任务详情页支持文字评论
- 附件支持上传：图片（jpg/png/gif）、PDF、Office 文档（doc/docx/xls/xlsx/ppt/pptx）
- 单文件上传限制：20MB
- 附件仅限任务所在团队成员或任务创建人下载

### 6.4 每日邮件提醒

- 每天早上 8:00（可由管理员配置）由 APScheduler 触发
- 邮件接收人：
  - **任务责任人**：汇总名下当天截止及已逾期的任务
  - **团队负责人**：汇总所负责团队中当天截止及逾期的全部任务
- 仅向 `email_notify = true` 的用户发送
- SMTP 配置由管理员在后台动态设置，无需重启服务

---

## 7. 前端页面设计

### 配色方案

- **背景色：** 米白 / 浅暖灰（#F5F0EB）
- **主强调色：** 橙红色（#E8572A）
- **次强调色：** 暖橙（#F4A259）
- **文字色：** 深炭灰（#2C2C2C）
- **边框/分割线：** 暖灰（#D9D0C7）

### 主要页面

| 页面 | 路由 | 说明 |
|------|------|------|
| 登录 | `/login` | 用户名+密码登录 |
| 我的任务 | `/my-tasks` | 个人任务看板，三列拖拽 |
| 团队任务 | `/team/:id` | 团队任务列表，支持筛选 |
| 任务详情 | `/task/:id` | 详情、评论、附件 |
| 团队管理 | `/team/:id/manage` | 成员管理（负责人） |
| 用户管理 | `/admin/users` | 账号管理（管理员） |
| 系统设置 | `/admin/settings` | SMTP 配置（管理员） |

---

## 8. 错误处理

- 前端 axios 统一拦截 401（Token 过期）→ 自动跳转登录页
- 后端统一返回格式：`{"code": 0, "message": "ok", "data": ...}`
- 文件上传失败、邮件发送失败均记录到后端日志，不影响主流程

---

## 9. 后续可扩展方向（当前不实现）

- WebSocket 实时通知（新评论、任务被分配时弹出提示）
- 数据库迁移至 PostgreSQL（团队规模扩大时）
- 任务甘特图视图
- 微信/钉钉消息通知
