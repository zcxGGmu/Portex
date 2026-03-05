import type { ChatMessage } from '../../stores/chat'

interface MessageListProps {
  messages: ChatMessage[]
}

export function MessageList({ messages }: MessageListProps) {
  return (
    <div className="chat-stream">
      {messages.length === 0 ? <p className="muted">No messages yet.</p> : null}
      {messages.map((message) => (
        <article className={`chat-message chat-message--${message.role}`} key={message.id}>
          <p className="chat-meta">{message.role}</p>
          <p className="chat-content">{message.content}</p>
        </article>
      ))}
    </div>
  )
}
