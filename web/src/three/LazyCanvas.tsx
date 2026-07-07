import { lazy, Suspense, useEffect, useRef, useState, type ComponentProps } from 'react'

// Defers the three.js bundle + Canvas mount until the blob is actually near the
// viewport, so Landing's first paint never waits on WebGL.

const CfiBlobLazy = lazy(() =>
  import('./CfiBlob').then((m) => ({ default: m.CfiBlob })),
)

export function LazyCfiBlob(props: ComponentProps<typeof CfiBlobLazy>) {
  const holderRef = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = holderRef.current
    if (!el) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setVisible(true)
          observer.disconnect()
        }
      },
      { rootMargin: '200px' },
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return (
    <div ref={holderRef} className={props.className}>
      {visible && (
        <Suspense fallback={null}>
          <CfiBlobLazy {...props} className="h-full w-full" />
        </Suspense>
      )}
    </div>
  )
}
