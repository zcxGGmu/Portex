import { type FormEvent, useMemo, useState } from 'react'

import { apiClient, type GroupSummary } from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import { PrimaryButton } from '../components/ui/PrimaryButton'
import {
  useGlobalMemoryQuery,
  useGroupsQuery,
  useWorkspaceMemoryFileQuery,
  useWorkspaceMemoryFilesQuery,
  useWorkspaceMemorySearchQuery,
} from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'

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

function todayMemoryFileName(): string {
  const now = new Date()
  const year = String(now.getFullYear())
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}.md`
}

export function Memory() {
  const token = useAuthStore((state) => state.token)
  const { data: groupsData, isLoading: groupsLoading, error: groupsError } = useGroupsQuery()
  const groups = useMemo(() => groupsData?.groups ?? [], [groupsData])
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null)
  const [selectedPath, setSelectedPath] = useState<string | null>(null)
  const [globalDraft, setGlobalDraft] = useState('')
  const [workspaceDraft, setWorkspaceDraft] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionNotice, setActionNotice] = useState<string | null>(null)
  const [isGlobalDirty, setIsGlobalDirty] = useState(false)
  const [isWorkspaceDirty, setIsWorkspaceDirty] = useState(false)
  const activeGroupId = selectedGroupId ?? groups[0]?.group_id ?? null

  const {
    data: globalMemoryData,
    isLoading: globalMemoryLoading,
    error: globalMemoryError,
    refetch: refetchGlobalMemory,
  } = useGlobalMemoryQuery()

  const {
    data: workspaceFilesData,
    isLoading: workspaceFilesLoading,
    error: workspaceFilesError,
    refetch: refetchWorkspaceFiles,
  } = useWorkspaceMemoryFilesQuery(activeGroupId)

  const {
    data: workspaceFileData,
    isLoading: workspaceFileLoading,
    error: workspaceFileError,
    refetch: refetchWorkspaceFile,
  } = useWorkspaceMemoryFileQuery(activeGroupId, selectedPath, Boolean(selectedPath))

  const {
    data: searchData,
    isLoading: searchLoading,
    error: searchError,
    refetch: refetchSearch,
  } = useWorkspaceMemorySearchQuery(activeGroupId, searchQuery, Boolean(searchQuery))

  const activeWorkspace = useMemo<GroupSummary | undefined>(
    () => groups.find((group) => group.group_id === activeGroupId),
    [groups, activeGroupId],
  )
  const resolvedGlobalDraft = isGlobalDirty ? globalDraft : (globalMemoryData?.content ?? '')
  const resolvedWorkspaceDraft = isWorkspaceDirty ? workspaceDraft : (workspaceFileData?.content ?? '')

  async function handleSaveGlobalMemory() {
    if (!token) {
      return
    }
    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.updateGlobalMemory(token, resolvedGlobalDraft)
      setGlobalDraft(resolvedGlobalDraft)
      setIsGlobalDirty(false)
      await refetchGlobalMemory()
      setActionNotice('Global memory saved.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to save global memory')
    }
  }

  async function handleSaveWorkspaceMemory() {
    if (!token || !activeGroupId || !selectedPath) {
      return
    }
    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.updateWorkspaceMemoryFile(
        token,
        activeGroupId,
        selectedPath,
        resolvedWorkspaceDraft,
      )
      setWorkspaceDraft(resolvedWorkspaceDraft)
      setIsWorkspaceDirty(false)
      await refetchWorkspaceFiles()
      await refetchWorkspaceFile()
      if (searchQuery) {
        await refetchSearch()
      }
      setActionNotice('Workspace memory file saved.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to save workspace memory')
    }
  }

  function handleOpenToday() {
    setSelectedPath(todayMemoryFileName())
    setIsWorkspaceDirty(false)
    setActionError(null)
    setActionNotice(null)
  }

  function handleWorkspaceChange(nextGroupId: string) {
    setSelectedGroupId(nextGroupId)
    setSelectedPath(null)
    setWorkspaceDraft('')
    setSearchInput('')
    setSearchQuery('')
    setActionError(null)
    setActionNotice(null)
    setIsWorkspaceDirty(false)
  }

  function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSearchQuery(searchInput.trim())
    setActionError(null)
    setActionNotice(null)
  }

  return (
    <AppLayout title="Memory">
      <section className="panel" style={{ marginBottom: '1rem' }}>
        <h2 style={{ marginTop: 0 }}>My Global Memory</h2>
        {globalMemoryLoading ? <p className="muted">Loading global memory...</p> : null}
        {globalMemoryError ? (
          <p className="error-text">
            {globalMemoryError instanceof Error ? globalMemoryError.message : 'Failed to load global memory'}
          </p>
        ) : null}
        <textarea
          className="memory-editor"
          onChange={(event) => {
            setGlobalDraft(event.target.value)
            setIsGlobalDirty(true)
          }}
          value={resolvedGlobalDraft}
        />
        <div className="memory-editor-actions">
          <PrimaryButton onClick={handleSaveGlobalMemory} type="button">
            Save Global Memory
          </PrimaryButton>
          <span className="muted">
            Updated: {formatDate(globalMemoryData?.updated_at ?? null)} · Size: {globalMemoryData?.size ?? 0} B
          </span>
        </div>
      </section>

      <section className="panel">
        <h2 style={{ marginTop: 0 }}>Workspace Memory</h2>
        <div className="memory-toolbar">
          <label className="field" htmlFor="memory-workspace-select">
            <span>Workspace</span>
            <select
              id="memory-workspace-select"
              onChange={(event) => handleWorkspaceChange(event.target.value)}
              value={activeGroupId ?? ''}
            >
              {groupsLoading ? <option value="">Loading...</option> : null}
              {!groupsLoading && groups.length === 0 ? <option value="">No workspaces</option> : null}
              {groups.map((group) => (
                <option key={group.group_id} value={group.group_id}>
                  {group.name}
                </option>
              ))}
            </select>
          </label>
          <div className="memory-toolbar-actions">
            <PrimaryButton className="button--ghost" onClick={handleOpenToday} type="button">
              Today
            </PrimaryButton>
            <PrimaryButton className="button--ghost" onClick={() => refetchWorkspaceFiles()} type="button">
              Refresh Files
            </PrimaryButton>
          </div>
        </div>

        <form className="memory-search-form" onSubmit={handleSearchSubmit}>
          <input
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search workspace memory..."
            type="text"
            value={searchInput}
          />
          <PrimaryButton type="submit">Search</PrimaryButton>
          <PrimaryButton
            className="button--ghost"
            onClick={() => {
              setSearchInput('')
              setSearchQuery('')
            }}
            type="button"
          >
            Clear
          </PrimaryButton>
        </form>

        <p className="muted">
          {activeWorkspace
            ? `${activeWorkspace.name} (${activeWorkspace.group_id})`
            : 'Select a workspace to manage memory'}
        </p>

        {groupsError ? (
          <p className="error-text">
            {groupsError instanceof Error ? groupsError.message : 'Failed to load workspaces'}
          </p>
        ) : null}
        {actionError ? <p className="error-text">{actionError}</p> : null}
        {actionNotice ? <p className="muted">{actionNotice}</p> : null}

        <div className="memory-layout">
          <aside className="memory-sidebar">
            <h3 style={{ marginTop: 0 }}>Files</h3>
            {workspaceFilesLoading ? <p className="muted">Loading files...</p> : null}
            {workspaceFilesError ? (
              <p className="error-text">
                {workspaceFilesError instanceof Error ? workspaceFilesError.message : 'Failed to load memory files'}
              </p>
            ) : null}
            {!workspaceFilesLoading && workspaceFilesData?.files.length === 0 ? (
              <p className="muted">No memory files yet.</p>
            ) : null}
            <div className="memory-file-list">
              {workspaceFilesData?.files.map((file) => (
                <button
                  className={`memory-file-button ${selectedPath === file.path ? 'active' : ''}`}
                  key={file.path}
                  onClick={() => {
                    setSelectedPath(file.path)
                    setWorkspaceDraft('')
                    setIsWorkspaceDirty(false)
                    setActionError(null)
                    setActionNotice(null)
                  }}
                  type="button"
                >
                  <strong>{file.path}</strong>
                  <span className="muted">
                    {formatDate(file.updated_at)} · {file.size} B
                  </span>
                </button>
              ))}
            </div>

            <h3>Search Hits</h3>
            {searchQuery && searchLoading ? <p className="muted">Searching...</p> : null}
            {searchError ? (
              <p className="error-text">
                {searchError instanceof Error ? searchError.message : 'Search failed'}
              </p>
            ) : null}
            {!searchQuery ? <p className="muted">Run a search to list hits.</p> : null}
            {searchQuery && !searchLoading && !searchData?.hits.length ? (
              <p className="muted">No matches.</p>
            ) : null}
            <div className="memory-file-list">
              {searchData?.hits.map((hit) => (
                <button
                  className={`memory-file-button ${selectedPath === hit.path ? 'active' : ''}`}
                  key={hit.path}
                  onClick={() => {
                    setSelectedPath(hit.path)
                    setWorkspaceDraft('')
                    setIsWorkspaceDirty(false)
                    setActionError(null)
                    setActionNotice(null)
                  }}
                  type="button"
                >
                  <strong>{hit.path}</strong>
                </button>
              ))}
            </div>
          </aside>

          <div>
            <h3 style={{ marginTop: 0 }}>{selectedPath ? `Editing: ${selectedPath}` : 'Note Editor'}</h3>
            {!selectedPath ? <p className="muted">Choose a file from the list, search hits, or click Today.</p> : null}
            {selectedPath && workspaceFileLoading ? <p className="muted">Loading note...</p> : null}
            {workspaceFileError ? (
              <p className="error-text">
                {workspaceFileError instanceof Error ? workspaceFileError.message : 'Failed to load note'}
              </p>
            ) : null}
            {selectedPath ? (
              <>
                <textarea
                  className="memory-editor"
                  onChange={(event) => {
                    setWorkspaceDraft(event.target.value)
                    setIsWorkspaceDirty(true)
                  }}
                  value={resolvedWorkspaceDraft}
                />
                <div className="memory-editor-actions">
                  <PrimaryButton onClick={handleSaveWorkspaceMemory} type="button">
                    Save Workspace Memory
                  </PrimaryButton>
                  <span className="muted">
                    Updated: {formatDate(workspaceFileData?.updated_at ?? null)} · Size: {workspaceFileData?.size ?? 0}{' '}
                    B
                  </span>
                </div>
              </>
            ) : null}
          </div>
        </div>
      </section>
    </AppLayout>
  )
}
