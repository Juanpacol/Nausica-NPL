"""add recommendations table for Layer 4 tracking

Revision ID: d4f8b2c19a3e
Revises: fc0a01f4b7da
Create Date: 2026-07-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4f8b2c19a3e'
down_revision: Union[str, Sequence[str], None] = 'fc0a01f4b7da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the `recommendations` table (Phase 10, Layer 4).

    Mirrors src.db.models.Recommendation:
    - id (PK, str uuid)
    - user_id (FK -> users.id, the patient)
    - session_id (FK -> sessions.id)
    - turn_id (FK -> turns.id)
    - recommendation_json (JSON — the VerifiedRecommendation output from Layer 3)
    - clinician_id (FK -> users.id, nullable — set on review)
    - clinician_approved (bool, nullable — None until reviewed; never
      defaults to True, per the Layer 4 safety gate)
    - clinician_notes (text, nullable)
    - alternative_recommendation (text, nullable)
    - approved_at (timestamp, nullable)
    - patient_feedback_rating (int, nullable — 1-5)
    - created_at, updated_at (timestamp, non-null)

    SKELETON: raises until Phase 10 fills in the `op.create_table(...)` /
    `op.create_index(...)` calls. Do not run `alembic upgrade head` against
    this revision until then.
    """
    raise NotImplementedError("Phase 10 — see src.db.models.Recommendation for the target schema.")


def downgrade() -> None:
    """Drop the `recommendations` table."""
    raise NotImplementedError("Phase 10 — see upgrade() for the target schema.")
