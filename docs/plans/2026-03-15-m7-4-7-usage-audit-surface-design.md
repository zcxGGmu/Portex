# M7.4.7 Usage And Audit Operator Surface Design

## Goal

Close the remaining `M7.4` operator-surface gap by adding a minimal but real usage + audit read surface in Portex, with explicit scope boundaries where full HappyClaw parity is intentionally deferred.

## Scope

- add authenticated operator usage API (`GET /usage/stats`)
- add authenticated operator audit API (`GET /audit/messages`)
- add a `/usage` page for usage summary and trend/breakdown tables
- add a `/audit` page for recent message-level audit feed
- add OpenAPI tags/contracts and route registration for usage/audit

## Out Of Scope

- no token/cost/model-usage parity (Portex does not persist token usage yet)
- no auth/user/invite/security event audit log stream in this slice
- no CSV export / download endpoint
- no mutable operator controls on usage/audit pages (read-only only)
- no new persistence schema or migration; reuse current `messages` table + `attachments`

## Current Gap

`M7.4.1` ~ `M7.4.6` completed monitor/files/memory/skills/mcp/settings surfaces, but parity backlog still explicitly calls out usage/audit/operator pages. Portex currently has no usage page and no operator audit feed.

## Options Considered

### Option A: Full HappyClaw parity (token cost + auth audit + export)

Pros:
- closest parity outcome
- richer operator insights

Cons:
- requires additional runtime persistence and broader auth event instrumentation
- too large/risky for one incremental `M7.4.x` step

Reject.

### Option B: Message-backed minimal usage + audit pages (recommended)

Pros:
- real user-visible operator surface in one slice
- reuses existing persisted `messages` + metadata (`attachments`)
- keeps risk low and avoids schema churn

Cons:
- usage metrics are message/run-count oriented, not token/cost oriented
- audit feed is currently message-centric

Choose this option.

### Option C: Declare all usage/audit out-of-scope with docs only

Pros:
- zero implementation risk

Cons:
- weak parity progress and little product value

Reject.

## Recommended Design

### 1. Data Source And Aggregation

Use `messages` table as the single source:

- base fields: `id/chat_jid/sender/content/is_from_me/slot_id/timestamp`
- metadata from `attachments` JSON when present:
  - `channel`
  - `group_folder`
  - `run_id`
  - `external_message_id`

Aggregation is read-only and in-process:

- usage summary: total messages, distinct runs, user vs assistant messages, active days
- usage daily: per-day message/run/user/assistant counts
- usage channel breakdown: per-channel message/run counts
- audit feed: recent messages with normalized metadata

### 2. API Surface

- `GET /usage/stats?days=7`
  - `days` clamped to `[1, 365]`
  - owner/admin only
  - response: summary + daily rows + channel rows + effective `days`

- `GET /audit/messages?limit=100&group_id=<optional>`
  - `limit` clamped to `[1, 200]`
  - owner/admin only
  - optional `group_id` filter over workspace/group folder metadata
  - response: items + effective limit + optional filter echo

### 3. Permission Boundary

Keep consistent with current operator pages:

- owner/admin allowed
- member forbidden (`403`)

No new permission-template resource is introduced in this slice.

### 4. Web Surface

Add two operator-only pages and nav entries:

- `/usage`
  - period selector (`7/14/30/90` days)
  - summary cards
  - daily usage table
  - channel breakdown table

- `/audit`
  - optional group/workspace filter input
  - recent message feed table with timestamp/run/channel/sender/direction/content preview

Both pages reuse existing panel/table styles and show explicit forbidden/unavailable states.

### 5. Explicit Deferred Parity

Document that the following remain intentionally deferred after `M7.4.7`:

- token/cost usage accounting
- auth/user management audit event stream
- audit export pipeline

## Testing Strategy

- service tests for usage aggregation correctness, invalid JSON tolerance, and audit filtering/limits
- route tests for auth + role gates + response shape
- OpenAPI contract tests for usage/audit tags and paths
- frontend lint/build verification

## Acceptance

`M7.4.7` is complete when:

- usage/audit APIs are implemented with focused backend tests
- `/usage` and `/audit` pages are reachable and role-gated in web navigation
- OpenAPI includes usage/audit tags and contracts
- focused tests + full regression + lint/build pass
- progress handoff moves next entrypoint beyond `M7.4.7`
