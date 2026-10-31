"""(1+4) evolution strategy for retuning the present element (sim_tune.py), scored after the best feed match.

Variables: L1 (driven patch), L2 (parasitic), h (air gap), ins (inset depth). Each candidate is simulated
(port 1, 0.4 mm cells) and scored by tune_match.best(): the worst VSWR over the band after the best two-section
series match on the 100-ohm branch. Four runs per generation; resume-safe (finished tags are re-used).

usage:  python opt_tune.py [--gens 6] [--start "L1=17.07,L2=16.2,h=4,ins=0"] [--band 4.9 6.4]
Log: 03_results/opt_tune_log.txt
"""
import os, json, argparse, subprocess
import numpy as np
import tune_match as TM

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, '..', '03_results')
BOUNDS = dict(L1=(15.0, 19.5), L2=(14.0, 21.0), h=(3.0, 6.5), ins=(0.0, 4.0))
ap = argparse.ArgumentParser()
ap.add_argument('--gens', type=int, default=6)
ap.add_argument('--start', default='L1=17.07,L2=16.2,h=4,ins=0')
ap.add_argument('--band', type=float, nargs=2, default=(4.9, 6.4))
ap.add_argument('--seed', type=int, default=5)
ap.add_argument('--prefix', default='ot')
ap.add_argument('--step', type=float, default=0.15)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)


def score(tag):
    p, g, f, d, P = TM.best(tag, tuple(a.band))
    m = (f >= a.band[0] * 1e9) & (f <= a.band[1] * 1e9)
    return float(((1 + g[m]) / (1 - g[m])).max()), p


def run(batch):
    procs = []
    for tag, p in batch:
        if os.path.exists(os.path.join(R, f'{tag}_S.csv')):
            continue
        s = ','.join(f'{k}={v:.2f}' for k, v in p.items())
        procs.append(subprocess.Popen(['python', 'sim_tune.py', '--tag', tag, '--set', s, '--res', '0.4', '--threads', '4'],
                                      cwd=HERE, stdout=open(os.path.join(HERE, f'log_{tag}.txt'), 'w'), stderr=subprocess.STDOUT))
    for q in procs:
        q.wait()
    return [(tag, p) + score(tag) for tag, p in batch]


log = open(os.path.join(R, 'opt_tune_log.txt'), 'a')
best = {k: float(v) for k, v in (kv.split('=') for kv in a.start.split(','))}
(_, _, bv, bm), = run([(f'{a.prefix}00_0', best)])
log.write(f'{a.prefix}00_0 matched worst VSWR {bv:.2f} {json.dumps(best)}\n'); log.flush()
step = a.step
for gen in range(1, a.gens + 1):
    batch = []
    for k in range(4):
        p = {n: float(np.clip(v + rng.normal() * step * (BOUNDS[n][1] - BOUNDS[n][0]), *BOUNDS[n])) for n, v in best.items()}
        batch.append((f'{a.prefix}{gen:02d}_{k}', p))
    res = run(batch)
    for tag, p, v, m in res:
        log.write(f'{tag} matched worst VSWR {v:.2f} {json.dumps({k: round(x, 2) for k, x in p.items()})}\n')
    tag, p, v, m = min(res, key=lambda r: r[2])
    if v < bv:
        best, bv = p, v; step = min(step * 1.2, 0.3)
    else:
        step *= 0.7
    log.write(f'-- gen {gen}: best matched worst VSWR {bv:.2f} step {step:.3f} {json.dumps({k: round(x, 2) for k, x in best.items()})}\n'); log.flush()
print('best', bv, best)
