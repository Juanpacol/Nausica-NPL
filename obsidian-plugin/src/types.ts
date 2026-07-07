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
