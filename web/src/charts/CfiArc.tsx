import { useTranslation } from 'react-i18next'
import { cfiColor } from './palette'

// Minimal arc gauge for the current CFI value. Hero number wears ink tokens;
// only the arc carries the CFI ramp color. Decorative ends rounded, track recessive.

export function CfiArc({ cfi, size = 180 }: { cfi: number; size?: number }) {
  const { t } = useTranslation()

  const stroke = 12
  const r = (size - stroke) / 2
  const cx = size / 2
  const cy = size / 2
  // 270° arc from 135° to 405°
  const circumference = 2 * Math.PI * r
  const arcFraction = 0.75
  const arcLength = circumference * arcFraction
  const filled = arcLength * Math.min(1, Math.max(0, cfi))

  return (
    <figure className="flex flex-col items-center" aria-label={`${t('analyze.cfiTitle')}: ${cfi.toFixed(3)}`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img">
        {/* Track */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="var(--color-surface-2)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${arcLength} ${circumference}`}
          transform={`rotate(135 ${cx} ${cy})`}
        />
        {/* Value arc */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={cfiColor(cfi)}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
          transform={`rotate(135 ${cx} ${cy})`}
          style={{ transition: 'stroke-dasharray 800ms ease, stroke 800ms ease' }}
        />
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          className="fill-[var(--color-text)]"
          fontSize={size * 0.2}
          fontWeight={700}
        >
          {cfi.toFixed(2)}
        </text>
        <text
          x={cx}
          y={cy + size * 0.13}
          textAnchor="middle"
          className="fill-[var(--color-text-muted)]"
          fontSize={size * 0.07}
        >
          CFI
        </text>
      </svg>
      <figcaption className="flex w-full justify-between px-4 text-xs text-ink-muted -mt-6">
        <span>0 · {t('analyze.cfiFlexible')}</span>
        <span>{t('analyze.cfiRigid')} · 1</span>
      </figcaption>
    </figure>
  )
}
