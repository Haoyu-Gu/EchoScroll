# M2 · Affective Projection

Maps the fused multimodal feature `z` (output of M1) to a 2D **valence-arousal**
vector on the Russell circumplex. This V-A vector is the affective control
signal consumed by M4 (MusicGen) and exposed to the user in the front-end
emotion panel.

## I/O contract

- **Input**: `z: torch.Tensor` of shape `(B, d)`, `d = 768` by default.
- **Output**: `(v_hat, a_hat)` each `(B,)`, in `[-1, 1]` (tanh-squashed).
- **Loss** (training-time only): `va_loss(pred_va, target_va, z, labels_categorical=None, tau=0.1, lam=0.5)`
  returning `{"loss", "mse", "contrastive"}`.
- **Utility**: `va_to_word(v, a) -> str` returns a Russell-style affect word.

## Model

`AffectiveProjection` is a 2-layer MLP `g_phi: R^d -> R^2` with GELU and a
final `tanh`. Tiny by design — the heavy lifting happens upstream in M1.

## Hyperparameters (defaults)

| name        | default | meaning                                 |
|-------------|--------:|-----------------------------------------|
| `in_dim`    | 768     | dimensionality of `z` from M1           |
| `hidden_dim`| 256     | MLP hidden width                        |
| `tau`       | 0.1     | NT-Xent temperature                     |
| `lam`       | 0.5     | weight of the contrastive term in `L_VA`|

## Loss

`L_VA = MSE(pred, target) + lam * InfoNCE(z | labels_categorical)`

The contrastive term is a supervised NT-Xent: positives = same coarse emotion
class, negatives = the rest of the batch. If `labels_categorical=None` the
contrastive term is exactly 0 (i.e. plain regression).

## V-A quadrant map (Russell circumplex)

```
                    arousal +1
                        |
      tense/anxious  -- + -- powerful
                        |
                        |
   sad/depressed  <-----+----->  excited/joyful
            valence -1  |  +1
                        |
                        |
      melancholic   -- + --  calm/serene
                        |
                       -1
```

Special centre region (`sqrt(v^2+a^2) < 0.15`) and the mild
positive-valence / low-arousal band are mapped to **"tender"**, matching the
soft/gentle sector used in ArtEmis-style art-emotion annotations.

The eight returned words are:

`{"calm/serene", "tender", "sad/depressed", "tense/anxious",`
` "excited/joyful", "powerful", "melancholic", "bored"}`.

## Run the demo

```bash
pip install -r requirements.txt
python demo.py
```

The demo:

1. randomly initialises `AffectiveProjection`,
2. feeds a `(4, 768)` random `z`, prints `(v_hat, a_hat)` and the word label,
3. builds a fake `target_va` + class labels and prints the three loss
   components (MSE, contrastive, total), then repeats without labels.

CPU-only. No training loop, no external data, no cross-module imports.
