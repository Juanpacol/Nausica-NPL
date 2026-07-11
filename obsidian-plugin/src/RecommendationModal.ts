// Layer 4 (Phase 10) — clinician approval gate for a VerifiedRecommendation.
// Skeleton only: signatures + behavior description, no rendering/network
// logic yet. See docs/IMPLEMENTATION_PLAN.md §3 (Layer 4) and §4 (Phase 10)
// for the end-to-end flow this modal sits in the middle of:
//
//   patient writes -> POST /recommend (held) -> clinician notified -> THIS MODAL
//   -> approve/edit/reject -> POST /turns/{id}/clinician_approval
//   -> patient sees approved output (or generic psychoeducation if rejected)
//
// The recommendation must never reach the patient before
// submitClinicianApproval resolves with approved: true — that gate is
// enforced here, not by convention (docs/IMPLEMENTATION_PLAN.md §7).

import { App, Modal } from 'obsidian';
import { submitClinicianApproval } from './api';
import type { VerifiedRecommendation } from './types';

export class RecommendationModal extends Modal {
  private readonly baseUrl: string;
  private readonly authToken: string;
  private readonly recommendation: VerifiedRecommendation;
  /** Free-text notes the clinician attaches to their approve/reject/edit decision. */
  private clinicianNotes = '';
  /** Set when the clinician chooses "Edit" instead of Approve/Reject. */
  private alternativeRecommendation: string | undefined;

  constructor(app: App, baseUrl: string, authToken: string, recommendation: VerifiedRecommendation) {
    super(app);
    this.baseUrl = baseUrl;
    this.authToken = authToken;
    this.recommendation = recommendation;
  }

  /**
   * Render:
   *   1. `reasoning_chain` (Layer 3 output) as an ordered, auditable list —
   *      this is the interpretability guarantee from CLAUDE.md's Layer 3
   *      section made visible to the clinician, not just logged.
   *   2. `recommendation` text + `safety_flags` (if any, styled as warnings).
   *   3. Approve / Edit / Reject controls:
   *      - Approve -> `submitApproval(true, notes)`.
   *      - Edit -> a text area for `alternativeRecommendation`, then
   *        `submitApproval(true, notes)` (approved with a substituted body).
   *      - Reject -> `submitApproval(false, notes)` (patient sees generic
   *        psychoeducation instead — src/api/main.py::submit_clinician_approval).
   *   4. A notes field bound to `this.clinicianNotes`.
   *   5. A submit button wired to `submitApproval`.
   */
  onOpen(): void {
    throw new Error('Not implemented yet — Phase 10 (see docs/IMPLEMENTATION_PLAN.md §4).');
  }

  /**
   * POST /turns/{turn_id}/clinician_approval via
   * {@link submitClinicianApproval}. On success, closes the modal and
   * surfaces a Notice; on failure, keeps the modal open and shows the error
   * inline (the recommendation must stay held, never silently drop through
   * to "approved" on a network error).
   */
  private async submitApproval(approved: boolean, clinicianNotes: string): Promise<void> {
    throw new Error('Not implemented yet — Phase 10 (see docs/IMPLEMENTATION_PLAN.md §4).');
  }

  onClose(): void {
    this.contentEl.empty();
  }
}
