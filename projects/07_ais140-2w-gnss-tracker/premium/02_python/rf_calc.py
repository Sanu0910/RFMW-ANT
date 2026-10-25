"""50-ohm line widths for JLC04161H-7628 (L1 over L2, prepreg 7628 0.2104 mm, er 4.4, 35 um Cu).

CPWG: conformal mapping with lower ground (Wadell 3.4.3); microstrip: Hammerstad-Jensen with
thickness correction. Results are cross-checked against JLCPCB's online calculator numbers in the
design notes; order the board with impedance control on the RF nets.
"""
import math

H, ER, T = 0.2104, 4.4, 0.035


def K(k):
    a, b = 1.0, math.sqrt(1 - k * k)
    for _ in range(30):
        a, b = (a + b) / 2, math.sqrt(a * b)
    return math.pi / (2 * a)


def cpwg(w, g, h=H, er=ER):
    a, b = w / 2, w / 2 + g
    k = a / b; kp = math.sqrt(1 - k * k)
    k3 = math.tanh(math.pi * a / (2 * h)) / math.tanh(math.pi * b / (2 * h)); k3p = math.sqrt(1 - k3 * k3)
    q = K(kp) / K(k) * K(k3) / K(k3p)
    eeff = (1 + er * q) / (1 + q)
    return 60 * math.pi / math.sqrt(eeff) / (K(k) / K(kp) + K(k3) / K(k3p)), eeff


def microstrip(w, h=H, er=ER, t=T):
    dw = t / math.pi * (1 + math.log(4 * math.e / math.sqrt((t / h) ** 2 + (1 / math.pi / (w / t + 1.1)) ** 2)))
    u = (w + dw * (1 + 1 / math.cosh(math.sqrt(er - 1))) / 2) / h
    a = 1 + math.log((u ** 4 + (u / 52) ** 2) / (u ** 4 + 0.432)) / 49 + math.log(1 + (u / 18.1) ** 3) / 18.7
    b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
    eeff = (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a * b)
    f = 6 + (2 * math.pi - 6) * math.exp(-(30.666 / u) ** 0.7528)
    z = 60 / math.sqrt(eeff) * math.log(f / u + math.sqrt(1 + (2 / u) ** 2))
    return z, eeff


def solve(fn, target=50.0):
    lo, hi = 0.05, 1.5
    for _ in range(60):
        m = (lo + hi) / 2
        if fn(m)[0] > target:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


if __name__ == "__main__":
    wm = solve(microstrip)
    print(f"microstrip 50R: w = {wm:.3f} mm  eeff={microstrip(wm)[1]:.2f}")
    for g in (0.15, 0.2, 0.25, 0.3):
        w = solve(lambda x: cpwg(x, g))
        print(f"CPWG gap {g:.2f}: w = {w:.3f} mm  eeff={cpwg(w, g)[1]:.2f}")
    for w, g in ((0.33, 0.20), (0.35, 0.25), (0.36, 0.30)):
        print(f"check w={w} g={g}: Z0={cpwg(w, g)[0]:.1f} R")
