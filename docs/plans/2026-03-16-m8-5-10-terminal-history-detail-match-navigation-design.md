# M8.5.10 Terminal History Detail Match Navigation Design

## Goal

Add local match navigation inside the terminal history detail panel so operators can move between occurrences of the active search term within one session's output.

## Scope

- add match counting and previous/next navigation inside the existing `/terminals` history detail panel
- compute match locations locally from the active search term and the loaded detail output
- highlight all matches and distinguish the currently active match
- scroll the active match into view when navigation changes
- keep all backend contracts unchanged

## Out Of Scope

- no new backend routes, DTOs, or search-position APIs
- no cross-session next/previous navigation
- no search results pagination
- no URL-state syncing for the active match
- no regex, fuzzy search, or alternative query syntax

## Current Gap

`M8.5.9` lets operators search within a workspace and open a matching session in the detail panel, but once the full output is visible there is no way to jump through multiple matches. Operators must visually scan long output blocks by hand.

## Recommended Architecture

### 1. Local Match Computation

Reuse the current active search term and `detailData.output` on the frontend. When either changes, compute all case-insensitive substring match offsets locally in the detail panel component state.

This keeps the backend focused on search discovery and keeps per-detail navigation as a presentation concern.

### 2. Navigation State

Maintain:

- `detailMatchIndexes`
- `activeMatchIndex`

Behavior:

- if the search term is empty, there are no matches and no navigation controls
- if a new detail session opens and matches exist, activate the first match
- if the search term changes, recompute matches and reset the active index to the first match

### 3. Highlight + Scroll

Render detail output as segmented text spans instead of one raw `pre` block:

- all matches get a base highlight style
- the active match gets a stronger highlight style

Track the active match element with a ref and scroll it into view when `activeMatchIndex` changes.

### 4. Minimal Operator UI

Add a compact control row above the detail output:

- `Previous`
- `Next`
- `Match N / M`

Controls are only shown when the current detail output has at least one match.

## Risks And Mitigations

- **Risk:** frontend match logic drifts from backend search matching.
  - **Mitigation:** keep both sides on the same case-insensitive substring rule.
- **Risk:** rendering large output as many spans hurts readability or performance.
  - **Mitigation:** only split output when there is an active search term with matches; otherwise keep the simple text rendering path.
- **Risk:** navigation state leaks across sessions.
  - **Mitigation:** reset active match state whenever detail session or search term changes.

## Testing Strategy

### Backend / Regression

- no new backend route/service behavior required
- continue running the terminal focused suite to ensure existing search/detail contracts are untouched

### Frontend

- lint/build green
- verify active search term triggers match count and controls
- verify previous/next navigation changes the active highlight and scroll target
- verify controls disappear when there are no matches

## Completion Signal

`M8.5.10` is complete when:

- operators can see how many matches exist in the current detail output
- operators can move to previous/next match locally in the detail panel
- active match highlighting and scrolling work without changing backend contracts
- existing search/detail/timeline/current-history APIs remain unchanged
