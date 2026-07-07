// Chart color helpers. Colors resolve through CSS custom properties so both
// themes work without re-rendering logic. Validated with the dataviz six-checks
// (categorical: light + dark surfaces; CFI ramp: ordinal single-hue).

import type { DistortionLabel } from '../api/client'

// Color follows the ENTITY (distortion type), never its rank — sorting the bars
// must not repaint them.
export const CATEGORY_COLOR: Record<DistortionLabel, string> = {
  all_or_nothing: 'var(--color-cat-all-or-nothing)',
  overgeneralization: 'var(--color-cat-overgeneralization)',
  emotional_reasoning: 'var(--color-cat-emotional-reasoning)',
  catastrophizing: 'var(--color-cat-catastrophizing)',
  mind_reading: 'var(--color-cat-mind-reading)',
}

// Icons pair with color so identity is never color-alone (CVD relief).
export const CATEGORY_ICON: Record<DistortionLabel, string> = {
  all_or_nothing: '◐',
  overgeneralization: '∞',
  emotional_reasoning: '♥',
  catastrophizing: '⌁',
  mind_reading: '◎',
}

// CFI single-hue teal ramp, dark = rigid (cfi→1), light = flexible (cfi→0).
const CFI_RAMP = [
  'var(--color-cfi-5)', // lightest — most flexible
  'var(--color-cfi-4)',
  'var(--color-cfi-3)',
  'var(--color-cfi-2)',
  'var(--color-cfi-1)', // darkest — most rigid
]

export function cfiColor(cfi: number): string {
  const idx = Math.min(CFI_RAMP.length - 1, Math.max(0, Math.floor(cfi * CFI_RAMP.length)))
  return CFI_RAMP[idx]
}

// Concrete hex ramp for contexts that can't resolve CSS vars (three.js materials)
export const CFI_RAMP_HEX = ['#379e8f', '#248579', '#1a6c64', '#16554f', '#123f3b']
