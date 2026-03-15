import { create } from 'zustand'

import type { StreamEvent } from '../types/events'

export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  createdAt: string
}

interface ChatContextSnapshot {
  messages: ChatMessage[]
  streamEvents: StreamEvent[]
  draft: string
  isRunning: boolean
  activeRunId: string | null
}

interface ChatState extends ChatContextSnapshot {
  contexts: Record<string, ChatContextSnapshot>
  activeContextId: string
  switchContext: (contextId: string) => void
  addMessage: (
    message: Omit<ChatMessage, 'id' | 'createdAt'> & Partial<Pick<ChatMessage, 'id' | 'createdAt'>>,
  ) => void
  addStreamEvent: (event: StreamEvent) => void
  setDraft: (nextDraft: string) => void
  clearRunState: () => void
  clearMessages: () => void
}

const DEFAULT_CONTEXT_ID = 'group-demo::main'

function createEmptyContext(): ChatContextSnapshot {
  return {
    messages: [],
    streamEvents: [],
    draft: '',
    isRunning: false,
    activeRunId: null,
  }
}

function cloneContext(context: ChatContextSnapshot): ChatContextSnapshot {
  return {
    messages: [...context.messages],
    streamEvents: [...context.streamEvents],
    draft: context.draft,
    isRunning: context.isRunning,
    activeRunId: context.activeRunId,
  }
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
  ...createEmptyContext(),
  contexts: {},
  activeContextId: DEFAULT_CONTEXT_ID,
  switchContext(contextId) {
    const normalizedContextId = contextId.trim()
    if (!normalizedContextId) {
      return
    }

    set((state) => {
      if (normalizedContextId === state.activeContextId) {
        return {}
      }

      const currentSnapshot = cloneContext({
        messages: state.messages,
        streamEvents: state.streamEvents,
        draft: state.draft,
        isRunning: state.isRunning,
        activeRunId: state.activeRunId,
      })

      const nextContexts = {
        ...state.contexts,
        [state.activeContextId]: currentSnapshot,
      }
      const restoredSnapshot = cloneContext(nextContexts[normalizedContextId] ?? createEmptyContext())
      nextContexts[normalizedContextId] = cloneContext(restoredSnapshot)

      return {
        contexts: nextContexts,
        activeContextId: normalizedContextId,
        ...restoredSnapshot,
      }
    })
  },
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
  clearRunState() {
    set({ isRunning: false, activeRunId: null })
  },
  clearMessages() {
    set({ messages: [], streamEvents: [], draft: '', isRunning: false, activeRunId: null })
  },
}))
