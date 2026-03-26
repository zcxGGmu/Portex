# Terminal Relevance Offline Baseline Convergence Audit Design

## Goal

Audit the current 81-case offline terminal relevance baseline against the landed `M8.5.17` through `M8.5.51` service semantics so the project can decide whether baseline expansion should pause before any post-`M8.5.51` ranking refinement is considered.

## Scope

- audit `tests/services/test_terminal_sessions.py` relevance tests from `M8.5.17` through `M8.5.51`
- compare those semantics against `tests/fixtures/terminal_relevance_baseline.json`
- keep only non-duplicate offline evidence requirements
- update `tests/scripts/test_evaluate_terminal_relevance.py` and the fixture only if a real uncovered semantic gap still exists
- sync restart-oriented docs and session notes with the convergence conclusion

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no new diagnostic tooling unless the audit proves the current manual mapping is insufficient

## Why This Audit Is The Right Next Step

The current search relevance chain is already deep and highly specific. The project has spent the last several sessions converting landed service behavior into a fixed offline benchmark rather than continuing to add tie-break rules without evidence. That strategy has now produced an 81-case fixture covering:

- the foundational `M8.5.17` ordering chain
- whole-word and line-start branches
- wrapper and marker families
- whitespace-family direct comparisons, pagination, and fallback behavior
- the `M8.5.50` and `M8.5.51` mixed-whitespace tail of the current chain

Given that coverage, the next risk is not an obvious missing branch. The next risk is adding another ranking rule without first proving the existing offline benchmark still has a real semantic hole. This audit keeps the project on the baseline-first path and prevents speculative ranking complexity.

## Audit Decision Rules

Treat a service-test behavior as already covered when the existing offline fixture already fixes the same ordering semantics, even if the exact transcript or wrapper family differs.

Treat a service-test behavior as a real offline gap only when all of the following are true:

- the ordering semantic is not already pinned by an existing fixture case
- the behavior is stable enough to merit long-term offline regression coverage
- the new case would increase evidence rather than restate an already-covered direct comparison, pagination slice, or fallback branch

If no such gap remains, baseline expansion stops for now and the next ranking refinement is blocked until one of these triggers appears:

- a newly added service test proves an uncovered semantic branch
- the offline benchmark exposes a metric regression
- production or operator feedback identifies a concrete ranking failure that the current fixture cannot express

## Approaches Considered

### 1. Audit coverage first and only patch true gaps (recommended)

Pros:

- stays aligned with the current baseline-first development strategy
- minimizes regression risk by avoiding speculative new tie-breaks
- produces a clear decision record for when future ranking work is justified

Cons:

- this session may end with docs-only changes if the baseline is already converged

### 2. Add new audit tooling before making the decision

Pros:

- could make future audits faster

Cons:

- introduces maintenance work before proving a tooling gap exists
- solves a workflow problem before confirming there is still a product or relevance problem

### 3. Jump directly to a post-`M8.5.51` ranking refinement

Pros:

- fastest path to a new behavior change

Cons:

- increases ranking complexity without stable evidence of a missing semantic branch
- expands the regression surface in the densest part of the search sort key

## Recommended Approach

Use approach 1. Perform a targeted audit of `M8.5.17` through `M8.5.51`, keep production ranking unchanged, and only extend the offline fixture if the audit still finds a non-duplicate uncovered semantic gap. Otherwise, record that the 81-case baseline is converged enough to pause expansion until new evidence appears.

## Expected Outcome

The most likely outcome is that the current fixture already covers the remaining non-duplicate service semantics, including the `M8.5.50` and `M8.5.51` mixed-whitespace tail. If that expectation holds, this session should end by documenting convergence rather than adding more fixture volume.

## Verification

- if the audit is docs-only, re-run the offline fixture script tests and benchmark summary plus `git diff --check`
- if the audit finds a real gap, use RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`, re-run the benchmark summary, and then run the existing terminal-focused regression commands

## Risks And Mitigations

- Risk: a service-level test might look uncovered because the fixture uses a different transcript while still fixing the same ordering rule.
  - Mitigation: judge coverage by semantic ordering, not by textual duplication.
- Risk: the audit could still miss a small uncovered branch in the `M8.5.50` or `M8.5.51` family.
  - Mitigation: explicitly compare count, offset, pagination, and fallback evidence for the mixed-whitespace tail before declaring convergence.
- Risk: restart docs could keep implying more baseline expansion is expected by default.
  - Mitigation: update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with a clear stop condition for future expansion.
