import { useTranslation } from 'react-i18next'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TrajectoryPoint } from '../api/client'

// CFI (0-1 rigidity) over conversation turns. Lower = more flexible (the goal).
// Single series -> no legend box (the title names it). 2px line, soft area fill,
// crosshair tooltip, shaded "flexible zone" reference band below 0.35.

const FLEXIBLE_ZONE_MAX = 0.35

function TrajectoryTooltip({
  active,
  payload,
  label,
  turnWord,
}: {
  active?: boolean
  payload?: Array<{ value: number }>
  label?: number
  turnWord: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-edge bg-card px-3 py-2 text-sm shadow-md">
      <div className="text-ink-muted">
        {turnWord} {label}
      </div>
      <div className="text-ink font-semibold tabular-nums">CFI {payload[0].value.toFixed(3)}</div>
    </div>
  )
}

export function CfiTrajectory({ points }: { points: TrajectoryPoint[] }) {
  const { t } = useTranslation()

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer>
        <AreaChart data={points} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id="cfiFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-cfi-3)" stopOpacity={0.25} />
              <stop offset="100%" stopColor="var(--color-cfi-3)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--color-border)" strokeDasharray="2 4" vertical={false} />
          {/* Flexible zone: the target region, kept recessive */}
          <ReferenceArea
            y1={0}
            y2={FLEXIBLE_ZONE_MAX}
            fill="var(--color-cfi-5)"
            fillOpacity={0.08}
            label={{
              value: t('reframe.flexibleZone'),
              position: 'insideBottomRight',
              fill: 'var(--color-text-muted)',
              fontSize: 11,
            }}
          />
          <XAxis
            dataKey="turn"
            stroke="var(--color-text-muted)"
            tickLine={false}
            axisLine={{ stroke: 'var(--color-border)' }}
            fontSize={12}
            allowDecimals={false}
          />
          <YAxis
            domain={[0, 1]}
            stroke="var(--color-text-muted)"
            tickLine={false}
            axisLine={false}
            fontSize={12}
            tickFormatter={(v: number) => v.toFixed(1)}
          />
          <Tooltip
            content={<TrajectoryTooltip turnWord={t('reframe.turn')} />}
            cursor={{ stroke: 'var(--color-text-muted)', strokeDasharray: '3 3' }}
          />
          <Area
            type="monotone"
            dataKey="cfi"
            stroke="var(--color-cfi-2)"
            strokeWidth={2}
            fill="url(#cfiFill)"
            dot={{ r: 4, fill: 'var(--color-cfi-2)', strokeWidth: 2, stroke: 'var(--color-surface)' }}
            activeDot={{ r: 6 }}
            isAnimationActive={points.length <= 12}
          />
        </AreaChart>
      </ResponsiveContainer>
      <p className="mt-1 text-center text-xs text-ink-muted">↓ {t('reframe.trajectoryHint')}</p>
    </div>
  )
}
