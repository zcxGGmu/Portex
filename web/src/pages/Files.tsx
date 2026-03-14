import { useEffect, useMemo, useState } from 'react'

import {
  apiClient,
  type GroupSummary,
  type WorkspaceFileEntry,
} from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import {
  useCurrentUserQuery,
  useGroupsQuery,
  useWorkspaceFileContentQuery,
  useWorkspaceFilesQuery,
} from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'
import { PrimaryButton } from '../components/ui/PrimaryButton'

const TEXT_FILE_EXTENSIONS = new Set([
  '.txt',
  '.md',
  '.py',
  '.json',
  '.toml',
  '.yaml',
  '.yml',
  '.js',
  '.ts',
  '.tsx',
  '.jsx',
  '.css',
  '.html',
  '.sh',
])

const PREVIEW_FILE_EXTENSIONS = new Set(['.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf'])

function getExtension(path: string): string {
  const segments = path.split('/')
  const fileName = segments[segments.length - 1] ?? path
  const index = fileName.lastIndexOf('.')
  return index >= 0 ? fileName.slice(index).toLowerCase() : ''
}

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString()
}

function parentPath(currentPath: string): string {
  if (!currentPath) {
    return ''
  }
  const parts = currentPath.split('/').filter(Boolean)
  parts.pop()
  return parts.join('/')
}

export function Files() {
  const token = useAuthStore((state) => state.token)
  const storedUser = useAuthStore((state) => state.currentUser)
  const { data: currentUserData } = useCurrentUserQuery()
  const currentUser = currentUserData ?? storedUser
  const canWrite = currentUser?.role === 'owner' || currentUser?.role === 'admin'

  const { data: groupsData, isLoading: groupsLoading, error: groupsError } = useGroupsQuery()
  const groups = useMemo(() => groupsData?.groups ?? [], [groupsData])
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null)
  const [currentPath, setCurrentPath] = useState('')
  const [selectedEntry, setSelectedEntry] = useState<WorkspaceFileEntry | null>(null)
  const [editorDraft, setEditorDraft] = useState('')
  const [actionError, setActionError] = useState<string | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isPreviewLoading, setIsPreviewLoading] = useState(false)

  useEffect(() => {
    if (!selectedGroupId && groups.length > 0) {
      setSelectedGroupId(groups[0].group_id)
    }
  }, [groups, selectedGroupId])

  useEffect(() => {
    setCurrentPath('')
    setSelectedEntry(null)
    setEditorDraft('')
    setActionError(null)
  }, [selectedGroupId])

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  const {
    data: filesData,
    isLoading: filesLoading,
    error: filesError,
    refetch: refetchFiles,
  } = useWorkspaceFilesQuery(selectedGroupId, currentPath)

  const selectedEntryExtension = selectedEntry ? getExtension(selectedEntry.path) : ''
  const isTextSelection =
    selectedEntry?.type === 'file' && TEXT_FILE_EXTENSIONS.has(selectedEntryExtension)
  const isPreviewSelection =
    selectedEntry?.type === 'file' && PREVIEW_FILE_EXTENSIONS.has(selectedEntryExtension)

  const {
    data: fileContentData,
    isLoading: fileContentLoading,
    error: fileContentError,
    refetch: refetchFileContent,
  } = useWorkspaceFileContentQuery(
    selectedGroupId,
    isTextSelection && selectedEntry ? selectedEntry.path : null,
    isTextSelection,
  )

  useEffect(() => {
    if (fileContentData) {
      setEditorDraft(fileContentData.content)
    }
  }, [fileContentData])

  useEffect(() => {
    if (!isPreviewSelection || !selectedEntry || !selectedGroupId || !token) {
      setPreviewUrl((currentPreviewUrl) => {
        if (currentPreviewUrl) {
          URL.revokeObjectURL(currentPreviewUrl)
        }
        return null
      })
      return
    }

    let cancelled = false
    setIsPreviewLoading(true)
    setActionError(null)
    apiClient
      .previewWorkspaceFile(token, selectedGroupId, selectedEntry.path)
      .then((blob) => {
        if (cancelled) {
          return
        }
        const objectUrl = URL.createObjectURL(blob)
        setPreviewUrl((currentPreviewUrl) => {
          if (currentPreviewUrl) {
            URL.revokeObjectURL(currentPreviewUrl)
          }
          return objectUrl
        })
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return
        }
        setActionError(error instanceof Error ? error.message : 'Failed to preview file')
      })
      .finally(() => {
        if (!cancelled) {
          setIsPreviewLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [isPreviewSelection, selectedEntry, selectedGroupId, token])

  const activeWorkspace = useMemo<GroupSummary | undefined>(
    () => groups.find((group) => group.group_id === selectedGroupId),
    [groups, selectedGroupId],
  )

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? [])
    if (!token || !selectedGroupId || files.length === 0) {
      return
    }
    setActionError(null)
    try {
      await apiClient.uploadWorkspaceFiles(token, selectedGroupId, currentPath, files)
      await refetchFiles()
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to upload files')
    } finally {
      event.target.value = ''
    }
  }

  async function handleSave() {
    if (!token || !selectedGroupId || !selectedEntry || !isTextSelection) {
      return
    }
    setActionError(null)
    try {
      await apiClient.updateWorkspaceFileContent(token, selectedGroupId, selectedEntry.path, editorDraft)
      await refetchFiles()
      await refetchFileContent()
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to save file')
    }
  }

  async function handleDelete(entry: WorkspaceFileEntry) {
    if (!token || !selectedGroupId) {
      return
    }
    setActionError(null)
    try {
      await apiClient.deleteWorkspaceFile(token, selectedGroupId, entry.path)
      if (selectedEntry?.path === entry.path) {
        setSelectedEntry(null)
        setEditorDraft('')
      }
      await refetchFiles()
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to delete file')
    }
  }

  async function handleDownload(entry: WorkspaceFileEntry) {
    if (!token || !selectedGroupId || entry.type !== 'file') {
      return
    }
    setActionError(null)
    try {
      const blob = await apiClient.downloadWorkspaceFile(token, selectedGroupId, entry.path)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = entry.name
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to download file')
    }
  }

  function handleEntrySelect(entry: WorkspaceFileEntry) {
    if (entry.type === 'directory') {
      setCurrentPath(entry.path)
      setSelectedEntry(null)
      setEditorDraft('')
      setActionError(null)
      return
    }
    setSelectedEntry(entry)
    setActionError(null)
  }

  return (
    <AppLayout title="Files">
      <section className="panel" style={{ marginBottom: '1rem' }}>
        <div className="files-toolbar">
          <div className="files-toolbar-group">
            <label className="field" htmlFor="workspace-select">
              <span>Workspace</span>
              <select
                id="workspace-select"
                onChange={(event) => setSelectedGroupId(event.target.value)}
                value={selectedGroupId ?? ''}
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
          </div>
          <div className="files-toolbar-actions">
            <PrimaryButton
              className="button--ghost"
              disabled={!currentPath}
              onClick={() => setCurrentPath(parentPath(currentPath))}
              type="button"
            >
              Up
            </PrimaryButton>
            <PrimaryButton className="button--ghost" onClick={() => refetchFiles()} type="button">
              Refresh
            </PrimaryButton>
            <label className={`button ${canWrite ? '' : 'button--disabled'}`}>
              Upload
              <input
                disabled={!canWrite || !selectedGroupId}
                hidden
                multiple
                onChange={handleUpload}
                type="file"
              />
            </label>
          </div>
        </div>
        <p className="muted" style={{ marginBottom: 0 }}>
          {activeWorkspace ? `${activeWorkspace.name} / ${currentPath || '/'}` : 'Select a workspace'}
        </p>
      </section>

      {groupsError ? (
        <section className="panel">
          <p className="error-text">
            {groupsError instanceof Error ? groupsError.message : 'Failed to load workspaces'}
          </p>
        </section>
      ) : null}

      <div className="files-layout">
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Directory</h2>
          {filesLoading ? <p className="muted">Loading files...</p> : null}
          {filesError ? (
            <p className="error-text">
              {filesError instanceof Error ? filesError.message : 'Failed to load files'}
            </p>
          ) : null}
          {!filesLoading && filesData?.entries.length === 0 ? <p className="muted">No files yet.</p> : null}
          <div className="files-list">
            {filesData?.entries.map((entry) => (
              <div className="files-list-row" key={entry.path}>
                <button className="files-entry-button" onClick={() => handleEntrySelect(entry)} type="button">
                  <strong>{entry.type === 'directory' ? `[DIR] ${entry.name}` : entry.name}</strong>
                  <span className="muted">
                    {entry.size} B · {formatDate(entry.modified_at)}
                  </span>
                </button>
                {entry.type === 'file' ? (
                  <PrimaryButton className="button--ghost" onClick={() => handleDownload(entry)} type="button">
                    Download
                  </PrimaryButton>
                ) : null}
                {canWrite ? (
                  <PrimaryButton className="button--ghost" onClick={() => handleDelete(entry)} type="button">
                    Delete
                  </PrimaryButton>
                ) : null}
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Preview</h2>
          {actionError ? <p className="error-text">{actionError}</p> : null}
          {!selectedEntry ? <p className="muted">Select a file or directory to inspect it.</p> : null}
          {selectedEntry?.type === 'directory' ? (
            <p className="muted">Directory selected. Use the list to enter it.</p>
          ) : null}
          {selectedEntry && isTextSelection ? (
            <>
              {fileContentLoading ? <p className="muted">Loading text content...</p> : null}
              {fileContentError ? (
                <p className="error-text">
                  {fileContentError instanceof Error ? fileContentError.message : 'Failed to load file content'}
                </p>
              ) : null}
              {!fileContentLoading ? (
                <>
                  <textarea
                    className="files-editor"
                    onChange={(event) => setEditorDraft(event.target.value)}
                    value={editorDraft}
                  />
                  {canWrite ? (
                    <div className="files-editor-actions">
                      <PrimaryButton onClick={handleSave} type="button">
                        Save
                      </PrimaryButton>
                    </div>
                  ) : null}
                </>
              ) : null}
            </>
          ) : null}
          {selectedEntry && isPreviewSelection ? (
            <>
              {isPreviewLoading ? <p className="muted">Loading preview...</p> : null}
              {previewUrl && selectedEntryExtension === '.pdf' ? (
                <iframe className="files-preview-frame" src={previewUrl} title={selectedEntry.name} />
              ) : null}
              {previewUrl && selectedEntryExtension !== '.pdf' ? (
                <img alt={selectedEntry.name} className="files-preview-image" src={previewUrl} />
              ) : null}
            </>
          ) : null}
          {selectedEntry && !isTextSelection && !isPreviewSelection && selectedEntry.type === 'file' ? (
            <p className="muted">Preview is not available for this file type. Use download instead.</p>
          ) : null}
        </section>
      </div>
    </AppLayout>
  )
}
