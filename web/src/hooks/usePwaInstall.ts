import { useSyncExternalStore } from 'react'

import {
  applyPwaUpdate,
  dismissPwaInstallHint,
  getPwaState,
  requestPwaInstall,
  subscribePwaState,
} from '../pwa'

export function usePwaInstall() {
  const state = useSyncExternalStore(subscribePwaState, getPwaState, getPwaState)

  return {
    ...state,
    applyUpdate: applyPwaUpdate,
    dismissInstallHint: dismissPwaInstallHint,
    requestInstall: requestPwaInstall,
  }
}
