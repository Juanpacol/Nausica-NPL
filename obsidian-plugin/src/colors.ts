// Ported verbatim from web/src/charts/palette.ts and web/src/theme/tokens.css.
// Do not invent new hex values — these are dataviz-validated.

import type { DistortionLabel } from './types';

// CFI single-hue teal ramp; index 0 = lightest = most flexible (cfi→0),
// index 4 = darkest = most rigid (cfi→1). Same as CFI_RAMP_HEX in the web app.
export const CFI_RAMP_HEX = ['#379e8f', '#248579', '#1a6c64', '#16554f', '#123f3b'];

export function cfiHex(cfi: number): string {
  const idx = Math.min(
    CFI_RAMP_HEX.length - 1,
    Math.max(0, Math.floor(cfi * CFI_RAMP_HEX.length)),
  );
  // Index is clamped to [0, length-1], so this is always defined.
  return CFI_RAMP_HEX[idx] as string;
}

export function cfiLabelText(cfi: number): string {
  if (cfi < 0.35) return 'flexible';
  if (cfi < 0.6) return 'moderate';
  return 'rigid';
}

// Icons pair with color so identity is never color-alone (CVD relief).
// Icons match web CATEGORY_ICON; hexes are the validated light-mode
// categoricals from web/src/theme/tokens.css.
export const DISTORTION_DISPLAY: Record<DistortionLabel, { icon: string; en: string }> = {
  all_or_nothing: { icon: '◐', en: 'All-or-nothing' },
  overgeneralization: { icon: '∞', en: 'Overgeneralization' },
  emotional_reasoning: { icon: '♥', en: 'Emotional reasoning' },
  catastrophizing: { icon: '⌁', en: 'Catastrophizing' },
  mind_reading: { icon: '◎', en: 'Mind reading' },
};

export const DISTORTION_HEX: Record<DistortionLabel, string> = {
  all_or_nothing: '#4c77c9',
  overgeneralization: '#0a9187',
  emotional_reasoning: '#ae6e1f',
  catastrophizing: '#8e66cc',
  mind_reading: '#c25573',
};
