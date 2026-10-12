"""
Phase 2.1: Skill-based Matchmaking without Abandonment (Terk Yok)
- Oyuncular: Poisson(λ) varışları.
- Beceri Sınıfları: Good (İyi) olasılığı p, Bad (Kötü) olasılığı 1-p.
- Renk kısıtı yok (1v1 skill-based).
- Homojen Öncelik: Good-Good, Bad-Bad.
- Cross-match Eşiği (τ): Bekleme süresi τ aşılınca esnek (flexible) moda geçer,
  karşı sınıfla eşleşebilir (Good-Bad).
- Terk etme yok (θ = 0).

Analitik Uç Nokta Doğrulaması:
  * τ = 0 (Single Pool): L = 0.500, W = 0.500, Cross-match = 2p(1-p) = %48.0
  * τ = ∞ (Strict Separation): L = 1.000, W = 1.000, Cross-match = %0.0, W_G = 1/(2λp), W_B = 1/(2λ(1-p))
"""

import argparse
import csv
import heapq
import math
import os
from collections import deque

import numpy as np
import matplotlib.pyplot as plt

GOOD, BAD = 0, 1
TIER_NAME = {GOOD: "İyi (Good)", BAD: "Kötü (Bad)"}

# Oyuncu durumları
WAITING = 0     # Kendi sınıfını bekliyor (< tau)
FLEXIBLE = 1    # tau süresini aştı, cross-match havuzunda
MATCHED = 2     # Eşleşti

# Olay tipleri
EVT_ARRIVAL = 1
EVT_TIMEOUT = 2

# Maç tipleri
MATCH_HOMOGENEOUS = 0  # G-G veya B-B
MATCH_CROSS = 1        # G-B


def simulate_phase2_1(lam=1.0, p=0.6, tau=3.0, T=20_000, warmup=1_000.0, seed=42):
    """
    Phase 2.1 Olay Tabanlı Ayrık Simülasyon (Terk Yok)
    """
    rng = np.random.default_rng(seed)

    arrival, tier, end, status = [], [], [], []
    partner_id, match_type = [], []

    queues = {GOOD: deque(), BAD: deque()}
    n_waiting = {GOOD: 0, BAD: 0}
    events = []

    area = {GOOD: 0.0, BAD: 0.0}
    last_t = 0.0
    trace_t = [0.0]
    trace_q_good, trace_q_bad, trace_q_total = [0], [0], [0]

    def advance(to):
        nonlocal last_t
        start = max(last_t, warmup)
        if to > start:
            for c in (GOOD, BAD):
                area[c] += n_waiting[c] * (to - start)
        last_t = to

    def record_trace(t):
        trace_t.append(t)
        trace_q_good.append(n_waiting[GOOD])
        trace_q_bad.append(n_waiting[BAD])
        trace_q_total.append(n_waiting[GOOD] + n_waiting[BAD])

    t_first = rng.exponential(1.0 / lam)
    heapq.heappush(events, (t_first, EVT_ARRIVAL, -1))

    while events:
        evt_t, evt_type, pid = heapq.heappop(events)

        if evt_t > T:
            advance(T)
            break

        advance(evt_t)

        if evt_type == EVT_ARRIVAL:
            t_next = evt_t + rng.exponential(1.0 / lam)
            if t_next <= T:
                heapq.heappush(events, (t_next, EVT_ARRIVAL, -1))

            c = GOOD if rng.random() < p else BAD
            other = 1 - c
            curr_id = len(arrival)
            arrival.append(evt_t)
            tier.append(c)
            end.append(np.nan)
            status.append(WAITING)
            partner_id.append(-1)
            match_type.append(-1)

            # 1. Kendi sınıfında bekleyen var mı?
            matched_partner = None
            while queues[c]:
                candidate = queues[c].popleft()
                if status[candidate] in (WAITING, FLEXIBLE):
                    matched_partner = candidate
                    break

            if matched_partner is not None:
                status[matched_partner] = MATCHED
                end[matched_partner] = evt_t
                partner_id[matched_partner] = curr_id
                match_type[matched_partner] = MATCH_HOMOGENEOUS

                status[curr_id] = MATCHED
                end[curr_id] = evt_t
                partner_id[curr_id] = matched_partner
                match_type[curr_id] = MATCH_HOMOGENEOUS

                n_waiting[c] -= 1
                record_trace(evt_t)
                continue

            # 2. Karşı sınıfta FLEXIBLE (>= tau) var mı?
            cross_partner = None
            if tau == 0.0:
                while queues[other]:
                    cand = queues[other].popleft()
                    if status[cand] in (WAITING, FLEXIBLE):
                        cross_partner = cand
                        break
            else:
                for cand in queues[other]:
                    if status[cand] == FLEXIBLE:
                        cross_partner = cand
                        break

            if cross_partner is not None:
                if tau > 0.0:
                    queues[other].remove(cross_partner)
                status[cross_partner] = MATCHED
                end[cross_partner] = evt_t
                partner_id[cross_partner] = curr_id
                match_type[cross_partner] = MATCH_CROSS

                status[curr_id] = MATCHED
                end[curr_id] = evt_t
                partner_id[curr_id] = cross_partner
                match_type[curr_id] = MATCH_CROSS

                n_waiting[other] -= 1
                record_trace(evt_t)
                continue

            # Eşleşme olmadı -> kuyruğa gir
            queues[c].append(curr_id)
            n_waiting[c] += 1
            if tau > 0.0:
                heapq.heappush(events, (evt_t + tau, EVT_TIMEOUT, curr_id))
            else:
                status[curr_id] = FLEXIBLE
            record_trace(evt_t)

        elif evt_type == EVT_TIMEOUT:
            if status[pid] == WAITING:
                status[pid] = FLEXIBLE
                c = tier[pid]
                other = 1 - c

                cross_partner = None
                while queues[other]:
                    candidate = queues[other].popleft()
                    if status[candidate] in (WAITING, FLEXIBLE):
                        cross_partner = candidate
                        break

                if cross_partner is not None:
                    queues[c].remove(pid)
                    status[pid] = MATCHED
                    end[pid] = evt_t
                    partner_id[pid] = cross_partner
                    match_type[pid] = MATCH_CROSS

                    status[cross_partner] = MATCHED
                    end[cross_partner] = evt_t
                    partner_id[cross_partner] = pid
                    match_type[cross_partner] = MATCH_CROSS

                    n_waiting[c] -= 1
                    n_waiting[other] -= 1
                    record_trace(evt_t)

    players = {
        "arrival": np.array(arrival),
        "tier": np.array(tier),
        "end": np.array(end),
        "status": np.array(status),
        "partner_id": np.array(partner_id),
        "match_type": np.array(match_type),
    }
    span = T - warmup
    avg_queue = {
        GOOD: area[GOOD] / span,
        BAD: area[BAD] / span,
        "total": (area[GOOD] + area[BAD]) / span
    }
    trace = {
        "t": np.array(trace_t),
        "good": np.array(trace_q_good),
        "bad": np.array(trace_q_bad),
        "total": np.array(trace_q_total),
    }
    return players, avg_queue, trace


def compute_kpis_phase2_1(players, avg_queue, warmup=1_000.0):
    kpis = {}
    for c in (GOOD, BAD):
        sel = (players["tier"] == c) & (players["arrival"] >= warmup) & (players["status"] == MATCHED)
        w = players["end"][sel] - players["arrival"][sel]
        mt = players["match_type"][sel]

        kpis[TIER_NAME[c]] = {
            "oyuncu sayisi": int(sel.sum()),
            "ort. bekleme": float(w.mean()) if len(w) > 0 else 0.0,
            "medyan bekleme": float(np.median(w)) if len(w) > 0 else 0.0,
            "p90 bekleme": float(np.percentile(w, 90)) if len(w) > 0 else 0.0,
            "beklemeden eslesme orani": float((w == 0).mean()) if len(w) > 0 else 0.0,
            "ort. kuyruk uzunlugu": avg_queue[c],
            "homojen mac sayisi": int((mt == MATCH_HOMOGENEOUS).sum()),
            "capraz mac sayisi": int((mt == MATCH_CROSS).sum()),
            "capraz mac orani (%)": float((mt == MATCH_CROSS).mean() * 100.0) if len(mt) > 0 else 0.0,
        }

    sel_all = (players["arrival"] >= warmup) & (players["status"] == MATCHED)
    w_all = players["end"][sel_all] - players["arrival"][sel_all]
    mt_all = players["match_type"][sel_all]

    total_matched = len(w_all)
    cross_matched = int((mt_all == MATCH_CROSS).sum())
    cross_ratio = cross_matched / total_matched if total_matched > 0 else 0.0

    kpis["genel"] = {
        "toplam eslesen oyuncu": total_matched,
        "ort. bekleme (genel)": float(w_all.mean()) if len(w_all) > 0 else 0.0,
        "p90 bekleme (genel)": float(np.percentile(w_all, 90)) if len(w_all) > 0 else 0.0,
        "ort. toplam kuyruk": avg_queue["total"],
        "capraz eslesme orani (%)": cross_ratio * 100.0,
        "homojen eslesme orani (%)": (1.0 - cross_ratio) * 100.0,
    }
    return kpis


T975 = [math.nan, 12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262]

def run_replications_phase2_1(lam=1.0, p=0.6, tau=3.0, T=20_000, n_reps=5, warmup=1_000.0, seed0=1000):
    records = []
    for r in range(n_reps):
        pl, aq, _ = simulate_phase2_1(lam=lam, p=p, tau=tau, T=T, warmup=warmup, seed=seed0 + r)
        records.append(compute_kpis_phase2_1(pl, aq, warmup))

    def ci(vals):
        arr = np.array(vals, dtype=float)
        m = float(np.mean(arr))
        h = T975[n_reps - 1] * float(np.std(arr, ddof=1)) / math.sqrt(n_reps) if n_reps > 1 else 0.0
        return m, h

    res = {TIER_NAME[GOOD]: {}, TIER_NAME[BAD]: {}, "genel": {}}
    for grp in res:
        for k in records[0][grp]:
            res[grp][k] = ci([rec[grp][k] for rec in records])
    return res


def fmt_ci(mh, digits=3, pct=False):
    m, h = mh
    if pct:
        return f"{m:.1f}% ± {h:.1f}"
    return f"{m:.{digits}f} ± {h:.{digits}f}"


def format_table(head, rows):
    widths = [max(len(str(x)) for x in col) for col in zip(head, *rows)]
    line = "  ".join(str(h).ljust(widths[i]) if i == 0 else str(h).rjust(widths[i]) for i, h in enumerate(head))
    sep = "-" * len(line)
    body = ["  ".join(str(x).ljust(widths[i]) if i == 0 else str(x).rjust(widths[i]) for i, x in enumerate(r)) for r in rows]
    return "\n".join([line, sep] + body)


def analytical_endpoints_phase2_1(lam=1.0, p=0.6):
    """
    Terk yokken analitik uç noktalar:
      τ = 0: tek havuz (single pool), kuyruk <= 1
      τ = inf: kesin ayrım (strict separation), her sınıf bağımsız 0/1 kuyruk
    """
    # tau = 0
    l_pool = 0.500
    w_pool = 0.500
    cross_pool = 2.0 * p * (1.0 - p) * 100.0
    w_g_pool = 0.500
    w_b_pool = 0.500

    # tau = inf
    l_g_sep = 0.500
    l_b_sep = 0.500
    w_g_sep = 1.0 / (2.0 * lam * p)
    w_b_sep = 1.0 / (2.0 * lam * (1.0 - p))
    l_sep = 1.000
    w_sep = 1.000
    cross_sep = 0.0

    return {
        "tau_0": {"L": l_pool, "W": w_pool, "cross": cross_pool, "W_G": w_g_pool, "W_B": w_b_pool,
                  "L_G": p * l_pool, "L_B": (1.0 - p) * l_pool},
        "tau_inf": {"L": l_sep, "W": w_sep, "cross": cross_sep, "W_G": w_g_sep, "W_B": w_b_sep,
                    "L_G": l_g_sep, "L_B": l_b_sep}
    }


def run_phase2_1_experiments(lam=1.0, p=0.6, tau=3.0, T=20_000, n_reps=5, warmup=1_000.0,
                             plot=False, out_dir="results"):
    os.makedirs(out_dir, exist_ok=True)
    fig_dir = os.path.join(out_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    an = analytical_endpoints_phase2_1(lam=lam, p=p)

    print(f"\n==========================================================================")
    print(f"Phase 2.1: Terksiz Beceri Bazlı Eşleştirme (λ = {lam}, p = {p}, τ = {tau})")
    print(f"Deney Düzeni: {n_reps} replikasyon × T = {T:.0f}, Isınma = {warmup:.0f}")
    print(f"==========================================================================\n")

    R = run_replications_phase2_1(lam=lam, p=p, tau=tau, T=T, n_reps=n_reps, warmup=warmup)

    rows = [
        ["Varış hızı λ_i", f"{lam*p:.2f}", f"{lam*(1-p):.2f}", f"{lam:.2f}"],
        ["Oyuncu sayısı / rep", f"{R[TIER_NAME[GOOD]]['oyuncu sayisi'][0]:.0f}",
         f"{R[TIER_NAME[BAD]]['oyuncu sayisi'][0]:.0f}", f"{R['genel']['toplam eslesen oyuncu'][0]:.0f}"],
        ["Çapraz eşleşme oranı", fmt_ci(R[TIER_NAME[GOOD]]["capraz mac orani (%)"], pct=True),
         fmt_ci(R[TIER_NAME[BAD]]["capraz mac orani (%)"], pct=True), fmt_ci(R["genel"]["capraz eslesme orani (%)"], pct=True)],
        ["Ortalama bekleme W_i", fmt_ci(R[TIER_NAME[GOOD]]["ort. bekleme"]),
         fmt_ci(R[TIER_NAME[BAD]]["ort. bekleme"]), fmt_ci(R["genel"]["ort. bekleme (genel)"])],
        ["Medyan bekleme", fmt_ci(R[TIER_NAME[GOOD]]["medyan bekleme"], 2),
         fmt_ci(R[TIER_NAME[BAD]]["medyan bekleme"], 2), "–"],
        ["P90 bekleme", fmt_ci(R[TIER_NAME[GOOD]]["p90 bekleme"], 2),
         fmt_ci(R[TIER_NAME[BAD]]["p90 bekleme"], 2), fmt_ci(R["genel"]["p90 bekleme (genel)"], 2)],
        ["P(W = 0)", fmt_ci(R[TIER_NAME[GOOD]]["beklemeden eslesme orani"], pct=True),
         fmt_ci(R[TIER_NAME[BAD]]["beklemeden eslesme orani"], pct=True), "–"],
        ["Ortalama kuyruk L_i", fmt_ci(R[TIER_NAME[GOOD]]["ort. kuyruk uzunlugu"]),
         fmt_ci(R[TIER_NAME[BAD]]["ort. kuyruk uzunlugu"]), fmt_ci(R["genel"]["ort. toplam kuyruk"])],
        ["Little: λ_i · W_i", f"{lam*p*R[TIER_NAME[GOOD]]['ort. bekleme'][0]:.3f}",
         f"{lam*(1-p)*R[TIER_NAME[BAD]]['ort. bekleme'][0]:.3f}", f"{lam*R['genel']['ort. bekleme (genel)'][0]:.3f}"],
    ]
    print("Sınıf Bazlı Performans (Ortalama ± %95 Güven Aralığı)")
    head = ["Metrik", "İyi (Good)", "Kötü (Bad)", "Toplam"]
    print(format_table(head, rows), "\n")

    # tau sweep
    taus = [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 20.0, 50.0]
    sweep_results = []
    for t_val in taus:
        pl, aq, _ = simulate_phase2_1(lam=lam, p=p, tau=t_val, T=T, warmup=warmup, seed=42)
        kp = compute_kpis_phase2_1(pl, aq, warmup)
        sweep_results.append((t_val, kp))

    s_rows = []
    for t_val, kp in sweep_results:
        t_label = "∞" if t_val >= 50.0 else f"{t_val:g}"
        if t_val == tau:
            t_label += " *"
        r = [
            t_label,
            f"{kp['genel']['capraz eslesme orani (%)']:.1f}%",
            f"{kp['genel']['ort. bekleme (genel)']:.3f}",
            f"{kp[TIER_NAME[GOOD]]['ort. bekleme']:.3f}",
            f"{kp[TIER_NAME[BAD]]['ort. bekleme']:.3f}",
            f"{kp['genel']['p90 bekleme (genel)']:.2f}",
            f"{kp['genel']['ort. toplam kuyruk']:.3f}"
        ]
        s_rows.append(r)
    s_head = ["τ", "Çapraz Maç", "W", "W_G", "W_B", "P90", "L"]
    print("τ Duyarlılık Analizi (Sweep): Maç Kalitesi ↔ Bekleme Süresi Ödünleşimi (* = varsayılan τ)")
    print(format_table(s_head, s_rows), "\n")

    # Uç Nokta Doğrulaması
    kp_0 = sweep_results[0][1]
    kp_inf = sweep_results[-1][1]
    rel = lambda x, y: f"{100*abs(x/y - 1):.1f}%" if y > 0 else "–"

    val_rows = [
        ["τ = 0 · L (toplam)", f"{kp_0['genel']['ort. toplam kuyruk']:.3f}", f"{an['tau_0']['L']:.3f}", rel(kp_0['genel']['ort. toplam kuyruk'], an['tau_0']['L'])],
        ["τ = 0 · Çapraz Maç (%)", f"{kp_0['genel']['capraz eslesme orani (%)']:.1f}%", f"{an['tau_0']['cross']:.1f}%", rel(kp_0['genel']['capraz eslesme orani (%)'], an['tau_0']['cross'])],
        ["τ = 0 · W_G", f"{kp_0[TIER_NAME[GOOD]]['ort. bekleme']:.3f}", f"{an['tau_0']['W_G']:.3f}", rel(kp_0[TIER_NAME[GOOD]]['ort. bekleme'], an['tau_0']['W_G'])],
        ["τ = 0 · W_B", f"{kp_0[TIER_NAME[BAD]]['ort. bekleme']:.3f}", f"{an['tau_0']['W_B']:.3f}", rel(kp_0[TIER_NAME[BAD]]['ort. bekleme'], an['tau_0']['W_B'])],
        ["τ = ∞ · L (toplam)", f"{kp_inf['genel']['ort. toplam kuyruk']:.3f}", f"{an['tau_inf']['L']:.3f}", rel(kp_inf['genel']['ort. toplam kuyruk'], an['tau_inf']['L'])],
        ["τ = ∞ · Çapraz Maç (%)", f"{kp_inf['genel']['capraz eslesme orani (%)']:.1f}%", f"{an['tau_inf']['cross']:.1f}%", "0 (tanım gereği)"],
        ["τ = ∞ · W_G", f"{kp_inf[TIER_NAME[GOOD]]['ort. bekleme']:.3f}", f"{an['tau_inf']['W_G']:.3f}", rel(kp_inf[TIER_NAME[GOOD]]['ort. bekleme'], an['tau_inf']['W_G'])],
        ["τ = ∞ · W_B", f"{kp_inf[TIER_NAME[BAD]]['ort. bekleme']:.3f}", f"{an['tau_inf']['W_B']:.3f}", rel(kp_inf[TIER_NAME[BAD]]['ort. bekleme'], an['tau_inf']['W_B'])],
    ]
    val_head = ["Metrik", "Simülasyon", "Analitik Kapalı Form", "Bağıl Hata"]
    print("Uç Nokta Doğrulaması (τ = 0 Single Pool ve τ = ∞ Strict Separation)")
    print(format_table(val_head, val_rows), "\n")

    # CSV yazımı
    csv_path = os.path.join(out_dir, "tau_sweep.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["tau", "cross_match_ratio", "W_all", "W_good", "W_bad", "P90_all", "L_total", "L_good", "L_bad"])
        for t_val, kp in sweep_results:
            wr.writerow([
                t_val,
                kp["genel"]["capraz eslesme orani (%)"] / 100.0,
                kp["genel"]["ort. bekleme (genel)"],
                kp[TIER_NAME[GOOD]]["ort. bekleme"],
                kp[TIER_NAME[BAD]]["ort. bekleme"],
                kp["genel"]["p90 bekleme (genel)"],
                kp["genel"]["ort. toplam kuyruk"],
                kp[TIER_NAME[GOOD]]["ort. kuyruk uzunlugu"],
                kp[TIER_NAME[BAD]]["ort. kuyruk uzunlugu"]
            ])
    print(f"Sonuçlar CSV dosyasına kaydedildi: {csv_path}")

    if plot:
        plt.style.use("default")
        fig, axs = plt.subplots(1, 2, figsize=(12, 4.5), dpi=150)
        t_arr = [s[0] for s in sweep_results if s[0] < 50.0]
        cross_arr = [s[1]["genel"]["capraz eslesme orani (%)"] for s in sweep_results if s[0] < 50.0]
        w_all_arr = [s[1]["genel"]["ort. bekleme (genel)"] for s in sweep_results if s[0] < 50.0]
        w_g_arr = [s[1][TIER_NAME[GOOD]]["ort. bekleme"] for s in sweep_results if s[0] < 50.0]
        w_b_arr = [s[1][TIER_NAME[BAD]]["ort. bekleme"] for s in sweep_results if s[0] < 50.0]

        axs[0].plot(cross_arr, w_all_arr, "o-", color="#6250d6", lw=1.8, label="Genel Ortalama W")
        axs[0].scatter([an["tau_0"]["cross"]], [an["tau_0"]["W"]], color="blue", marker="D", s=50, label="τ=0 Kapalı Form")
        axs[0].scatter([an["tau_inf"]["cross"]], [an["tau_inf"]["W"]], color="red", marker="D", s=50, label="τ=∞ Kapalı Form")
        axs[0].set_xlabel("Çapraz Eşleşme Oranı (%)")
        axs[0].set_ylabel("Ortalama Bekleme Süresi W")
        axs[0].set_title("Ödünleşim Eğrisi: Maç Kalitesi vs Bekleme Süresi")
        axs[0].grid(True, alpha=0.3)
        axs[0].legend()

        axs[1].plot(t_arr, w_g_arr, "o-", color="#1d7f4e", lw=1.5, label="İyi (Good) W_G")
        axs[1].plot(t_arr, w_b_arr, "s-", color="#d63b3a", lw=1.5, label="Kötü (Bad) W_B")
        axs[1].plot(t_arr, w_all_arr, "^--", color="#6250d6", lw=1.5, label="Genel W")
        axs[1].axhline(an["tau_inf"]["W_G"], color="#1d7f4e", linestyle=":", label="W_G (τ=∞ limit)")
        axs[1].axhline(an["tau_inf"]["W_B"], color="#d63b3a", linestyle=":", label="W_B (τ=∞ limit)")
        axs[1].set_xlabel("Cross-match Eşiği τ")
        axs[1].set_ylabel("Ortalama Bekleme Süresi")
        axs[1].set_title("Sınıf Bazında Bekleme Süreleri")
        axs[1].grid(True, alpha=0.3)
        axs[1].legend()

        plt.tight_layout()
        tr_path = os.path.join(fig_dir, "tradeoff.png")
        plt.savefig(tr_path)
        plt.close(fig)
        print(f"Grafik kaydedildi: {tr_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 2.1: Skill-based matchmaking without abandonment")
    parser.add_argument("--lam", type=float, default=1.0, help="Geliş hızı λ")
    parser.add_argument("--p", type=float, default=0.6, help="Good oranı p")
    parser.add_argument("--tau", type=float, default=3.0, help="Cross-match eşiği τ")
    parser.add_argument("--T", type=float, default=20_000, help="Simülasyon süresi T")
    parser.add_argument("--warmup", type=float, default=1_000.0, help="Isınma süresi")
    parser.add_argument("--reps", type=int, default=5, help="Replikasyon sayısı")
    parser.add_argument("--plot", action="store_true", default=True, help="Grafikleri kaydet")
    parser.add_argument("--out-dir", type=str,
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"),
                        help="Çıktı klasörü")
    args = parser.parse_args()

    run_phase2_1_experiments(lam=args.lam, p=args.p, tau=args.tau, T=args.T, n_reps=args.reps,
                             warmup=args.warmup, plot=args.plot, out_dir=args.out_dir)
