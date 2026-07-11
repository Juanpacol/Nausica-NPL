// Shapes mirror the Nausica FastAPI backend (src/api/main.py) exactly,
// as typed in web/src/api/client.ts. Do not diverge from the web client.

export type DistortionLabel =
  | 'all_or_nothing'
  | 'overgeneralization'
  | 'emotional_reasoning'
  | 'catastrophizing'
  | 'mind_reading';

export const DISTORTION_LABELS: DistortionLabel[] = [
  'all_or_nothing',
  'overgeneralization',
  'emotional_reasoning',
  'catastrophizing',
  'mind_reading',
];

export type Distortions = Record<DistortionLabel, number>;

export interface AnalyzeResponse {
  distortions: Distortions;
  cfi: number;
  disclaimer: string;
}

// Plugin-local: what we cache per note (no disclaimer — rendered statically).
export interface NoteAnalysis {
  distortions: Distortions;
  cfi: number;
  analyzedAt: string; // ISO timestamp
}

// Keyed by vault-relative file path.
export type NausicaCache = Record<string, NoteAnalysis>;

// --- Layer 4 (Phase 10): clinician-gated recommendations -------------------
// Shapes mirror src/rules_engine/verification.py::VerifiedRecommendation and
// the /recommend, /turns/{id}/clinician_approval, /turns/{id}/approval_status
// endpoint stubs in src/api/main.py. Skeleton only — Phase 10 wires these up.

export interface SessionTurn {
  role: 'client' | 'counselor';
  text: string;
}

export interface VerifiedRecommendation {
  recommendation: string;
  reasoning_chain: string[];
  safety_flags: string[];
  confidence: number;
  turn_id: string;
  disclaimer: string;
}

export interface ApprovalStatus {
  approved: boolean;
  approved_at?: string;
}

export interface FeedbackReceipt {
  feedback_id: string;
  recorded_at: string;
}
