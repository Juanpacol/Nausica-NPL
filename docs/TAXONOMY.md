# Cognitive Distortion Taxonomy (5 types)

Adopted from CBT-LLM (arXiv:2403.16008), grounded in Beck (1963) and Burns (1980).
These 5 labels are the multi-label output space of the distortion classifier and the
input space of the CFI aggregation. Machine-readable copy lives in `configs/data.yaml` —
keep both in sync.

A text can carry **multiple** distortions (multi-label, not mutually exclusive).

---

## 1. `all_or_nothing` — All-or-Nothing Thinking
Viewing situations in absolute, binary categories: total success or total failure,
with no middle ground. Linguistic markers: *always, never, completely, totally,
everything, nothing, perfect, ruined*.

- "If I don't get this scholarship, my entire career is over."
- "I made one mistake in the presentation, so the whole thing was a disaster."
- "Either I do this perfectly or there's no point in doing it at all."

## 2. `overgeneralization` — Overgeneralization
Drawing a sweeping, permanent conclusion from a single event or limited evidence.
Markers: *every time, this always happens to me, I'll never, nobody ever*.

- "She didn't reply to my message — nobody ever wants to talk to me."
- "I failed one exam. I fail everything I try."
- "This always happens to me; things will never work out."

## 3. `emotional_reasoning` — Emotional Reasoning
Treating a feeling as evidence for a fact: "I feel it, therefore it is true."
Markers: *I feel like a..., it feels hopeless so it is, I feel stupid so I must be*.

- "I feel like a burden, so I must actually be one."
- "I feel so anxious about the flight — that means something bad will happen."
- "I feel worthless, which proves I really am worthless."

## 4. `catastrophizing` — Catastrophizing
Expecting the worst possible outcome and inflating its probability or severity;
"what if" spirals. Markers: *what if, it will be a disaster, I couldn't survive,
worst thing ever*.

- "If I stumble in the interview, I'll never get hired anywhere and end up broke."
- "My chest hurt for a second — what if it's a heart attack?"
- "If my partner leaves me, my life will literally be over."

## 5. `mind_reading` — Mind Reading
Assuming, without evidence, that you know what others are thinking (usually something
negative about you). Markers: *they must think, I know she hates me, everyone can tell*.

- "My boss didn't smile at me this morning — he obviously thinks I'm incompetent."
- "Everyone at the party could tell how awkward I am."
- "She's quiet today; I know she's angry at me."

---

## CFI severity weights (initial, fixed)

Used by `src/metrics/cognitive_flexibility_index.py` (values in `configs/data.yaml`).
Rationale: distortions that most strongly predict rigidity/helplessness in the CBT
literature weigh higher. These are a defensible starting point, to be revisited after
Phase 2 calibration — a learned weighting head is the documented upgrade path.

| Label | Weight |
|---|---|
| all_or_nothing | 0.25 |
| overgeneralization | 0.25 |
| catastrophizing | 0.20 |
| emotional_reasoning | 0.15 |
| mind_reading | 0.15 |

CFI = Σ (weight_i × calibrated_probability_i) ∈ [0, 1]. Higher = more rigid.
