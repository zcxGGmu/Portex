import { registerSW } from 'virtual:pwa-register'

type BeforeInstallPromptChoice = {
  outcome: 'accepted' | 'dismissed'
  platform: string
}

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<BeforeInstallPromptChoice>
}

export type PwaInstallOutcome = 'accepted' | 'dismissed' | 'unavailable'

export interface PwaState {
  canInstall: boolean
  installHintDismissed: boolean
  isStandalone: boolean
  isSupported: boolean
  needsManualInstallHint: boolean
  updateReady: boolean
}

const DEFAULT_PWA_STATE: PwaState = {
  canInstall: false,
  installHintDismissed: false,
  isStandalone: false,
  isSupported: false,
  needsManualInstallHint: false,
  updateReady: false,
}

let state: PwaState = { ...DEFAULT_PWA_STATE }
let runtimeInstalled = false
let deferredPrompt: BeforeInstallPromptEvent | null = null
let applyUpdateHandler: ((reloadPage?: boolean) => Promise<void>) | null = null
const listeners = new Set<() => void>()

function isStandaloneDisplay(): boolean {
  if (typeof window === 'undefined') {
    return false
  }

  const nav = navigator as Navigator & { standalone?: boolean }
  return (window.matchMedia?.('(display-mode: standalone)').matches ?? false) || Boolean(nav.standalone)
}

function needsIosManualInstallHint(): boolean {
  if (typeof window === 'undefined') {
    return false
  }

  const userAgent = navigator.userAgent.toLowerCase()
  const isAppleMobile =
    /iphone|ipad|ipod/.test(userAgent) || (userAgent.includes('macintosh') && navigator.maxTouchPoints > 1)
  const isSafari = userAgent.includes('safari') && !/crios|fxios|edgios/.test(userAgent)

  return isAppleMobile && isSafari && !isStandaloneDisplay()
}

function emitChange(): void {
  listeners.forEach((listener) => listener())
}

function setState(nextState: Partial<PwaState>): void {
  state = { ...state, ...nextState }
  emitChange()
}

function resetRuntimeState(): void {
  state = {
    ...DEFAULT_PWA_STATE,
    isStandalone: isStandaloneDisplay(),
    isSupported:
      typeof window !== 'undefined' &&
      typeof navigator !== 'undefined' &&
      'serviceWorker' in navigator,
    needsManualInstallHint: needsIosManualInstallHint(),
  }
}

function cleanupDevServiceWorkers(): void {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker
      .getRegistrations()
      .then((registrations) => Promise.all(registrations.map((registration) => registration.unregister())))
      .catch(() => undefined)
  }

  if ('caches' in window) {
    window.caches
      .keys()
      .then((keys) => Promise.all(keys.map((key) => window.caches.delete(key))))
      .catch(() => undefined)
  }
}

function handleBeforeInstallPrompt(event: Event): void {
  const promptEvent = event as BeforeInstallPromptEvent
  promptEvent.preventDefault()
  deferredPrompt = promptEvent
  setState({
    canInstall: !isStandaloneDisplay(),
    installHintDismissed: false,
    isStandalone: isStandaloneDisplay(),
    needsManualInstallHint: false,
  })
}

function handleAppInstalled(): void {
  deferredPrompt = null
  setState({
    canInstall: false,
    installHintDismissed: false,
    isStandalone: true,
    needsManualInstallHint: false,
  })
}

export function installPwaRuntime(): void {
  if (typeof window === 'undefined' || runtimeInstalled) {
    return
  }

  runtimeInstalled = true
  resetRuntimeState()

  if (import.meta.env.DEV) {
    window.addEventListener('load', cleanupDevServiceWorkers, { once: true })
    return
  }

  window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
  window.addEventListener('appinstalled', handleAppInstalled)

  applyUpdateHandler = registerSW({
    immediate: true,
    onNeedRefresh() {
      setState({ updateReady: true })
    },
  })
}

export function subscribePwaState(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function getPwaState(): PwaState {
  return state
}

export function dismissPwaInstallHint(): void {
  if (!state.canInstall && !state.needsManualInstallHint) {
    return
  }

  setState({ installHintDismissed: true })
}

export async function requestPwaInstall(): Promise<PwaInstallOutcome> {
  if (!deferredPrompt) {
    return 'unavailable'
  }

  const promptEvent = deferredPrompt
  deferredPrompt = null

  await promptEvent.prompt()
  const result = await promptEvent.userChoice
  const accepted = result.outcome === 'accepted'

  if (accepted) {
    setState({
      canInstall: false,
      installHintDismissed: false,
      isStandalone: true,
      needsManualInstallHint: false,
    })
    return 'accepted'
  }

  setState({
    canInstall: false,
    installHintDismissed: true,
    isStandalone: isStandaloneDisplay(),
    needsManualInstallHint: needsIosManualInstallHint(),
  })
  return 'dismissed'
}

export async function applyPwaUpdate(): Promise<boolean> {
  if (!applyUpdateHandler) {
    return false
  }

  setState({ updateReady: false })
  await applyUpdateHandler(true)
  return true
}
