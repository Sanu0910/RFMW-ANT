"""2D finite-difference (Laplace) Z0 of a microstrip in a closed channel, to size the cage walls.
Cross-section: ground plane, substrate h (er), strip W x t on top, coplanar top ground beyond the clearance g,
cage side walls at distance d from the strip edge, lid at a above the substrate.
    Z0 = 1 / (c * sqrt(C * C_air))."""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as sla

EPS0 = 8.854187817e-12
C_LIGHT = 299792458.0


def capacitance(W, t, h, er, d, a, g=None, step=0.02):
    """Per-unit-length capacitance (F/m) of the half-structure (symmetry at x = 0), times 2."""
    xs_end = W / 2 + d
    nx = int(round(xs_end / step)); ny = int(round((h + a) / step))
    X = (np.arange(nx + 1)) * step; Y = (np.arange(ny + 1)) * step
    V = np.full((ny + 1, nx + 1), np.nan)
    fixed = np.zeros_like(V, bool)
    # metal: bottom ground (y=0), lid (y=h+a), wall (x=xs_end)
    V[0, :] = 0; fixed[0, :] = True
    V[-1, :] = 0; fixed[-1, :] = True
    V[:, -1] = 0; fixed[:, -1] = True
    jh = int(round(h / step)); jt = int(round((h + t) / step))
    strip = X <= W / 2 + 1e-9
    for j in range(jh, max(jt, jh + 1) + 0):
        V[j, strip] = 1.0; fixed[j, strip] = True
    V[jh, strip] = 1.0; fixed[jh, strip] = True
    if g is not None:                                  # coplanar top ground from W/2+g outward
        cg = X >= W / 2 + g - 1e-9
        V[jh, cg] = 0.0; fixed[jh, cg] = True
    # permittivity per cell row (cell between rows j and j+1)
    eps_c = np.where((np.arange(ny) + 0.5) * step < h, er, 1.0)
    idx = -np.ones(V.shape, int); free = ~fixed; idx[free] = np.arange(free.sum())
    rows, cols, vals = [], [], []; b = np.zeros(free.sum())
    for j in range(ny + 1):
        for i in range(nx + 1):
            k = idx[j, i]
            if k < 0: continue
            # neighbours with face permittivities (average of adjacent cells)
            eu = eps_c[j] if j < ny else 1.0
            ed = eps_c[j - 1] if j > 0 else eps_c[0]
            eh = (eu + ed) / 2
            nb = []
            if j + 1 <= ny: nb.append((j + 1, i, eu))
            if j - 1 >= 0: nb.append((j - 1, i, ed))
            if i + 1 <= nx: nb.append((j, i + 1, eh))
            if i - 1 >= 0: nb.append((j, i - 1, eh))
            else: nb.append((j, i + 1, eh))           # symmetry plane x = 0 (Neumann): mirror
            diag = 0.0
            for jj, ii, e in nb:
                diag += e
                kk = idx[jj, ii]
                if kk >= 0: rows.append(k); cols.append(kk); vals.append(-e)
                else: b[k] += e * V[jj, ii]
            rows.append(k); cols.append(k); vals.append(diag)
    A = sp.csr_matrix((vals, (rows, cols)), shape=(free.sum(), free.sum()))
    sol = sla.spsolve(A, b); Vf = V.copy(); Vf[free] = sol
    # charge from energy: W = 1/2 C V^2, energy = 1/2 sum eps |grad V|^2
    gx = np.diff(Vf, axis=1) / step; gy = np.diff(Vf, axis=0) / step
    ex = (gx[:-1, :] ** 2 + gx[1:, :] ** 2) / 2; ey = (gy[:, :-1] ** 2 + gy[:, 1:] ** 2) / 2
    energy = np.sum(eps_c[:, None] * (ex + ey)) * step * step       # (unitless grid), per metre: eps0 * ...
    return 2 * EPS0 * energy                                        # x2: both halves (V = 1)


def z0(W, t, h, er, d, a, g=None, step=0.02):
    c1 = capacitance(W, t, h, er, d, a, g, step)
    c0 = capacitance(W, t, h, 1.0, d, a, g, step)
    return 1.0 / (C_LIGHT * np.sqrt(c1 * c0)), c1 / c0


if __name__ == "__main__":
    W, t, h, er = 1.686, 0.035, 0.762, 3.48
    print("open (d=20, a=20):  Z0 %.2f  eeff %.3f" % z0(W, t, h, er, 20, 20, None, 0.04))
    for g in (4.215,):
        for d, a in ((20, 20), (4.515, 4.0), (3.5, 4.0), (3.0, 4.0), (2.5, 4.0), (2.0, 4.0)):
            print("pour g=%.2f, wall d=%.2f, lid a=%.1f:  Z0 %.2f  eeff %.3f" % ((g, d, a) + tuple(z0(W, t, h, er, d, a, g if g < d else None, 0.04))))
