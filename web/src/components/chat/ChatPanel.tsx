import type { FormEvent } from 'react'

import { useChatStore } from '../../stores/chat'
import { PrimaryButton } from '../ui/PrimaryButton'

export function ChatPanel() {
  const messages = useChatStore((state) => state.messages)
  const draft = useChatStore((state) => state.draft)
  const setDraft = useChatStore((state) => state.setDraft)
  const sendDraft = useChatStore((state) => state.sendDraft)
  const clearMessages = useChatStore((state) => state.clearMessages)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    sendDraft()
  }

  return (
    <section className="panel chat-panel">
      <div className="chat-stream">
        {messages.length === 0 ? <p className="muted">No messages yet.</p> : null}
        {messages.map((message) => (
          <article
            className={`chat-message chat-message--${message.role}`}
            key={message.id}
          >
            <p className="chat-meta">{message.role}</p>
            <p className="chat-content">{message.content}</p>
          </article>
        ))}
      </div>
      <form className="chat-form" onSubmit={handleSubmit}>
        <textarea
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Type your message..."
          value={draft}
        />
        <div className="app-nav">
          <PrimaryButton disabled={draft.trim().length === 0} type="submit">
            Send
          </PrimaryButton>
          <PrimaryButton className="button--ghost" onClick={clearMessages} type="button">
            Clear
          </PrimaryButton>
        </div>
      </form>
    </section>
  )
}
