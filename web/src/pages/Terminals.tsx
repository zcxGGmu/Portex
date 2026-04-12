import { type FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import type {
  TerminalHistorySearchSort,
  TerminalSessionHistorySearchMatch,
  TerminalSessionStatus,
  TerminalWorkspaceSummary,
} from '../api/client'
import { ApiError, apiClient } from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import { PrimaryButton } from '../components/ui/PrimaryButton'
import {
  useCurrentUserQuery,
  useTerminalHistoryDetailQuery,
  useTerminalHistorySearchQuery,
  useTerminalHistoryTimelineQuery,
  useTerminalOverviewQuery,
} from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'

const TIMELINE_PAGE_SIZE = 5
const SEARCH_PAGE_SIZE = 5
const TERMINAL_HISTORY_STATUS_OPTIONS: Array<{ value: TerminalSessionStatus; label: string }> = [
  { value: 'created', label: 'Created' },
  { value: 'attached', label: 'Attached' },
  { value: 'detached', label: 'Detached' },
  { value: 'closed', label: 'Closed' },
  { value: 'exited', label: 'Exited' },
]
const DEFAULT_TIMELINE_FILTERS = {
  status: '' as TerminalSessionStatus | '',
  ownerUserId: '',
  sessionIdPrefix: '',
  snapshotFromLocal: '',
  snapshotToLocal: '',
}
const DEFAULT_ARCHIVE_FILTERS = {
  groupNamePrefix: '',
  groupIdPrefix: '',
  chatAccessible: '' as '' | 'true' | 'false',
  status: '' as TerminalSessionStatus | '',
  ownerUserId: '',
  sessionIdPrefix: '',
  snapshotFromLocal: '',
  snapshotToLocal: '',
}
type TerminalTimeRangePresetId = '1h' | '6h' | '24h' | '7d' | '30d'
const TERMINAL_TIME_RANGE_PRESETS: Array<{
  id: TerminalTimeRangePresetId
  label: string
  durationMinutes: number
}> = [
  { id: '1h', label: '1h', durationMinutes: 60 },
  { id: '6h', label: '6h', durationMinutes: 6 * 60 },
  { id: '24h', label: '24h', durationMinutes: 24 * 60 },
  { id: '7d', label: '7d', durationMinutes: 7 * 24 * 60 },
  { id: '30d', label: '30d', durationMinutes: 30 * 24 * 60 },
]

type MatchRange = {
  start: number
  end: number
}

type OutputSegment = {
  text: string
  matchIndex: number | null
}

type PendingMatchTarget =
  | { kind: 'first' }
  | { kind: 'last' }
  | {
      kind: 'exact'
      matchIndex: number
      matchOffset: number
    }

function normalizeSnippetMatches(entry: TerminalSessionHistorySearchMatch) {
  if (entry.snippet_matches.length > 0) {
    return entry.snippet_matches
  }
  return entry.snippets.map((text, matchIndex) => ({
    text,
    match_index: matchIndex,
    match_offset: -1,
  }))
}

function formatDate(value: string | null): string {
  if (!value) {
    return '-'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString()
}

function localDateTimeToUtcIso(value: string): string | undefined {
  const normalized = value.trim()
  if (!normalized) {
    return undefined
  }

  const localDate = new Date(normalized)
  if (Number.isNaN(localDate.getTime())) {
    return undefined
  }
  return localDate.toISOString()
}

function padDateTimePart(value: number): string {
  return String(value).padStart(2, '0')
}

function toLocalDateTimeInputValue(value: Date): string {
  const year = value.getFullYear()
  const month = padDateTimePart(value.getMonth() + 1)
  const day = padDateTimePart(value.getDate())
  const hours = padDateTimePart(value.getHours())
  const minutes = padDateTimePart(value.getMinutes())
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function buildPresetLocalRange(
  presetId: TerminalTimeRangePresetId,
  now: Date = new Date(),
): {
  snapshotFromLocal: string
  snapshotToLocal: string
} {
  const preset = TERMINAL_TIME_RANGE_PRESETS.find((item) => item.id === presetId)
  if (!preset) {
    return {
      snapshotFromLocal: '',
      snapshotToLocal: '',
    }
  }

  const end = new Date(now)
  end.setSeconds(0, 0)
  const start = new Date(end.getTime() - preset.durationMinutes * 60 * 1000)

  return {
    snapshotFromLocal: toLocalDateTimeInputValue(start),
    snapshotToLocal: toLocalDateTimeInputValue(end),
  }
}

function summarize(items: TerminalWorkspaceSummary[]) {
  let activeCount = 0
  let detachedCount = 0
  let closedCount = 0
  let emptyCount = 0

  for (const item of items) {
    if (!item.session) {
      emptyCount += 1
      continue
    }
    if (item.session.status === 'detached') {
      detachedCount += 1
      continue
    }
    if (item.session.status === 'created' || item.session.status === 'attached') {
      activeCount += 1
      continue
    }
    if (item.session.status === 'closed' || item.session.status === 'exited') {
      closedCount += 1
    }
  }

  return { activeCount, detachedCount, closedCount, emptyCount }
}

function findCaseInsensitiveMatches(text: string, query: string): MatchRange[] {
  const normalizedQuery = query.trim().toLowerCase()
  if (!normalizedQuery || !text) {
    return []
  }

  const normalizedText = text.toLowerCase()
  const ranges: MatchRange[] = []
  let cursor = 0
  while (cursor < normalizedText.length) {
    const index = normalizedText.indexOf(normalizedQuery, cursor)
    if (index < 0) {
      break
    }
    ranges.push({ start: index, end: index + normalizedQuery.length })
    cursor = index + Math.max(1, normalizedQuery.length)
  }
  return ranges
}

function buildOutputSegments(output: string, ranges: MatchRange[]): OutputSegment[] {
  if (ranges.length === 0) {
    return [{ text: output, matchIndex: null }]
  }

  const segments: OutputSegment[] = []
  let cursor = 0
  for (let index = 0; index < ranges.length; index += 1) {
    const range = ranges[index]
    if (cursor < range.start) {
      segments.push({
        text: output.slice(cursor, range.start),
        matchIndex: null,
      })
    }
    segments.push({
      text: output.slice(range.start, range.end),
      matchIndex: index,
    })
    cursor = range.end
  }

  if (cursor < output.length) {
    segments.push({
      text: output.slice(cursor),
      matchIndex: null,
    })
  }

  return segments
}

function buildTerminalHistoryDownloadFileName(groupId: string, sessionId: string, extension: 'log' | 'json'): string {
  const sanitize = (value: string) => value.trim().replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^[-.]+|[-.]+$/g, '') || 'snapshot'
  return `terminal-history-${sanitize(groupId)}-${sanitize(sessionId)}.${extension}`
}

function buildTerminalOverviewExportFileName(): string {
  return 'terminal-overview.json'
}

function buildTerminalLatestHistoriesExportFileName(): string {
  return 'terminal-latest-histories.json'
}

function buildTerminalHistoryArchiveBundleFileName(): string {
  return 'terminal-history-archive.json'
}

function buildTerminalHistoryExportFileName(groupId: string, offset: number, limit: number): string {
  const sanitize = (value: string) => value.trim().replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^[-.]+|[-.]+$/g, '') || 'snapshot'
  return `terminal-history-export-${sanitize(groupId)}-offset-${offset}-limit-${limit}.json`
}

function buildTerminalHistoryArchiveFileName(groupId: string): string {
  const sanitize = (value: string) => value.trim().replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^[-.]+|[-.]+$/g, '') || 'snapshot'
  return `terminal-history-archive-${sanitize(groupId)}.json`
}

function buildTerminalHistorySearchExportFileName(
  groupId: string,
  query: string,
  offset: number,
  limit: number,
): string {
  const sanitize = (value: string) => value.trim().replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^[-.]+|[-.]+$/g, '') || 'snapshot'
  return `terminal-history-search-${sanitize(groupId)}-${sanitize(query)}-offset-${offset}-limit-${limit}.json`
}

function buildTerminalHistorySearchArchiveFileName(groupId: string, query: string): string {
  const sanitize = (value: string) => value.trim().replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^[-.]+|[-.]+$/g, '') || 'snapshot'
  return `terminal-history-search-archive-${sanitize(groupId)}-${sanitize(query)}.json`
}

function triggerBrowserDownload(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export function Terminals() {
  const token = useAuthStore((state) => state.token)
  const storedUser = useAuthStore((state) => state.currentUser)
  const { data: currentUserData } = useCurrentUserQuery()
  const currentUser = currentUserData ?? storedUser
  const isOperator = currentUser?.role === 'owner' || currentUser?.role === 'admin'
  const { data, isLoading, isError, error, refetch } = useTerminalOverviewQuery(isOperator)
  const isForbidden = error instanceof ApiError && error.status === 403

  const [actionKey, setActionKey] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionNotice, setActionNotice] = useState<string | null>(null)
  const [timelineGroupId, setTimelineGroupId] = useState<string | null>(null)
  const [timelineOffset, setTimelineOffset] = useState(0)
  const [timelineFilters, setTimelineFilters] = useState<{
    status: TerminalSessionStatus | ''
    ownerUserId: string
    sessionIdPrefix: string
    snapshotFromLocal: string
    snapshotToLocal: string
  }>(DEFAULT_TIMELINE_FILTERS)
  const [archiveFilters, setArchiveFilters] = useState<{
    groupNamePrefix: string
    groupIdPrefix: string
    chatAccessible: '' | 'true' | 'false'
    status: TerminalSessionStatus | ''
    ownerUserId: string
    sessionIdPrefix: string
    snapshotFromLocal: string
    snapshotToLocal: string
  }>(DEFAULT_ARCHIVE_FILTERS)
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchOffset, setSearchOffset] = useState(0)
  const [searchSort, setSearchSort] = useState<TerminalHistorySearchSort>('relevance')
  const [activePresetId, setActivePresetId] = useState<TerminalTimeRangePresetId | null>(null)
  const [pendingSearchPageMove, setPendingSearchPageMove] = useState<'next' | 'previous' | null>(null)
  const [pendingMatchTarget, setPendingMatchTarget] = useState<PendingMatchTarget | null>(null)
  const [detailSessionId, setDetailSessionId] = useState<string | null>(null)
  const [activeDetailMatchIndex, setActiveDetailMatchIndex] = useState(0)
  const activeMatchRef = useRef<HTMLElement | null>(null)
  const timelineArchiveQueryOptions = useMemo(
    () => ({
      status: timelineFilters.status || undefined,
      ownerUserId: timelineFilters.ownerUserId || undefined,
      sessionIdPrefix: timelineFilters.sessionIdPrefix || undefined,
      snapshotFrom: localDateTimeToUtcIso(timelineFilters.snapshotFromLocal),
      snapshotTo: localDateTimeToUtcIso(timelineFilters.snapshotToLocal),
    }),
    [timelineFilters],
  )
  const archiveQueryOptions = useMemo(
    () => ({
      groupNamePrefix: archiveFilters.groupNamePrefix.trim() || undefined,
      groupIdPrefix: archiveFilters.groupIdPrefix.trim() || undefined,
      chatAccessible:
        archiveFilters.chatAccessible === ''
          ? undefined
          : archiveFilters.chatAccessible === 'true',
      status: archiveFilters.status || undefined,
      ownerUserId: archiveFilters.ownerUserId || undefined,
      sessionIdPrefix: archiveFilters.sessionIdPrefix || undefined,
      snapshotFrom: localDateTimeToUtcIso(archiveFilters.snapshotFromLocal),
      snapshotTo: localDateTimeToUtcIso(archiveFilters.snapshotToLocal),
    }),
    [archiveFilters],
  )
  const timelineQueryOptions = useMemo(
    () => ({
      limit: TIMELINE_PAGE_SIZE,
      offset: timelineOffset,
      status: timelineFilters.status || undefined,
      ownerUserId: timelineFilters.ownerUserId || undefined,
      sessionIdPrefix: timelineFilters.sessionIdPrefix || undefined,
      snapshotFrom: localDateTimeToUtcIso(timelineFilters.snapshotFromLocal),
      snapshotTo: localDateTimeToUtcIso(timelineFilters.snapshotToLocal),
    }),
    [timelineFilters, timelineOffset],
  )

  const {
    data: timelineData,
    isLoading: isTimelineLoading,
    isFetching: isTimelineFetching,
    isError: isTimelineError,
    error: timelineError,
    refetch: refetchTimeline,
  } = useTerminalHistoryTimelineQuery(
    timelineGroupId,
    timelineQueryOptions,
    isOperator && timelineGroupId !== null,
  )

  const normalizedSearchQuery = searchQuery.trim()
  const searchQueryOptions = useMemo(
    () => ({
      query: normalizedSearchQuery,
      limit: SEARCH_PAGE_SIZE,
      offset: searchOffset,
      sort: searchSort,
      status: timelineFilters.status || undefined,
      ownerUserId: timelineFilters.ownerUserId || undefined,
      sessionIdPrefix: timelineFilters.sessionIdPrefix || undefined,
      snapshotFrom: localDateTimeToUtcIso(timelineFilters.snapshotFromLocal),
      snapshotTo: localDateTimeToUtcIso(timelineFilters.snapshotToLocal),
    }),
    [normalizedSearchQuery, searchOffset, searchSort, timelineFilters],
  )
  const searchArchiveQueryOptions = useMemo(
    () => ({
      query: normalizedSearchQuery,
      sort: searchSort,
      status: timelineFilters.status || undefined,
      ownerUserId: timelineFilters.ownerUserId || undefined,
      sessionIdPrefix: timelineFilters.sessionIdPrefix || undefined,
      snapshotFrom: localDateTimeToUtcIso(timelineFilters.snapshotFromLocal),
      snapshotTo: localDateTimeToUtcIso(timelineFilters.snapshotToLocal),
    }),
    [normalizedSearchQuery, searchSort, timelineFilters],
  )
  const {
    data: searchData,
    isLoading: isSearchLoading,
    isFetching: isSearchFetching,
    isError: isSearchError,
    error: searchError,
  } = useTerminalHistorySearchQuery(
    timelineGroupId,
    searchQueryOptions,
    isOperator && timelineGroupId !== null && normalizedSearchQuery !== '',
  )

  const {
    data: detailData,
    isLoading: isDetailLoading,
    isError: isDetailError,
    error: detailError,
  } = useTerminalHistoryDetailQuery(
    timelineGroupId,
    detailSessionId,
    isOperator && timelineGroupId !== null && detailSessionId !== null,
  )

  const items = data?.items ?? []
  const summary = summarize(items)
  const currentUserId = currentUser?.id ?? null
  const searchItems = useMemo(() => searchData?.items ?? [], [searchData])
  const activeSearchResultIndex = useMemo(
    () => searchItems.findIndex((item) => item.session.session_id === detailSessionId),
    [searchItems, detailSessionId],
  )

  const detailMatchRanges = useMemo(() => {
    if (!detailData || normalizedSearchQuery === '') {
      return []
    }
    return findCaseInsensitiveMatches(detailData.output, normalizedSearchQuery)
  }, [detailData, normalizedSearchQuery])

  const detailOutputSegments = useMemo(() => {
    if (!detailData) {
      return []
    }
    return buildOutputSegments(detailData.output, detailMatchRanges)
  }, [detailData, detailMatchRanges])

  const canMoveToPreviousSession =
    activeSearchResultIndex > 0 || (activeSearchResultIndex === 0 && searchOffset > 0)
  const canMoveToNextSession =
    (activeSearchResultIndex >= 0 && activeSearchResultIndex < searchItems.length - 1) ||
    (activeSearchResultIndex >= 0 &&
      activeSearchResultIndex === searchItems.length - 1 &&
      Boolean(searchData?.has_more))
  const canMovePreviousMatch =
    detailMatchRanges.length > 0 &&
    (activeDetailMatchIndex > 0 || (canMoveToPreviousSession && !isSearchFetching))
  const canMoveNextMatch =
    detailMatchRanges.length > 0 &&
    (activeDetailMatchIndex < detailMatchRanges.length - 1 || (canMoveToNextSession && !isSearchFetching))

  useEffect(() => {
    if (!pendingSearchPageMove || !searchData) {
      return
    }
    if (searchData.items.length === 0) {
      setPendingSearchPageMove(null)
      return
    }

    const targetIndex = pendingSearchPageMove === 'next' ? 0 : searchData.items.length - 1
    const session = searchData.items[targetIndex]?.session
    if (session) {
      setDetailSessionId(session.session_id)
      setPendingMatchTarget({ kind: pendingSearchPageMove === 'next' ? 'first' : 'last' })
    }
    setPendingSearchPageMove(null)
  }, [pendingSearchPageMove, searchData])

  useEffect(() => {
    if (detailMatchRanges.length === 0) {
      setActiveDetailMatchIndex(0)
      setPendingMatchTarget(null)
      return
    }

    if (pendingMatchTarget?.kind === 'first') {
      setActiveDetailMatchIndex(0)
      setPendingMatchTarget(null)
      return
    }
    if (pendingMatchTarget?.kind === 'last') {
      setActiveDetailMatchIndex(detailMatchRanges.length - 1)
      setPendingMatchTarget(null)
      return
    }

    if (pendingMatchTarget?.kind === 'exact') {
      const offsetIndex =
        pendingMatchTarget.matchOffset >= 0
          ? detailMatchRanges.findIndex((range) => range.start === pendingMatchTarget.matchOffset)
          : -1
      if (offsetIndex >= 0) {
        setActiveDetailMatchIndex(offsetIndex)
        setPendingMatchTarget(null)
        return
      }

      const clampedByIndex = Math.max(
        0,
        Math.min(detailMatchRanges.length - 1, pendingMatchTarget.matchIndex),
      )
      setActiveDetailMatchIndex(clampedByIndex)
      setPendingMatchTarget(null)
      return
    }

    setActiveDetailMatchIndex((current) => {
      if (current < 0) {
        return 0
      }
      if (current >= detailMatchRanges.length) {
        return detailMatchRanges.length - 1
      }
      return current
    })
  }, [detailMatchRanges, pendingMatchTarget])

  useEffect(() => {
    if (!activeMatchRef.current || detailMatchRanges.length === 0) {
      return
    }
    activeMatchRef.current.scrollIntoView({ block: 'center' })
  }, [detailSessionId, activeDetailMatchIndex, detailMatchRanges.length])

  function isActiveSession(item: TerminalWorkspaceSummary): boolean {
    if (!item.session) {
      return false
    }
    return (
      item.session.status === 'created' ||
      item.session.status === 'attached' ||
      item.session.status === 'detached'
    )
  }

  function resetSearchState() {
    setSearchInput('')
    setSearchQuery('')
    setSearchOffset(0)
    setSearchSort('relevance')
    setPendingSearchPageMove(null)
    setPendingMatchTarget(null)
  }

  function toggleTimeline(groupId: string) {
    setActionError(null)
    setActionNotice(null)
    if (timelineGroupId === groupId) {
      setTimelineGroupId(null)
      setTimelineOffset(0)
      setTimelineFilters(DEFAULT_TIMELINE_FILTERS)
      setActivePresetId(null)
      resetSearchState()
      setDetailSessionId(null)
      return
    }
    setTimelineGroupId(groupId)
    setTimelineOffset(0)
    setTimelineFilters(DEFAULT_TIMELINE_FILTERS)
    setActivePresetId(null)
    resetSearchState()
    setDetailSessionId(null)
  }

  function updateTimelineFilters(
    patch: Partial<{
      status: TerminalSessionStatus | ''
      ownerUserId: string
      sessionIdPrefix: string
      snapshotFromLocal: string
      snapshotToLocal: string
    }>,
    options?: {
      activePresetId?: TerminalTimeRangePresetId | null
    },
  ) {
    setTimelineFilters((current) => ({
      ...current,
      ...patch,
    }))
    if (options && 'activePresetId' in options) {
      setActivePresetId(options.activePresetId ?? null)
    }
    setTimelineOffset(0)
    setSearchOffset(0)
    setPendingSearchPageMove(null)
    setDetailSessionId(null)
    setPendingMatchTarget(null)
  }

  function updateArchiveFilters(
    patch: Partial<{
      groupNamePrefix: string
      groupIdPrefix: string
      chatAccessible: '' | 'true' | 'false'
      status: TerminalSessionStatus | ''
      ownerUserId: string
      sessionIdPrefix: string
      snapshotFromLocal: string
      snapshotToLocal: string
    }>,
  ) {
    setArchiveFilters((current) => ({
      ...current,
      ...patch,
    }))
  }

  function handlePresetTimeRange(presetId: TerminalTimeRangePresetId) {
    updateTimelineFilters(buildPresetLocalRange(presetId), { activePresetId: presetId })
  }

  function openDetailFromSearch(index: number, anchor: 'first' | 'last') {
    const session = searchItems[index]?.session
    if (!session) {
      return
    }
    setDetailSessionId(session.session_id)
    setPendingMatchTarget({ kind: anchor })
  }

  function openDetailFromSnippet(searchResultIndex: number, entry: TerminalSessionHistorySearchMatch, snippetIndex: number) {
    const session = searchItems[searchResultIndex]?.session
    if (!session) {
      return
    }
    const snippet = normalizeSnippetMatches(entry)[snippetIndex]
    if (!snippet) {
      return
    }

    setDetailSessionId(session.session_id)
    setPendingMatchTarget({
      kind: 'exact',
      matchIndex: snippet.match_index,
      matchOffset: snippet.match_offset,
    })
  }

  function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const normalized = searchInput.trim()
    setSearchQuery(normalized)
    setSearchOffset(0)
    setPendingSearchPageMove(null)
    setPendingMatchTarget({ kind: 'first' })
    setDetailSessionId(null)
  }

  function clearSearch() {
    resetSearchState()
  }

  function handleSearchSortChange(nextSort: TerminalHistorySearchSort) {
    setSearchSort(nextSort)
    setSearchOffset(0)
    setPendingSearchPageMove(null)
    setPendingMatchTarget(null)
    if (normalizedSearchQuery !== '') {
      setDetailSessionId(null)
    }
  }

  function goToPreviousMatch() {
    if (detailMatchRanges.length === 0) {
      return
    }
    if (activeDetailMatchIndex > 0) {
      setActiveDetailMatchIndex((value) => Math.max(0, value - 1))
      return
    }

    if (activeSearchResultIndex > 0) {
      openDetailFromSearch(activeSearchResultIndex - 1, 'last')
      return
    }

    if (activeSearchResultIndex === 0 && searchOffset > 0 && !isSearchFetching) {
      setPendingSearchPageMove('previous')
      setSearchOffset((value) => Math.max(0, value - SEARCH_PAGE_SIZE))
    }
  }

  function goToNextMatch() {
    if (detailMatchRanges.length === 0) {
      return
    }
    if (activeDetailMatchIndex < detailMatchRanges.length - 1) {
      setActiveDetailMatchIndex((value) => Math.min(detailMatchRanges.length - 1, value + 1))
      return
    }

    if (activeSearchResultIndex >= 0 && activeSearchResultIndex < searchItems.length - 1) {
      openDetailFromSearch(activeSearchResultIndex + 1, 'first')
      return
    }

    if (
      activeSearchResultIndex >= 0 &&
      activeSearchResultIndex === searchItems.length - 1 &&
      searchData?.has_more &&
      !isSearchFetching
    ) {
      setPendingSearchPageMove('next')
      setSearchOffset((value) => value + SEARCH_PAGE_SIZE)
    }
  }

  async function handleClose(item: TerminalWorkspaceSummary) {
    if (!token || !item.session) {
      return
    }
    const key = `close:${item.group_id}`
    try {
      setActionKey(key)
      setActionError(null)
      setActionNotice(null)
      await apiClient.closeCurrentTerminalSession(token, item.group_id)
      await refetch()
      if (timelineGroupId === item.group_id) {
        await refetchTimeline()
      }
      setActionNotice(`Closed terminal session for ${item.group_id}.`)
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to close terminal session.')
    } finally {
      setActionKey(null)
    }
  }

  async function handleForceClose(item: TerminalWorkspaceSummary) {
    if (!token || !item.session) {
      return
    }
    const key = `force:${item.group_id}`
    try {
      setActionKey(key)
      setActionError(null)
      setActionNotice(null)
      await apiClient.forceCloseCurrentTerminalSession(token, item.group_id)
      await refetch()
      if (timelineGroupId === item.group_id) {
        await refetchTimeline()
      }
      setActionNotice(`Force-closed terminal session for ${item.group_id}.`)
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to force-close terminal session.')
    } finally {
      setActionKey(null)
    }
  }

  async function runTerminalDownloadAction({
    actionKeyValue,
    request,
    fileName,
    successMessage,
    failureMessage,
  }: {
    actionKeyValue: string
    request: () => Promise<Blob>
    fileName: string
    successMessage: string
    failureMessage: string
  }) {
    try {
      setActionKey(actionKeyValue)
      setActionError(null)
      setActionNotice(null)
      const blob = await request()
      triggerBrowserDownload(blob, fileName)
      setActionNotice(successMessage)
    } catch (error) {
      setActionError(error instanceof Error ? error.message : failureMessage)
    } finally {
      setActionKey(null)
    }
  }

  async function handleExportOverview() {
    if (!token) {
      return
    }
    const key = 'export-overview'
    await runTerminalDownloadAction({
      actionKeyValue: key,
      fileName: buildTerminalOverviewExportFileName(),
      request: () => apiClient.downloadTerminalOverview(token),
      successMessage: `Exported terminal overview for ${items.length.toLocaleString()} workspaces.`,
      failureMessage: 'Failed to export terminal overview.',
    })
  }

  async function handleExportLatestHistories() {
    if (!token) {
      return
    }
    const key = 'export-latest-histories'
    await runTerminalDownloadAction({
      actionKeyValue: key,
      fileName: buildTerminalLatestHistoriesExportFileName(),
      request: () => apiClient.downloadTerminalLatestHistories(token),
      successMessage: 'Exported latest terminal histories.',
      failureMessage: 'Failed to export latest terminal histories.',
    })
  }

  async function handleExportHistoryArchive() {
    if (!token) {
      return
    }
    const key = 'export-history-archive'
    await runTerminalDownloadAction({
      actionKeyValue: key,
      fileName: buildTerminalHistoryArchiveBundleFileName(),
      request: () => apiClient.downloadTerminalHistoryArchiveBundle(token, archiveQueryOptions),
      successMessage: 'Exported terminal history archive bundle.',
      failureMessage: 'Failed to export terminal history archive bundle.',
    })
  }

  async function handleDownloadDetail(format: 'text' | 'json') {
    if (!token || !timelineGroupId || !detailSessionId) {
      return
    }
    const key = `download-detail:${format}:${timelineGroupId}:${detailSessionId}`
    await runTerminalDownloadAction({
      actionKeyValue: key,
      fileName: buildTerminalHistoryDownloadFileName(
        timelineGroupId,
        detailSessionId,
        format === 'json' ? 'json' : 'log',
      ),
      request: () => apiClient.downloadTerminalHistoryDetail(token, timelineGroupId, detailSessionId, format),
      successMessage:
        format === 'json'
          ? `Downloaded terminal history JSON for ${detailSessionId}.`
          : `Downloaded terminal history output for ${detailSessionId}.`,
      failureMessage:
        format === 'json'
          ? 'Failed to download terminal history JSON.'
          : 'Failed to download terminal history output.',
    })
  }

  async function handleExportTimelinePage() {
    if (!token || !timelineGroupId || !timelineData) {
      return
    }
    const key = `export-timeline:${timelineGroupId}:${timelineData.offset}:${timelineData.limit}`
    await runTerminalDownloadAction({
      actionKeyValue: key,
      fileName: buildTerminalHistoryExportFileName(
        timelineGroupId,
        timelineData.offset,
        timelineData.limit,
      ),
      request: () => apiClient.downloadTerminalHistoryExport(token, timelineGroupId, timelineQueryOptions),
      successMessage: `Exported ${timelineData.items.length.toLocaleString()} terminal history snapshots for ${timelineGroupId}.`,
      failureMessage: 'Failed to export the current terminal history page.',
    })
  }

  async function handleExportTimelineArchive() {
    if (!token || !timelineGroupId) {
      return
    }
    const key = `export-archive:${timelineGroupId}`
    await runTerminalDownloadAction({
      actionKeyValue: key,
      fileName: buildTerminalHistoryArchiveFileName(timelineGroupId),
      request: () => apiClient.downloadTerminalHistoryArchive(token, timelineGroupId, timelineArchiveQueryOptions),
      successMessage: `Exported terminal history archive for ${timelineGroupId}.`,
      failureMessage: 'Failed to export the terminal history archive.',
    })
  }

  async function handleExportSearchPage() {
    if (!token || !timelineGroupId || !searchData || normalizedSearchQuery === '') {
      return
    }
    const key = `export-search:${timelineGroupId}:${normalizedSearchQuery}:${searchData.offset}:${searchData.limit}:${searchSort}`
    await runTerminalDownloadAction({
      actionKeyValue: key,
      fileName: buildTerminalHistorySearchExportFileName(
        timelineGroupId,
        normalizedSearchQuery,
        searchData.offset,
        searchData.limit,
      ),
      request: () => apiClient.downloadTerminalHistorySearch(token, timelineGroupId, searchQueryOptions),
      successMessage: `Exported ${searchData.items.length.toLocaleString()} terminal history search results for ${timelineGroupId}.`,
      failureMessage: 'Failed to export the current terminal history search page.',
    })
  }

  async function handleExportSearchArchive() {
    if (!token || !timelineGroupId || normalizedSearchQuery === '') {
      return
    }
    const key = `export-search-archive:${timelineGroupId}:${normalizedSearchQuery}:${searchSort}`
    await runTerminalDownloadAction({
      actionKeyValue: key,
      fileName: buildTerminalHistorySearchArchiveFileName(
        timelineGroupId,
        normalizedSearchQuery,
      ),
      request: () => apiClient.downloadTerminalHistorySearchArchive(
        token,
        timelineGroupId,
        searchArchiveQueryOptions,
      ),
      successMessage: `Exported terminal history search archive for ${timelineGroupId}.`,
      failureMessage: 'Failed to export the terminal history search archive.',
    })
  }

  return (
    <AppLayout title="Terminals">
      {!isOperator ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Operator Access Required</h2>
          <p className="muted">This page is available to owner and admin roles only.</p>
        </section>
      ) : null}

      {isOperator && isLoading ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Loading Terminals</h2>
          <p className="muted">Fetching terminal overview across workspaces...</p>
        </section>
      ) : null}

      {isOperator && isForbidden ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Forbidden</h2>
          <p className="error-text">Your account does not have permission to view terminal overview data.</p>
        </section>
      ) : null}

      {isOperator && isError && !isForbidden ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Terminals Unavailable</h2>
          <p className="error-text">The terminal overview API is currently unreachable.</p>
        </section>
      ) : null}

      {isOperator && data ? (
        <div className="monitor-grid">
          {actionError ? (
            <section className="panel">
              <p className="error-text">{actionError}</p>
            </section>
          ) : null}
          {actionNotice ? (
            <section className="panel">
              <p className="muted">{actionNotice}</p>
            </section>
          ) : null}
          <section className="panel">
            <h2 style={{ marginTop: 0 }}>Session Summary</h2>
            <p className="muted" style={{ marginTop: 0 }}>
              Archive filters apply only to <strong>Export History Archive JSON</strong>.
            </p>
            <div className="settings-grid" style={{ marginBottom: '0.75rem' }}>
              <label>
                <span className="muted">Workspace Name Prefix</span>
                <input
                  onChange={(event) => updateArchiveFilters({ groupNamePrefix: event.target.value })}
                  placeholder="Project"
                  style={{ width: '100%', marginTop: '0.35rem' }}
                  type="text"
                  value={archiveFilters.groupNamePrefix}
                />
              </label>
              <label>
                <span className="muted">Workspace Prefix</span>
                <input
                  onChange={(event) => updateArchiveFilters({ groupIdPrefix: event.target.value })}
                  placeholder="project-"
                  style={{ width: '100%', marginTop: '0.35rem' }}
                  type="text"
                  value={archiveFilters.groupIdPrefix}
                />
              </label>
              <label>
                <span className="muted">Chat Access</span>
                <select
                  onChange={(event) =>
                    updateArchiveFilters({
                      chatAccessible: (event.target.value as '' | 'true' | 'false') || '',
                    })
                  }
                  style={{ width: '100%', marginTop: '0.35rem' }}
                  value={archiveFilters.chatAccessible}
                >
                  <option value="">All workspaces</option>
                  <option value="true">Chat accessible only</option>
                  <option value="false">No chat access</option>
                </select>
              </label>
              <label>
                <span className="muted">Status</span>
                <select
                  onChange={(event) =>
                    updateArchiveFilters({
                      status: (event.target.value as TerminalSessionStatus | '') || '',
                    })
                  }
                  style={{ width: '100%', marginTop: '0.35rem' }}
                  value={archiveFilters.status}
                >
                  <option value="">All statuses</option>
                  {TERMINAL_HISTORY_STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span className="muted">Owner User ID</span>
                <input
                  onChange={(event) => updateArchiveFilters({ ownerUserId: event.target.value })}
                  placeholder="owner-1"
                  style={{ width: '100%', marginTop: '0.35rem' }}
                  type="text"
                  value={archiveFilters.ownerUserId}
                />
              </label>
              <label>
                <span className="muted">Session ID Prefix</span>
                <input
                  onChange={(event) => updateArchiveFilters({ sessionIdPrefix: event.target.value })}
                  placeholder="terminal-session"
                  style={{ width: '100%', marginTop: '0.35rem' }}
                  type="text"
                  value={archiveFilters.sessionIdPrefix}
                />
              </label>
              <label>
                <span className="muted">Snapshot From</span>
                <input
                  onChange={(event) => updateArchiveFilters({ snapshotFromLocal: event.target.value })}
                  style={{ width: '100%', marginTop: '0.35rem' }}
                  type="datetime-local"
                  value={archiveFilters.snapshotFromLocal}
                />
              </label>
              <label>
                <span className="muted">Snapshot To</span>
                <input
                  onChange={(event) => updateArchiveFilters({ snapshotToLocal: event.target.value })}
                  style={{ width: '100%', marginTop: '0.35rem' }}
                  type="datetime-local"
                  value={archiveFilters.snapshotToLocal}
                />
              </label>
            </div>
            <div className="terminal-actions" style={{ marginBottom: '0.75rem' }}>
              <PrimaryButton
                className="button--ghost"
                disabled={actionKey !== null}
                onClick={() => void handleExportOverview()}
                type="button"
              >
                {actionKey === 'export-overview' ? 'Exporting...' : 'Export Overview JSON'}
              </PrimaryButton>
              <PrimaryButton
                className="button--ghost"
                disabled={actionKey !== null}
                onClick={() => void handleExportLatestHistories()}
                type="button"
              >
                {actionKey === 'export-latest-histories'
                  ? 'Exporting...'
                  : 'Export Latest Histories JSON'}
              </PrimaryButton>
              <PrimaryButton
                className="button--ghost"
                disabled={actionKey !== null}
                onClick={() => void handleExportHistoryArchive()}
                type="button"
              >
                {actionKey === 'export-history-archive'
                  ? 'Exporting...'
                  : 'Export History Archive JSON'}
              </PrimaryButton>
            </div>
            <div className="settings-grid">
              <div className="stat-card">
                <strong>Workspaces</strong>
                <p>{items.length}</p>
              </div>
              <div className="stat-card">
                <strong>Active</strong>
                <p>{summary.activeCount}</p>
              </div>
              <div className="stat-card">
                <strong>Detached</strong>
                <p>{summary.detachedCount}</p>
              </div>
              <div className="stat-card">
                <strong>Closed / Exited</strong>
                <p>{summary.closedCount}</p>
              </div>
              <div className="stat-card">
                <strong>No Session</strong>
                <p>{summary.emptyCount}</p>
              </div>
            </div>
          </section>

          <section className="panel">
            <h2 style={{ marginTop: 0 }}>Workspace Sessions</h2>
            {items.length === 0 ? <p className="muted">No canonical workspaces found.</p> : null}
            <div className="monitor-table-wrap">
              <table className="monitor-table">
                <thead>
                  <tr>
                    <th>Workspace</th>
                    <th>Session</th>
                    <th>Status</th>
                    <th>Owner</th>
                    <th>Backend</th>
                    <th>Container</th>
                    <th>Created</th>
                    <th>Last Attached</th>
                    <th>Reconnect Deadline</th>
                    <th>History Session</th>
                    <th>History Bytes</th>
                    <th>History Truncated</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 ? (
                    <tr>
                      <td className="muted" colSpan={13}>
                        Terminal overview is empty.
                      </td>
                    </tr>
                  ) : (
                    items.map((item) => (
                      <tr key={item.group_id}>
                        <td>
                          <strong>{item.group_name}</strong>
                          <br />
                          <span className="muted">{item.group_id}</span>
                        </td>
                        <td>{item.session?.session_id ?? '-'}</td>
                        <td>{item.session?.status ?? 'none'}</td>
                        <td>{item.session?.owner_user_id ?? '-'}</td>
                        <td>{item.session?.backend ?? '-'}</td>
                        <td>{item.session?.container_name ?? '-'}</td>
                        <td>{formatDate(item.session?.created_at ?? null)}</td>
                        <td>{formatDate(item.session?.last_attached_at ?? null)}</td>
                        <td>{formatDate(item.session?.reconnect_deadline ?? null)}</td>
                        <td>{item.history ? item.history.session.status : '-'}</td>
                        <td>{item.history ? item.history.output_bytes.toLocaleString() : '-'}</td>
                        <td>{item.history ? (item.history.truncated ? 'yes' : 'no') : '-'}</td>
                        <td>
                          <div className="terminal-actions">
                            {item.chat_accessible ? (
                              <Link
                                className="app-nav-link terminal-open-link"
                                to={`/chat?workspace=${encodeURIComponent(item.group_id)}`}
                              >
                                Open in Chat
                              </Link>
                            ) : (
                              <span className="muted">No chat access</span>
                            )}
                            {item.session &&
                            item.chat_accessible &&
                            currentUserId === item.session.owner_user_id &&
                            isActiveSession(item) ? (
                              <PrimaryButton
                                className="button--ghost"
                                disabled={actionKey !== null}
                                onClick={() => void handleClose(item)}
                                type="button"
                              >
                                {actionKey === `close:${item.group_id}` ? 'Closing...' : 'Close'}
                              </PrimaryButton>
                            ) : null}
                            {item.session && isActiveSession(item) ? (
                              <PrimaryButton
                                className="button--ghost"
                                disabled={actionKey !== null}
                                onClick={() => void handleForceClose(item)}
                                type="button"
                              >
                                {actionKey === `force:${item.group_id}` ? 'Closing...' : 'Force Close'}
                              </PrimaryButton>
                            ) : null}
                            <PrimaryButton
                              className="button--ghost"
                              disabled={actionKey !== null}
                              onClick={() => toggleTimeline(item.group_id)}
                              type="button"
                            >
                              {timelineGroupId === item.group_id ? 'Hide Timeline' : 'View Timeline'}
                            </PrimaryButton>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {timelineGroupId ? (
            <section className="panel">
              <h2 style={{ marginTop: 0 }}>History Timeline: {timelineGroupId}</h2>
              <div className="settings-grid" style={{ marginBottom: '1rem' }}>
                <div style={{ gridColumn: '1 / -1' }}>
                  <span className="muted">Preset Ranges</span>
                  <div className="terminal-actions" style={{ marginTop: '0.35rem' }}>
                    {TERMINAL_TIME_RANGE_PRESETS.map((preset) => (
                      <PrimaryButton
                        key={preset.id}
                        className={activePresetId === preset.id ? '' : 'button--ghost'}
                        onClick={() => handlePresetTimeRange(preset.id)}
                        type="button"
                      >
                        {preset.label}
                      </PrimaryButton>
                    ))}
                  </div>
                </div>
                <label>
                  <span className="muted">Status</span>
                  <select
                    onChange={(event) =>
                      updateTimelineFilters({
                        status: (event.target.value as TerminalSessionStatus | '') || '',
                      })
                    }
                    style={{ width: '100%', marginTop: '0.35rem' }}
                    value={timelineFilters.status}
                  >
                    <option value="">All statuses</option>
                    {TERMINAL_HISTORY_STATUS_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span className="muted">Owner User ID</span>
                  <input
                    onChange={(event) => updateTimelineFilters({ ownerUserId: event.target.value })}
                    placeholder="owner-1"
                    style={{ width: '100%', marginTop: '0.35rem' }}
                    type="text"
                    value={timelineFilters.ownerUserId}
                  />
                </label>
                <label>
                  <span className="muted">Session ID Prefix</span>
                  <input
                    onChange={(event) => updateTimelineFilters({ sessionIdPrefix: event.target.value })}
                    placeholder="terminal-session"
                    style={{ width: '100%', marginTop: '0.35rem' }}
                    type="text"
                    value={timelineFilters.sessionIdPrefix}
                  />
                </label>
                <label>
                  <span className="muted">Snapshot From</span>
                  <input
                    onChange={(event) =>
                      updateTimelineFilters(
                        { snapshotFromLocal: event.target.value },
                        { activePresetId: null },
                      )
                    }
                    style={{ width: '100%', marginTop: '0.35rem' }}
                    type="datetime-local"
                    value={timelineFilters.snapshotFromLocal}
                  />
                </label>
                <label>
                  <span className="muted">Snapshot To</span>
                  <input
                    onChange={(event) =>
                      updateTimelineFilters(
                        { snapshotToLocal: event.target.value },
                        { activePresetId: null },
                      )
                    }
                    style={{ width: '100%', marginTop: '0.35rem' }}
                    type="datetime-local"
                    value={timelineFilters.snapshotToLocal}
                  />
                </label>
              </div>

              <div
                style={{
                  border: '1px solid #d0d7de',
                  borderRadius: '0.5rem',
                  padding: '0.85rem',
                  marginBottom: '1rem',
                }}
              >
                <h3 style={{ margin: '0 0 0.75rem 0' }}>Search Output</h3>
                <form
                  onSubmit={handleSearchSubmit}
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                    marginBottom: '0.75rem',
                  }}
                >
                  <input
                    onChange={(event) => setSearchInput(event.target.value)}
                    placeholder="error"
                    style={{ flex: '1 1 16rem' }}
                    type="text"
                    value={searchInput}
                  />
                    <label>
                      <span className="muted">Sort</span>
                      <select
                        onChange={(event) =>
                          handleSearchSortChange(event.target.value as TerminalHistorySearchSort)
                        }
                      style={{ display: 'block', marginTop: '0.35rem' }}
                      value={searchSort}
                    >
                      <option value="relevance">Relevance</option>
                      <option value="newest">Newest</option>
                      <option value="oldest">Oldest</option>
                    </select>
                  </label>
                  <PrimaryButton type="submit">Search</PrimaryButton>
                  <PrimaryButton className="button--ghost" onClick={clearSearch} type="button">
                    Clear
                  </PrimaryButton>
                </form>

                {normalizedSearchQuery ? (
                  <p className="muted" style={{ marginTop: 0 }}>
                    Query: <code>{normalizedSearchQuery}</code>
                  </p>
                ) : (
                  <p className="muted" style={{ marginTop: 0 }}>
                    Submit a query to search output snippets in this workspace timeline.
                  </p>
                )}

                {normalizedSearchQuery && isSearchLoading ? (
                  <p className="muted">Searching terminal history output...</p>
                ) : null}
                {normalizedSearchQuery && isSearchError ? (
                  <p className="error-text">
                    {searchError instanceof Error ? searchError.message : 'Failed to search terminal history output.'}
                  </p>
                ) : null}
                {normalizedSearchQuery && !isSearchLoading && !isSearchError && searchData ? (
                  <>
                    <div className="terminal-actions" style={{ marginBottom: '0.75rem' }}>
                      <PrimaryButton
                        className="button--ghost"
                        disabled={actionKey !== null || isSearchFetching}
                        onClick={() => void handleExportSearchPage()}
                        type="button"
                      >
                        {actionKey ===
                        `export-search:${timelineGroupId}:${normalizedSearchQuery}:${searchData.offset}:${searchData.limit}:${searchSort}`
                          ? 'Exporting...'
                          : 'Export Search Page JSON'}
                      </PrimaryButton>
                      <PrimaryButton
                        className="button--ghost"
                        disabled={actionKey !== null || isSearchFetching}
                        onClick={() => void handleExportSearchArchive()}
                        type="button"
                      >
                        {actionKey ===
                        `export-search-archive:${timelineGroupId}:${normalizedSearchQuery}:${searchSort}`
                          ? 'Exporting...'
                          : 'Export Search Archive JSON'}
                      </PrimaryButton>
                    </div>
                    {searchData.items.length === 0 ? (
                      <p className="muted">No matched sessions in this workspace for the current query.</p>
                    ) : (
                      <div className="monitor-table-wrap">
                        <table className="monitor-table">
                          <thead>
                            <tr>
                              <th>Session</th>
                              <th>Status</th>
                              <th>Owner</th>
                              <th>Snapshot At</th>
                              <th>Matches</th>
                              <th>Snippets</th>
                              <th>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {searchData.items.map((entry, index) => (
                              <tr key={entry.session.session_id}>
                                <td>{entry.session.session_id}</td>
                                <td>{entry.session.status}</td>
                                <td>{entry.session.owner_user_id}</td>
                                <td>{formatDate(entry.snapshot_at)}</td>
                                <td>{entry.match_count.toLocaleString()}</td>
                                <td>
                                  <div style={{ display: 'grid', gap: '0.25rem' }}>
                                    {normalizeSnippetMatches(entry).map((snippet, snippetIndex) => (
                                      <button
                                        key={`${entry.session.session_id}-snippet-${snippetIndex}`}
                                        onClick={() => openDetailFromSnippet(index, entry, snippetIndex)}
                                        style={{
                                          background: '#fff',
                                          border: '1px solid #d0d7de',
                                          borderRadius: '0.35rem',
                                          cursor: 'pointer',
                                          fontFamily:
                                            'ui-monospace, SFMono-Regular, SF Mono, Menlo, Monaco, Consolas, Liberation Mono, Courier New, monospace',
                                          fontSize: '0.75rem',
                                          lineHeight: 1.45,
                                          padding: '0.2rem 0.35rem',
                                          textAlign: 'left',
                                        }}
                                        type="button"
                                      >
                                        {snippet.text}
                                      </button>
                                    ))}
                                  </div>
                                </td>
                                <td>
                                  <PrimaryButton
                                    className="button--ghost"
                                    onClick={() => openDetailFromSearch(index, 'first')}
                                    type="button"
                                  >
                                    {detailSessionId === entry.session.session_id ? 'Viewing' : 'View Details'}
                                  </PrimaryButton>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                    <div className="terminal-timeline-pagination" style={{ marginTop: '0.75rem' }}>
                      <span className="muted">
                        Offset {searchData.offset} · Page Size {searchData.limit} · Total {searchData.total}
                      </span>
                      <div className="terminal-actions">
                        <PrimaryButton
                          className="button--ghost"
                          disabled={searchOffset === 0 || isSearchFetching}
                          onClick={() => setSearchOffset((value) => Math.max(0, value - SEARCH_PAGE_SIZE))}
                          type="button"
                        >
                          Previous
                        </PrimaryButton>
                        <PrimaryButton
                          className="button--ghost"
                          disabled={!searchData.has_more || isSearchFetching}
                          onClick={() => setSearchOffset((value) => value + SEARCH_PAGE_SIZE)}
                          type="button"
                        >
                          Next
                        </PrimaryButton>
                      </div>
                    </div>
                  </>
                ) : null}
              </div>

              {isTimelineLoading ? <p className="muted">Loading timeline...</p> : null}
              {isTimelineError ? (
                <p className="error-text">
                  {timelineError instanceof Error ? timelineError.message : 'Failed to load timeline.'}
                </p>
              ) : null}
              {!isTimelineLoading && !isTimelineError && timelineData ? (
                <>
                  <div className="terminal-actions" style={{ marginBottom: '0.75rem' }}>
                    <PrimaryButton
                      className="button--ghost"
                      disabled={actionKey !== null || isTimelineFetching}
                      onClick={() => void handleExportTimelinePage()}
                      type="button"
                    >
                      {actionKey === `export-timeline:${timelineGroupId}:${timelineData.offset}:${timelineData.limit}`
                        ? 'Exporting...'
                        : 'Export Current Page JSON'}
                    </PrimaryButton>
                    <PrimaryButton
                      className="button--ghost"
                      disabled={actionKey !== null || isTimelineFetching}
                      onClick={() => void handleExportTimelineArchive()}
                      type="button"
                    >
                      {actionKey === `export-archive:${timelineGroupId}`
                        ? 'Exporting...'
                        : 'Export Archive JSON'}
                    </PrimaryButton>
                  </div>
                  <div className="monitor-table-wrap">
                    <table className="monitor-table">
                      <thead>
                        <tr>
                          <th>Session</th>
                          <th>Status</th>
                          <th>Owner</th>
                          <th>Snapshot At</th>
                          <th>Created</th>
                          <th>Output Bytes</th>
                          <th>Truncated</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {timelineData.items.length === 0 ? (
                          <tr>
                            <td className="muted" colSpan={7}>
                              Timeline is empty.
                            </td>
                          </tr>
                        ) : (
                          timelineData.items.map((entry) => (
                            <tr key={entry.session.session_id}>
                              <td>{entry.session.session_id}</td>
                              <td>{entry.session.status}</td>
                              <td>{entry.session.owner_user_id}</td>
                              <td>{formatDate(entry.snapshot_at)}</td>
                              <td>{formatDate(entry.session.created_at)}</td>
                              <td>{entry.output_bytes.toLocaleString()}</td>
                              <td>{entry.truncated ? 'yes' : 'no'}</td>
                              <td>
                                <PrimaryButton
                                  className="button--ghost"
                                  onClick={() => {
                                    setDetailSessionId(entry.session.session_id)
                                    setPendingMatchTarget({ kind: 'first' })
                                  }}
                                  type="button"
                                >
                                  {detailSessionId === entry.session.session_id ? 'Viewing' : 'View Details'}
                                </PrimaryButton>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                  <div className="terminal-timeline-pagination">
                    <span className="muted">
                      Offset {timelineData.offset} · Page Size {timelineData.limit}
                    </span>
                    <div className="terminal-actions">
                      <PrimaryButton
                        className="button--ghost"
                        disabled={timelineOffset === 0 || isTimelineFetching}
                        onClick={() => setTimelineOffset((value) => Math.max(0, value - TIMELINE_PAGE_SIZE))}
                        type="button"
                      >
                        Previous
                      </PrimaryButton>
                      <PrimaryButton
                        className="button--ghost"
                        disabled={!timelineData.has_more || isTimelineFetching}
                        onClick={() => setTimelineOffset((value) => value + TIMELINE_PAGE_SIZE)}
                        type="button"
                      >
                        Next
                      </PrimaryButton>
                    </div>
                  </div>
                </>
              ) : null}
            </section>
          ) : null}

          {timelineGroupId && detailSessionId ? (
            <section className="panel">
              <h2 style={{ marginTop: 0 }}>History Detail: {detailSessionId}</h2>
              {isDetailLoading ? <p className="muted">Loading terminal history detail...</p> : null}
              {isDetailError ? (
                <p className="error-text">
                  {detailError instanceof Error ? detailError.message : 'Failed to load terminal history detail.'}
                </p>
              ) : null}
              {detailData ? (
                <>
                  <div className="settings-grid" style={{ marginBottom: '1rem' }}>
                    <div className="stat-card">
                      <strong>Status</strong>
                      <p>{detailData.session.status}</p>
                    </div>
                    <div className="stat-card">
                      <strong>Owner</strong>
                      <p>{detailData.session.owner_user_id}</p>
                    </div>
                    <div className="stat-card">
                      <strong>Snapshot At</strong>
                      <p>{formatDate(detailData.snapshot_at)}</p>
                    </div>
                    <div className="stat-card">
                      <strong>Output Bytes</strong>
                      <p>{detailData.output_bytes.toLocaleString()}</p>
                    </div>
                  </div>

                  <div className="terminal-actions" style={{ marginBottom: '0.75rem' }}>
                    <PrimaryButton
                      className="button--ghost"
                      disabled={actionKey !== null}
                      onClick={() => void handleDownloadDetail('text')}
                      type="button"
                    >
                      {actionKey === `download-detail:text:${timelineGroupId}:${detailSessionId}`
                        ? 'Downloading...'
                        : 'Download Output'}
                    </PrimaryButton>
                    <PrimaryButton
                      className="button--ghost"
                      disabled={actionKey !== null}
                      onClick={() => void handleDownloadDetail('json')}
                      type="button"
                    >
                      {actionKey === `download-detail:json:${timelineGroupId}:${detailSessionId}`
                        ? 'Downloading...'
                        : 'Download JSON'}
                    </PrimaryButton>
                  </div>

                  {normalizedSearchQuery && detailMatchRanges.length > 0 ? (
                    <div
                      className="terminal-actions"
                      style={{ alignItems: 'center', marginBottom: '0.75rem' }}
                    >
                      <PrimaryButton
                        className="button--ghost"
                        disabled={!canMovePreviousMatch}
                        onClick={goToPreviousMatch}
                        type="button"
                      >
                        Previous Match
                      </PrimaryButton>
                      <PrimaryButton
                        className="button--ghost"
                        disabled={!canMoveNextMatch}
                        onClick={goToNextMatch}
                        type="button"
                      >
                        Next Match
                      </PrimaryButton>
                      <span className="muted">
                        Match {Math.min(activeDetailMatchIndex + 1, detailMatchRanges.length)} / {detailMatchRanges.length}
                      </span>
                    </div>
                  ) : null}

                  <pre
                    style={{
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      maxHeight: '24rem',
                      overflow: 'auto',
                    }}
                  >
                    {detailData.output === ''
                      ? '(no output)'
                      : detailOutputSegments.map((segment, index) => {
                          if (segment.matchIndex === null) {
                            return <span key={`segment-${index}`}>{segment.text}</span>
                          }
                          const isActive = segment.matchIndex === activeDetailMatchIndex
                          return (
                            <mark
                              key={`segment-${index}`}
                              ref={isActive ? activeMatchRef : undefined}
                              style={{
                                backgroundColor: isActive ? '#fbbf24' : '#fde68a',
                                color: 'inherit',
                                padding: 0,
                              }}
                            >
                              {segment.text}
                            </mark>
                          )
                        })}
                  </pre>
                </>
              ) : null}
            </section>
          ) : null}
        </div>
      ) : null}
    </AppLayout>
  )
}
