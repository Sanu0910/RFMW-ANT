"""Small (1+4) evolution strategy on the wideband element (single-pol, sim_wb_element.py --single).

Cost = mean |S11|^2 over 4-7 GHz + 0.5 * max |S11|^2 (both in linear power).  Four openEMS runs per
generation in parallel; the best design so far is perturbed with a step that shrinks on failure.
Log: 03_results/opt_wb_log.txt (one line per evaluation).  Resume-safe: evaluations already in
03_results (tag optNN_k) are read, not re-run.

usage:  python opt_wb_element.py [--gens 6] [--start "Lp1=20,Lp2=23,Ls=16"]
"""
import os, json, argparse, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, '..', '03_results')
BOUNDS = dict(Lp1=(14, 24), Lp2=(16, 28), h1=(1.5, 5), h2=(2.5, 8), Ls=(9, 20), Lst=(1.5, 9), Ws=(0.8, 3))
ap = argparse.ArgumentParser()
ap.add_argument('--gens', type=int, default=6)
ap.add_argument('--start', default='Lp1=20,Lp2=23,Ls=16,h1=3,h2=5,Lst=4,Ws=1.2')
ap.add_argument('--seed', type=int, default=3)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)


def cost(tag):
    d = np.loadtxt(os.path.join(R, f'{tag}_S.csv'), delimiter=',')
    m = (d[:, 0] >= 4) & (d[:, 0] <= 7)
    g2 = 10 ** (d[m, 1] / 10)
    return g2.mean() + 0.5 * g2.max()


def run(batch):
    procs = []
    for tag, p in batch:
        if os.path.exists(os.path.join(R, f'{tag}_S.csv')):
            continue
        s = ','.join(f'{k}={v:.2f}' for k, v in p.items())
        procs.append(subprocess.Popen(['python', 'sim_wb_element.py', '--single', '--no-nf2ff', '--res', '0.5',
                                       '--threads', '4', '--tag', tag, '--set', f'G=50,{s}'], cwd=HERE,
                                      stdout=open(os.path.join(HERE, f'log_{tag}.txt'), 'w'), stderr=subprocess.STDOUT))
    for q in procs:
        q.wait()
    return [(tag, p, cost(tag)) for tag, p in batch]


best = {k: float(v) for k, v in (kv.split('=') for kv in a.start.split(','))}
log = open(os.path.join(R, 'opt_wb_log.txt'), 'a')
(_, _, bc), = run([('opt00_0', best)])
log.write(f'opt00_0 cost {bc:.4f} {json.dumps(best)}\n'); log.flush()
step = 0.12                                         # relative to each parameter's range
for gen in range(1, a.gens + 1):
    batch = []
    for k in range(4):
        p = {}
        for n, v in best.items():
            lo, hi = BOUNDS[n]
            p[n] = float(np.clip(v + rng.normal() * step * (hi - lo), lo, hi))
        batch.append((f'opt{gen:02d}_{k}', p))
    res = run(batch)
    for tag, p, c in res:
        log.write(f'{tag} cost {c:.4f} {json.dumps({k: round(v, 2) for k, v in p.items()})}\n')
    tag, p, c = min(res, key=lambda r: r[2])
    if c < bc:
        best, bc = p, c; step = min(step * 1.2, 0.25)
    else:
        step *= 0.7
    log.write(f'-- gen {gen}: best cost {bc:.4f} step {step:.3f} {json.dumps({k: round(v, 2) for k, v in best.items()})}\n'); log.flush()
print('best', bc, best)
