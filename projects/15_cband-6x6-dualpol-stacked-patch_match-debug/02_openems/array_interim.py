"""Preliminary array S-parameters from a full-array run that is still going (sim/array_pN port probe files).

The lumped-port voltage/current traces are written while openEMS runs. This takes what is there so far
(truncated time signal, so expect ripple until the field energy has decayed) and computes S_ii and S_ji
the same way openEMS' LumpedPort.CalcPort does: u_inc = (U + Z0 I)/2, u_ref = (U - Z0 I)/2.

usage:  python array_interim.py      (writes 03_results/array_interim_S.csv and array_interim.png)
"""
import os
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, '..', '03_results')
Z0 = 50.0
f = np.linspace(3.5e9, 7.5e9, 401)


def trace(sim, name):
    d = np.loadtxt(os.path.join(sim, name), comments='%')
    return d[:, 0], d[:, 1]


def dft(t, x):
    return np.array([np.sum(x * np.exp(-2j * np.pi * fi * t)) for fi in f]) * (t[1] - t[0])


out, lines = [f / 1e9], []
for exc in (1, 2):
    sim = os.path.join(HERE, 'sim', f'array_p{exc}')
    if not os.path.exists(os.path.join(sim, f'port_ut_{exc}')):
        continue
    U, I = {}, {}
    for k in (1, 2):
        t, u = trace(sim, f'port_ut_{k}'); ti, i = trace(sim, f'port_it_{k}')
        n = min(len(t), len(ti))
        U[k], I[k] = dft(t[:n], u[:n]), dft(ti[:n], i[:n])
    inc = 0.5 * (U[exc] + Z0 * I[exc])
    sii = 0.5 * (U[exc] - Z0 * I[exc]) / inc
    j = 3 - exc
    sji = 0.5 * (U[j] - Z0 * I[j]) / inc
    out += [20 * np.log10(abs(sii)), 20 * np.log10(abs(sji))]
    lines.append((exc, t[n - 1] * 1e9, sii, sji))

hdr = 'f_GHz' + ''.join(f',S{e}{e}_dB,S{3-e}{e}_dB' for e, *_ in lines)
np.savetxt(os.path.join(R, 'array_interim_S.csv'), np.c_[tuple(out)], delimiter=',', header=hdr, fmt='%.4f')

fig, ax = plt.subplots(figsize=(9, 5))
for e, tend, sii, sji in lines:
    ax.plot(f / 1e9, 20 * np.log10(abs(sii)), lw=1.6, label=f'S{e}{e} (port {e}, {"V" if e == 1 else "H"}-pol), {tend:.1f} ns recorded')
    ax.plot(f / 1e9, 20 * np.log10(abs(sji)), lw=1.0, ls='--', label=f'S{3-e}{e} coupling')
for v, ls in ((3, '--'), (2, ':')):
    g = (v - 1) / (v + 1); ax.axhline(20 * np.log10(g), color='k', ls=ls, lw=0.8)
ax.axvspan(4, 7, color='tab:green', alpha=0.06)
ax.set(xlabel='Frequency (GHz)', ylabel='dB (50 ohm)', xlim=(3.5, 7.5), ylim=(-40, 5),
       title='Full 6x6 array - PRELIMINARY (runs not finished, truncated signals)')
ax.grid(alpha=0.3); ax.legend(fontsize=8, loc='lower left')
fig.tight_layout(); fig.savefig(os.path.join(R, 'array_interim.png'), dpi=130)
for e, tend, sii, sji in lines:
    m = (f >= 4e9) & (f <= 7e9); g = abs(sii[m]); v = (1 + g) / (1 - g)
    print(f'port {e}: {tend:.1f} ns recorded, share of 4-7 GHz with VSWR<=3: {(v <= 3).mean()*100:.0f} %, '
          f'best S{e}{e} {20*np.log10(g.min()):.1f} dB at {f[m][np.argmin(g)]/1e9:.2f} GHz')
