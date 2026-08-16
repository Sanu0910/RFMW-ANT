# RFMW-ANT

RF / microwave & antenna work.

## Contents

### `mvdr_video/` — MVDR beamforming explainer
An animated, ~2-minute 1080p video explaining the **MVDR (Minimum Variance
Distortionless Response / Capon) adaptive beamformer** — how it steers a beam,
how it places nulls, the maths behind it, and what its inputs are — with a focus
on **anti-jamming** and **anti-spoofing** for GNSS / RF antenna arrays.

Every beam pattern, null, covariance matrix and SINR figure in the video is
computed live from the algorithm (`mvdr_video/mvdr_core.py`), not drawn by hand.

- Video: [`mvdr_video/mvdr_explainer.mp4`](mvdr_video/mvdr_explainer.mp4)
- The maths + how to regenerate it: [`mvdr_video/README.md`](mvdr_video/README.md)
