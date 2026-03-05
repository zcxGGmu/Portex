import { create } from 'zustand'

export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  createdAt: string
}

interface ChatState {
  messages: ChatMessage[]
  draft: string
  setDraft: (nextDraft: string) => void
  sendDraft: () => void
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
  messages: [
    createMessage(
      'assistant',
      'Welcome to Portex. This is a placeholder chat stream for M1.5 scaffolding.',
    ),
  ],
  draft: '',
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
        messages: [
          ...state.messages,
          createMessage('user', trimmedDraft),
          createMessage('assistant', `Echo: ${trimmedDraft}`),
        ],
      }
    })
  },
  clearMessages() {
    set({ messages: [] })
  },
}))
