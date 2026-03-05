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
- `M1.5` 已完成（前端工程初始化 + Tailwind 接入 + 页面结构 + 登录页）。
- 当前应从 `M1.6.1` 开始继续开发（M1 阶段验收）。
- 最近一次验证结果：
  - 命令: `.venv/bin/pytest -q`
  - 结果: `38 passed`
  - 命令: `.venv/bin/ruff check .`
  - 结果: `All checks passed!`
  - 命令: `cd web && npm run build`
  - 结果: `vite build` 通过
  - 命令: `cd web && npm run lint`
  - 结果: `eslint` 通过
  - 备注: 测试输出仍有 `passlib` 的 `DeprecationWarning`（`crypt` 在 Python 3.13 移除）。

---

## 2. 本轮新增（M1.5）

### M1.5.1 前端项目初始化
- 在 `web/` 初始化 Vite + React + TypeScript 工程。
- 安装依赖：
  - `tailwindcss`, `@tailwindcss/vite`
  - `zustand`, `@tanstack/react-query`, `react-router-dom`
  - `@radix-ui/react-dialog`, `@radix-ui/react-dropdown-menu`

### M1.5.2 Tailwind 配置
- `web/vite.config.ts` 接入 `@tailwindcss/vite` 插件。
- `web/src/index.css` 补充 `@import "tailwindcss";`。

### M1.5.3 页面与目录骨架
- 创建并接入以下目录与模块：
  - `web/src/api/client.ts`
  - `web/src/components/ui|layout|chat/*`
  - `web/src/pages/Login.tsx|Register.tsx|Chat.tsx|Settings.tsx`
  - `web/src/stores/auth.ts|chat.ts`
  - `web/src/hooks/useApi.ts`
- `web/src/App.tsx` / `web/src/main.tsx` 已接入 Router + QueryClient。

### M1.5.4 登录页面
- `web/src/pages/Login.tsx` 实现用户名/密码表单。
- 登录调用 `useAuthStore().login()`，成功后跳转 `/chat`。
- 登录失败显示后端错误信息。

---

## 3. 关键产物索引（重启后优先读）

1. `docs/TODO.md`（主任务清单，真源）
2. `docs/PORTEX_PLAN.md`（总体架构与阶段规划）
3. `web/src/App.tsx`、`web/src/main.tsx`（前端入口与路由）
4. `web/src/stores/auth.ts`、`web/src/api/client.ts`（前端认证调用主线）
5. `web/src/pages/Login.tsx`（M1.5 登录页面）

---

## 4. 下一步建议（直接执行）

1. `M1.6.1` 执行阶段单元测试检查（按 TODO 命令）
2. `M1.6.2` 启动后端并验证 `GET /health`
3. `M1.6.3` 复核前端 build 产物（可补 smoke check）
4. M1 验收完成后转入 `M2.1` WebSocket 基础设施

---

## 5. 一句话版

> Portex 已完成 M1.5 前端骨架，当前进入 M1 阶段验收（M1.6），起点是 `M1.6.1`。
