# M8.5.2 Terminal Resize Fidelity Design

## Goal

Replace the current terminal-resize no-op with real size propagation so terminal sessions can react to browser panel/window size changes.

## Scope

- implement real resize handling in `DockerExecTerminalBridge.resize()`
- keep resize flowing through existing websocket message `terminal.resize` and `TerminalSessionService.resize()` contracts
- improve frontend terminal panel resize emission from fixed `120x32` to panel-based dynamic values
- keep current ownership/session lifecycle rules unchanged

## Out Of Scope

- no terminal session persistence (still in-memory per process)
- no terminal takeover/owner-transfer changes
- no host/openai terminal backend expansion
- no ANSI rendering overhaul or xterm.js migration in this slice

## Current Gap

`terminal.resize` messages are accepted by websocket and forwarded to `TerminalSessionService`, but `DockerExecTerminalBridge.resize()` is currently an explicit no-op, and frontend only sends one fixed `120x32` resize on connect.

## Recommended Architecture

### 1. Bridge-Side Real PTY Resize

Use a host PTY for the docker exec subprocess:

- start `docker exec` with `-it` and attach stdin/stdout/stderr to the PTY slave fd
- keep PTY master fd in bridge state for I/O and resize control
- implement `resize(cols, rows)` by applying `TIOCSWINSZ` on PTY master fd

This makes resize effective for the running interactive shell instead of being a placeholder.

### 2. Preserve Existing Service/Route Contracts

Keep the existing call chain unchanged:

- websocket `terminal.resize` message validation remains in route
- route forwards to `TerminalSessionService.resize()`
- service enforces ownership and forwards to bridge

No protocol shape change, only behavior fidelity uplift.

### 3. Frontend Dynamic Resize Emission

In `TerminalPanel`:

- compute `cols/rows` from transcript panel pixel size and approximate cell size
- send resize on `terminal.ready`
- re-send resize on window resize while socket is open
- keep lightweight throttling/guarding to avoid event storms

This removes the fixed hardcoded geometry and aligns terminal size with actual UI dimensions.

## Risks And Mitigations

- **Risk:** PTY read loop can surface `EIO` during shutdown.
  - **Mitigation:** treat `EIO`/`EBADF` as EOF and exit reader task cleanly.
- **Risk:** frequent resize events can spam backend.
  - **Mitigation:** add basic interval throttle + dedupe for unchanged dimensions.
- **Risk:** behavior regressions in attach/output flow.
  - **Mitigation:** add focused bridge/session/websocket tests and keep existing suites green.

## Testing Strategy

### Backend

- add bridge-focused tests for:
  - docker exec command includes TTY flags
  - resize performs PTY ioctl with expected dimensions
- keep service/websocket resize forwarding coverage green

### Frontend

- keep lint/build checks green
- ensure compile-safe resize helper/hooks with no protocol/type regressions

## Completion Signal

`M8.5.2` is complete when:

- bridge resize is no longer no-op and applies PTY window size updates
- websocket/service resize flow still works for valid payloads
- frontend emits dynamic resize (ready + window resize) instead of fixed `120x32`
- focused tests, full regression, lint/build, and diff hygiene all pass
