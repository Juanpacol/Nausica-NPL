import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { GradientBackdrop } from '../three/GradientBackdrop'
import { LazyCfiBlob } from '../three/LazyCanvas'
import { Disclaimer } from '../components/Disclaimer'

export function Landing() {
  const { t } = useTranslation()

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] overflow-hidden">
      <GradientBackdrop />

      <section className="mx-auto flex max-w-5xl flex-col items-center gap-6 px-6 pt-16 pb-10 text-center md:flex-row md:text-left">
        <div className="flex-1">
          <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-brand-2">
            {t('landing.tagline')}
          </p>
          <h1 className="mb-5 text-5xl font-bold tracking-tight text-ink md:text-6xl">
            {t('landing.title')}
          </h1>
          <p className="mx-auto mb-8 max-w-xl text-lg leading-relaxed text-ink-muted md:mx-0">
            {t('landing.pitch')}
          </p>
          <div className="flex flex-wrap justify-center gap-3 md:justify-start">
            <Link
              to="/analyze"
              className="rounded-full bg-cta px-6 py-3 font-semibold text-white shadow-md hover:opacity-90"
            >
              {t('landing.cta')}
            </Link>
            <Link
              to="/reframe"
              className="rounded-full border border-edge bg-card px-6 py-3 font-semibold text-ink hover:bg-card-2"
            >
              {t('landing.ctaSecondary')}
            </Link>
          </div>
        </div>

        {/* Breathing blob at a mid CFI — pure atmosphere on the landing */}
        <LazyCfiBlob cfi={0.45} className="h-72 w-72 shrink-0 md:h-96 md:w-96" />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="mb-6 text-center text-2xl font-semibold text-ink">
          {t('landing.how.title')}
        </h2>
        <div className="grid gap-4 md:grid-cols-3">
          {(['step1', 'step2', 'step3'] as const).map((step) => (
            <div
              key={step}
              className="rounded-2xl border border-edge bg-card p-6 shadow-sm"
            >
              <h3 className="mb-2 font-semibold text-brand-2">
                {t(`landing.how.${step}Title`)}
              </h3>
              <p className="text-sm leading-relaxed text-ink-muted">
                {t(`landing.how.${step}`)}
              </p>
            </div>
          ))}
        </div>
      </section>

      <div className="px-6 pb-10">
        <Disclaimer />
      </div>
    </div>
  )
}
