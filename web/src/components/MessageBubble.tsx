export interface ChatMessage {
  role: 'client' | 'counselor'
  text: string
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isClient = message.role === 'client'
  return (
    <div className={`flex ${isClient ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
          isClient
            ? 'rounded-br-md bg-brand text-white'
            : 'rounded-bl-md border border-edge bg-card text-ink'
        }`}
      >
        {message.text}
      </div>
    </div>
  )
}
