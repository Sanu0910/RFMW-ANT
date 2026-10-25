"""Grounded coplanar waveguide (CPWG) impedance on the Lite's 2-layer 1.6 mm FR-4 (conformal mapping,
Wadell eq. 3.4.3.1, zero metal thickness). Used to pick the RF line width / gap in make_pcb.py."""
import math


def K_ratio(k):
    kp = math.sqrt(1 - k * k)
    if k <= 1 / math.sqrt(2):
        return math.pi / math.log(2 * (1 + math.sqrt(kp)) / (1 - math.sqrt(kp)))
    return math.log(2 * (1 + math.sqrt(k)) / (1 - math.sqrt(k))) / math.pi


def cpwg(w, s, h, er):
    k = w / (w + 2 * s)
    k3 = math.tanh(math.pi * w / (4 * h)) / math.tanh(math.pi * (w + 2 * s) / (4 * h))
    r, r3 = K_ratio(k), K_ratio(k3)          # K(k)/K(k')
    eeff = (1 + er * r3 / r) / (1 + r3 / r)
    z0 = 60 * math.pi / math.sqrt(eeff) / (r + r3)
    return z0, eeff


if __name__ == "__main__":
    H, ER = 1.51, 4.4        # JLC 2-layer 1.6 mm: ~1.51 mm FR-4 core between the copper, er 4.4 @ 1-2 GHz
    for w, s in ((0.8, 0.25), (1.0, 0.2), (1.2, 0.2), (0.5, 0.25)):
        z, e = cpwg(w, s, H, ER)
        print(f"w {w:.2f} mm  gap {s:.2f} mm  ->  Z0 {z:5.1f} ohm  eeff {e:.2f}")
