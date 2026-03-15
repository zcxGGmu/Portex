const SETUP_COMPLETED_STORAGE_KEY = 'portex.setup.completed'

export function hasCompletedSetup(): boolean {
  if (typeof window === 'undefined') {
    return false
  }
  return window.localStorage.getItem(SETUP_COMPLETED_STORAGE_KEY) === '1'
}

export function markSetupCompleted(): void {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(SETUP_COMPLETED_STORAGE_KEY, '1')
}

