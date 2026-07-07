import { useTranslation } from 'react-i18next'
import type { Distortions, DistortionLabel } from '../api/client'
import { DISTORTION_LABELS } from '../api/client'
import { CATEGORY_COLOR, CATEGORY_ICON } from './palette'

// Sorted horizontal bars for the 5 multi-label probabilities.
// Plain SVG-free HTML bars: full theme-token support, direct labels, per-row
// hover tooltip via title, icon+label so identity is never color-alone.

export function DistortionBars({ distortions }: { distortions: Distortions }) {
  const { t } = useTranslation()

  const rows = [...DISTORTION_LABELS].sort((a, b) => distortions[b] - distortions[a])

  return (
    <div className="flex flex-col gap-3" role="list" aria-label={t('analyze.resultsTitle')}>
      {rows.map((label: DistortionLabel) => {
        const value = distortions[label]
        const pct = Math.round(value * 100)
        return (
          <div
            key={label}
            role="listitem"
            title={`${t(`distortions.${label}`)}: ${pct}%`}
            className="group"
          >
            <div className="mb-1 flex items-baseline justify-between gap-2 text-sm">
              <span className="text-ink flex items-center gap-1.5">
                <span aria-hidden="true" style={{ color: CATEGORY_COLOR[label] }}>
                  {CATEGORY_ICON[label]}
                </span>
                {t(`distortions.${label}`)}
              </span>
              {/* Value label wears ink, never the series color */}
              <span className="text-ink-muted tabular-nums font-medium">{pct}%</span>
            </div>
            <div className="h-2.5 w-full rounded-full bg-card-2 overflow-hidden">
              <div
                className="h-full rounded-full transition-[width] duration-700 ease-out"
                style={{
                  width: `${Math.max(pct, 1)}%`,
                  backgroundColor: CATEGORY_COLOR[label],
                }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
