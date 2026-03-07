# Portex vs happyclaw 开发状态对照

最后更新：2026-03-08（Asia/Shanghai）

## 1. 文档目的

本文用于回答两个问题：

1. `Portex` 当前已经重构到了 happyclaw 的哪一层能力。
2. 接下来为了逼近 happyclaw 的完整产品态，还缺哪些模块。

这份对照主要基于以下本地材料：

- `docs/progress.md`
- `docs/TODO.md`
- `docs/PORTEX_PLAN.md`
- `/home/zcxggmu/workspace/hello-projs/agents/happyclaw/README.md`
- `/home/zcxggmu/workspace/hello-projs/agents/happyclaw/CLAUDE.md`

---

## 2. 一句话结论

`Portex` 现在已经完成了 **PoC、核心骨架、消息运行链路、执行底座，以及 M4.1 的基础多用户能力**，当前起点在 `M4.2.1`（RBAC 权限模板）。

如果和 happyclaw 对比：

- **执行/runtime 底座**：Portex 已经追到相当接近的阶段。
- **多用户产品能力**：Portex 只完成了“起步版”，还没有追上 happyclaw 的完整产品闭环。
- **管理端 / 配置 / 审计 / 任务 / 记忆 / 初始化流程**：Portex 仍明显落后于 happyclaw。

换句话说，Portex 已经过了“底层能不能跑”的阶段，正在进入“多用户产品能力补齐”的阶段。

---

## 3. 当前 Portex 状态

根据 `docs/progress.md`，Portex 当前状态如下：

- `M0` 完成：预研、PoC、事件契约。
- `M1` 完成：后端骨架与基础表。
- `M2` 完成：消息发送、WebSocket、运行/取消主链路。
- `M3` 完成：Docker SDK、agent-runner、挂载安全、容器生命周期、宿主机模式、安全限制。
- `M4.1.1` 完成：扩展用户模型。
- `M4.1.2` 完成：管理员用户管理 API。
- `M4.1.3` 完成：邀请码系统。
- 当前起点：`M4.2.1`（定义权限模板）。

当前 `M4.1` 的实现特点：

- 用户与邀请码的运行态仍主要由 **in-memory `AuthService`** 承担。
- 已有：
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /users/me`
  - `GET /admin/users`
  - `PATCH /admin/users/{user_id}`
  - `GET /admin/invites`
  - `POST /admin/invites`
- 当前邀请码是 **可选消费、单次使用** 的最小实现。
- 当前还没有注册模式开关（开放注册 / 必须邀请码 / 关闭注册）。

---

## 4. happyclaw 当前能力画像

根据 `happyclaw` 的 README 与 `CLAUDE.md`，happyclaw 已经不是“重构骨架”，而是一个更接近完整产品态的系统。其核心能力包括：

- 多端接入：飞书 / Telegram / Web。
- 完整认证流程：
  - 初始化 setup
  - 首管理员创建
  - 登录 / 登出 / `me`
  - 注册
  - Profile 更新
  - 修改密码
- 更完整的多用户系统：
  - 用户管理
  - 邀请码
  - 注册设置
  - 审计日志
- RBAC 与权限体系：
  - 角色
  - 权限模板
  - 用户权限
  - 群组成员权限
- 群组与主容器体系：
  - per-user home group
  - admin 主容器特权
  - 自动注册群组
- 任务系统：
  - CRUD
  - 执行日志
  - 跨组任务管理
- 记忆系统：
  - 全局记忆
  - 群组记忆
  - memory 搜索 / 读取 / 追加
- 配置系统：
  - appearance
  - system
  - provider
  - user IM config
  - registration config
- 更完整的 MCP / Sub-Agent / 目录浏览 / 系统监控能力。

所以 happyclaw 的参考意义，已经不只是“某个模块的实现方式”，而是 **完整产品能力的上界**。

---

## 5. 对照表：Portex 已追上 vs 尚未追上

### 5.1 已基本追上的部分

#### A. 执行底座

Portex 在 `M3` 完成后，已经具备：

- Docker SDK 封装
- agent-runner 容器 scaffold
- volume mount 安全校验
- 容器启动 / 停止 / 健康检查 / 优雅关闭
- host mode 运行器
- execution mode 选择逻辑
- host mode 安全限制

这说明 Portex 已经完成了 happyclaw 中最难替代、也最容易引入工程复杂度的 **执行与隔离底座**。

#### B. 基础消息运行主链路

Portex 的消息收发、WebSocket、run/cancel 主链路已经完成，因此“消息进来 -> 运行 Agent -> 把结果返回前端/客户端”的主干已经存在。

#### C. 多用户系统的最小骨架

Portex 已经有 happyclaw 对应能力的第一版骨架：

- 用户模型扩展
- 登录/注册/当前用户
- admin 用户列表/更新
- 邀请码创建/查看/消费

这意味着 Portex 已经具备继续长成完整管理端的基础接口。

---

### 5.2 部分追上、但还明显不完整的部分

#### A. 用户系统

Portex 已经有：

- 用户字段扩展
- admin 管理用户 API
- 邀请码 API

但还缺：

- setup / 首管理员引导
- profile 更新
- 修改密码
- 用户删除 / 恢复
- 登录会话管理
- 用户禁用后的真正访问阻断
- 审计日志

#### B. 邀请码系统

Portex 当前邀请码仅实现了“最小可用”版本：

- admin 创建邀请码
- admin 查看邀请码
- 注册时可选消费邀请码
- 邀请角色继承
- 单次使用

但 happyclaw 对应能力更完整，通常还包括：

- 删除邀请码
- 最大使用次数
- 注册模式开关
- 与权限模板/权限集合更深绑定
- 邀请码相关审计日志

#### C. 权限系统

Portex 当前只有：

- `role` 字段
- `require_role("admin")`

这只能算“管理员角色守门”。

而 happyclaw 已经是：

- RBAC
- 权限模板
- 权限检查
- 群组成员级权限
- admin 主容器与普通主容器的权限差异

所以这一块是 Portex 当前最明确的下一阶段主线。

---

### 5.3 仍明显落后的部分

#### A. 任务系统

Portex 的 `M4.3` 还未开始，因此当前还缺：

- scheduler
- task CRUD
- task_run_logs
- cron / interval / once 调度

happyclaw 已经把任务作为正式产品能力暴露。

#### B. 记忆系统

Portex 的 `M4.4` 还未开始，因此当前还缺：

- `CLAUDE.md` 用户级记忆
- 日期记忆
- 记忆搜索
- MCP 工具封装

这部分在 happyclaw 里已经是主容器体验的重要组成部分。

#### C. 管理与配置平面

Portex 现在还没有对齐 happyclaw 的这些管理能力：

- registration settings
- audit log
- system config
- appearance config
- user IM config
- provider 配置测试与应用
- MCP server 管理

#### D. 初始化与产品化流程

happyclaw 已经有完整产品化体验：

- 初始化状态检查
- setup wizard
- 首管理员创建
- 用户注册后自动创建 home group
- Web 页面与 IM 的用户体验闭环

Portex 当前还没有走到这一层。

#### E. 群组/主容器/共享工作区权限体系

Portex 已有 groups 相关基础能力，但尚未完成 happyclaw 那套完整的：

- home group 自动创建
- group_members
- 主容器权限层级
- 跨组权限边界
- 共享工作区成员管理

---

## 6. 差距本质：不是“有没有 API”，而是“是不是完整产品闭环”

Portex 与 happyclaw 当前最大的差距，不在某一个接口，而在 **产品闭环完整度**。

### Portex 当前更像

- 已有底层执行能力
- 已有核心后端骨架
- 已有部分多用户接口
- 正在逐步按里程碑补业务能力

也就是：**工程化重构中段**

### happyclaw 当前更像

- 用户可以从 setup 开始一路用到管理端
- 有权限、邀请码、任务、记忆、配置、审计、群组管理
- Web / IM / 容器 / MCP / Sub-Agent 已形成完整产品体验

也就是：**多用户 AI Agent 成品系统**

---

## 7. 如果映射到 Portex 当前 TODO，最关键的差距在哪里

按 `docs/TODO.md` 的路线，Portex 接下来最关键的几段如下：

### 第一优先级：`M4.2` RBAC 权限系统

这是当前最关键的补齐点，因为：

- `M4.1` 刚把用户、admin 用户管理、邀请码补出来
- 下一步必须把这些 role 真正变成权限能力
- 不做 `M4.2`，后面的群组成员、管理员权限边界都很难稳定展开

### 第二优先级：`M4.3` 定时任务系统

这是从“聊天/触发式 Agent”向“可调度工作系统”推进的关键一步。

### 第三优先级：`M4.4` 记忆系统

这是从“能执行”走向“连续协作体验”的关键模块。

### 第四优先级：后续 M5/M6 的产品化补齐

如果要逼近 happyclaw，最终还会继续补：

- 更完整的管理后台
- 更完整的配置面
- 真实持久化用户系统
- 初始化流程
- 更丰富的前端与运维能力

---

## 8. 当前最准确的阶段判断

如果一定要给一个对齐结论，当前最准确的表述是：

> Portex 已经完成了 happyclaw 底层执行能力与基础多用户骨架的重构，但距离 happyclaw 的完整产品能力，仍明显缺少 RBAC、任务、记忆、配置、审计和初始化流程。

也可以拆成更直白的版本：

- **底座层**：Portex 已经追上很多
- **业务后端层**：Portex 追到一半左右，正进入多用户/RBAC阶段
- **完整产品层**：Portex 还没追上 happyclaw

---

## 9. 建议的阅读/续作顺序

如果后续继续以“尽快逼近 happyclaw”为目标，建议下一位 Codex 按这个顺序推进：

1. `M4.2.1`：权限模板
2. `M4.2.2`：权限检查依赖
3. `M4.2.3`：群组成员模型
4. `M4.3`：任务调度与日志
5. `M4.4`：记忆系统

同时每一阶段都要继续保留这两个现实约束：

- 当前 Docker daemon 不可用，真实容器烟测仍未做
- 当前用户/邀请码仍以 in-memory `AuthService` 为主，后续要谨慎规划 DB-backed 迁移

---

## 10. 给后续开发的简短判断

如果只是问“Portex 现在离 happyclaw 还有多远”，最短答案是：

> Portex 已经过了最难的执行底座阶段，当前卡位在多用户产品能力的前中段；接下来真正决定它能不能逼近 happyclaw 的，是 `M4.2` RBAC、`M4.3` 任务系统、`M4.4` 记忆系统，以及后续配置/审计/初始化产品化补齐。
