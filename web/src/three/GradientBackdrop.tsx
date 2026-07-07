// Slow indigo->teal mesh-gradient backdrop for the hero (CSS-based: cheap,
// theme-aware, honors reduced-motion via the global CSS rule). A shader canvas
// would double GPU cost for a decorative layer that CSS handles at 60fps.

import './gradient.css'

export function GradientBackdrop() {
  return (
    <div className="nausica-gradient absolute inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <div className="nausica-gradient-blob nausica-gradient-a" />
      <div className="nausica-gradient-blob nausica-gradient-b" />
      <div className="nausica-gradient-blob nausica-gradient-c" />
    </div>
  )
}
