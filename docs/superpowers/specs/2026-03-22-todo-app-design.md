# 待办应用设计文档

**日期：** 2026-03-22
**版本：** 1.1

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
| 数据库 | SQLite（WAL 模式，解决并发写入问题） |
| 定时任务 | APScheduler（BackgroundScheduler） |
| 后端服务器 | Uvicorn |
| 前端框架 | Vue 3 + Vite |
| UI 组件库 | Element Plus |
| 前端状态管理 | Pinia |
| 拖拽库 | Vue Draggable（基于 Sortable.js） |
| 认证方式 | JWT Access Token（8 小时） + Refresh Token（7 天） |

**部署方式：** 单台服务器，前端打包后由 Nginx 反向代理托管，后端运行在 Uvicorn 进程中。

**SQLite 并发说明：** 开启 WAL（Write-Ahead Logging）模式，允许读写并发；SQLAlchemy 连接池配置 `check_same_thread=False`，APScheduler 使用独立 Session，避免与 Web 请求产生锁竞争。

---

## 3. 目录结构

```
todo-app/
├── backend/
│   ├── main.py           # 程序入口，注册路由、启动服务
│   ├── config.py         # 环境配置（SECRET_KEY、上传目录等）
│   ├── database.py       # 数据库连接与 Session 管理（WAL 模式）
│   ├── models.py         # SQLAlchemy 数据库模型
│   ├── schemas.py        # Pydantic 数据校验模型
│   ├── dependencies.py   # 公共依赖（当前用户获取、权限校验装饰器）
│   ├── routers/
│   │   ├── auth.py       # 登录、Token 刷新
│   │   ├── users.py      # 用户管理（管理员）
│   │   ├── tasks.py      # 任务 CRUD
│   │   ├── teams.py      # 团队管理
│   │   ├── comments.py   # 评论
│   │   ├── attachments.py# 附件上传下载（带权限校验流式传输）
│   │   └── settings.py   # 系统配置（SMTP 等）
│   ├── services/
│   │   ├── email.py      # 邮件发送逻辑
│   │   └── auth.py       # 密码哈希、Token 生成验证
│   ├── scheduler.py      # APScheduler 定时任务配置
│   └── scripts/
│       └── init_admin.py # 首次部署：初始化管理员账号
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
    │   │   ├── TaskBoard.vue     # 看板（拖拽，使用 Vue Draggable）
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

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | 主键 |
| username | TEXT | UNIQUE NOT NULL | 用户名，登录用 |
| password_hash | TEXT | NOT NULL | bcrypt 加密密码 |
| email | TEXT | UNIQUE NOT NULL | 邮箱，用于接收提醒 |
| is_admin | BOOLEAN | DEFAULT false | 是否系统管理员 |
| email_notify | BOOLEAN | DEFAULT true | 是否开启每日邮件提醒 |
| is_active | BOOLEAN | DEFAULT true | 账号是否启用 |
| created_at | DATETIME | NOT NULL | 创建时间（UTC） |

### teams（团队表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | 主键 |
| name | TEXT | NOT NULL | 团队名称 |
| created_by | INTEGER | FK → users.id | 创建人（即团队负责人） |
| created_at | DATETIME | NOT NULL | 创建时间（UTC） |

**团队负责人转让：** 当团队负责人账号被停用时，管理员可在用户管理页面将该团队转让给其他成员（更新 `teams.created_by`）。

### team_members（团队成员表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| user_id | INTEGER | FK → users.id | 用户 ID |
| team_id | INTEGER | FK → teams.id | 团队 ID |
| joined_at | DATETIME | NOT NULL | 加入时间（UTC） |

联合主键：`(user_id, team_id)`，防止重复加入同一团队。

### tasks（任务表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | 主键 |
| title | TEXT | NOT NULL | 任务标题 |
| description | TEXT | | 详细描述 |
| status | TEXT | NOT NULL DEFAULT 'pending' | 状态：pending / in_progress / done |
| priority | TEXT | NOT NULL DEFAULT 'medium' | 优先级：low / medium / high |
| due_date | DATE | | 截止日期 |
| created_by | INTEGER | FK → users.id | 创建人 |
| assigned_to | INTEGER | FK → users.id NULL | 负责人，为空表示未分配 |
| team_id | INTEGER | FK → teams.id NULL | 所属团队，为空表示个人任务 |
| created_at | DATETIME | NOT NULL | 创建时间（UTC） |
| updated_at | DATETIME | NOT NULL | 最后更新时间（UTC） |

**标签设计：** 使用独立 `task_labels` 表（见下），支持按标签索引筛选。

### task_labels（任务标签表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| task_id | INTEGER | FK → tasks.id | 任务 ID |
| label | TEXT | NOT NULL | 标签名称 |

联合主键：`(task_id, label)`

### comments（评论表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | 主键 |
| task_id | INTEGER | FK → tasks.id | 所属任务 |
| user_id | INTEGER | FK → users.id | 评论人 |
| content | TEXT | NOT NULL | 评论内容 |
| created_at | DATETIME | NOT NULL | 创建时间（UTC） |

**评论删除权限：** 仅评论作者本人或系统管理员可删除评论。

### attachments（附件表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | 主键 |
| task_id | INTEGER | FK → tasks.id | 所属任务 |
| uploaded_by | INTEGER | FK → users.id | 上传人 |
| filename | TEXT | NOT NULL | 原始文件名（供下载时显示） |
| stored_name | TEXT | NOT NULL | UUID 命名的磁盘文件名（防冲突） |
| file_size | INTEGER | NOT NULL | 文件大小（字节） |
| mime_type | TEXT | NOT NULL | 服务端验证的真实 MIME 类型 |
| created_at | DATETIME | NOT NULL | 上传时间（UTC） |

### system_settings（系统配置表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| key | TEXT | PK | 配置项名称 |
| value | TEXT | | 配置值 |
| updated_at | DATETIME | NOT NULL | 最后修改时间（UTC） |

SMTP 相关配置项：`smtp_host`、`smtp_port`、`smtp_user`、`smtp_password`、`smtp_from`、`email_send_hour`（默认 8，取值 0-23）

**SMTP 密码存储：** 以 Fernet 对称加密存储，密钥来自 `SECRET_KEY`，避免明文落库。

**`email_send_hour` 变更：** APScheduler Job 在每次读取配置后动态 `reschedule`，无需重启服务。

---

## 5. 权限设计

### 角色定义

| 角色 | 判断条件 | 权限范围 |
|------|---------|---------|
| 普通用户 | 默认 | 管理自己的任务；查看/评论所在团队的任务 |
| 团队负责人 | team.created_by == user.id | 额外：管理团队成员、查看/删除团队所有任务、转让团队 |
| 系统管理员 | user.is_admin == true | 额外：管理所有用户账号、配置 SMTP、转让任意团队 |

### 任务操作权限

| 操作 | 允许的角色 |
|------|-----------|
| 查看任务 | 任务创建人 / 任务负责人 / 同团队成员 / 管理员 |
| 编辑任务内容（标题、描述、优先级、截止日期、标签） | 任务创建人 / 团队负责人 / 管理员 |
| 修改任务状态 | 任务创建人 / 任务负责人 / 团队负责人 / 管理员 |
| 分配任务负责人 | 任务创建人 / 团队负责人 / 管理员 |
| 删除任务 | 任务创建人 / 团队负责人 / 管理员 |

### 权限执行方式

所有权限检查通过 `dependencies.py` 中的可复用 FastAPI 依赖函数实现，路由层统一注入，不在各 Router 内散写。

---

## 6. 核心功能说明

### 6.1 任务管理

- 创建、编辑、删除任务（权限见上表）
- 任务状态流转：待处理 → 进行中 → 已完成（支持拖拽，使用 Vue Draggable）
- 截止日期临近（≤ 1 天）时任务卡片高亮红色警示
- 支持按状态、优先级、负责人、标签、截止日期筛选
- 列表接口支持分页（默认每页 20 条）

### 6.2 团队协作

- 用户可创建团队，成为该团队负责人
- 负责人可添加/移除团队成员
- 团队任务可分配给任意团队成员
- 同一用户可属于多个团队；"团队任务"页按团队分组展示，用户只能看到自己所属团队的任务

### 6.3 评论与附件

- 任务详情页支持文字评论；评论人本人或管理员可删除
- 附件支持上传：图片（jpg/png/gif）、PDF、Office 文档（doc/docx/xls/xlsx/ppt/pptx）
- 单文件上传限制：20MB
- 服务端通过 `python-magic` 验证真实 MIME 类型，不信任文件扩展名
- 附件存储路径由环境变量 `TODO_UPLOAD_DIR` 指定（绝对路径，如 `/var/todo/uploads`），默认值为后端工作目录下的 `uploads/`
- 附件下载通过 `GET /api/attachments/{id}/download` 接口流式传输，后端校验权限后才允许下载；不暴露磁盘路径

### 6.4 每日邮件提醒

- 每天指定小时整点（默认 8:00，时区以服务器本地时区为准）由 APScheduler 触发
- 判断"今日截止"时，`due_date`（日期型，无时区）与服务器本地日期比较，统一用 `datetime.date.today()` 取本地日期，不依赖 UTC
- 邮件接收人：
  - **任务负责人**：汇总名下当天截止及已逾期的任务
  - **团队负责人**：汇总所负责团队中当天截止及逾期的全部任务
- 仅向 `email_notify = true` 且 `is_active = true` 的用户发送
- SMTP 配置由管理员在后台动态设置；`email_send_hour` 修改后立即重新调度，无需重启
- 邮件发送失败记录错误日志，不影响其他用户的邮件发送

---

## 7. API 接口概览

所有接口前缀：`/api/v1`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/auth/login` | 登录，返回 access_token + refresh_token | 公开 |
| POST | `/auth/logout` | 注销，清除 refresh_token Cookie | 登录用户 |
| POST | `/auth/refresh` | 用 refresh_token 换新 access_token | 持有 refresh_token |
| GET | `/tasks` | 任务列表（支持分页、筛选） | 登录用户 |
| POST | `/tasks` | 创建任务 | 登录用户 |
| GET | `/tasks/{id}` | 任务详情 | 有权限的用户 |
| PUT | `/tasks/{id}` | 编辑任务内容（标题/描述/优先级/截止日期/标签） | 创建人/团队负责人/管理员 |
| PATCH | `/tasks/{id}/status` | 修改任务状态 | 创建人/负责人/团队负责人/管理员 |
| PATCH | `/tasks/{id}/assignee` | 修改任务负责人 | 创建人/团队负责人/管理员 |
| DELETE | `/tasks/{id}` | 删除任务 | 创建人/团队负责人/管理员 |
| POST | `/tasks/{id}/comments` | 发布评论 | 有查看权限的用户 |
| DELETE | `/comments/{id}` | 删除评论 | 作者或管理员 |
| POST | `/tasks/{id}/attachments` | 上传附件 | 有查看权限的用户 |
| GET | `/attachments/{id}/download` | 下载附件（权限校验后流式传输） | 有查看权限的用户 |
| DELETE | `/attachments/{id}` | 删除附件及磁盘文件 | 上传人/团队负责人/管理员 |
| GET | `/teams` | 我的团队列表 | 登录用户 |
| POST | `/teams` | 创建团队 | 登录用户 |
| GET | `/teams/{id}/tasks` | 团队任务列表（分页） | 团队成员 |
| POST | `/teams/{id}/members` | 添加成员 | 团队负责人 |
| DELETE | `/teams/{id}/members/{uid}` | 移除成员 | 团队负责人 |
| PUT | `/teams/{id}/transfer` | 转让团队负责人 | 团队负责人 / 管理员 |
| GET | `/admin/users` | 用户列表 | 管理员 |
| POST | `/admin/users` | 创建用户 | 管理员 |
| PUT | `/admin/users/{id}` | 编辑用户（含停用） | 管理员 |
| GET | `/admin/settings` | 读取系统配置 | 管理员 |
| PUT | `/admin/settings` | 更新系统配置（SMTP 等） | 管理员 |

**统一响应格式：**
```json
{ "code": 0, "message": "ok", "data": { ... } }
```

---

## 8. 安全设计

### 认证与 Token

- Access Token：JWT，有效期 8 小时，存于前端内存（不存 localStorage，防 XSS）
- Refresh Token：有效期 7 天，存于 HttpOnly Cookie，前端无法通过 JS 读取；用户注销或账号被停用时，后端清除 Cookie 并将 token 加入内存黑名单（服务重启后黑名单清空，此为局域网可接受的权衡）
- `SECRET_KEY`：从环境变量 `TODO_SECRET_KEY` 读取，不写入代码或配置文件；首次部署时由运维生成随机字符串

### 登录防暴力破解

- 同一 IP 5 分钟内登录失败超过 10 次，锁定 15 分钟（基于内存计数器，重启后重置，局域网场景够用）

### 附件安全

- 服务端用 `python-magic` 检查真实 MIME 类型，不依赖文件扩展名
- 附件通过 API 接口下载，后端验权后流式传输，不暴露磁盘路径

### 管理员权限执行

- 所有 `is_admin` 检查通过 `dependencies.py` 的 `require_admin` 依赖统一执行，不在各路由散写

---

## 9. 前端页面设计

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
| 团队任务 | `/team/:id` | 团队任务列表，支持筛选、分页 |
| 任务详情 | `/task/:id` | 详情、评论、附件 |
| 团队管理 | `/team/:id/manage` | 成员管理（负责人） |
| 用户管理 | `/admin/users` | 账号管理（管理员） |
| 系统设置 | `/admin/settings` | SMTP 配置（管理员） |

---

## 10. 错误处理与日志

- 前端 axios 统一拦截 401（Token 过期）→ 自动用 refresh_token 换新 token，失败则跳转登录页
- 后端日志使用 Python `logging` 模块，输出到文件 `logs/app.log`，按天滚动（`TimedRotatingFileHandler`），保留 30 天
- 文件上传失败、邮件发送失败均记录 ERROR 级别日志，不影响主流程

---

## 11. 初始部署流程

1. 配置环境变量 `TODO_SECRET_KEY`（随机生成，如 `openssl rand -hex 32`）
2. 配置环境变量 `TODO_UPLOAD_DIR`（附件存储绝对路径，如 `/var/todo/uploads`，默认 `./uploads`）
3. 运行 `python scripts/init_admin.py --username admin --email admin@company.com`，脚本交互式提示输入密码；若账号已存在则跳过，避免重复执行问题
3. 管理员登录后台，配置 SMTP 信息
4. 前端执行 `npm run build`，产物由 Nginx 托管
5. 后端执行 `uvicorn main:app --host 0.0.0.0 --port 8000`

---

## 12. 后续可扩展方向（当前不实现）

- WebSocket 实时通知（新评论、任务被分配时弹出提示）
- 数据库迁移至 PostgreSQL（团队规模扩大时）
- 任务甘特图视图
- 微信/钉钉消息通知
