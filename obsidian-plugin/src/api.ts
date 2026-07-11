// Minimal, dependency-free client for the Nausica backend.

import type { AnalyzeResponse, ApprovalStatus, FeedbackReceipt, SessionTurn, VerifiedRecommendation } from './types';

export function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.trim().replace(/\/+$/, '');
}

/** SHA-256 of note content, hex-encoded. The backend stores only this hash —
 * never the note text or path — keeping the local-first promise. */
export async function sha256Hex(text: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  let hex = '';
  for (const byte of new Uint8Array(digest)) {
    hex += byte.toString(16).padStart(2, '0');
  }
  return hex;
}

export async function analyzeText(
  baseUrl: string,
  text: string,
  authToken: string,
  fileHash: string,
): Promise<AnalyzeResponse> {
  const url = `${normalizeBaseUrl(baseUrl)}/analyze`;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  let res: Response;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({ text, source: 'obsidian', file_hash: fileHash }),
    });
  } catch (err) {
    const reason = err instanceof Error ? err.message : String(err);
    throw new Error(`Could not reach Nausica backend at ${url}: ${reason}`);
  }
  if (res.status === 401) {
    throw new Error('Nausica: unauthorized — log in via Settings → Nausica Cognitive Map.');
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`Nausica API ${res.status}: ${detail || res.statusText}`);
  }
  return (await res.json()) as AnalyzeResponse;
}

/** Exchange email+password for a JWT. Only the token is ever persisted. */
export async function loginForToken(
  baseUrl: string,
  email: string,
  password: string,
): Promise<string> {
  const url = `${normalizeBaseUrl(baseUrl)}/auth/login`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
  } catch (err) {
    const reason = err instanceof Error ? err.message : String(err);
    throw new Error(`Could not reach Nausica backend at ${url}: ${reason}`);
  }
  const body = await res.text().catch(() => '');
  if (!res.ok) {
    let message = body || res.statusText;
    try {
      const parsed = JSON.parse(body) as { detail?: unknown };
      if (typeof parsed.detail === 'string') message = parsed.detail;
    } catch {
      // non-JSON body — keep raw text
    }
    throw new Error(`Nausica login failed: ${message}`);
  }
  return (JSON.parse(body) as { access_token: string }).access_token;
}

// --- Layer 4 (Phase 10): clinician-gated recommendations -------------------
// Skeletons only — signatures + docs, no fetch logic yet. Follow the
// analyzeText/loginForToken pattern above when implementing: normalizeBaseUrl,
// Bearer header when authToken is set, network-error -> "Could not reach…",
// non-2xx -> "Nausica API {status}: {detail}".

/**
 * POST /recommend — run patient text through Layers 1-3 and return the
 * verified recommendation, HELD pending clinician approval (the caller must
 * not display `recommendation`/`reasoning_chain` to the patient until
 * {@link getApprovalStatus} or {@link submitClinicianApproval} confirms
 * `approved: true` — see src/api/main.py::recommend docstring).
 *
 * @param text - the patient's current note/journal text.
 * @param sessionHistory - prior turns in this session, oldest first.
 */
export async function getRecommendation(
  baseUrl: string,
  text: string,
  sessionHistory: SessionTurn[],
  authToken: string,
): Promise<VerifiedRecommendation> {
  throw new Error('Not implemented yet — Phase 10 (see docs/IMPLEMENTATION_PLAN.md §4).');
}

/**
 * POST /turns/{turnId}/clinician_approval — the Layer 4 safety gate. After
 * this resolves, the patient may see the approved recommendation (or
 * `alternativeRecommendation` if the clinician edited it, or generic
 * psychoeducation if `approved` is false).
 */
export async function submitClinicianApproval(
  baseUrl: string,
  turnId: string,
  approved: boolean,
  clinicianNotes: string,
  authToken: string,
  alternativeRecommendation?: string,
): Promise<ApprovalStatus> {
  throw new Error('Not implemented yet — Phase 10 (see docs/IMPLEMENTATION_PLAN.md §4).');
}

/**
 * GET /turns/{turnId}/approval_status — poll before rendering a recommendation
 * to the patient (see {@link getRecommendation} docs on the hold-until-approved
 * contract).
 */
export async function getApprovalStatus(
  baseUrl: string,
  turnId: string,
  authToken: string,
): Promise<ApprovalStatus> {
  throw new Error('Not implemented yet — Phase 10 (see docs/IMPLEMENTATION_PLAN.md §4).');
}

/**
 * POST /turns/{turnId}/feedback — clinician quality judgment on a counselor
 * turn. The endpoint already exists (src/api/main.py::turn_feedback,
 * Phase 7) — this is the plugin-side call still to be wired up, so the
 * shape mirrors `TurnFeedbackRequest` exactly rather than inventing a new
 * one: `goodReframe` maps to `good_reframe`, `correctionText` to
 * `correction_text`. A separate 1-5 patient-outcome rating
 * (`recommendations.patient_feedback_rating`, see the Phase 10 migration)
 * is a different, not-yet-exposed concept — do not conflate the two.
 */
export async function submitFeedback(
  baseUrl: string,
  turnId: string,
  goodReframe: boolean,
  correctionText: string | undefined,
  authToken: string,
): Promise<FeedbackReceipt> {
  throw new Error('Not implemented yet — Phase 10 (see docs/IMPLEMENTATION_PLAN.md §4).');
}
