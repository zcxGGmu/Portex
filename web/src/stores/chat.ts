import { create } from 'zustand'

import type { StreamEvent } from '../types/events'

export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  createdAt: string
}

interface ChatState {
  messages: ChatMessage[]
  streamEvents: StreamEvent[]
  draft: string
  isRunning: boolean
  activeRunId: string | null
  addMessage: (message: Omit<ChatMessage, 'id' | 'createdAt'> & Partial<Pick<ChatMessage, 'id' | 'createdAt'>>) => void
  addStreamEvent: (event: StreamEvent) => void
  setDraft: (nextDraft: string) => void
  sendDraft: () => void
  clearRunState: () => void
  clearMessages: () => void
}

function createMessage(role: ChatRole, content: string): ChatMessage {
  const id =
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`

  return {
    id,
    role,
    content,
    createdAt: new Date().toISOString(),
  }
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  streamEvents: [],
  draft: '',
  isRunning: false,
  activeRunId: null,
  addMessage(message) {
    const normalized =
      message.id && message.createdAt
        ? { ...message, id: message.id, createdAt: message.createdAt }
        : createMessage(message.role, message.content)

    set((state) => ({ messages: [...state.messages, normalized] }))
  },
  addStreamEvent(event) {
    set((state) => {
      const nextState: Partial<ChatState> = {
        streamEvents: [...state.streamEvents, event],
      }

      if (event.event_type === 'run.started') {
        nextState.isRunning = true
        nextState.activeRunId = event.run_id
      }

      if (
        event.event_type === 'run.completed' ||
        event.event_type === 'run.failed' ||
        event.event_type === 'run.timeout'
      ) {
        if (state.activeRunId === event.run_id) {
          nextState.isRunning = false
          nextState.activeRunId = null
        }
      }

      return nextState
    })
  },
  setDraft(nextDraft) {
    set({ draft: nextDraft })
  },
  sendDraft() {
    set((state) => {
      const trimmedDraft = state.draft.trim()
      if (!trimmedDraft) {
        return {}
      }

      return {
        draft: '',
        messages: [...state.messages, createMessage('user', trimmedDraft)],
      }
    })
  },
  clearRunState() {
    set({ isRunning: false, activeRunId: null })
  },
  clearMessages() {
    set({ messages: [], streamEvents: [], isRunning: false, activeRunId: null })
  },
}))
