"""Clinical progress report (Phase 4) — multi-page PDF via matplotlib PdfPages.

Deviation from the original plan: weasyprint requires native GTK libraries
(libgobject etc.) not present on this machine; matplotlib's PdfPages needs
nothing beyond matplotlib itself and renders the same charts the web UI shows.

Every page carries the research-prototype disclaimer. The report renders only
derived scores (CFI, distortions, archetypes) — raw client text never appears,
so an exported PDF leaks no journal content.

Colors are the validated "Calm Clinical" palette from web/src/theme/tokens.css /
web/src/charts/palette.ts — ported, not re-derived.
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

import matplotlib

matplotlib.use("Agg")  # headless — must precede pyplot import
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

from src.utils.config import taxonomy_labels  # noqa: E402

DISCLAIMER = (
    "Research prototype — not a clinical diagnosis or medical device. "
    "Scores derive from models trained on synthetic data."
)

# Validated palette (web/src/charts/palette.ts) — categorical + CFI ramp anchors
CATEGORICAL = ["#4c77c9", "#0a9187", "#ae6e1f", "#8e66cc", "#c25573"]
BRAND = "#34406b"
CFI_FLEXIBLE = "#379e8f"
CFI_RIGID = "#123f3b"
INK_MUTED = "#5a6178"

LABEL_DISPLAY = {
    "all_or_nothing": "All-or-nothing",
    "overgeneralization": "Overgeneralization",
    "emotional_reasoning": "Emotional reasoning",
    "catastrophizing": "Catastrophizing",
    "mind_reading": "Mind reading",
}


def _stamp(fig: plt.Figure) -> None:
    fig.text(0.5, 0.02, DISCLAIMER, ha="center", fontsize=7, color=INK_MUTED)


def build_report(
    email: str,
    cfi_points: list[dict],
    archetype_summary: dict,
    generated_at: datetime,
) -> bytes:
    """Render the PDF and return its bytes.

    cfi_points: chronological [{"when": iso_str, "cfi": float, "distortions": {...}}].
    archetype_summary: output of dominant_archetype() (+ n_texts).
    """
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        # ---- page 1: header + CFI trajectory --------------------------------
        fig, ax = plt.subplots(figsize=(8.27, 11.69))  # A4 portrait
        fig.subplots_adjust(top=0.78, bottom=0.30)
        fig.text(0.08, 0.94, "Nausica — Cognitive Flexibility Report",
                 fontsize=18, fontweight="bold", color=BRAND)
        fig.text(0.08, 0.905, f"Account: {email}", fontsize=10, color=INK_MUTED)
        fig.text(0.08, 0.885, f"Generated: {generated_at:%Y-%m-%d %H:%M UTC}",
                 fontsize=10, color=INK_MUTED)
        fig.text(0.08, 0.855,
                 f"Texts analyzed: {archetype_summary.get('n_texts', len(cfi_points))}"
                 f"   ·   Dominant pattern: "
                 f"{archetype_summary.get('archetype', '—').replace('_', ' ')}"
                 f"   ·   Trend: {archetype_summary.get('trend') or 'n/a'}",
                 fontsize=11, color="#1a1e2e")

        if cfi_points:
            xs = range(1, len(cfi_points) + 1)
            ys = [p["cfi"] for p in cfi_points]
            ax.axhspan(0.0, 0.35, color=CFI_FLEXIBLE, alpha=0.08)
            ax.plot(xs, ys, color=BRAND, linewidth=2, marker="o", markersize=5)
            ax.set_ylim(0, 1)
            ax.set_xlabel("Analysis # (chronological)")
            ax.set_ylabel("CFI — lower is more flexible")
            ax.set_title("Cognitive Flexibility Index over time", color=BRAND)
            ax.spines[["top", "right"]].set_visible(False)
            ax.grid(axis="y", alpha=0.25)
        else:
            ax.axis("off")
            ax.text(0.5, 0.5, "No analyses yet.", ha="center", fontsize=12,
                    color=INK_MUTED)
        _stamp(fig)
        pdf.savefig(fig)
        plt.close(fig)

        # ---- page 2: distortion distribution + archetype counts -------------
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.27, 11.69))
        fig.subplots_adjust(hspace=0.45, top=0.92, bottom=0.12)

        labels = taxonomy_labels()
        if cfi_points:
            means = [
                sum(p["distortions"].get(label, 0.0) for p in cfi_points) / len(cfi_points)
                for label in labels
            ]
        else:
            means = [0.0] * len(labels)
        order = sorted(range(len(labels)), key=lambda i: -means[i])
        ax1.barh(
            [LABEL_DISPLAY.get(labels[i], labels[i]) for i in order][::-1],
            [means[i] for i in order][::-1],
            color=[CATEGORICAL[i % len(CATEGORICAL)] for i in order][::-1],
            height=0.55,
        )
        ax1.set_xlim(0, 1)
        ax1.set_title("Mean distortion signal across analyses", color=BRAND)
        ax1.spines[["top", "right"]].set_visible(False)

        counts = archetype_summary.get("counts", {})
        if counts:
            names = sorted(counts, key=lambda k: -counts[k])
            ax2.bar(
                [n.replace("_", "\n") for n in names],
                [counts[n] for n in names],
                color=CFI_RIGID, width=0.5,
            )
            ax2.set_title("Archetype frequency", color=BRAND)
            ax2.spines[["top", "right"]].set_visible(False)
            ax2.tick_params(axis="x", labelsize=8)
        else:
            ax2.axis("off")
        _stamp(fig)
        pdf.savefig(fig)
        plt.close(fig)

    return buf.getvalue()
