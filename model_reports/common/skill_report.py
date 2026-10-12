"""
Model 2 ve Model 3 için ortak analiz akışı (report.html'deki tablo ve grafiklerin Python karşılığı):
  - Per-class performance (5 replikasyon, %95 CI)
  - tau sweep (trade-off: cross-match rate ↔ W, L, P(abandon); W_i sınıf bazında)
  - Match-type matrix
  - Validation at end points (tau = 0 single pool, tau = inf separate classes)
"""

import csv
import math
import os

import matching_sim as M

TAUS = [0, 0.5, 1, 2, 3, 4, 6, 8, 12, 16, 20]


def analyse(title, names, letters, lam, probs, build_d, theta, tau, abandon, pool_at_zero, out_dir,
            T=20000, n_reps=5, plot=False, extra=''):
    K = len(names)
    th = theta if abandon else [0.0] * K
    print(f'{title}  λ = {lam}, p = {[round(p, 3) for p in probs]}, τ = {tau}, θ = {th}{extra}')
    print(f'Experiment setup: {n_reps} replications × T = {T:.0f}, warm-up 1000, seeds 1000–{999 + n_reps}; '
          f'τ sweep: {len(TAUS) + 1} nokta × T = {T:.0f}, ortak seed 42\n')

    # --- per-class performance ---
    R = M.reps(lam, probs, build_d(tau), th, T=T, n=n_reps)
    ci = lambda key, d=3, pct=False: M.fmt_ci(R[key], d, pct)
    rows = [['Arrival rate λ_i'] + [f'{lam * p:.2f}' for p in probs] + [f'{lam:.2f}'],
            ['Players / replication'] + [f'{R[f"n{c}"][0]:.0f}' for c in range(K)] + [f'{R["T_n"][0]:.0f}']]
    if abandon:
        rows.append(['P(abandon_i)'] + [ci(f'abRate{c}', pct=True) for c in range(K)] + [ci('T_abRate', pct=True)])
    rows.append(['Cross-match rate'] + [ci(f'crossRate{c}', pct=True) for c in range(K)] + [ci('T_crossRate', pct=True)])
    rows.append(['Mean wait W_i'] + [ci(f'wAll{c}') for c in range(K)] + [ci('T_wAll')])
    if abandon:
        rows.append(['Mean wait W_i (matched)'] + [ci(f'wM{c}') for c in range(K)] + [ci('T_wM')])
    rows.append(['Median wait'] + [ci(f'wMed{c}', 2) for c in range(K)] + ['–'])
    rows.append(['P90 wait'] + [ci(f'wP90{c}', 2) for c in range(K)] + [ci('T_wP90', 2)])
    rows.append(['P(W = 0)'] + [ci(f'zeroRate{c}', pct=True) for c in range(K)] + ['–'])
    rows.append(['Mean queue L_i'] + [ci(f'L{c}') for c in range(K)] + [ci('T_L')])
    rows.append(['Little λ_i·W_i'] + [f'{lam * probs[c] * R[f"wAll{c}"][0]:.3f}' for c in range(K)] + [f'{lam * R["T_wAll"][0]:.3f}'])
    print('Per-class performance (mean ± 95% CI)')
    print(M.table(['Metric'] + names + ['Total'], rows), '\n')

    # --- tau sweep ---
    taus = sorted(set(TAUS + [tau])) + [M.INF]
    sweep = [(t, M.run(lam, probs, build_d(t), th, T, seed=42)[0]) for t in taus]
    lab = lambda t: '∞' if not math.isfinite(t) else f'{t:g}'
    rows = []
    for t, k in sweep:
        tot = k['total']
        r = [lab(t) + (' *' if t == tau else ''), f'{100 * tot["crossRate"]:.1f}%', f'{tot["wAll"]:.3f}'] + \
            [f'{k["cls"][c]["wAll"]:.3f}' for c in range(K)] + [f'{tot["wP90"]:.2f}', f'{tot["L"]:.3f}']
        if abandon:
            r.append(f'{100 * tot["abRate"]:.1f}%')
        rows.append(r)
    head = ['τ', 'cross-match', 'W'] + [f'W_{l}' for l in letters] + ['P90', 'L'] + (['P(abandon)'] if abandon else [])
    print('τ sweep · trade-off  (* = mevcut τ)')
    print(M.table(head, rows), '\n')

    # --- match-type matrix (ana koşu, T = 30 000) ---
    kmain, _, _ = M.run(lam, probs, build_d(tau), th, 30000, seed=42)
    P, N = kmain['pairs'], kmain['n_pairs']
    rows = [[names[i]] + ['·' if j < i else f'{100 * P[i, j] / N:.1f}%' for j in range(K)] for i in range(K)]
    print('Match-type matrix (tüm maçlardaki pay)')
    print(M.table(['Match type'] + names, rows), '\n')

    # --- validation at end points ---
    rows = []
    rel = lambda x, y: f'{100 * abs(x / y - 1):.1f}%' if y > 0 else '–'

    def block(name, an, k):
        rows.append([f'{name} · L', f'{k["total"]["L"]:.3f}', f'{an["L"]:.3f}', rel(k['total']['L'], an['L'])])
        rows.append([f'{name} · cross-match', f'{100 * k["total"]["crossRate"]:.1f}%', f'{100 * an["cross"]:.1f}%',
                     rel(k['total']['crossRate'], an['cross']) if an['cross'] > 0 else '0 by definition'])
        if abandon:
            rows.append([f'{name} · P(abandon)', f'{100 * k["total"]["abRate"]:.2f}%', f'{100 * an["ab"]:.2f}%', rel(k['total']['abRate'], an['ab'])])
        for c in range(K):
            rows.append([f'{name} · W_{letters[c]}', f'{k["cls"][c]["wAll"]:.3f}', f'{an["cls"][c]["W"]:.3f}', rel(k['cls'][c]['wAll'], an['cls'][c]['W'])])

    if pool_at_zero:
        block('τ = 0', M.pool_one(lam, probs, th), sweep[0][1])
    block('τ = ∞', M.separate(lam, probs, th), sweep[-1][1])
    print('Validation at end points (simulation vs analytical)')
    print(M.table(['Metric', 'Simulation', 'Analytical', 'Rel. error'], rows), '\n')

    path = os.path.join(out_dir, 'tau_sweep.csv')
    with open(path, 'w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['tau', 'cross_match', 'W', *[f'W_{l}' for l in letters], 'P90', 'L', 'P_abandon', *[f'L_{l}' for l in letters]])
        for t, k in sweep:
            tot = k['total']
            wr.writerow([t, tot['crossRate'], tot['wAll'], *[k['cls'][c]['wAll'] for c in range(K)], tot['wP90'], tot['L'], tot['abRate'],
                         *[k['cls'][c]['L'] for c in range(K)]])
    print('τ sweep tablosu: tau_sweep.csv')

    if plot:
        _plot(out_dir, names, letters, sweep, tau)


def _plot(out_dir, names, letters, sweep, tau):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cols = ['#2a78d6', '#1baf7a', '#eb6834'] if len(names) == 3 else ['#2a78d6', '#eb6834']
    out = os.path.join(out_dir, 'figures')
    os.makedirs(out, exist_ok=True)
    x = [100 * k['total']['crossRate'] for _, k in sweep]
    y = [k['total']['wAll'] for _, k in sweep]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(x, y, 'k.-')
    for (t, _), xi, yi in zip(sweep, x, y):
        if t in (0, 2, 6, tau) or not math.isfinite(t):
            ax.annotate('τ=∞' if not math.isfinite(t) else f'τ={t:g}', (xi, yi), textcoords='offset points', xytext=(5, 5), fontsize=8)
    ax.set_xlabel('cross-match rate (%)'); ax.set_ylabel('mean waiting time W'); ax.set_title('Trade-off: match quality ↔ waiting time')
    fig.tight_layout(); fig.savefig(os.path.join(out, 'tradeoff.png'), dpi=150); plt.close(fig)

    fin = [(t, k) for t, k in sweep if math.isfinite(t)]
    fig, ax = plt.subplots(figsize=(7, 4))
    for c, (n, l) in enumerate(zip(names, letters)):
        ax.plot([t for t, _ in fin], [k['cls'][c]['wAll'] for _, k in fin], '.-', color=cols[c], label=f'W_{l} · {n}')
    ax.plot([t for t, _ in fin], [k['total']['wAll'] for _, k in fin], 'k--', label='W · total')
    ax.set_xlabel('cross-match threshold τ'); ax.set_ylabel('mean waiting time W_i'); ax.set_title('Waiting time by class'); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(out, 'waiting_by_class.png'), dpi=150); plt.close(fig)
    print('Grafikler: figures/tradeoff.png, figures/waiting_by_class.png')
