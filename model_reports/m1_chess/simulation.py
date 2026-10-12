"""
Model 1 · Chess: White vs Black (FCFS, colour constraint, Exp(theta) abandonment)

report.html'deki sonuçları üretir:
  - Per-colour performance: W_w, W_b, W · L_w, L_b, L · P(abandon_i) (5 replikasyon, %95 CI) ve CTMC
  - p sweep: simulation vs CTMC
  - Patience trade-off (theta sweep, CTMC)
  - Steady-state distribution pi_n (simulation vs CTMC)

Kullanım:
  python3 simulation.py                       # rapordaki varsayılanlar
  python3 simulation.py --p 0.7 --theta 0.1
  python3 simulation.py --no-abandon          # theta = 0 (kararsız sistem)
  python3 simulation.py --plot                # figures/ altına grafikleri kaydeder
"""

import argparse
import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'common'))
import matching_sim as M  # noqa: E402

I = M.INF
D = [[I, 0], [0, I]]  # yalnızca karşı renkle eşleşme


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--lam', type=float, default=1.0, help='arrival rate λ')
    ap.add_argument('--p', type=float, default=0.6, help='White share p')
    ap.add_argument('--theta', type=float, default=0.05, help='abandonment rate θ')
    ap.add_argument('--no-abandon', action='store_true', help='abandonment kapalı (θ = 0)')
    ap.add_argument('--T', type=float, default=20000, help='replikasyon uzunluğu')
    ap.add_argument('--reps', type=int, default=5, help='replikasyon sayısı')
    ap.add_argument('--plot', action='store_true', help='figures/ altına PNG kaydet')
    a = ap.parse_args()

    th = 0.0 if a.no_abandon else a.theta
    probs, theta = [a.p, 1 - a.p], [th, th]
    lam_c = [a.lam * a.p, a.lam * (1 - a.p)]
    ct = M.ctmc_chess(a.lam, a.p, th)

    print(f'Model 1 · Chess  λ = {a.lam}, p = {a.p}, θ = {th}')
    print(f'Experiment setup: {a.reps} replications × T = {a.T:.0f}, warm-up 1000, seeds 1000–{999 + a.reps}\n')
    if not th > 0:
        print('UYARI: θ = 0 → zincir ' + ('null-recurrent' if a.p == 0.5 else 'transient') + '; steady state yok, sayılar T\'ye bağlı.\n')

    # --- per-colour performance ---
    R = M.reps(a.lam, probs, D, theta, T=a.T, n=a.reps)
    cx = lambda x, d=3, pct=False: '–' if ct is None else (f'{100 * x:.1f}%' if pct else f'{x:.{d}f}')
    rows = [
        ['Arrival rate λ_i', f'{lam_c[0]:.2f}', '', f'{lam_c[1]:.2f}', '', f'{a.lam:.2f}', ''],
        ['Players / replication', f'{R["n0"][0]:.0f}', '', f'{R["n1"][0]:.0f}', '', f'{R["T_n"][0]:.0f}', ''],
    ]
    if th > 0:
        rows.append(['P(abandon_i)', M.fmt_ci(R['abRate0'], pct=True), cx(ct['abW'], pct=True), M.fmt_ci(R['abRate1'], pct=True), cx(ct['abB'], pct=True),
                     M.fmt_ci(R['T_abRate'], pct=True), cx(a.p * ct['abW'] + (1 - a.p) * ct['abB'], pct=True)])
    rows += [
        ['Mean wait W_i', M.fmt_ci(R['wAll0']), cx(ct and ct['Ww']), M.fmt_ci(R['wAll1']), cx(ct and ct['Wb']), M.fmt_ci(R['T_wAll']), cx(ct and ct['L'] / a.lam)],
        ['P90 wait (matched)', M.fmt_ci(R['wP900'], 2), '', M.fmt_ci(R['wP901'], 2), '', M.fmt_ci(R['T_wP90'], 2), ''],
        ['P(W = 0)', M.fmt_ci(R['zeroRate0'], pct=True), '', M.fmt_ci(R['zeroRate1'], pct=True), '', '', ''],
        ['Mean queue L_i', M.fmt_ci(R['L0']), cx(ct and ct['Lw']), M.fmt_ci(R['L1']), cx(ct and ct['Lb']), M.fmt_ci(R['T_L']), cx(ct and ct['L'])],
        ['Little λ_i·W_i', f'{lam_c[0] * R["wAll0"][0]:.3f}', '', f'{lam_c[1] * R["wAll1"][0]:.3f}', '', f'{a.lam * R["T_wAll"][0]:.3f}', ''],
    ]
    print('Per-colour performance (mean ± 95% CI | CTMC)')
    print(M.table(['Metric', 'White sim', 'CTMC', 'Black sim', 'CTMC', 'Total sim', 'CTMC'], rows), '\n')

    # --- p sweep ---
    ps = sorted(set([0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, a.p]))
    sweep = []
    for p in ps:
        k, _, _ = M.run(a.lam, [p, 1 - p], D, theta, a.T, seed=42)
        sweep.append((p, k, M.ctmc_chess(a.lam, p, th)))
    rows = []
    for p, k, c in sweep:
        r = [f'{p:.2f}' + (' *' if p == a.p else ''), f'{k["cls"][0]["wAll"]:.3f}', cx(c and c['Ww']), f'{k["cls"][1]["wAll"]:.3f}', cx(c and c['Wb']),
             f'{k["cls"][0]["L"]:.3f}', cx(c and c['Lw']), f'{k["cls"][1]["L"]:.3f}', cx(c and c['Lb'])]
        if th > 0:
            r += [f'{100 * k["cls"][0]["abRate"]:.1f}%', cx(c['abW'], pct=True)]
        rows.append(r)
    head = ['p', 'W_w sim', 'CTMC', 'W_b sim', 'CTMC', 'L_w sim', 'CTMC', 'L_b sim', 'CTMC'] + (['P(ab_w) sim', 'CTMC'] if th > 0 else [])
    print('p sweep · simulation vs CTMC  (* = mevcut p)')
    print(M.table(head, rows), '\n')

    # --- patience trade-off (CTMC) ---
    thetas = [0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0]
    rows = []
    for t in thetas:
        c = M.ctmc_chess(a.lam, a.p, t)
        rows.append([f'{t:g}', f'{1 / t:.1f}', f'{c["L"]:.2f}', f'{c["L"] / a.lam:.2f}', f'{100 * (a.p * c["abW"] + (1 - a.p) * c["abB"]):.1f}%'])
    print(f'Patience trade-off · θ sweep (CTMC, p = {a.p})')
    print(M.table(['θ', '1/θ', 'L', 'W', 'P(abandon)'], rows), '\n')

    with open(os.path.join(HERE, 'p_sweep.csv'), 'w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['p', 'W_w', 'W_b', 'L_w', 'L_b', 'P_ab_w', 'P_ab_b', 'W_w_ctmc', 'W_b_ctmc', 'L_w_ctmc', 'L_b_ctmc'])
        for p, k, c in sweep:
            wr.writerow([p, k['cls'][0]['wAll'], k['cls'][1]['wAll'], k['cls'][0]['L'], k['cls'][1]['L'], k['cls'][0]['abRate'], k['cls'][1]['abRate'],
                         *(c and [c['Ww'], c['Wb'], c['Lw'], c['Lb']] or ['', '', '', ''])])
    print('p sweep tablosu: p_sweep.csv')

    if a.plot:
        plot(a, th, sweep, ct)


def plot(a, th, sweep, ct):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out = os.path.join(HERE, 'figures')
    os.makedirs(out, exist_ok=True)
    ps = [s[0] for s in sweep]
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, (name, col, key) in enumerate([('W_w', '#2a78d6', 'Ww'), ('W_b', '#eb6834', 'Wb')]):
        ax.scatter(ps, [s[1]['cls'][i]['wAll'] for s in sweep], color=col, label=f'{name} simulation', zorder=3)
        if th > 0:
            ax.plot(ps, [s[2][key] for s in sweep], color=col, label=f'{name} CTMC')
    ax.set_xlabel('white share p'); ax.set_ylabel('mean waiting time W_i'); ax.set_title('Colour imbalance · p sweep'); ax.legend(); fig.tight_layout()
    fig.savefig(os.path.join(out, 'p_sweep.png'), dpi=150); plt.close(fig)

    _, H, _ = M.run(a.lam, [a.p, 1 - a.p], D, [th, th], 30000, seed=42, hist=lambda s: s.n_wait[0] - s.n_wait[1])
    ns = sorted(n for n in H if H[n] > 0.002)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(ns, [100 * H[n] for n in ns], color=['#2a78d6' if n > 0 else '#eb6834' if n < 0 else '#8a91a0' for n in ns], label='simulation')
    if ct:
        ax.plot(ns, [100 * ct['dist'].get(n, 0) for n in ns], 'k.-', label='CTMC π_n')
    ax.set_xlabel('state n = N_w − N_b'); ax.set_ylabel('probability (%)'); ax.set_title('Steady-state distribution'); ax.legend(); fig.tight_layout()
    fig.savefig(os.path.join(out, 'steady_state.png'), dpi=150); plt.close(fig)
    print('Grafikler: figures/p_sweep.png, figures/steady_state.png')


if __name__ == '__main__':
    main()
