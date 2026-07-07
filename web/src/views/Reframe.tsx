import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { reframe, type TrajectoryPoint } from '../api/client'
import { CfiTrajectory } from '../charts/CfiTrajectory'
import { MessageBubble, type ChatMessage } from '../components/MessageBubble'
import { LazyCfiBlob } from '../three/LazyCanvas'
import { Disclaimer } from '../components/Disclaimer'

export function Reframe() {
  const { t } = useTranslation()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [points, setPoints] = useState<TrajectoryPoint[]>([])
  const [sessionId, setSessionId] = useState<string | undefined>()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const currentCfi = points.length ? points[points.length - 1].cfi : 0.45

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function reset() {
    setMessages([])
    setPoints([])
    setSessionId(undefined)
    setError(false)
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return
    setLoading(true)
    setError(false)
    setInput('')
    setMessages((m) => [...m, { role: 'client', text }])
    try {
      const res = await reframe(text, sessionId)
      setSessionId(res.session_id)
      setMessages((m) => [...m, { role: 'counselor', text: res.counselor_reply }])
      setPoints((p) => [
        ...p,
        { turn: p.length + 1, cfi: res.cfi, distortions: res.distortions },
      ])
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <header className="mb-6 text-center">
        <h1 className="mb-1 text-3xl font-bold text-ink">{t('reframe.title')}</h1>
        <p className="text-ink-muted">{t('reframe.subtitle')}</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        {/* Chat column */}
        <section className="flex h-[32rem] flex-col rounded-2xl border border-edge bg-card shadow-sm">
          <div className="flex-1 space-y-3 overflow-y-auto p-5">
            {messages.length === 0 && (
              <p className="pt-16 text-center text-sm text-ink-muted">
                {t('reframe.emptyChat')}
              </p>
            )}
            {messages.map((m, i) => (
              <MessageBubble key={i} message={m} />
            ))}
            {loading && (
              <p className="text-sm italic text-ink-muted">{t('reframe.sending')}</p>
            )}
            {error && (
              <p className="rounded-xl bg-card-2 p-3 text-center text-sm text-ink">
                {t('common.error')}
              </p>
            )}
            <div ref={chatEndRef} />
          </div>

          <form onSubmit={onSubmit} className="flex gap-2 border-t border-edge p-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t('reframe.placeholder')}
              className="flex-1 rounded-full border border-edge bg-canvas px-4 py-2.5 text-sm text-ink outline-none placeholder:text-ink-muted focus:border-brand-2"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="rounded-full bg-cta px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-40"
            >
              {t('reframe.send')}
            </button>
          </form>
        </section>

        {/* Live trajectory rail */}
        <aside className="flex flex-col gap-4">
          <div className="rounded-2xl border border-edge bg-card p-5 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-semibold text-ink">{t('reframe.trajectoryTitle')}</h2>
              {messages.length > 0 && (
                <button
                  onClick={reset}
                  className="text-xs text-ink-muted underline hover:text-ink"
                >
                  {t('reframe.newSession')}
                </button>
              )}
            </div>
            {points.length > 0 ? (
              <CfiTrajectory points={points} />
            ) : (
              <p className="py-10 text-center text-sm text-ink-muted">
                {t('analyze.empty')}
              </p>
            )}
          </div>
          <div className="flex justify-center rounded-2xl border border-edge bg-card p-4 shadow-sm">
            <LazyCfiBlob cfi={currentCfi} className="h-44 w-44" />
          </div>
        </aside>
      </div>

      <div className="mt-8">
        <Disclaimer />
      </div>
    </div>
  )
}
