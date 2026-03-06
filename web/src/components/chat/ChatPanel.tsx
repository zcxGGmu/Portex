import type { FormEvent } from 'react'
import { useEffect, useRef } from 'react'

import { createWebSocket, subscribeWebSocketMessages } from '../../api/ws'
import { useChatStore } from '../../stores/chat'
import { isStreamEvent } from '../../types/events'
import { MessageList } from './MessageList'
import { ThinkingPanel } from './ThinkingPanel'
import { ToolCallTracker } from './ToolCallTracker'
import { PrimaryButton } from '../ui/PrimaryButton'

export function ChatPanel() {
  const messages = useChatStore((state) => state.messages)
  const streamEvents = useChatStore((state) => state.streamEvents)
  const draft = useChatStore((state) => state.draft)
  const isRunning = useChatStore((state) => state.isRunning)
  const activeRunId = useChatStore((state) => state.activeRunId)
  const addMessage = useChatStore((state) => state.addMessage)
  const addStreamEvent = useChatStore((state) => state.addStreamEvent)
  const setDraft = useChatStore((state) => state.setDraft)
  const sendDraft = useChatStore((state) => state.sendDraft)
  const clearRunState = useChatStore((state) => state.clearRunState)
  const clearMessages = useChatStore((state) => state.clearMessages)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const websocket = createWebSocket('group-demo')
    wsRef.current = websocket

    const unsubscribe = subscribeWebSocketMessages(websocket, (message) => {
      if (isStreamEvent(message)) {
        addStreamEvent(message)
        if (message.event_type === 'run.completed' && typeof message.payload?.final_output === 'string') {
          addMessage({ role: 'assistant', content: message.payload.final_output })
        } else if (message.event_type === 'run.failed') {
          if (message.payload?.status === 'cancelled') {
            addMessage({ role: 'assistant', content: 'Run cancelled.' })
            return
          }
          const errorMessage = message.payload?.error ?? message.payload?.status ?? 'unknown error'
          addMessage({ role: 'assistant', content: `Run failed: ${errorMessage}` })
        } else if (message.event_type === 'run.timeout') {
          addMessage({ role: 'assistant', content: 'Run timed out.' })
        }
        return
      }

      if (typeof message === 'string' && message.trim()) {
        addMessage({ role: 'assistant', content: message })
      }
    })

    return () => {
      unsubscribe()
      websocket.close()
      wsRef.current = null
      clearRunState()
    }
  }, [addMessage, addStreamEvent, clearRunState])

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (isRunning) {
      return
    }

    const trimmed = draft.trim()
    if (!trimmed) {
      return
    }

    sendDraft()
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(trimmed)
    }
  }

  function handleCancel() {
    if (!activeRunId || wsRef.current?.readyState !== WebSocket.OPEN) {
      return
    }

    wsRef.current.send(
      JSON.stringify({
        type: 'cancel',
        run_id: activeRunId,
      }),
    )
  }

  return (
    <section className="panel chat-panel">
      <MessageList messages={messages} />
      <ThinkingPanel events={streamEvents} />
      <ToolCallTracker events={streamEvents} />
      <form className="chat-form" onSubmit={handleSubmit}>
        <textarea
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Type your message..."
          value={draft}
        />
        <div className="app-nav">
          <PrimaryButton disabled={draft.trim().length === 0 || isRunning} type="submit">
            Send
          </PrimaryButton>
          <PrimaryButton className="button--ghost" disabled={!isRunning} onClick={handleCancel} type="button">
            Cancel
          </PrimaryButton>
          <PrimaryButton className="button--ghost" disabled={isRunning} onClick={clearMessages} type="button">
            Clear
          </PrimaryButton>
        </div>
      </form>
    </section>
  )
}
