import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { apiClient } from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import { PrimaryButton } from '../components/ui/PrimaryButton'
import {
  useSettingsChannelsQuery,
  useSettingsProviderQuery,
  useSettingsSystemQuery,
} from '../hooks/useApi'
import { markSetupCompleted } from '../onboarding'
import { useAuthStore } from '../stores/auth'

type ExecutionMode = 'openai' | 'host' | 'container'

interface ProviderFormState {
  enabled: boolean
  base_url: string
  default_model: string
  api_key: string
}

interface ChannelsFormState {
  feishu_enabled: boolean
  feishu_app_id: string
  feishu_app_secret: string
  feishu_encrypt_key: string
  feishu_verification_token: string
  telegram_enabled: boolean
  telegram_bot_token: string
}

interface SystemFormState {
  default_execution_mode: ExecutionMode
  allow_host_execution: boolean
}

const SETUP_STEPS = ['Provider', 'Channels', 'System', 'Finish'] as const

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

export function Setup() {
  const navigate = useNavigate()
  const token = useAuthStore((state) => state.token)
  const currentUser = useAuthStore((state) => state.currentUser)
  const canReadSystemSettings = currentUser?.role === 'owner' || currentUser?.role === 'admin'
  const canWriteSystemSettings = currentUser?.role === 'owner'

  const {
    data: providerData,
    isLoading: providerLoading,
    error: providerError,
    refetch: refetchProvider,
  } = useSettingsProviderQuery()
  const {
    data: channelsData,
    isLoading: channelsLoading,
    error: channelsError,
    refetch: refetchChannels,
  } = useSettingsChannelsQuery()
  const {
    data: systemData,
    isLoading: systemLoading,
    error: systemError,
    refetch: refetchSystem,
  } = useSettingsSystemQuery(canReadSystemSettings)

  const [providerDraft, setProviderDraft] = useState<ProviderFormState | null>(null)
  const [channelsDraft, setChannelsDraft] = useState<ChannelsFormState | null>(null)
  const [systemDraft, setSystemDraft] = useState<SystemFormState | null>(null)
  const [stepIndex, setStepIndex] = useState(0)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionNotice, setActionNotice] = useState<string | null>(null)

  const providerForm: ProviderFormState =
    providerDraft ?? {
      enabled: providerData?.enabled ?? false,
      base_url: providerData?.base_url ?? '',
      default_model: providerData?.default_model ?? '',
      api_key: '',
    }

  const channelsForm: ChannelsFormState =
    channelsDraft ?? {
      feishu_enabled: channelsData?.feishu_enabled ?? false,
      feishu_app_id: channelsData?.feishu_app_id ?? '',
      feishu_app_secret: '',
      feishu_encrypt_key: '',
      feishu_verification_token: '',
      telegram_enabled: channelsData?.telegram_enabled ?? false,
      telegram_bot_token: '',
    }

  const systemForm: SystemFormState =
    systemDraft ?? {
      default_execution_mode: systemData?.default_execution_mode ?? 'openai',
      allow_host_execution: systemData?.allow_host_execution ?? false,
    }

  function goNextStep() {
    setStepIndex((current) => Math.min(current + 1, SETUP_STEPS.length - 1))
  }

  function goPreviousStep() {
    setStepIndex((current) => Math.max(current - 1, 0))
  }

  function handleSkipSetup() {
    markSetupCompleted()
    navigate('/chat', { replace: true })
  }

  function handleFinishSetup() {
    markSetupCompleted()
    navigate('/chat', { replace: true })
  }

  async function handleSaveProvider() {
    if (!token) {
      return
    }
    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.updateSettingsProvider(token, {
        enabled: providerForm.enabled,
        base_url: providerForm.base_url,
        default_model: providerForm.default_model,
        api_key: providerForm.api_key || undefined,
      })
      setProviderDraft(null)
      await refetchProvider()
      setActionNotice('Provider step saved.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to save provider settings')
    }
  }

  async function handleSaveChannels() {
    if (!token) {
      return
    }
    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.updateSettingsChannels(token, channelsForm)
      setChannelsDraft(null)
      await refetchChannels()
      setActionNotice('Channel step saved.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to save channel settings')
    }
  }

  async function handleSaveSystem() {
    if (!token || !canWriteSystemSettings) {
      return
    }
    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.updateSettingsSystem(token, systemForm)
      setSystemDraft(null)
      await refetchSystem()
      setActionNotice('System step saved.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to save system settings')
    }
  }

  return (
    <AppLayout title="Setup Wizard">
      <section className="panel setup-hero">
        <div>
          <h2 style={{ marginTop: 0, marginBottom: '0.5rem' }}>First-Run Onboarding</h2>
          <p className="muted" style={{ margin: 0 }}>
            Configure provider, channels, and runtime defaults before entering full workspace chat.
          </p>
        </div>
        <PrimaryButton className="button--ghost" onClick={handleSkipSetup} type="button">
          Skip For Now
        </PrimaryButton>
      </section>

      <section className="panel setup-progress-panel">
        <ol className="setup-progress">
          {SETUP_STEPS.map((step, index) => (
            <li key={step}>
              <button
                className={`setup-step-chip ${index === stepIndex ? 'active' : ''}`}
                onClick={() => setStepIndex(index)}
                type="button"
              >
                <span>{index + 1}</span>
                <strong>{step}</strong>
              </button>
            </li>
          ))}
        </ol>
      </section>

      {actionError ? <p className="error-text">{actionError}</p> : null}
      {actionNotice ? <p className="muted">{actionNotice}</p> : null}

      <section className="panel setup-step-panel">
        {stepIndex === 0 ? (
          <div className="setup-step-content">
            <h3>Step 1 · Provider</h3>
            <p className="muted">Set model provider base URL and default model for runtime calls.</p>
            {providerLoading ? <p className="muted">Loading provider settings...</p> : null}
            {providerError ? (
              <p className="error-text">
                {providerError instanceof Error ? providerError.message : 'Failed to load provider settings'}
              </p>
            ) : null}
            <div className="settings-form">
              <label className="settings-checkbox">
                <input
                  checked={providerForm.enabled}
                  onChange={(event) =>
                    setProviderDraft({ ...providerForm, enabled: event.target.checked })
                  }
                  type="checkbox"
                />
                Provider enabled
              </label>
              <div className="field">
                <label htmlFor="setup-provider-base-url">Base URL</label>
                <input
                  id="setup-provider-base-url"
                  onChange={(event) =>
                    setProviderDraft({ ...providerForm, base_url: event.target.value })
                  }
                  placeholder="https://api.example.com/v1"
                  type="text"
                  value={providerForm.base_url}
                />
              </div>
              <div className="field">
                <label htmlFor="setup-provider-default-model">Default Model</label>
                <input
                  id="setup-provider-default-model"
                  onChange={(event) =>
                    setProviderDraft({ ...providerForm, default_model: event.target.value })
                  }
                  placeholder="gpt-5.1"
                  type="text"
                  value={providerForm.default_model}
                />
              </div>
              <div className="field">
                <label htmlFor="setup-provider-api-key">API Key (optional replace)</label>
                <input
                  id="setup-provider-api-key"
                  onChange={(event) => setProviderDraft({ ...providerForm, api_key: event.target.value })}
                  placeholder={providerData?.has_api_key ? 'Stored (set new value to replace)' : 'sk-...'}
                  type="password"
                  value={providerForm.api_key}
                />
              </div>
            </div>
            <div className="setup-actions">
              <PrimaryButton onClick={handleSaveProvider} type="button">
                Save Provider
              </PrimaryButton>
              <span className="muted">Updated: {formatDate(providerData?.updated_at ?? null)}</span>
            </div>
          </div>
        ) : null}

        {stepIndex === 1 ? (
          <div className="setup-step-content">
            <h3>Step 2 · Channels</h3>
            <p className="muted">Configure Feishu and Telegram credentials for inbound/outbound message paths.</p>
            {channelsLoading ? <p className="muted">Loading channel settings...</p> : null}
            {channelsError ? (
              <p className="error-text">
                {channelsError instanceof Error ? channelsError.message : 'Failed to load channel settings'}
              </p>
            ) : null}
            <div className="settings-form">
              <label className="settings-checkbox">
                <input
                  checked={channelsForm.feishu_enabled}
                  onChange={(event) =>
                    setChannelsDraft({ ...channelsForm, feishu_enabled: event.target.checked })
                  }
                  type="checkbox"
                />
                Feishu enabled
              </label>
              <div className="field">
                <label htmlFor="setup-feishu-app-id">Feishu App ID</label>
                <input
                  id="setup-feishu-app-id"
                  onChange={(event) =>
                    setChannelsDraft({ ...channelsForm, feishu_app_id: event.target.value })
                  }
                  type="text"
                  value={channelsForm.feishu_app_id}
                />
              </div>
              <div className="field">
                <label htmlFor="setup-feishu-app-secret">Feishu App Secret (optional replace)</label>
                <input
                  id="setup-feishu-app-secret"
                  onChange={(event) =>
                    setChannelsDraft({ ...channelsForm, feishu_app_secret: event.target.value })
                  }
                  placeholder={
                    channelsData?.feishu_has_app_secret ? 'Stored (set new value to replace)' : ''
                  }
                  type="password"
                  value={channelsForm.feishu_app_secret}
                />
              </div>
              <div className="field">
                <label htmlFor="setup-feishu-encrypt-key">Feishu Encrypt Key (optional replace)</label>
                <input
                  id="setup-feishu-encrypt-key"
                  onChange={(event) =>
                    setChannelsDraft({ ...channelsForm, feishu_encrypt_key: event.target.value })
                  }
                  placeholder={
                    channelsData?.feishu_has_encrypt_key ? 'Stored (set new value to replace)' : ''
                  }
                  type="password"
                  value={channelsForm.feishu_encrypt_key}
                />
              </div>
              <div className="field">
                <label htmlFor="setup-feishu-verification-token">
                  Feishu Verification Token (optional replace)
                </label>
                <input
                  id="setup-feishu-verification-token"
                  onChange={(event) =>
                    setChannelsDraft({
                      ...channelsForm,
                      feishu_verification_token: event.target.value,
                    })
                  }
                  placeholder={
                    channelsData?.feishu_has_verification_token
                      ? 'Stored (set new value to replace)'
                      : ''
                  }
                  type="password"
                  value={channelsForm.feishu_verification_token}
                />
              </div>
              <label className="settings-checkbox">
                <input
                  checked={channelsForm.telegram_enabled}
                  onChange={(event) =>
                    setChannelsDraft({ ...channelsForm, telegram_enabled: event.target.checked })
                  }
                  type="checkbox"
                />
                Telegram enabled
              </label>
              <div className="field">
                <label htmlFor="setup-telegram-token">Telegram Bot Token (optional replace)</label>
                <input
                  id="setup-telegram-token"
                  onChange={(event) =>
                    setChannelsDraft({ ...channelsForm, telegram_bot_token: event.target.value })
                  }
                  placeholder={
                    channelsData?.telegram_has_bot_token ? 'Stored (set new value to replace)' : ''
                  }
                  type="password"
                  value={channelsForm.telegram_bot_token}
                />
              </div>
            </div>
            <div className="setup-actions">
              <PrimaryButton onClick={handleSaveChannels} type="button">
                Save Channels
              </PrimaryButton>
              <span className="muted">Updated: {formatDate(channelsData?.updated_at ?? null)}</span>
            </div>
          </div>
        ) : null}

        {stepIndex === 2 ? (
          <div className="setup-step-content">
            <h3>Step 3 · System</h3>
            <p className="muted">
              Configure runtime defaults. Only owner can modify this step in current permission policy.
            </p>
            {!canReadSystemSettings ? (
              <p className="muted">Current role cannot read system settings. Continue to finish onboarding.</p>
            ) : (
              <>
                {systemLoading ? <p className="muted">Loading system settings...</p> : null}
                {systemError ? (
                  <p className="error-text">
                    {systemError instanceof Error ? systemError.message : 'Failed to load system settings'}
                  </p>
                ) : null}
                <div className="settings-form">
                  <div className="field">
                    <label htmlFor="setup-system-default-mode">Default Execution Mode</label>
                    <select
                      disabled={!canWriteSystemSettings}
                      id="setup-system-default-mode"
                      onChange={(event) =>
                        setSystemDraft({
                          ...systemForm,
                          default_execution_mode: event.target.value as ExecutionMode,
                        })
                      }
                      value={systemForm.default_execution_mode}
                    >
                      <option value="openai">openai</option>
                      <option value="host">host</option>
                      <option value="container">container</option>
                    </select>
                  </div>
                  <label className="settings-checkbox">
                    <input
                      checked={systemForm.allow_host_execution}
                      disabled={!canWriteSystemSettings}
                      onChange={(event) =>
                        setSystemDraft({
                          ...systemForm,
                          allow_host_execution: event.target.checked,
                        })
                      }
                      type="checkbox"
                    />
                    Allow host execution
                  </label>
                </div>
                <div className="setup-actions">
                  <PrimaryButton
                    disabled={!canWriteSystemSettings}
                    onClick={handleSaveSystem}
                    type="button"
                  >
                    Save System
                  </PrimaryButton>
                  <span className="muted">Updated: {formatDate(systemData?.updated_at ?? null)}</span>
                </div>
              </>
            )}
          </div>
        ) : null}

        {stepIndex === 3 ? (
          <div className="setup-step-content">
            <h3>Step 4 · Finish</h3>
            <p className="muted">
              Setup baseline is ready. You can continue into workspace chat or fine-tune all configs in Settings.
            </p>
            <div className="settings-grid">
              <div className="stat-card">
                <strong>Provider</strong>
                <p>
                  {providerData?.enabled ? 'Enabled' : 'Disabled'} · model: {providerData?.default_model ?? '-'}
                </p>
              </div>
              <div className="stat-card">
                <strong>Channels</strong>
                <p>
                  Feishu {channelsData?.feishu_enabled ? 'on' : 'off'} · Telegram{' '}
                  {channelsData?.telegram_enabled ? 'on' : 'off'}
                </p>
              </div>
              <div className="stat-card">
                <strong>System Mode</strong>
                <p>{systemData?.default_execution_mode ?? 'openai'}</p>
              </div>
              <div className="stat-card">
                <strong>Role</strong>
                <p>{currentUser?.role ?? '-'}</p>
              </div>
            </div>
            <div className="setup-link-row">
              <Link className="app-nav-link" to="/settings">
                Open Full Settings
              </Link>
              <Link className="app-nav-link" to="/chat">
                Open Chat
              </Link>
            </div>
            <div className="setup-actions">
              <PrimaryButton onClick={handleFinishSetup} type="button">
                Finish And Enter Chat
              </PrimaryButton>
            </div>
          </div>
        ) : null}

        <div className="setup-nav-actions">
          <PrimaryButton className="button--ghost" disabled={stepIndex === 0} onClick={goPreviousStep} type="button">
            Back
          </PrimaryButton>
          {stepIndex < SETUP_STEPS.length - 1 ? (
            <PrimaryButton onClick={goNextStep} type="button">
              Next
            </PrimaryButton>
          ) : null}
        </div>
      </section>
    </AppLayout>
  )
}

