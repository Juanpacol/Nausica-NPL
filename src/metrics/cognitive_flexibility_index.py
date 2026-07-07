"""Cognitive Flexibility Index (CFI) — the project's core contribution.

CFI operationalizes "cognitive rigidity" as a continuous scalar in [0, 1] instead of
a binary diagnostic label:

    CFI(text) = sum_i( weight_i * p_i )        p_i = calibrated probability of
                                               distortion i in the text

Higher CFI = more rigid thinking. Weights are fixed severity priors from the CBT
literature (configs/data.yaml, rationale in docs/TAXONOMY.md); a learned weighting
head is the documented upgrade path.

The trajectory tracker records CFI turn-by-turn across a reframing dialogue — the
headline evaluation is whether CFI trends downward as the Socratic dialogue advances.

Pure logic: no torch/network dependency, fully unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.utils.config import cfi_weights


def compute_cfi(distortion_probs: dict[str, float], weights: dict[str, float] | None = None) -> float:
    """Weighted aggregation of per-distortion probabilities into one rigidity scalar.

    Unknown labels in the input are ignored; missing labels count as probability 0.
    Result is normalized by total weight so it stays in [0, 1] even if the config
    weights don't sum exactly to 1.
    """
    w = weights if weights is not None else cfi_weights()
    total_weight = sum(w.values())
    if total_weight <= 0:
        raise ValueError("CFI weights must sum to a positive value")
    score = sum(w[label] * min(1.0, max(0.0, distortion_probs.get(label, 0.0))) for label in w)
    return score / total_weight


@dataclass
class TrajectoryPoint:
    turn: int
    cfi: float
    distortions: dict[str, float]


@dataclass
class ReframingTrajectory:
    """CFI evolution across one reframing session (client turns only)."""

    session_id: str
    points: list[TrajectoryPoint] = field(default_factory=list)

    def add_turn(self, distortion_probs: dict[str, float]) -> TrajectoryPoint:
        point = TrajectoryPoint(
            turn=len(self.points) + 1,
            cfi=compute_cfi(distortion_probs),
            distortions=dict(distortion_probs),
        )
        self.points.append(point)
        return point

    @property
    def delta(self) -> float | None:
        """Total CFI change first->last turn. Negative = rigidity decreased (goal)."""
        if len(self.points) < 2:
            return None
        return self.points[-1].cfi - self.points[0].cfi

    @property
    def is_improving(self) -> bool | None:
        d = self.delta
        return None if d is None else d < 0

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "points": [
                {"turn": p.turn, "cfi": p.cfi, "distortions": p.distortions}
                for p in self.points
            ],
            "delta": self.delta,
            "is_improving": self.is_improving,
        }
