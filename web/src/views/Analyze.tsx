import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { analyze, type AnalyzeResponse } from '../api/client'
import { DistortionBars } from '../charts/DistortionBars'
import { CfiArc } from '../charts/CfiArc'
import { LazyCfiBlob } from '../three/LazyCanvas'
import { Disclaimer } from '../components/Disclaimer'

export function Analyze() {
  const { t } = useTranslation()
  const [text, setText] = useState('')
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!text.trim() || loading) return
    setLoading(true)
    setError(false)
    try {
      setResult(await analyze(text.trim()))
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-8 text-center">
        <h1 className="mb-2 text-3xl font-bold text-ink">{t('analyze.title')}</h1>
        <p className="mx-auto max-w-2xl text-ink-muted">{t('analyze.subtitle')}</p>
      </header>

      <form onSubmit={onSubmit} className="mx-auto mb-8 max-w-2xl">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) onSubmit(e)
          }}
          placeholder={t('analyze.placeholder')}
          rows={4}
          className="w-full resize-y rounded-2xl border border-edge bg-card p-4 text-ink shadow-sm outline-none placeholder:text-ink-muted focus:border-brand-2"
        />
        <div className="mt-3 flex justify-end">
          <button
            type="submit"
            disabled={loading || !text.trim()}
            className="rounded-full bg-cta px-6 py-2.5 font-semibold text-white shadow-md hover:opacity-90 disabled:opacity-40"
          >
            {loading ? t('analyze.analyzing') : t('analyze.button')}
          </button>
        </div>
      </form>

      {error && (
        <p className="mx-auto mb-6 max-w-2xl rounded-xl border border-edge bg-card-2 p-4 text-center text-sm text-ink">
          {t('common.error')}
        </p>
      )}

      {result ? (
        <div className="grid items-start gap-6 md:grid-cols-2">
          <section className="rounded-2xl border border-edge bg-card p-6 shadow-sm">
            <h2 className="mb-4 font-semibold text-ink">{t('analyze.resultsTitle')}</h2>
            <DistortionBars distortions={result.distortions} />
          </section>

          <section className="flex flex-col items-center rounded-2xl border border-edge bg-card p-6 shadow-sm">
            <h2 className="mb-2 font-semibold text-ink">{t('analyze.cfiTitle')}</h2>
            <CfiArc cfi={result.cfi} />
            <LazyCfiBlob cfi={result.cfi} className="h-40 w-40" />
          </section>
        </div>
      ) : (
        !error && (
          <p className="text-center text-sm text-ink-muted">{t('analyze.empty')}</p>
        )
      )}

      <div className="mt-10">
        <Disclaimer />
      </div>
    </div>
  )
}
