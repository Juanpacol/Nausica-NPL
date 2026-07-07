// Typed client for the Nausica FastAPI backend (src/api/main.py).
// Shapes mirror the Pydantic models: AnalyzeResponse, ReframeResponse, and
// ReframingTrajectory.to_dict() from src/metrics/cognitive_flexibility_index.py.

export type DistortionLabel =
  | 'all_or_nothing'
  | 'overgeneralization'
  | 'emotional_reasoning'
  | 'catastrophizing'
  | 'mind_reading'

export const DISTORTION_LABELS: DistortionLabel[] = [
  'all_or_nothing',
  'overgeneralization',
  'emotional_reasoning',
  'catastrophizing',
  'mind_reading',
]

export type Distortions = Record<DistortionLabel, number>

export interface AnalyzeResponse {
  distortions: Distortions
  cfi: number
  disclaimer: string
}

export interface ReframeResponse {
  session_id: string
  counselor_reply: string
  distortions: Distortions
  cfi: number
  cfi_delta: number | null
  disclaimer: string
}

export interface TrajectoryPoint {
  turn: number
  cfi: number
  distortions: Distortions
}

export interface Trajectory {
  session_id: string
  points: TrajectoryPoint[]
  delta: number | null
  is_improving: boolean | null
}

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new Error(`API ${res.status}: ${detail || res.statusText}`)
  }
  return res.json() as Promise<T>
}

export function analyze(text: string): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>('/analyze', {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

export function reframe(text: string, sessionId?: string): Promise<ReframeResponse> {
  return request<ReframeResponse>('/reframe', {
    method: 'POST',
    body: JSON.stringify({ text, session_id: sessionId ?? null }),
  })
}

export function getTrajectory(sessionId: string): Promise<Trajectory> {
  return request<Trajectory>(`/trajectory/${sessionId}`)
}
