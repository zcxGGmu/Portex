import { useState } from 'react'

import { usePwaInstall } from '../../hooks/usePwaInstall'
import { PrimaryButton } from '../ui/PrimaryButton'

interface PwaControlsProps {
  variant?: 'inline' | 'stacked'
}

export function PwaControls({ variant = 'inline' }: PwaControlsProps) {
  const {
    updateReady,
    canInstall,
    installHintDismissed,
    needsManualInstallHint,
    applyUpdate,
    requestInstall,
    dismissInstallHint,
  } = usePwaInstall()
  const [busyAction, setBusyAction] = useState<'install' | 'update' | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  async function handleInstall() {
    setBusyAction('install')
    setNotice(null)
    try {
      const outcome = await requestInstall()
      if (outcome === 'unavailable') {
        setNotice('Install prompt is not available in this browser.')
      }
    } finally {
      setBusyAction(null)
    }
  }

  async function handleUpdate() {
    setBusyAction('update')
    setNotice(null)
    try {
      const applied = await applyUpdate()
      if (!applied) {
        setNotice('Update is not available right now.')
      }
    } finally {
      setBusyAction(null)
    }
  }

  if (updateReady) {
    return (
      <div className={`pwa-controls ${variant === 'stacked' ? 'pwa-controls--stacked' : ''}`}>
        <PrimaryButton disabled={busyAction !== null} onClick={handleUpdate} type="button">
          {busyAction === 'update' ? 'Updating...' : 'Update App'}
        </PrimaryButton>
        {notice ? <p className="pwa-note">{notice}</p> : null}
      </div>
    )
  }

  if (!canInstall || installHintDismissed) {
    if (!needsManualInstallHint || installHintDismissed) {
      return null
    }

    return (
      <div className={`pwa-controls ${variant === 'stacked' ? 'pwa-controls--stacked' : ''}`}>
        <p className="pwa-note">On iPhone or iPad, open Safari Share and choose Add to Home Screen.</p>
        <button className="pwa-dismiss-button" onClick={dismissInstallHint} type="button">
          Later
        </button>
      </div>
    )
  }

  return (
    <div className={`pwa-controls ${variant === 'stacked' ? 'pwa-controls--stacked' : ''}`}>
      <PrimaryButton disabled={busyAction !== null} onClick={handleInstall} type="button">
        {busyAction === 'install' ? 'Preparing...' : 'Install App'}
      </PrimaryButton>
      <button className="pwa-dismiss-button" onClick={dismissInstallHint} type="button">
        Later
      </button>
      {notice ? <p className="pwa-note">{notice}</p> : null}
    </div>
  )
}
