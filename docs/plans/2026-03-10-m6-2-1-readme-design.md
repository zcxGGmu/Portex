# M6.2.1 README Design

## Goal

Complete `M6.2.1` by replacing the placeholder root `README.md` with a minimal but comprehensive project README that serves first-time readers, self-hosting users, and contributors without overstating the current product maturity.

## Scope

- Rewrite the root `README.md`
- Cover:
  - project positioning
  - current status
  - implemented capabilities
  - quick start
  - development and verification commands
  - project structure overview
  - architecture summary
  - current boundaries and limitations
  - documentation links
  - upstream references
- Base all claims on the current repository state and recent verification evidence

## Out of Scope

- Do not create a separate docs site
- Do not rewrite deeper docs in `docs/`
- Do not add screenshots, badges, or marketing-heavy assets
- Do not promise unimplemented deployment or production-grade IM/runtime capabilities
- Do not start `M6.2.2` or later documentation tasks

## Design Constraints

- README must be accurate to the current codebase and current milestone state
- README must stay useful for three audiences at once:
  - first-time readers
  - self-hosting / operators
  - contributors
- README should stay concise enough to scan, but complete enough to bootstrap the repo
- Current deferred boundaries must remain visible instead of being hidden behind vague language

## Options Considered

### Option A: Developer-first README

- Emphasize setup, commands, and repository structure
- Keep product framing short

Pros:
- Fast to use for contributors

Cons:
- Weak first impression for new readers
- Undersells project goals and current scope

### Option B: Product-first README

- Emphasize positioning, features, and architecture
- Push setup and commands later

Pros:
- Better public-facing story

Cons:
- Slower to use as an actual repository entrypoint

### Option C: Layered README

- Start with positioning and current status
- Move quickly into quick start and developer commands
- End with architecture, boundaries, and doc links

Pros:
- Best balance across reader types
- Matches current project stage and repository needs

Cons:
- Slightly longer than a single-audience README

## Recommended Design

Choose **Option C**.

## Proposed Structure

### `# Portex`

- one-line project description
- relationship to HappyClaw

### `## Current Status`

- current milestone state
- what is already implemented

### `## Features`

- Web / WebSocket backend
- OpenAI Agents runtime integration
- execution modes
- multi-user / RBAC
- tasks and memory
- Feishu / Telegram
- unified message routing
- tests and CI

### `## Quick Start`

- create virtualenv
- install backend deps
- initialize database
- run backend
- install frontend deps
- run frontend

### `## Development`

- backend tests
- focused unit / integration commands
- lint commands
- frontend lint/build
- real provider sanity check

### `## Project Structure`

- concise directory overview

### `## Architecture`

- FastAPI + React + Agent Runner + runtime + exec + IM + memory summary

### `## Current Boundaries`

- current in-memory / file-backed boundaries
- current IM/runtime limitations
- current CI limitations
- current Docker limitation note

### `## Documents`

- `docs/TODO.md`
- `docs/progress.md`
- `docs/PORTEX_PLAN.md`

### `## Upstream Reference`

- HappyClaw repository
- local HappyClaw reference path

## Content Guidelines

### Must Include

- exact commands that work in this repository
- explicit note that Portex is a Python + OpenAI Agents SDK refactor of HappyClaw
- explicit note about current feature maturity and deferred boundaries

### Must Avoid

- phase-by-phase changelog detail
- claims of complete production readiness
- undocumented deploy/publish instructions
- environment-specific personal paths except the known local HappyClaw reference path already used by the project

## Expected Deliverables

- `README.md` becomes a useful project entrypoint
- claims align with `docs/progress.md` and current verification evidence
- `docs/progress.md` and `tasks/todo.md` advance to the next documentation task after verification
