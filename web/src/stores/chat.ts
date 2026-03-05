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
  addMessage: (message: Omit<ChatMessage, 'id' | 'createdAt'> & Partial<Pick<ChatMessage, 'id' | 'createdAt'>>) => void
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
  messages: [],
  draft: '',
  addMessage(message) {
    const normalized =
      message.id && message.createdAt
        ? { ...message, id: message.id, createdAt: message.createdAt }
        : createMessage(message.role, message.content)

    set((state) => ({ messages: [...state.messages, normalized] }))
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
  clearMessages() {
    set({ messages: [] })
  },
}))
