// Renders the inline analysis card. Uses plain DOM APIs (document.createElement,
// not Obsidian's createEl) so this module stays testable outside Obsidian.

import type { DistortionLabel, NoteAnalysis } from './types';
import { DISTORTION_LABELS } from './types';
import { cfiHex, cfiLabelText, DISTORTION_DISPLAY, DISTORTION_HEX } from './colors';

const BAR_THRESHOLD = 0.2;

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function renderInlineCard(container: HTMLElement, analysis: NoteAnalysis): void {
  const card = el('div', 'nausica-card');

  // Header: colored CFI dot + value + rigidity word.
  const header = el('div', 'nausica-card-header');
  const dot = el('span', 'nausica-dot');
  dot.style.backgroundColor = cfiHex(analysis.cfi);
  header.appendChild(dot);
  header.appendChild(el('span', 'nausica-cfi-value', `CFI ${analysis.cfi.toFixed(2)}`));
  header.appendChild(el('span', 'nausica-cfi-word', cfiLabelText(analysis.cfi)));
  card.appendChild(header);

  // Mini horizontal bar per distortion above threshold.
  const bars = el('div', 'nausica-bars');
  for (const label of DISTORTION_LABELS) {
    const p = analysis.distortions[label as DistortionLabel];
    if (typeof p !== 'number' || p < BAR_THRESHOLD) continue;

    const row = el('div', 'nausica-bar-row');
    const display = DISTORTION_DISPLAY[label];
    row.appendChild(el('span', 'nausica-bar-icon', display.icon));
    row.appendChild(el('span', 'nausica-bar-label', display.en));

    const track = el('div', 'nausica-bar-track');
    const fill = el('div', 'nausica-bar-fill');
    fill.style.width = `${Math.round(p * 100)}%`;
    fill.style.backgroundColor = DISTORTION_HEX[label];
    track.appendChild(fill);
    row.appendChild(track);

    row.appendChild(el('span', 'nausica-bar-pct', `${Math.round(p * 100)}%`));
    bars.appendChild(row);
  }
  if (bars.childElementCount === 0) {
    bars.appendChild(
      el('div', 'nausica-bar-none', 'No distortion above the display threshold.'),
    );
  }
  card.appendChild(bars);

  // Footer: analyzedAt date + disclaimer.
  const footer = el('div', 'nausica-card-footer');
  const when = new Date(analysis.analyzedAt);
  const whenText = isNaN(when.getTime()) ? analysis.analyzedAt : when.toLocaleString();
  footer.appendChild(el('span', 'nausica-analyzed-at', `Analyzed ${whenText}`));
  footer.appendChild(
    el('span', 'nausica-disclaimer', 'Research prototype — not a diagnosis.'),
  );
  card.appendChild(footer);

  container.appendChild(card);
}
