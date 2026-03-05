# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-05 (Asia/Shanghai)
仓库路径: `/home/zq/work-space/repo/ai-projs/posp/Portex`
当前分支: `main`

---

## 1. 当前状态（结论先看）

- `M0` 已全部完成（`M0.1` ~ `M0.5` 全勾选）。
- `M1.1` 已完成（项目骨架 + FastAPI 入口 + 日志配置）。
- `M1.2` 已完成（数据库连接层 + SQLAlchemy 模型 + 初始化脚本）。
- `M1.3` 已完成（健康检查、认证、用户信息、群组列表、消息发送 API 骨架）。
- 当前应从 `M1.4.1` 开始继续开发（认证与安全基础：密码哈希）。
- 最近一次验证结果：
  - 命令: `.venv/bin/pytest -q`
  - 结果: `31 passed`
  - 命令: `.venv/bin/ruff check .`
  - 结果: `All checks passed!`
  - 备注: 测试输出包含 `passlib` 的 `DeprecationWarning`（`crypt` 将在 Python 3.13 移除）。

---

## 2. 本轮新增（M1.3）

### M1.3.1 健康检查接口
- 新增 `app/routes/health.py`，实现 `GET /health`，返回 `{"status": "ok", "version": "0.1.0"}`。
- `app/main.py` 从内联健康检查改为统一注册路由。

### M1.3.2 ~ M1.3.4 认证与用户接口
- `app/routes/auth.py`
  - `POST /auth/register`（重复用户名返回 409）
  - `POST /auth/login`（失败返回 401）
  - 提供 `get_current_user` Bearer 鉴权依赖
- `app/routes/users.py`
  - `GET /users/me`（鉴权后返回当前用户）
- `services/auth.py`
  - 新增内存认证服务：注册、认证、token 生成/解析、按 id 查询、reset

### M1.3.5 ~ M1.3.6 群组与消息接口
- `app/routes/groups.py`
  - `GET /groups`（鉴权后返回样例群组）
- `app/routes/messages.py`
  - `POST /messages`（鉴权后返回 `message_id` 与 `status`）

### Schema 与测试
- 更新 `domain/schemas.py`：补齐 M1.3 所需请求/响应模型。
- 新增 `tests/app/routes/test_api_routes.py`：覆盖健康检查、注册/登录/me 全流程、鉴权校验、重复注册与登录失败。
- 新增 `tests/services/test_auth_service.py`：覆盖认证服务核心行为。

---

## 3. 关键产物索引（重启后优先读）

1. `docs/TODO.md`（主任务清单，真源）
2. `docs/PORTEX_PLAN.md`（总体架构与阶段规划）
3. `app/main.py`、`app/routes/auth.py`（API 主入口与认证链路）
4. `services/auth.py`（当前阶段认证服务实现）
5. `domain/schemas.py`（请求/响应契约）

---

## 4. 下一步建议（直接执行）

1. `M1.4.1` 密码哈希策略与配置化（secret/过期策略）
2. `M1.4.2` token 机制完善（过期、刷新、异常处理）
3. `M1.4.3+` 补权限校验与安全中间件
4. 同步清理当前 `passlib` 警告（依赖版本或算法策略）

---

## 5. 一句话版

> Portex 已完成 M1.3 基础 API 路由链路，当前进入 M1.4 认证与安全强化阶段，起点是 `M1.4.1`。
