import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  getOrgPatients,
  getArchetypeProfile,
  getConsent,
  setConsent,
  openReport,
  type PatientSummary,
  type ArchetypeProfile,
} from '../api/client'
import { cfiColor } from '../charts/palette'
import { Disclaimer } from '../components/Disclaimer'

function TrendBadge({ trend }: { trend: string | null }) {
  const { t } = useTranslation()
  if (!trend) return <span className="text-sm text-ink-muted">—</span>
  const icon = trend === 'improving' ? '↓' : trend === 'worsening' ? '↑' : '→'
  return (
    <span className="text-sm text-ink">
      {icon} {t(`clinician.trend.${trend}`)}
    </span>
  )
}

export function ClinicianDashboard() {
  const { t } = useTranslation()
  const [patients, setPatients] = useState<PatientSummary[] | null>(null)
  const [notClinician, setNotClinician] = useState(false)
  const [profile, setProfile] = useState<ArchetypeProfile | null>(null)
  const [consented, setConsented] = useState<boolean | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getOrgPatients()
      .then((res) => setPatients(res.patients))
      .catch(() => setNotClinician(true))
    getArchetypeProfile()
      .then(setProfile)
      .catch(() => {})
    getConsent()
      .then((res) => setConsented(res.consent_clinician_view))
      .catch(() => {})
  }, [])

  async function toggleConsent(next: boolean) {
    if (busy) return
    setBusy(true)
    try {
      const res = await setConsent(next)
      setConsented(res.consent_clinician_view)
    } catch {
      // leave state as-is; next click retries
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-8 text-center">
        <h1 className="mb-2 text-3xl font-bold text-ink">{t('clinician.title')}</h1>
        <p className="mx-auto max-w-2xl text-ink-muted">{t('clinician.subtitle')}</p>
      </header>

      {/* Own profile + consent — visible to every user */}
      <section className="mb-8 rounded-2xl border border-edge bg-card p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-ink">{t('clinician.myProfile')}</h2>
        {profile && profile.n_texts > 0 ? (
          <p className="mb-4 text-ink">
            {t('clinician.dominantPattern')}:{' '}
            <strong>{profile.archetype.replace(/_/g, ' ')}</strong>
            {' · '}
            <TrendBadge trend={profile.trend} />
            {' · '}
            <span className="text-ink-muted">
              {profile.n_texts} {t('clinician.textsAnalyzed')}
            </span>
          </p>
        ) : (
          <p className="mb-4 text-ink-muted">{t('clinician.noProfileYet')}</p>
        )}
        <label className="flex items-center gap-3 text-sm text-ink">
          <input
            type="checkbox"
            checked={consented ?? false}
            disabled={busy}
            onChange={(e) => void toggleConsent(e.target.checked)}
            className="h-4 w-4 accent-[var(--color-brand)]"
          />
          {t('clinician.consentLabel')}
        </label>
        <p className="mt-2 text-xs text-ink-muted">{t('clinician.consentNote')}</p>
      </section>

      {/* Patient list — clinicians only */}
      {!notClinician && (
        <section className="rounded-2xl border border-edge bg-card p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-ink">{t('clinician.patients')}</h2>
          {patients === null ? (
            <p className="text-ink-muted">{t('common.loading')}</p>
          ) : patients.length === 0 ? (
            <p className="text-ink-muted">{t('clinician.noPatients')}</p>
          ) : (
            <ul className="divide-y divide-edge">
              {patients.map((p) => (
                <li key={p.user_id} className="flex items-center gap-4 py-3">
                  <span
                    aria-hidden="true"
                    className="inline-block h-3 w-3 shrink-0 rounded-full"
                    style={{ backgroundColor: cfiColor(p.latest_cfi ?? 0) }}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-ink">{p.email}</p>
                    <p className="text-sm text-ink-muted">
                      {p.archetype.replace(/_/g, ' ')} · {p.n_texts}{' '}
                      {t('clinician.textsAnalyzed')}
                    </p>
                  </div>
                  <TrendBadge trend={p.trend} />
                  <span className="w-16 text-right font-mono text-sm text-ink">
                    {p.latest_cfi != null ? p.latest_cfi.toFixed(2) : '—'}
                  </span>
                  <button
                    onClick={() => void openReport(p.user_id)}
                    className="rounded-full border border-edge px-3 py-1 text-sm text-ink hover:bg-card-2"
                  >
                    {t('clinician.report')}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      <div className="mt-8">
        <Disclaimer />
      </div>
    </div>
  )
}
