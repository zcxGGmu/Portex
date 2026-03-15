import { useState } from 'react'

import { apiClient } from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import { PrimaryButton } from '../components/ui/PrimaryButton'
import {
  useCurrentUserQuery,
  useSettingsAppearanceQuery,
  useSettingsChannelsQuery,
  useSettingsProviderQuery,
  useSettingsRegistrationQuery,
  useSettingsSystemQuery,
} from '../hooks/useApi'
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

interface RegistrationFormState {
  allow_registration: boolean
  require_invite_code: boolean
}

interface AppearanceFormState {
  app_name: string
  ai_name: string
  ai_avatar_emoji: string
  ai_avatar_color: string
}

interface SystemFormState {
  default_execution_mode: ExecutionMode
  allow_host_execution: boolean
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

export function Settings() {
  const storedUser = useAuthStore((state) => state.currentUser)
  const token = useAuthStore((state) => state.token)
  const { data, isLoading } = useCurrentUserQuery()
  const currentUser = data ?? storedUser
  const tokenPreview = token ? `${token.slice(0, 24)}...` : 'Not available'

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
    data: registrationData,
    isLoading: registrationLoading,
    error: registrationError,
    refetch: refetchRegistration,
  } = useSettingsRegistrationQuery(canReadSystemSettings)
  const {
    data: appearanceData,
    isLoading: appearanceLoading,
    error: appearanceError,
    refetch: refetchAppearance,
  } = useSettingsAppearanceQuery(canReadSystemSettings)
  const {
    data: systemData,
    isLoading: systemLoading,
    error: systemError,
    refetch: refetchSystem,
  } = useSettingsSystemQuery(canReadSystemSettings)

  const [providerDraft, setProviderDraft] = useState<ProviderFormState | null>(null)
  const [channelsDraft, setChannelsDraft] = useState<ChannelsFormState | null>(null)
  const [registrationDraft, setRegistrationDraft] = useState<RegistrationFormState | null>(null)
  const [appearanceDraft, setAppearanceDraft] = useState<AppearanceFormState | null>(null)
  const [systemDraft, setSystemDraft] = useState<SystemFormState | null>(null)

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

  const registrationForm: RegistrationFormState =
    registrationDraft ?? {
      allow_registration: registrationData?.allow_registration ?? true,
      require_invite_code: registrationData?.require_invite_code ?? false,
    }

  const appearanceForm: AppearanceFormState =
    appearanceDraft ?? {
      app_name: appearanceData?.app_name ?? 'Portex',
      ai_name: appearanceData?.ai_name ?? 'Portex',
      ai_avatar_emoji: appearanceData?.ai_avatar_emoji ?? '🤖',
      ai_avatar_color: appearanceData?.ai_avatar_color ?? '#0ea5e9',
    }

  const systemForm: SystemFormState =
    systemDraft ?? {
      default_execution_mode: systemData?.default_execution_mode ?? 'openai',
      allow_host_execution: systemData?.allow_host_execution ?? false,
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
      setActionNotice('Provider settings saved.')
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
      setActionNotice('Channel settings saved.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to save channel settings')
    }
  }

  async function handleSaveRegistrationPolicy() {
    if (!token || !canWriteSystemSettings) {
      return
    }

    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.updateSettingsRegistration(
        token,
        registrationForm.allow_registration,
        registrationForm.require_invite_code,
      )
      setRegistrationDraft(null)
      await refetchRegistration()
      setActionNotice('Registration policy saved.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to save registration policy')
    }
  }

  async function handleSaveAppearance() {
    if (!token || !canWriteSystemSettings) {
      return
    }

    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.updateSettingsAppearance(token, appearanceForm)
      setAppearanceDraft(null)
      await refetchAppearance()
      setActionNotice('Appearance settings saved.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to save appearance settings')
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
      setActionNotice('System settings saved.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to save system settings')
    }
  }

  return (
    <AppLayout title="Settings">
      <section className="panel">
        <h2 style={{ marginTop: 0 }}>Account</h2>
        <div className="settings-grid">
          <div className="stat-card">
            <strong>Username</strong>
            <p>{isLoading ? 'Loading...' : currentUser?.username ?? 'Unknown'}</p>
          </div>
          <div className="stat-card">
            <strong>Role</strong>
            <p>{isLoading ? 'Loading...' : currentUser?.role ?? 'Unknown'}</p>
          </div>
          <div className="stat-card">
            <strong>Status</strong>
            <p>{isLoading ? 'Loading...' : currentUser?.status ?? 'Unknown'}</p>
          </div>
          <div className="stat-card token-preview">
            <strong>Token Preview</strong>
            <p>{tokenPreview}</p>
          </div>
        </div>
      </section>

      <section className="panel settings-panel">
        <h2 style={{ marginTop: 0 }}>Configuration</h2>
        <p className="muted" style={{ marginTop: 0 }}>
          Provider and channel settings are user-scoped. Registration, appearance, and system settings
          are owner-managed.
        </p>

        {actionError ? <p className="error-text">{actionError}</p> : null}
        {actionNotice ? <p className="muted">{actionNotice}</p> : null}

        <div className="settings-sections">
          <div className="settings-section">
            <h3>Provider Config</h3>
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
                <label htmlFor="provider-base-url">Base URL</label>
                <input
                  id="provider-base-url"
                  onChange={(event) =>
                    setProviderDraft({ ...providerForm, base_url: event.target.value })
                  }
                  placeholder="https://api.example.com/v1"
                  type="text"
                  value={providerForm.base_url}
                />
              </div>
              <div className="field">
                <label htmlFor="provider-default-model">Default Model</label>
                <input
                  id="provider-default-model"
                  onChange={(event) =>
                    setProviderDraft({ ...providerForm, default_model: event.target.value })
                  }
                  placeholder="gpt-5.1"
                  type="text"
                  value={providerForm.default_model}
                />
              </div>
              <div className="field">
                <label htmlFor="provider-api-key">API Key (leave blank to keep existing)</label>
                <input
                  id="provider-api-key"
                  onChange={(event) => setProviderDraft({ ...providerForm, api_key: event.target.value })}
                  placeholder={providerData?.has_api_key ? 'Stored (set new value to replace)' : 'sk-...'}
                  type="password"
                  value={providerForm.api_key}
                />
              </div>
              <div className="settings-row">
                <PrimaryButton onClick={handleSaveProvider} type="button">
                  Save Provider
                </PrimaryButton>
                <span className="muted">Updated: {formatDate(providerData?.updated_at ?? null)}</span>
              </div>
            </div>
          </div>

          <div className="settings-section">
            <h3>Channel Config</h3>
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
                <label htmlFor="feishu-app-id">Feishu App ID</label>
                <input
                  id="feishu-app-id"
                  onChange={(event) =>
                    setChannelsDraft({ ...channelsForm, feishu_app_id: event.target.value })
                  }
                  type="text"
                  value={channelsForm.feishu_app_id}
                />
              </div>
              <div className="field">
                <label htmlFor="feishu-app-secret">Feishu App Secret (optional replace)</label>
                <input
                  id="feishu-app-secret"
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
                <label htmlFor="feishu-encrypt-key">Feishu Encrypt Key (optional replace)</label>
                <input
                  id="feishu-encrypt-key"
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
                <label htmlFor="feishu-verification-token">Feishu Verification Token (optional replace)</label>
                <input
                  id="feishu-verification-token"
                  onChange={(event) =>
                    setChannelsDraft({ ...channelsForm, feishu_verification_token: event.target.value })
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
                <label htmlFor="telegram-bot-token">Telegram Bot Token (optional replace)</label>
                <input
                  id="telegram-bot-token"
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
              <div className="settings-row">
                <PrimaryButton onClick={handleSaveChannels} type="button">
                  Save Channels
                </PrimaryButton>
                <span className="muted">Updated: {formatDate(channelsData?.updated_at ?? null)}</span>
              </div>
            </div>
          </div>

          <div className="settings-section">
            <h3>Registration Policy</h3>
            {!canReadSystemSettings ? (
              <p className="muted">Your role cannot read system-managed settings.</p>
            ) : (
              <>
                {registrationLoading ? <p className="muted">Loading registration policy...</p> : null}
                {registrationError ? (
                  <p className="error-text">
                    {registrationError instanceof Error
                      ? registrationError.message
                      : 'Failed to load registration policy'}
                  </p>
                ) : null}
                <div className="settings-form">
                  <label className="settings-checkbox">
                    <input
                      checked={registrationForm.allow_registration}
                      disabled={!canWriteSystemSettings}
                      onChange={(event) =>
                        setRegistrationDraft({
                          ...registrationForm,
                          allow_registration: event.target.checked,
                        })
                      }
                      type="checkbox"
                    />
                    Allow new registrations
                  </label>
                  <label className="settings-checkbox">
                    <input
                      checked={registrationForm.require_invite_code}
                      disabled={!canWriteSystemSettings}
                      onChange={(event) =>
                        setRegistrationDraft({
                          ...registrationForm,
                          require_invite_code: event.target.checked,
                        })
                      }
                      type="checkbox"
                    />
                    Require invite code
                  </label>
                  <div className="settings-row">
                    <PrimaryButton
                      disabled={!canWriteSystemSettings}
                      onClick={handleSaveRegistrationPolicy}
                      type="button"
                    >
                      Save Policy
                    </PrimaryButton>
                    <span className="muted">Updated: {formatDate(registrationData?.updated_at ?? null)}</span>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="settings-section">
            <h3>Appearance</h3>
            {!canReadSystemSettings ? (
              <p className="muted">Your role cannot read system-managed settings.</p>
            ) : (
              <>
                {appearanceLoading ? <p className="muted">Loading appearance settings...</p> : null}
                {appearanceError ? (
                  <p className="error-text">
                    {appearanceError instanceof Error
                      ? appearanceError.message
                      : 'Failed to load appearance settings'}
                  </p>
                ) : null}
                <div className="settings-form">
                  <div className="field">
                    <label htmlFor="appearance-app-name">App Name</label>
                    <input
                      disabled={!canWriteSystemSettings}
                      id="appearance-app-name"
                      onChange={(event) =>
                        setAppearanceDraft({ ...appearanceForm, app_name: event.target.value })
                      }
                      type="text"
                      value={appearanceForm.app_name}
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="appearance-ai-name">AI Name</label>
                    <input
                      disabled={!canWriteSystemSettings}
                      id="appearance-ai-name"
                      onChange={(event) =>
                        setAppearanceDraft({ ...appearanceForm, ai_name: event.target.value })
                      }
                      type="text"
                      value={appearanceForm.ai_name}
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="appearance-ai-emoji">AI Avatar Emoji</label>
                    <input
                      disabled={!canWriteSystemSettings}
                      id="appearance-ai-emoji"
                      onChange={(event) =>
                        setAppearanceDraft({ ...appearanceForm, ai_avatar_emoji: event.target.value })
                      }
                      type="text"
                      value={appearanceForm.ai_avatar_emoji}
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="appearance-ai-color">AI Avatar Color</label>
                    <input
                      disabled={!canWriteSystemSettings}
                      id="appearance-ai-color"
                      onChange={(event) =>
                        setAppearanceDraft({ ...appearanceForm, ai_avatar_color: event.target.value })
                      }
                      type="text"
                      value={appearanceForm.ai_avatar_color}
                    />
                  </div>
                  <div className="settings-row">
                    <PrimaryButton
                      disabled={!canWriteSystemSettings}
                      onClick={handleSaveAppearance}
                      type="button"
                    >
                      Save Appearance
                    </PrimaryButton>
                    <span className="muted">Updated: {formatDate(appearanceData?.updated_at ?? null)}</span>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="settings-section">
            <h3>System Settings</h3>
            {!canReadSystemSettings ? (
              <p className="muted">Your role cannot read system-managed settings.</p>
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
                    <label htmlFor="system-default-mode">Default Execution Mode</label>
                    <select
                      disabled={!canWriteSystemSettings}
                      id="system-default-mode"
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
                  <div className="settings-row">
                    <PrimaryButton
                      disabled={!canWriteSystemSettings}
                      onClick={handleSaveSystem}
                      type="button"
                    >
                      Save System
                    </PrimaryButton>
                    <span className="muted">Updated: {formatDate(systemData?.updated_at ?? null)}</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </section>
    </AppLayout>
  )
}
