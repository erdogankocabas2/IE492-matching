"""
Model 2 · Good–Bad (same-class priority + τ-threshold cross-match, heterogeneous abandonment)

Politika: aynı sınıfta bekleyen varsa anında eşleşir; W ≥ τ olan oyuncu karşı sınıfın sıra başıyla eşleşir.
Abandonment kapalıyken (--no-abandon) Phase 2.1, açıkken Phase 2.2.

Kullanım:
  python3 simulation.py                         # rapordaki varsayılanlar
  python3 simulation.py --tau 5 --p 0.7
  python3 simulation.py --no-abandon
  python3 simulation.py --plot                  # figures/ altına grafikleri kaydeder
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'common'))
import skill_report  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--lam', type=float, default=1.0, help='arrival rate λ')
    ap.add_argument('--p', type=float, default=0.6, help='Good share p')
    ap.add_argument('--tau', type=float, default=3.0, help='cross-match threshold τ')
    ap.add_argument('--theta-g', type=float, default=0.08, help='θ_G')
    ap.add_argument('--theta-b', type=float, default=0.04, help='θ_B')
    ap.add_argument('--no-abandon', action='store_true')
    ap.add_argument('--T', type=float, default=20000)
    ap.add_argument('--reps', type=int, default=5)
    ap.add_argument('--plot', action='store_true')
    a = ap.parse_args()
    skill_report.analyse(
        'Model 2 · Good–Bad', ['Good', 'Bad'], ['G', 'B'], a.lam, [a.p, 1 - a.p],
        build_d=lambda t: [[0, t], [t, 0]],
        theta=[a.theta_g, a.theta_b], tau=a.tau, abandon=not a.no_abandon, pool_at_zero=True,
        out_dir=HERE, T=a.T, n_reps=a.reps, plot=a.plot)


if __name__ == '__main__':
    main()
