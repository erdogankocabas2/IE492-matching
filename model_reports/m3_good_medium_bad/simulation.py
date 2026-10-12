"""
Model 3 · Good–Medium–Bad (neighbour threshold τ, far threshold 2τ, heterogeneous abandonment)

Threshold matrix d: aynı sınıf 0, komşu (G–M, M–B) τ, uç (G–B) 2τ; --no-far ile G–B kapalı (∞).
Önce en küçük eşik, eşitlikte en uzun bekleyen.

Kullanım:
  python3 simulation.py                         # rapordaki varsayılanlar
  python3 simulation.py --pg 0.3 --pb 0.3 --tau 2
  python3 simulation.py --no-far --no-abandon
  python3 simulation.py --plot
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'common'))
import matching_sim as M  # noqa: E402
import skill_report  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--lam', type=float, default=1.0, help='arrival rate λ')
    ap.add_argument('--pg', type=float, default=0.2, help='Good share p_G')
    ap.add_argument('--pb', type=float, default=0.3, help='Bad share p_B (p_M = 1 − p_G − p_B)')
    ap.add_argument('--tau', type=float, default=3.0, help='neighbour threshold τ')
    ap.add_argument('--no-far', action='store_true', help='G–B maçını kapat')
    ap.add_argument('--theta-g', type=float, default=0.08)
    ap.add_argument('--theta-m', type=float, default=0.06)
    ap.add_argument('--theta-b', type=float, default=0.04)
    ap.add_argument('--no-abandon', action='store_true')
    ap.add_argument('--T', type=float, default=20000)
    ap.add_argument('--reps', type=int, default=5)
    ap.add_argument('--plot', action='store_true')
    a = ap.parse_args()
    if a.pg + a.pb >= 1:
        ap.error('p_G + p_B < 1 olmalı')
    far = not a.no_far

    def build_d(t):
        f = 2 * t if far else M.INF
        return [[0, t, f], [t, 0, t], [f, t, 0]]

    skill_report.analyse(
        'Model 3 · Good–Medium–Bad', ['Good', 'Medium', 'Bad'], ['G', 'M', 'B'], a.lam, [a.pg, 1 - a.pg - a.pb, a.pb],
        build_d=build_d, theta=[a.theta_g, a.theta_m, a.theta_b], tau=a.tau, abandon=not a.no_abandon,
        pool_at_zero=far, out_dir=HERE, T=a.T, n_reps=a.reps, plot=a.plot,
        extra=f', G–B {"2τ" if far else "kapalı"}')


if __name__ == '__main__':
    main()
