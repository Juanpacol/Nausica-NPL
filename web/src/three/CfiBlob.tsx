import { useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { MeshDistortMaterial, Float } from '@react-three/drei'
import * as THREE from 'three'
import { CFI_RAMP_HEX } from '../charts/palette'
import { useReducedMotion } from './useReducedMotion'

// The blob IS the metric made visible: distortion amplitude + color track CFI.
// Rigid (cfi -> 1): dark teal, agitated surface. Flexible (cfi -> 0): light teal,
// calm surface. Purely decorative — the same number is always shown in the arc
// and charts beside it (data is never encoded only in 3D).

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t
}

function cfiHex(cfi: number): string {
  const idx = Math.min(CFI_RAMP_HEX.length - 1, Math.max(0, Math.floor(cfi * CFI_RAMP_HEX.length)))
  return CFI_RAMP_HEX[idx]
}

function Blob({ cfi, frozen }: { cfi: number; frozen: boolean }) {
  // Smoothly spring the material toward the target each frame
  const matRef = useRef<React.ComponentRef<typeof MeshDistortMaterial>>(null)
  const targetColor = useMemo(() => new THREE.Color(cfiHex(cfi)), [cfi])
  const targetDistort = lerp(0.15, 0.55, cfi)
  const targetSpeed = frozen ? 0 : lerp(0.8, 2.4, cfi)

  useFrame(() => {
    const mat = matRef.current
    if (!mat) return
    mat.distort = lerp(mat.distort, targetDistort, 0.04)
    mat.color.lerp(targetColor, 0.03)
  })

  return (
    <Float
      enabled={!frozen}
      speed={1.2}
      rotationIntensity={0.4}
      floatIntensity={0.6}
    >
      <mesh>
        <icosahedronGeometry args={[1.35, 48]} />
        <MeshDistortMaterial
          ref={matRef}
          color={cfiHex(cfi)}
          distort={targetDistort}
          speed={frozen ? 0 : targetSpeed}
          roughness={0.25}
          metalness={0.1}
        />
      </mesh>
    </Float>
  )
}

export function CfiBlob({ cfi, className }: { cfi: number; className?: string }) {
  const reduced = useReducedMotion()

  return (
    <div className={className} aria-hidden="true">
      <Canvas
        dpr={[1, 1.5]}
        camera={{ position: [0, 0, 4], fov: 45 }}
        frameloop={reduced ? 'demand' : 'always'}
        gl={{ antialias: true, alpha: true }}
      >
        <ambientLight intensity={0.7} />
        <directionalLight position={[3, 4, 5]} intensity={1.4} />
        <directionalLight position={[-3, -2, 2]} intensity={0.4} color="#e8927c" />
        <Blob cfi={cfi} frozen={reduced} />
      </Canvas>
    </div>
  )
}
