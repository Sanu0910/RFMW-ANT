# MVDR Beamforming — an animated explainer

A ~2-minute, 1080p video that explains the **MVDR (Minimum Variance
Distortionless Response)** adaptive beamformer — Capon's beamformer — from the
ground up, with an emphasis on its use for **anti-jamming** and **anti-spoofing**
in GNSS / RF antenna arrays.

Everything on screen — the beam patterns, the nulls, the covariance matrix, the
eigenvalues and the SINR numbers — is **computed live from the algorithm**
(`mvdr_core.py`), not drawn by hand. The animation *is* the algorithm running.

| file | what it is |
|------|------------|
| `mvdr_core.py`   | The MVDR maths: steering vectors, covariance, weights, beam patterns, SINR. Self-contained and unit-tested. |
| `render.py`      | The animation engine — draws each frame with matplotlib and pipes it to ffmpeg. |
| `mvdr_explainer.mp4` | The rendered video (1920×1080, 30 fps). |

---

## What the video covers

1. **The problem** — many signals hit the array at once; the wanted satellite is
   the weakest, buried under jammers and a spoofer.
2. **The input** — a *snapshot* `x(t)`: one complex sample from each of the `M`
   antenna elements. That vector is all the algorithm ever sees.
3. **The steering vector** `a(θ)` — the phase ramp a plane wave from angle θ
   stamps across the array; the array's "fingerprint" for a direction.
4. **The covariance matrix** `R = E[x xᴴ]` — how the elements correlate; strong
   jammers dominate it (shown via its eigenvalues).
5. **The optimisation** — *minimise output power* subject to *unit gain on the
   look direction*.
6. **The weights** — the closed-form MVDR solution.
7. **Steering + nulling** — the real beam pattern: main lobe locked on the
   satellite, deep nulls dug automatically onto every interferer.
8. **Anti-jam / anti-spoof** — why this defeats jammers (CRPA nulling) and
   spoofers (direction-of-arrival discrimination), with a before/after SINR.
9. **The whole pipeline** — `x(t) → R̂ → w → steer + null`.

---

## The maths, in one page

### Signal model (uniform linear array, narrowband)

For an array of `M` elements spaced `d` wavelengths apart, a plane wave from
angle `θ` (measured from broadside) arrives at successive elements with a
constant extra path `d·sinθ`, i.e. a constant phase step. That phase ramp is the
**steering vector**:

```
a(θ) = [ 1, e^{jψ}, e^{j2ψ}, …, e^{j(M-1)ψ} ]ᵀ ,   ψ = 2π (d/λ) sinθ
```

A received **snapshot** superposes the desired signal, the interferers and noise:

```
x(t) = a(θ_d) s(t)  +  Σ_j a(θ_j) i_j(t)  +  n(t)
```

### Spatial covariance

```
R = E[ x(t) xᴴ(t) ]                         (the ideal)
R̂ = (1/N) Σ_{t=1..N} x(t) xᴴ(t)             (estimated from N snapshots)
```

Because a jammer can be 10³–10⁵× stronger than the satellite, `R` is dominated by
a few huge eigenvalues — one per strong source. That is exactly the structure
MVDR exploits.

### The MVDR problem (Capon, 1969)

Combine the elements as `y(t) = wᴴ x(t)` and choose `w` to

```
minimise    wᴴ R w            ← "minimum variance": least total output power
subject to  wᴴ a(θ_d) = 1     ← "distortionless": unit gain on the look direction
```

Minimising the total power drives down *everything* the array receives — but the
constraint forbids it from touching the desired direction. So the only place left
to spend power reduction is on the interferers: the algorithm sinks **nulls**
onto them automatically. It never needs to be told where the jammers are.

### The closed-form solution (via a Lagrange multiplier)

```
              R⁻¹ a(θ_d)
w_MVDR = ─────────────────────
          aᴴ(θ_d) R⁻¹ a(θ_d)
```

`R⁻¹` whitens (cancels) the dominant interference; the denominator is a scalar
that re-imposes unit gain on `θ_d`. The array's gain pattern is then
`G(θ) = |w_MVDRᴴ a(θ)|` — 0 dB on the satellite, deep notches on the jammers.

### Why it beats jamming and spoofing

- **Anti-jamming.** A high-power jammer dominates `R`, so MVDR spends the array's
  degrees of freedom (an `M`-element array can null up to `M−1` sources) sinking a
  deep null on its bearing. This is the **CRPA** (Controlled Reception Pattern
  Antenna) principle used in protected GNSS receivers. (The `w = R⁻¹u`
  *power-inversion* variant nulls strong signals without even knowing `θ_d`.)
- **Anti-spoofing.** A spoofer fakes the whole constellation from a *single*
  antenna, so every counterfeit PRN arrives from **one** direction — whereas real
  satellites are spread across the sky. That single shared direction-of-arrival is
  a spatial signature MVDR (and DOA estimation via the Capon spectrum
  `P(θ) = 1 / aᴴ(θ) R⁻¹ a(θ)`) can detect and null out.

---

## Scenario used in the video

| source | angle | power vs noise |
|--------|------:|---------------:|
| satellite (desired) | +20° | 0 dB (weak) |
| jammer 1 | −42° | +40 dB |
| jammer 2 | +58° | +40 dB |
| spoofer | −14° | +30 dB |

Array: `M = 8` elements, half-wavelength spacing. Running `mvdr_core.py` prints
the verification:

```
Look direction (satellite): +20 deg  -> gain  +0.00 dB
Jammer  @ -42 deg  -> MVDR gain -125.72 dB  (deep null)
Jammer  @ +58 deg  -> MVDR gain  -60.60 dB  (deep null)
Spoofer @ -14 deg  -> MVDR gain  -62.42 dB  (deep null)
Output SINR  conventional : -13.74 dB
Output SINR  MVDR         :  +8.94 dB
SINR improvement          : +22.69 dB
```

---

## Regenerating the video

```bash
pip install numpy matplotlib imageio-ffmpeg      # ffmpeg is bundled with imageio-ffmpeg

python3 mvdr_core.py            # print the algorithm's numbers (self-test)
python3 render.py --preview     # quick contact sheet of key frames -> preview.png
python3 render.py               # full render -> mvdr_explainer.mp4  (~6 min)

# handy while tuning:
python3 render.py --fps 24 --range 86,107   # render just the beam-pattern scene
```

The render draws each frame in matplotlib (dark theme, `mathtext` for the
equations — no LaTeX needed) and streams raw RGB to the ffmpeg binary that ships
with `imageio-ffmpeg`, so there are no system-level media dependencies.
