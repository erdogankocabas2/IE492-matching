# %% [markdown]
# # IE492 — Aşama 1: Renk bazlı FCFS satranç eşleştirmesi (terkli model)
#
# **Model**
# - Oyuncular Poisson($\lambda$) süreciyle gelir.
# - Her oyuncu $p$ olasılıkla **beyaz**, $1-p$ olasılıkla **siyah**.
# - FCFS: sıranın başındaki beyaz ile sıranın başındaki siyah anında eşleşir. Bu yüzden aynı anda yalnızca tek renk bekleyebilir.
# - **Terk:** her bekleyen oyuncunun sabrı $\text{Exp}(\theta)$; sabrı biten oyuncu kuyruktan ayrılır.
#
# **KPI'lar (renk bazında):** eşleşme oranı, terk oranı, ortalama / medyan / p90 bekleme, hiç beklemeden eşleşme oranı P(W=0), zaman ortalamalı kuyruk uzunluğu (L_i).
#
# **Analitik Karşılaştırma & CTMC:**
# $X(t) = \#\text{beyaz} - \#\text{siyah}$ tek boyutlu bir doğum-ölüm zinciri (Birth-Death Process / CTMC).
# - $n > 0$ iken $n \to n+1$ geçiş hızı $p\lambda$, $n \to n-1$ geçiş hızı $(1-p)\lambda + n\theta$.
# - $n < 0$ iken $n \to n-1$ geçiş hızı $(1-p)\lambda$, $n \to n+1$ geçiş hızı $p\lambda + |n|\theta$.
# Durağan dağılımdan Little Yasası:
# $$E[W_\text{beyaz}] = \frac{L_\text{beyaz}}{p\lambda}, \qquad P(\text{beyaz terk}) = \frac{\theta L_\text{beyaz}}{p\lambda}$$

# %%
import argparse
import csv
import heapq
import math
import os
import sys
from collections import deque

import numpy as np
import matplotlib.pyplot as plt

WHITE, BLACK = 0, 1
COLOR_NAME = {WHITE: "beyaz", BLACK: "siyah"}
WAITING, MATCHED, ABANDONED = 0, 1, 2

# %% [markdown]
# ## Simülasyon Motoru

# %%
def simulate(lam=1.0, p=0.6, theta=0.05, T=20_000, warmup=1_000.0, seed=42):
    """
    Renk bazlı FCFS satranç eşleştirme olay tabanlı simülasyonu.
    """
    rng = np.random.default_rng(seed)

    arrival, color, end, status = [], [], [], []
    queues = {WHITE: deque(), BLACK: deque()}
    n_waiting = {WHITE: 0, BLACK: 0}
    abandon_heap = []

    area = {WHITE: 0.0, BLACK: 0.0}
    last_t = 0.0
    trace_t, trace_x = [0.0], [0]

    def advance(to):
        nonlocal last_t
        start = max(last_t, warmup)
        if to > start:
            for c in (WHITE, BLACK):
                area[c] += n_waiting[c] * (to - start)
        last_t = to

    def record_trace(t):
        trace_t.append(t)
        trace_x.append(n_waiting[WHITE] - n_waiting[BLACK])

    t = 0.0
    while True:
        t_next = t + rng.exponential(1.0 / lam)

        while abandon_heap and abandon_heap[0][0] <= min(t_next, T):
            d, i = heapq.heappop(abandon_heap)
            if status[i] == WAITING:
                advance(d)
                status[i], end[i] = ABANDONED, d
                n_waiting[color[i]] -= 1
                record_trace(d)

        if t_next > T:
            advance(T)
            break

        t = t_next
        advance(t)
        c = WHITE if rng.random() < p else BLACK
        other = 1 - c

        i = len(arrival)
        arrival.append(t)
        color.append(c)
        end.append(np.nan)
        status.append(WAITING)

        partner = None
        while queues[other]:
            j = queues[other].popleft()
            if status[j] == WAITING:
                partner = j
                break

        if partner is not None:
            status[partner], end[partner] = MATCHED, t
            status[i], end[i] = MATCHED, t
            n_waiting[other] -= 1
        else:
            queues[c].append(i)
            n_waiting[c] += 1
            if theta > 0:
                heapq.heappush(abandon_heap, (t + rng.exponential(1.0 / theta), i))
        record_trace(t)

    players = {
        "arrival": np.array(arrival),
        "color": np.array(color),
        "end": np.array(end),
        "status": np.array(status),
    }
    span = T - warmup
    avg_queue = {c: area[c] / span for c in (WHITE, BLACK)}
    trace = (np.array(trace_t), np.array(trace_x))
    return players, avg_queue, trace


def compute_kpis(players, avg_queue, warmup=1_000.0):
    kpis = {}
    for c in (WHITE, BLACK):
        sel = (players["color"] == c) & (players["arrival"] >= warmup) & (players["status"] != WAITING)
        st = players["status"][sel]
        w = players["end"][sel] - players["arrival"][sel]
        w_matched = w[st == MATCHED]
        kpis[COLOR_NAME[c]] = {
            "oyuncu sayisi": int(sel.sum()),
            "eslesme orani": float((st == MATCHED).mean()) if len(st) > 0 else 0.0,
            "terk orani": float((st == ABANDONED).mean()) if len(st) > 0 else 0.0,
            "ort. bekleme (tumu)": float(w.mean()) if len(w) > 0 else 0.0,
            "ort. bekleme (eslesen)": float(w_matched.mean()) if len(w_matched) > 0 else 0.0,
            "medyan bekleme (eslesen)": float(np.median(w_matched)) if len(w_matched) > 0 else 0.0,
            "p90 bekleme (eslesen)": float(np.percentile(w_matched, 90)) if len(w_matched) > 0 else 0.0,
            "beklemeden eslesme orani": float((w == 0).mean()) if len(w) > 0 else 0.0,
            "ort. kuyruk uzunlugu": avg_queue[c],
        }

    sel_all = (players["arrival"] >= warmup) & np.isin(players["status"], [MATCHED, ABANDONED])
    st_all = players["status"][sel_all]
    w_all = players["end"][sel_all] - players["arrival"][sel_all]
    w_m_all = w_all[st_all == MATCHED]

    kpis["toplam"] = {
        "oyuncu sayisi": int(len(st_all)),
        "eslesme orani": float((st_all == MATCHED).mean()) if len(st_all) > 0 else 0.0,
        "terk orani": float((st_all == ABANDONED).mean()) if len(st_all) > 0 else 0.0,
        "ort. bekleme (tumu)": float(w_all.mean()) if len(w_all) > 0 else 0.0,
        "ort. bekleme (eslesen)": float(w_m_all.mean()) if len(w_m_all) > 0 else 0.0,
        "p90 bekleme (eslesen)": float(np.percentile(w_m_all, 90)) if len(w_m_all) > 0 else 0.0,
        "ort. kuyruk uzunlugu": avg_queue[WHITE] + avg_queue[BLACK],
    }
    return kpis


def print_kpis(kpis):
    print("=" * 66)
    print(f"{'KPI':<28}{'Beyaz':>18}{'Siyah':>18}")
    print("-" * 66)
    metrics = [
        "oyuncu sayisi", "eslesme orani", "terk orani", "ort. bekleme (tumu)",
        "ort. bekleme (eslesen)", "medyan bekleme (eslesen)", "p90 bekleme (eslesen)",
        "beklemeden eslesme orani", "ort. kuyruk uzunlugu"
    ]
    for m in metrics:
        v_w = kpis["beyaz"][m]
        v_b = kpis["siyah"][m]
        if m in ("eslesme orani", "terk orani", "beklemeden eslesme orani"):
            print(f"{m:<28}{f'%{100*v_w:.2f}':>18}{f'%{100*v_b:.2f}':>18}")
        elif m == "oyuncu sayisi":
            print(f"{m:<28}{int(v_w):>18d}{int(v_b):>18d}")
        else:
            print(f"{m:<28}{v_w:>18.3f}{v_b:>18.3f}")
    print("-" * 66)
    tot = kpis["toplam"]
    print(f"Toplam Ortalama Kuyruk (L)    : {tot['ort. kuyruk uzunlugu']:>10.3f}")
    print(f"Toplam Ortalama Bekleme (W)   : {tot['ort. bekleme (tumu)']:>10.3f}")
    print(f"Genel Terk Oranı              : %{100*tot['terk orani']:>9.2f}")
    print("=" * 66)


# %% [markdown]
# ## Analitik Model (Birth-Death CTMC)

# %%
def ctmc_abandon(lam, p, theta, N=500):
    """
    X(t) = #beyaz - #siyah tek boyutlu CTMC analitik çözücüsü.
    """
    if not theta > 0:
        return None
    a, b = p * lam, (1.0 - p) * lam
    log_pi = {0: 0.0}
    for n in range(1, N):
        log_pi[n] = log_pi[n - 1] + math.log(a) - math.log(b + n * theta)
        log_pi[-n] = log_pi[-(n - 1)] + math.log(b) - math.log(a + n * theta)
    m = max(log_pi.values())
    pi = {n: math.exp(v - m) for n, v in log_pi.items()}
    Z = sum(pi.values())
    pi = {n: v / Z for n, v in pi.items()}
    L_w = sum(n * v for n, v in pi.items() if n > 0)
    L_b = sum(-n * v for n, v in pi.items() if n < 0)
    return {
        "dist": pi,
        "beyaz": {"ort. bekleme (tumu)": L_w / a, "terk orani": theta * L_w / a, "ort. kuyruk uzunlugu": L_w},
        "siyah": {"ort. bekleme (tumu)": L_b / b, "terk orani": theta * L_b / b, "ort. kuyruk uzunlugu": L_b},
        "toplam": {"ort. kuyruk uzunlugu": L_w + L_b, "ort. bekleme (tumu)": (L_w + L_b) / lam,
                   "terk orani": p * (theta * L_w / a) + (1.0 - p) * (theta * L_b / b)},
        "Lw": L_w, "Lb": L_b, "L": L_w + L_b, "Ww": L_w / a, "Wb": L_b / b,
        "abW": theta * L_w / a, "abB": theta * L_b / b
    }


T975 = [math.nan, 12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262]

def run_replications(lam, p, theta, T=20_000, n_reps=5, warmup=1_000.0, seed0=1000):
    """
    n bağımsız replikasyon ile ortalama ve %95 güven aralığı hesaplar.
    """
    records = []
    for r in range(n_reps):
        pl, aq, _ = simulate(lam, p, theta, T, warmup, seed=seed0 + r)
        records.append(compute_kpis(pl, aq, warmup))

    def ci(vals):
        arr = np.array(vals, dtype=float)
        m = float(np.mean(arr))
        h = T975[n_reps - 1] * float(np.std(arr, ddof=1)) / math.sqrt(n_reps) if n_reps > 1 else 0.0
        return m, h

    res = {}
    for grp in ("beyaz", "siyah", "toplam"):
        res[grp] = {}
        for k in records[0][grp]:
            res[grp][k] = ci([rec[grp][k] for rec in records])
    return res


def fmt_ci(mh, digits=3, pct=False):
    m, h = mh
    if pct:
        return f"{100 * m:.1f}% ± {100 * h:.1f}"
    return f"{m:.{digits}f} ± {h:.{digits}f}"


def format_table(head, rows):
    widths = [max(len(str(x)) for x in col) for col in zip(head, *rows)]
    line = "  ".join(str(h).ljust(widths[i]) if i == 0 else str(h).rjust(widths[i]) for i, h in enumerate(head))
    sep = "-" * len(line)
    body = ["  ".join(str(x).ljust(widths[i]) if i == 0 else str(x).rjust(widths[i]) for i, x in enumerate(r)) for r in rows]
    return "\n".join([line, sep] + body)


# %% [markdown]
# ## Ana Deney Akışı & Çıktılar

# %%
def run_phase1_experiments(lam=1.0, p=0.6, theta=0.05, T=20_000, n_reps=5, warmup=1_000.0,
                           plot=False, out_dir="results"):
    os.makedirs(out_dir, exist_ok=True)
    fig_dir = os.path.join(out_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    ct = ctmc_abandon(lam, p, theta)
    cx = lambda x, d=3, pct=False: "–" if ct is None else (f"{100 * x:.1f}%" if pct else f"{x:.{d}f}")

    print(f"\n==========================================================================")
    print(f"Phase 1: Renk Bazlı FCFS Satranç Eşleştirmesi (λ = {lam}, p = {p}, θ = {theta})")
    print(f"Deney Düzeni: {n_reps} replikasyon × T = {T:.0f}, Isınma = {warmup:.0f}")
    print(f"==========================================================================\n")

    R = run_replications(lam, p, theta, T=T, n_reps=n_reps, warmup=warmup)

    rows = [
        ["Varış hızı λ_i", f"{lam*p:.2f}", "", f"{lam*(1-p):.2f}", "", f"{lam:.2f}", ""],
        ["Oyuncu sayısı / rep", f"{R['beyaz']['oyuncu sayisi'][0]:.0f}", "", f"{R['siyah']['oyuncu sayisi'][0]:.0f}", "", f"{R['toplam']['oyuncu sayisi'][0]:.0f}", ""],
        ["P(terk_i)", fmt_ci(R['beyaz']['terk orani'], pct=True), cx(ct['abW'], pct=True),
         fmt_ci(R['siyah']['terk orani'], pct=True), cx(ct['abB'], pct=True),
         fmt_ci(R['toplam']['terk orani'], pct=True), cx(ct['toplam']['terk orani'], pct=True)],
        ["Ortalama bekleme W_i", fmt_ci(R['beyaz']['ort. bekleme (tumu)']), cx(ct['Ww']),
         fmt_ci(R['siyah']['ort. bekleme (tumu)']), cx(ct['Wb']),
         fmt_ci(R['toplam']['ort. bekleme (tumu)']), cx(ct['L']/lam)],
        ["P90 bekleme (eşleşen)", fmt_ci(R['beyaz']['p90 bekleme (eslesen)'], 2), "",
         fmt_ci(R['siyah']['p90 bekleme (eslesen)'], 2), "",
         fmt_ci(R['toplam']['p90 bekleme (eslesen)'], 2), ""],
        ["P(W = 0)", fmt_ci(R['beyaz']['beklemeden eslesme orani'], pct=True), "",
         fmt_ci(R['siyah']['beklemeden eslesme orani'], pct=True), "", "–", ""],
        ["Ortalama kuyruk L_i", fmt_ci(R['beyaz']['ort. kuyruk uzunlugu']), cx(ct['Lw']),
         fmt_ci(R['siyah']['ort. kuyruk uzunlugu']), cx(ct['Lb']),
         fmt_ci(R['toplam']['ort. kuyruk uzunlugu']), cx(ct['L'])],
        ["Little: λ_i · W_i", f"{lam*p * R['beyaz']['ort. bekleme (tumu)'][0]:.3f}", "",
         f"{lam*(1-p) * R['siyah']['ort. bekleme (tumu)'][0]:.3f}", "",
         f"{lam * R['toplam']['ort. bekleme (tumu)'][0]:.3f}", ""],
    ]
    print("Renk Bazlı Performans (Ortalama ± %95 Güven Aralığı | CTMC)")
    head = ["Metrik", "Beyaz sim", "CTMC", "Siyah sim", "CTMC", "Toplam sim", "CTMC"]
    print(format_table(head, rows), "\n")

    # p sweep
    ps = sorted(set([0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, p]))
    sweep = []
    for cur_p in ps:
        pl, aq, _ = simulate(lam, cur_p, theta, T, warmup, seed=42)
        kp = compute_kpis(pl, aq, warmup)
        c_th = ctmc_abandon(lam, cur_p, theta)
        sweep.append((cur_p, kp, c_th))

    s_rows = []
    for cur_p, kp, c_th in sweep:
        r = [
            f"{cur_p:.2f}" + (" *" if cur_p == p else ""),
            f"{kp['beyaz']['ort. bekleme (tumu)']:.3f}", cx(c_th['Ww']),
            f"{kp['siyah']['ort. bekleme (tumu)']:.3f}", cx(c_th['Wb']),
            f"{kp['beyaz']['ort. kuyruk uzunlugu']:.3f}", cx(c_th['Lw']),
            f"{kp['siyah']['ort. kuyruk uzunlugu']:.3f}", cx(c_th['Lb']),
            f"{100*kp['beyaz']['terk orani']:.1f}%", cx(c_th['abW'], pct=True)
        ]
        s_rows.append(r)
    s_head = ["p", "W_w sim", "CTMC", "W_b sim", "CTMC", "L_w sim", "CTMC", "L_b sim", "CTMC", "P(ab_w) sim", "CTMC"]
    print("p Duyarlılık Analizi (Sweep): Simülasyon vs CTMC (* = varsayılan p)")
    print(format_table(s_head, s_rows), "\n")

    # theta sweep
    thetas = [0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0]
    th_rows = []
    for th in thetas:
        c_th = ctmc_abandon(lam, p, th)
        th_rows.append([f"{th:g}", f"{1.0/th:.1f}", f"{c_th['L']:.2f}", f"{c_th['L']/lam:.2f}",
                        f"{100*c_th['toplam']['terk orani']:.1f}%"])
    th_head = ["θ", "1/θ (sabır)", "L", "W", "P(terk)"]
    print(f"Sabır Ödünleşimi · θ Sweep (CTMC, p = {p})")
    print(format_table(th_head, th_rows), "\n")

    # CSV yazımı
    csv_path = os.path.join(out_dir, "p_sweep.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["p", "W_w_sim", "W_b_sim", "L_w_sim", "L_b_sim", "P_ab_w_sim", "P_ab_b_sim",
                     "W_w_ctmc", "W_b_ctmc", "L_w_ctmc", "L_b_ctmc", "P_ab_w_ctmc", "P_ab_b_ctmc"])
        for cur_p, kp, c_th in sweep:
            wr.writerow([
                cur_p,
                kp["beyaz"]["ort. bekleme (tumu)"], kp["siyah"]["ort. bekleme (tumu)"],
                kp["beyaz"]["ort. kuyruk uzunlugu"], kp["siyah"]["ort. kuyruk uzunlugu"],
                kp["beyaz"]["terk orani"], kp["siyah"]["terk orani"],
                c_th["Ww"] if c_th else "", c_th["Wb"] if c_th else "",
                c_th["Lw"] if c_th else "", c_th["Lb"] if c_th else "",
                c_th["abW"] if c_th else "", c_th["abB"] if c_th else ""
            ])
    print(f"Sonuçlar CSV dosyasına kaydedildi: {csv_path}")

    if plot:
        # Grafik 1: p sweep
        plt.style.use("default")
        fig, axs = plt.subplots(1, 2, figsize=(12, 4.5), dpi=150)
        p_vals = [s[0] for s in sweep]
        w_w_sim = [s[1]["beyaz"]["ort. bekleme (tumu)"] for s in sweep]
        w_w_th = [s[2]["Ww"] for s in sweep]
        w_b_sim = [s[1]["siyah"]["ort. bekleme (tumu)"] for s in sweep]
        w_b_th = [s[2]["Wb"] for s in sweep]

        axs[0].plot(p_vals, w_w_th, "b-", label="Beyaz CTMC", lw=1.5)
        axs[0].plot(p_vals, w_w_sim, "bo", label="Beyaz sim", markersize=5)
        axs[0].plot(p_vals, w_b_th, "r--", label="Siyah CTMC", lw=1.5)
        axs[0].plot(p_vals, w_b_sim, "rs", label="Siyah sim", markersize=5)
        axs[0].set_yscale("log")
        axs[0].set_xlabel("Beyaz Payı p")
        axs[0].set_ylabel("Ortalama Bekleme Süresi W_i (log)")
        axs[0].set_title("Bekleme Süresi: Simülasyon vs CTMC")
        axs[0].grid(True, alpha=0.3)
        axs[0].legend()

        ab_w_sim = [100 * s[1]["beyaz"]["terk orani"] for s in sweep]
        ab_w_th = [100 * s[2]["abW"] for s in sweep]
        ab_b_sim = [100 * s[1]["siyah"]["terk orani"] for s in sweep]
        ab_b_th = [100 * s[2]["abB"] for s in sweep]

        axs[1].plot(p_vals, ab_w_th, "b-", label="Beyaz CTMC", lw=1.5)
        axs[1].plot(p_vals, ab_w_sim, "bo", label="Beyaz sim", markersize=5)
        axs[1].plot(p_vals, ab_b_th, "r--", label="Siyah CTMC", lw=1.5)
        axs[1].plot(p_vals, ab_b_sim, "rs", label="Siyah sim", markersize=5)
        axs[1].plot(p_vals, [max(0, 100 * (2 * x - 1) / x) if x > 0 else 0 for x in p_vals], "k:", label="Alt sınır (2p-1)/p")
        axs[1].set_xlabel("Beyaz Payı p")
        axs[1].set_ylabel("Terk Oranı (%)")
        axs[1].set_title("Terk Oranı: Simülasyon vs CTMC")
        axs[1].grid(True, alpha=0.3)
        axs[1].legend()

        plt.tight_layout()
        p_fig_path = os.path.join(fig_dir, "p_sweep.png")
        plt.savefig(p_fig_path)
        plt.close(fig)

        # Grafik 2: Steady state & trace
        pl, _, tr = simulate(lam, p, theta, T=10_000, warmup=1_000, seed=42)
        tt, xx = tr
        fig, axs = plt.subplots(1, 2, figsize=(12, 4.5), dpi=150)
        mask = (tt >= 1000) & (tt <= 3000)
        axs[0].step(tt[mask], xx[mask], where="post", color="#2a78d6", lw=1.2)
        axs[0].axhline(0, color="gray", linestyle="--", alpha=0.7)
        axs[0].set_xlabel("Zaman")
        axs[0].set_ylabel("X(t) = #Beyaz - #Siyah")
        axs[0].set_title("Kuyruk İzi X(t)")
        axs[0].grid(True, alpha=0.3)

        if ct:
            n_vals = np.arange(-15, 30)
            pi_th = [ct["dist"].get(int(n), 0.0) for n in n_vals]
            axs[1].plot(n_vals, pi_th, "r-", lw=1.5, label="CTMC π_n")
            axs[1].hist(xx[tt >= 1000], bins=np.arange(-15.5, 30.5, 1), density=True,
                         alpha=0.5, color="#2a78d6", label="Simülasyon")
            axs[1].set_xlabel("Durum n")
            axs[1].set_ylabel("Durağan Olasılık π_n")
            axs[1].set_title("Durağan Dağılım Doğrulaması")
            axs[1].grid(True, alpha=0.3)
            axs[1].legend()

        plt.tight_layout()
        st_fig_path = os.path.join(fig_dir, "steady_state.png")
        plt.savefig(st_fig_path)
        plt.close(fig)
        print(f"Grafikler kaydedildi: {p_fig_path}, {st_fig_path}")


# %%
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 1: Renk bazlı FCFS satranç eşleştirmesi")
    parser.add_argument("--lam", type=float, default=1.0, help="Geliş hızı λ")
    parser.add_argument("--p", type=float, default=0.6, help="Beyaz oyuncu olasılığı p")
    parser.add_argument("--theta", type=float, default=0.05, help="Terk hızı θ")
    parser.add_argument("--no-abandon", action="store_true", help="Terk mekanizmasını kapat (θ = 0)")
    parser.add_argument("--T", type=float, default=20_000, help="Simülasyon süresi T")
    parser.add_argument("--warmup", type=float, default=1_000.0, help="Isınma süresi")
    parser.add_argument("--reps", type=int, default=5, help="Replikasyon sayısı")
    parser.add_argument("--plot", action="store_true", default=True, help="Grafikleri kaydet")
    parser.add_argument("--out-dir", type=str, default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"),
                        help="Sonuçların kaydedileceği klasör")
    args = parser.parse_args()

    th = 0.0 if args.no_abandon else args.theta
    run_phase1_experiments(lam=args.lam, p=args.p, theta=th, T=args.T, n_reps=args.reps,
                           warmup=args.warmup, plot=args.plot, out_dir=args.out_dir)
