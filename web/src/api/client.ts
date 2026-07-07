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

export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: string
}

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem('nausica_token')
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  })
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith('/auth/')) {
      window.dispatchEvent(new CustomEvent('nausica:unauthorized'))
    }
    const body = await res.text().catch(() => '')
    let message = body || res.statusText
    try {
      const parsed = JSON.parse(body) as { detail?: unknown }
      if (typeof parsed.detail === 'string') message = parsed.detail
    } catch {
      // non-JSON error body — keep raw text
    }
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

export function registerUser(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function loginUser(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
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

// ---- Phase 4/5: profiling, consent, clinician dashboard ----

export interface ArchetypeProfile {
  archetype: string
  counts: Record<string, number>
  trend: 'improving' | 'worsening' | 'stable' | null
  n_texts: number
  disclaimer: string
}

export interface PatientSummary {
  user_id: string
  email: string
  n_texts: number
  latest_cfi: number | null
  archetype: string
  trend: string | null
}

export function getArchetypeProfile(): Promise<ArchetypeProfile> {
  return request<ArchetypeProfile>('/profile/archetype')
}

export function getConsent(): Promise<{ consent_clinician_view: boolean }> {
  return request('/profile/consent')
}

export function setConsent(consent: boolean): Promise<{ consent_clinician_view: boolean }> {
  return request('/profile/consent', {
    method: 'POST',
    body: JSON.stringify({ consent_clinician_view: consent }),
  })
}

export function getOrgPatients(): Promise<{ patients: PatientSummary[] }> {
  return request('/org/patients')
}

/** PDF endpoints need the Authorization header, so a plain <a href> can't work —
 * fetch as blob and open an object URL instead. */
export async function openReport(userId: string): Promise<void> {
  const token = localStorage.getItem('nausica_token')
  const res = await fetch(`${BASE}/reports/${userId}.pdf`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error(`Report failed: ${res.status}`)
  const url = URL.createObjectURL(await res.blob())
  window.open(url, '_blank')
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
