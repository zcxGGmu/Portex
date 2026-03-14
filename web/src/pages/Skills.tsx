import { useMemo, useState } from 'react'

import { apiClient } from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import { PrimaryButton } from '../components/ui/PrimaryButton'
import { useSkillDetailQuery, useSkillsQuery } from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'

const SKILL_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*$/

const DEFAULT_SKILL_TEMPLATE = `---
name: New Skill
description: Add a concise skill description.
---

# New Skill

Describe how this skill should guide behavior.
`

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

export function Skills() {
  const token = useAuthStore((state) => state.token)
  const {
    data: skillsData,
    isLoading: skillsLoading,
    error: skillsError,
    refetch: refetchSkills,
  } = useSkillsQuery()
  const skills = useMemo(() => skillsData?.skills ?? [], [skillsData])
  const [selectedSkillId, setSelectedSkillId] = useState<string | null>(null)
  const [createSkillId, setCreateSkillId] = useState('')
  const [editorDraft, setEditorDraft] = useState('')
  const [isDirty, setIsDirty] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionNotice, setActionNotice] = useState<string | null>(null)
  const activeSkillId = useMemo(() => {
    if (selectedSkillId && skills.some((skill) => skill.skill_id === selectedSkillId)) {
      return selectedSkillId
    }
    return skills[0]?.skill_id ?? null
  }, [selectedSkillId, skills])

  const {
    data: skillDetail,
    isLoading: skillLoading,
    error: skillError,
    refetch: refetchSkill,
  } = useSkillDetailQuery(activeSkillId, Boolean(activeSkillId))

  const resolvedDraft = isDirty ? editorDraft : (skillDetail?.content ?? '')

  async function handleCreateSkill() {
    if (!token) {
      return
    }

    const normalizedSkillId = createSkillId.trim()
    if (!SKILL_ID_PATTERN.test(normalizedSkillId)) {
      setActionError('Skill id must match [A-Za-z0-9][A-Za-z0-9._-]*')
      setActionNotice(null)
      return
    }

    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.updateSkill(token, normalizedSkillId, DEFAULT_SKILL_TEMPLATE)
      setCreateSkillId('')
      setSelectedSkillId(normalizedSkillId)
      setEditorDraft('')
      setIsDirty(false)
      await refetchSkills()
      await refetchSkill()
      setActionNotice('Skill created.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to create skill')
    }
  }

  async function handleSaveSkill() {
    if (!token || !activeSkillId) {
      return
    }

    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.updateSkill(token, activeSkillId, resolvedDraft)
      setEditorDraft(resolvedDraft)
      setIsDirty(false)
      await refetchSkills()
      await refetchSkill()
      setActionNotice('Skill saved.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to save skill')
    }
  }

  async function handleToggleSkillState() {
    if (!token || !activeSkillId || !skillDetail) {
      return
    }

    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.updateSkillState(token, activeSkillId, !skillDetail.enabled)
      await refetchSkills()
      await refetchSkill()
      setActionNotice(skillDetail.enabled ? 'Skill disabled.' : 'Skill enabled.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to update skill state')
    }
  }

  async function handleDeleteSkill() {
    if (!token || !activeSkillId) {
      return
    }

    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.deleteSkill(token, activeSkillId)
      setEditorDraft('')
      setIsDirty(false)
      setSelectedSkillId(null)
      await refetchSkills()
      setActionNotice('Skill deleted.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to delete skill')
    }
  }

  return (
    <AppLayout title="Skills">
      <section className="panel">
        <h2 style={{ marginTop: 0 }}>My Skills</h2>
        <div className="memory-toolbar">
          <div className="field" style={{ minWidth: '260px' }}>
            <span>New Skill ID</span>
            <input
              onChange={(event) => setCreateSkillId(event.target.value)}
              placeholder="writer-guide"
              type="text"
              value={createSkillId}
            />
          </div>
          <div className="memory-toolbar-actions">
            <PrimaryButton onClick={handleCreateSkill} type="button">
              Create
            </PrimaryButton>
            <PrimaryButton className="button--ghost" onClick={() => refetchSkills()} type="button">
              Refresh
            </PrimaryButton>
          </div>
        </div>

        {actionError ? <p className="error-text">{actionError}</p> : null}
        {actionNotice ? <p className="muted">{actionNotice}</p> : null}

        <div className="memory-layout">
          <aside className="memory-sidebar">
            <h3 style={{ marginTop: 0 }}>Skill List</h3>
            {skillsLoading ? <p className="muted">Loading skills...</p> : null}
            {skillsError ? (
              <p className="error-text">
                {skillsError instanceof Error ? skillsError.message : 'Failed to load skills'}
              </p>
            ) : null}
            {!skillsLoading && skills.length === 0 ? <p className="muted">No skills yet.</p> : null}
            <div className="memory-file-list">
              {skills.map((skill) => (
                <button
                  className={`memory-file-button ${activeSkillId === skill.skill_id ? 'active' : ''}`}
                  key={skill.skill_id}
                  onClick={() => {
                    setSelectedSkillId(skill.skill_id)
                    setEditorDraft('')
                    setIsDirty(false)
                    setActionError(null)
                    setActionNotice(null)
                  }}
                  type="button"
                >
                  <strong>{skill.skill_id}</strong>
                  <span className="muted">
                    {skill.enabled ? 'Enabled' : 'Disabled'} · {formatDate(skill.updated_at)} · {skill.size} B
                  </span>
                </button>
              ))}
            </div>
          </aside>

          <div>
            <h3 style={{ marginTop: 0 }}>{activeSkillId ? `Editing: ${activeSkillId}` : 'Skill Editor'}</h3>
            {!activeSkillId ? <p className="muted">Create a skill or select one from the list.</p> : null}
            {activeSkillId && skillLoading ? <p className="muted">Loading skill...</p> : null}
            {skillError ? (
              <p className="error-text">
                {skillError instanceof Error ? skillError.message : 'Failed to load skill'}
              </p>
            ) : null}
            {activeSkillId && skillDetail ? (
              <>
                <div className="memory-toolbar-actions" style={{ marginBottom: '0.75rem' }}>
                  <PrimaryButton className="button--ghost" onClick={handleToggleSkillState} type="button">
                    {skillDetail.enabled ? 'Disable' : 'Enable'}
                  </PrimaryButton>
                  <PrimaryButton className="button--ghost" onClick={handleDeleteSkill} type="button">
                    Delete
                  </PrimaryButton>
                </div>
                <textarea
                  className="memory-editor"
                  onChange={(event) => {
                    setEditorDraft(event.target.value)
                    setIsDirty(true)
                  }}
                  value={resolvedDraft}
                />
                <div className="memory-editor-actions">
                  <PrimaryButton onClick={handleSaveSkill} type="button">
                    Save Skill
                  </PrimaryButton>
                  <span className="muted">
                    State: {skillDetail.enabled ? 'enabled' : 'disabled'} · Updated:{' '}
                    {formatDate(skillDetail.updated_at)} · Size: {skillDetail.size} B
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
