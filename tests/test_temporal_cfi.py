"""Temporal CFI Transformer tests — no trained checkpoint or long training needed."""

import pytest

torch = pytest.importorskip("torch")

from src.models.temporal_cfi import TemporalCFITransformer, _collate, _direction_accuracy
from src.utils.config import taxonomy_labels

N = len(taxonomy_labels())


def _toy_sequences():
    # 4 tiny dialogues with a downward (improving) trend
    return [
        [[0.9] * N, [0.7] * N, [0.5] * N],
        [[0.8] * N, [0.6] * N, [0.4] * N, [0.3] * N],
        [[0.7] * N, [0.5] * N],
        [[0.6] * N, [0.5] * N, [0.2] * N],
    ]


def test_forward_shape_and_range():
    model = TemporalCFITransformer(n_labels=N)
    x, _, mask = _collate(_toy_sequences()[:2])
    out = model(x, padding_mask=~mask)
    assert out.shape == x.shape
    assert float(out.min()) >= 0.0 and float(out.max()) <= 1.0


def test_causal_mask_blocks_future():
    """Changing a LATER turn must not change an EARLIER position's output."""
    torch.manual_seed(0)
    model = TemporalCFITransformer(n_labels=N)
    model.eval()
    a = torch.rand(1, 4, N)
    b = a.clone()
    b[0, -1] = torch.rand(N)  # perturb only the last turn
    with torch.no_grad():
        out_a, out_b = model(a), model(b)
    assert torch.allclose(out_a[0, :-1], out_b[0, :-1], atol=1e-6)


def test_collate_padding_and_masked_loss():
    x, y, mask = _collate(_toy_sequences())
    assert x.shape == y.shape and mask.shape == x.shape[:2]
    # shortest dialogue (2 turns) has exactly 1 real position
    assert int(mask[2].sum()) == 1
    model = TemporalCFITransformer(n_labels=N)
    loss = ((model(x, padding_mask=~mask) - y) ** 2)[mask].mean()
    assert torch.isfinite(loss)


def test_micro_train_loss_decreases():
    torch.manual_seed(42)
    model = TemporalCFITransformer(n_labels=N)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    x, y, mask = _collate(_toy_sequences())
    losses = []
    for _ in range(15):
        opt.zero_grad()
        loss = ((model(x, padding_mask=~mask) - y) ** 2)[mask].mean()
        loss.backward()
        opt.step()
        losses.append(float(loss))
    assert losses[-1] < losses[0]


def test_predict_next_output_contract():
    model = TemporalCFITransformer(n_labels=N)
    history = [dict.fromkeys(taxonomy_labels(), 0.8), dict.fromkeys(taxonomy_labels(), 0.6)]
    pred = model.predict_next(history)
    assert set(pred.keys()) == set(taxonomy_labels())
    assert all(0.0 <= v <= 1.0 for v in pred.values())


def test_direction_accuracy_metric():
    cur = torch.tensor([[0.5, 0.5]])
    true = torch.tensor([[0.7, 0.3]])  # up, down
    perfect = torch.tensor([[0.9, 0.1]])
    inverted = torch.tensor([[0.1, 0.9]])
    assert _direction_accuracy(cur, perfect, true) == 1.0
    assert _direction_accuracy(cur, inverted, true) == 0.0
