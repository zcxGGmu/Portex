# M6.5.1 Version Planning Design

## Goal

Complete `M6.5.1` by defining the release-version strategy for the current repository without prematurely creating tags, changing runtime version strings, or building release artifacts.

## Scope

- define the target first release version
- define how git tags and repository/package version strings should relate
- document the decision and rationale in repo-facing docs
- update restart-oriented handoff so the next step becomes `M6.5.2`

## Out of Scope

- do not create a git tag
- do not push anything to a remote
- do not change `pyproject.toml` from `0.1.0` yet
- do not change runtime/API version responses yet
- do not build Docker images or release bundles
- do not start release automation or GitHub release workflows

## Design Constraints

- `docs/TODO.md` shows `v1.0.0` as the intended release example for `M6.5.1`
- the current repository still exposes `0.1.0` in package metadata and API responses, so changing it now would blur the line between “planning” and “release execution”
- `M6.5.2` and `M6.5.3` still exist explicitly for tag creation and artifact building, so `M6.5.1` should stop before those actions

## Options Considered

### Option A: Planning-only decision, no version-string changes yet

Pros:
- cleanest match to the milestone name
- keeps `M6.5.1` distinct from tag/release execution
- avoids half-finished release state where docs say one version but runtime still behaves like another

Cons:
- leaves an intentional temporary mismatch between planned release version and current package/runtime version

### Option B: Planning plus immediate `pyproject.toml` / runtime version bump

Pros:
- removes the visible version mismatch earlier

Cons:
- effectively starts release execution one phase too early
- would require broader consistency updates across app responses and docs

### Option C: Planning plus tag creation

Pros:
- fastest path to an actual release

Cons:
- directly overlaps with `M6.5.2`
- too large for the current milestone

## Recommended Design

Choose **Option A**.

## Proposed Version Strategy

- target first formal release tag: `v1.0.0`
- reserve the `v` prefix for git tags and release labels
- when the repository/package version is later synchronized, use bare semver `1.0.0` in `pyproject.toml` and runtime metadata
- keep the current `0.1.0` package/runtime version unchanged during `M6.5.1`
- defer actual synchronization of package/runtime version strings to the tag/release execution phases so the repository never enters a partially released state

## Documentation Changes

- add a dedicated version-planning design doc and implementation plan
- update `README.md` to mention the planned first release target and the fact that actual version-string synchronization is deferred
- update `docs/progress.md` with the milestone decision, verification evidence, and next starting point `M6.5.2`
- update `tasks/todo.md` with the current session checklist and review notes
- update `AGENTS.md` so restart context points to `M6.5.2`

## Risks and Boundaries

- until `M6.5.2` or later, the repository will intentionally keep the planning decision (`v1.0.0`) separate from the current package/runtime version (`0.1.0`)
- that temporary mismatch must be documented clearly so future sessions do not mistake it for a bug or forget to finish the sync

## Expected Deliverables

- documented version strategy centered on `v1.0.0`
- restart-oriented docs that clearly separate planning from execution
- next starting point advanced to `M6.5.2`
