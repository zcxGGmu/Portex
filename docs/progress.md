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
- `M1.4` 已完成（密码哈希、JWT 过期、当前用户依赖注入、CORS 限制）。
- 当前应从 `M1.5.1` 开始继续开发（前端骨架）。
- 最近一次验证结果：
  - 命令: `.venv/bin/pytest -q`
  - 结果: `38 passed`
  - 命令: `.venv/bin/ruff check .`
  - 结果: `All checks passed!`
  - 备注: 测试输出仍有 `passlib` 的 `DeprecationWarning`（`crypt` 在 Python 3.13 移除）。

---

## 2. 本轮新增（M1.4）

### M1.4.1 密码哈希
- `services/auth.py`
  - 新增 `hash_password()` 与 `verify_password()`。
  - 密码上下文优先尝试 `bcrypt`，不可用时自动回退 `pbkdf2_sha256`。

### M1.4.2 JWT 生成与验证
- `services/auth.py`
  - 新增模块级 `create_access_token(data, expires_delta)` 与 `decode_access_token(token)`。
  - token payload 包含 `exp`，默认有效期 24 小时。
  - `AuthService.create_access_token(user_id)` 保持兼容，内部同样写入 `exp`。

### M1.4.3 当前用户依赖注入
- 新增 `app/middleware/auth.py`
  - `security = HTTPBearer(auto_error=False)`
  - `get_current_user(credentials, db=Depends(get_db))`
  - 统一 401 错误处理
- 路由依赖从 `app/routes/auth.py` 内部函数迁移到 `app.middleware.auth`。

### M1.4.4 CORS 中间件
- `app/main.py`
  - `allow_origins=["http://localhost:5173"]`
  - `allow_methods=["*"]`
  - `allow_headers=["*"]`

### 新增测试
- `tests/services/test_auth_security.py`
  - 覆盖 hash/verify、token 过期与解码。
- `tests/app/middleware/test_auth_middleware.py`
  - 覆盖当前用户依赖的成功与 401 场景。
- `tests/app/routes/test_api_routes.py`
  - 新增 CORS 预检通过测试。

---

## 3. 关键产物索引（重启后优先读）

1. `docs/TODO.md`（主任务清单，真源）
2. `docs/PORTEX_PLAN.md`（总体架构与阶段规划）
3. `services/auth.py`（认证安全主线）
4. `app/middleware/auth.py`（鉴权依赖主线）
5. `app/main.py`（路由和 CORS 接入点）

---

## 4. 下一步建议（直接执行）

1. `M1.5.1` 初始化 `web/` 前端项目（Vite + React + TS）
2. `M1.5.2` 配置 Tailwind 与基础构建
3. `M1.5.3` ~ `M1.5.4` 搭建登录/注册/聊天页面骨架
4. `M1.6` 做阶段验收（后端接口 + 前端 build）

---

## 5. 一句话版

> Portex 已完成 M1.4 认证与安全基础，当前进入 M1.5 前端骨架开发，起点是 `M1.5.1`。
