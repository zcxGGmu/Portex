# Portex 开发进度上下文（重启续做入口）

最后更新: 2026-03-05 (Asia/Shanghai)
仓库路径: `/home/zq/work-space/repo/ai-projs/posp/Portex`
当前分支: `main`

---

## 1. 当前状态（结论先看）

- `M0` 已全部完成（`M0.1` ~ `M0.5` 全勾选）。
- `M1.1` 已完成（项目骨架 + FastAPI 入口 + 日志配置）。
- `M1.2` 已完成（数据库连接层 + SQLAlchemy 模型 + 初始化脚本）。
- 当前应从 `M1.3.1` 开始继续开发（基础 API 路由）。
- 最近一次验证结果：
  - 命令: `.venv/bin/pytest -q`
  - 结果: `21 passed`
  - 命令: `.venv/bin/ruff check .`
  - 结果: `All checks passed!`

---

## 2. 本轮新增（M1.2）

### M1.2.1 数据库连接
- `infra/db/database.py`
  - 新增 `DATABASE_URL`（支持环境变量覆盖，默认 sqlite+aiosqlite）
  - 新增 `engine`、`AsyncSessionLocal`、`get_db()`
- `infra/db/session.py`
  - 新增异步事务会话上下文 `session_scope()`（commit/rollback）

### M1.2.2 ~ M1.2.6 数据模型
- 新增统一模型基类：`domain/models/base.py` (`DeclarativeBase`)
- 完成 SQLAlchemy 模型：
  - `domain/models/user.py` (`users`)
  - `domain/models/message.py` (`messages`)
  - `domain/models/session.py` (`sessions`)
  - `domain/models/group.py` (`registered_groups`)
  - `domain/models/task.py` (`scheduled_tasks`)
- 更新导出：`domain/models/__init__.py` 导出 `Base` 和全部模型类

### M1.2.7 初始化脚本
- `scripts/init_db.py`
  - 基于统一 metadata 执行 `create_all`
  - 支持 `--database-url` 覆盖
  - 保留 `main()` 可执行入口

### 新增测试
- `tests/domain/models/test_models.py`
  - 覆盖表名、关键字段、共享 metadata
- `tests/infra/db/test_database.py`
  - 覆盖默认 `DATABASE_URL` 与 `get_db()` 产出 `AsyncSession`
- `tests/scripts/test_init_db.py`
  - 覆盖 `main()` 返回码与数据库建表行为

---

## 3. 关键产物索引（重启后优先读）

1. `docs/TODO.md`（主任务清单，真源）
2. `docs/PORTEX_PLAN.md`（总体架构与阶段规划）
3. `infra/db/database.py`、`infra/db/session.py`（数据库会话主线）
4. `domain/models/base.py`、`domain/models/__init__.py`（模型 metadata 主线）
5. `scripts/init_db.py`（初始化建表入口）

---

## 4. 下一步建议（直接执行）

1. `M1.3.1` 实现独立健康检查路由（`app/routes/health.py`）并接入 `app/main.py`
2. `M1.3.2` ~ `M1.3.4` 完成认证与用户基本接口（先测试后实现）
3. `M1.3.5` ~ `M1.3.6` 完成群组列表与消息发送接口骨架
4. 每完成一项：更新 `docs/TODO.md`、运行 `.venv/bin/pytest -q`、单任务单提交

---

## 5. 一句话版

> Portex 已完成 M1.2 数据库层，当前进入 M1.3 路由与 API 链路建设，起点是 `M1.3.1`。
