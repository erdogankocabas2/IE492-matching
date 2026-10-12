"""
Phase 2.2: Skill-based Matchmaking with Heterogeneous Abandonment (Terkli Model)
- Oyuncular: Poisson(λ) varışları.
- Beceri Sınıfları: Good (İyi) olasılığı p, Bad (Kötü) olasılığı 1-p.
- Renk kısıtı yok (1v1 skill-based).
- Farklı Terk Oranları:
    * İyi oyuncu terk hızı: theta_G (ortalama sabır 1/theta_G)
    * Kötü oyuncu terk hızı: theta_B (ortalama sabır 1/theta_B)
- Cross-match Eşiği (tau): Bekleme süresi tau aşılınca esnek moda geçer.
- Etkileşim: Sabır süresi < tau ise oyuncu cross-match göremeden terk edebilir;
  sabır > tau ise esnek havuza girer, yine de eşleşemezse sabrı bitince terk eder.
- Analitik Uç Nokta Doğrulaması:
    * τ = 0: Single Pool Markov Zinciri (pool_one)
    * τ = ∞: Ayrık Sınıf Markov Zincirleri (separate)
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
ABANDONED = 3   # Sabrı bitti, terk etti

# Olay tipleri
EVT_ARRIVAL = 1
EVT_TIMEOUT = 2
EVT_ABANDON = 3

# Maç tipleri
MATCH_HOMOGENEOUS = 0  # G-G veya B-B
MATCH_CROSS = 1        # G-B


def simulate_phase2_2(lam=1.0, p=0.6, tau=3.0, theta_g=0.08, theta_b=0.04,
                      T=20_000, warmup=1_000.0, seed=42):
    """
    Phase 2.2 Olay Tabanlı Ayrık Simülasyon (Heterojen Terk Oranları)
    """
    rng = np.random.default_rng(seed)
    theta_map = {GOOD: theta_g, BAD: theta_b}

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

            # 2. Karşı sınıfta FLEXIBLE var mı?
            cross_partner = None
            if tau == 0.0:
                while queues[other]:
                    candidate = queues[other].popleft()
                    if status[candidate] in (WAITING, FLEXIBLE):
                        cross_partner = candidate
                        break
            else:
                for candidate in queues[other]:
                    if status[candidate] == FLEXIBLE:
                        cross_partner = candidate
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

            th = theta_map[c]
            patience = rng.exponential(1.0 / th) if th > 0 else math.inf

            if tau > 0.0:
                if patience <= tau:
                    heapq.heappush(events, (evt_t + patience, EVT_ABANDON, curr_id))
                else:
                    heapq.heappush(events, (evt_t + tau, EVT_TIMEOUT, curr_id))
                    if math.isfinite(patience):
                        heapq.heappush(events, (evt_t + patience, EVT_ABANDON, curr_id))
            else:
                status[curr_id] = FLEXIBLE
                if math.isfinite(patience):
                    heapq.heappush(events, (evt_t + patience, EVT_ABANDON, curr_id))

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

        elif evt_type == EVT_ABANDON:
            if status[pid] in (WAITING, FLEXIBLE):
                c = tier[pid]
                status[pid] = ABANDONED
                end[pid] = evt_t
                queues[c].remove(pid)
                n_waiting[c] -= 1
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


def compute_kpis_phase2_2(players, avg_queue, warmup=1_000.0):
    kpis = {}
    for c in (GOOD, BAD):
        sel = (players["tier"] == c) & (players["arrival"] >= warmup) & np.isin(players["status"], [MATCHED, ABANDONED])
        st = players["status"][sel]
        w = players["end"][sel] - players["arrival"][sel]
        w_matched = w[st == MATCHED]
        mt = players["match_type"][sel]

        kpis[TIER_NAME[c]] = {
            "oyuncu sayisi": int(sel.sum()),
            "eslesme orani (%)": float((st == MATCHED).mean() * 100.0) if len(st) > 0 else 0.0,
            "terk orani (%)": float((st == ABANDONED).mean() * 100.0) if len(st) > 0 else 0.0,
            "ort. bekleme (tumu)": float(w.mean()) if len(w) > 0 else 0.0,
            "ort. bekleme (eslesen)": float(w_matched.mean()) if len(w_matched) > 0 else 0.0,
            "medyan bekleme (eslesen)": float(np.median(w_matched)) if len(w_matched) > 0 else 0.0,
            "p90 bekleme (eslesen)": float(np.percentile(w_matched, 90)) if len(w_matched) > 0 else 0.0,
            "beklemeden eslesme orani": float((w == 0).mean()) if len(w) > 0 else 0.0,
            "ort. kuyruk uzunlugu": avg_queue[c],
            "homojen mac sayisi": int((mt == MATCH_HOMOGENEOUS).sum()),
            "capraz mac sayisi": int((mt == MATCH_CROSS).sum()),
            "capraz mac orani (%)": float((mt == MATCH_CROSS).mean() * 100.0) if len(mt) > 0 else 0.0,
        }

    sel_all = (players["arrival"] >= warmup) & np.isin(players["status"], [MATCHED, ABANDONED])
    st_all = players["status"][sel_all]
    w_all = players["end"][sel_all] - players["arrival"][sel_all]
    w_matched_all = w_all[st_all == MATCHED]
    mt_matched = players["match_type"][sel_all & (players["status"] == MATCHED)]

    total_matched = len(w_matched_all)
    cross_matched = int((mt_matched == MATCH_CROSS).sum())
    cross_ratio = cross_matched / total_matched if total_matched > 0 else 0.0

    kpis["genel"] = {
        "toplam oyuncu": len(st_all),
        "genel eslesme orani (%)": float((st_all == MATCHED).mean() * 100.0) if len(st_all) > 0 else 0.0,
        "genel terk orani (%)": float((st_all == ABANDONED).mean() * 100.0) if len(st_all) > 0 else 0.0,
        "ort. bekleme (tumu)": float(w_all.mean()) if len(w_all) > 0 else 0.0,
        "ort. bekleme (eslesen)": float(w_matched_all.mean()) if len(w_matched_all) > 0 else 0.0,
        "p90 bekleme (eslesen)": float(np.percentile(w_matched_all, 90)) if len(w_matched_all) > 0 else 0.0,
        "ort. toplam kuyruk": avg_queue["total"],
        "capraz eslesme orani (%)": cross_ratio * 100.0,
        "homojen eslesme orani (%)": (1.0 - cross_ratio) * 100.0,
    }
    return kpis


def print_kpis_phase2_2(kpis):
    print("=" * 64)
    print(f"{'KPI':<30}{'İyi (Good)':>16}{'Kötü (Bad)':>16}")
    print("-" * 64)
    for k in ["oyuncu sayisi", "eslesme orani (%)", "terk orani (%)",
              "ort. bekleme (tumu)", "ort. bekleme (eslesen)",
              "medyan bekleme (eslesen)", "p90 bekleme (eslesen)",
              "ort. kuyruk uzunlugu", "capraz mac sayisi"]:
        print(f"{k:<30}{kpis[TIER_NAME[GOOD]][k]:>16.3f}{kpis[TIER_NAME[BAD]][k]:>16.3f}")
    print("-" * 64)
    print(f"Genel Eşleşme Oranı           : %{kpis['genel']['genel eslesme orani (%)']:>9.2f}")
    print(f"Genel Terk Oranı              : %{kpis['genel']['genel terk orani (%)']:>9.2f}")
    print(f"Genel Ort. Bekleme (Eşleşen)  : {kpis['genel']['ort. bekleme (eslesen)']:>10.3f}")
    print(f"Genel Ortalama Toplam Kuyruk  : {kpis['genel']['ort. toplam kuyruk']:>10.3f}")
    print(f"Çapraz Eşleşme Oranı (G-B)    : %{kpis['genel']['capraz eslesme orani (%)']:>9.2f}")
    print(f"Homojen Eşleşme Oranı (G-G,B-B): %{kpis['genel']['homojen eslesme orani (%)']:>8.2f}")
    print("=" * 64)


T975 = [math.nan, 12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262]

def run_replications_phase2_2(lam=1.0, p=0.6, tau=3.0, theta_g=0.08, theta_b=0.04,
                             T=20_000, n_reps=5, warmup=1_000.0, seed0=1000):
    records = []
    for r in range(n_reps):
        pl, aq, _ = simulate_phase2_2(lam=lam, p=p, tau=tau, theta_g=theta_g, theta_b=theta_b,
                                      T=T, warmup=warmup, seed=seed0 + r)
        records.append(compute_kpis_phase2_2(pl, aq, warmup))

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


def analytical_endpoints_phase2_2(lam=1.0, p=0.6, theta_g=0.08, theta_b=0.04):
    """
    Terkli model için analitik uç noktalar:
      τ = 0 (Single Pool / pool_one): Tek kuyruk Markov zinciri
      τ = ∞ (Separate Classes / separate): Ayrık 0/1 Markov zincirleri
    """
    probs = [p, 1.0 - p]
    thetas = [theta_g, theta_b]

    # tau = 0
    w_vec = [lam * pc / (lam + th) for pc, th in zip(probs, thetas)]
    Z = 1.0 + sum(w_vec)
    pi = [x / Z for x in w_vec]
    l_g_0, l_b_0 = pi[0], pi[1]
    w_g_0 = l_g_0 / (lam * p)
    w_b_0 = l_b_0 / (lam * (1.0 - p))
    ab_g_0 = theta_g * w_g_0
    ab_b_0 = theta_b * w_b_0
    l_tot_0 = l_g_0 + l_b_0
    w_tot_0 = l_tot_0 / lam
    cross_0 = (pi[0] * (lam * (1 - p)) + pi[1] * (lam * p)) / (lam * l_tot_0)
    ab_tot_0 = p * ab_g_0 + (1 - p) * ab_b_0

    # tau = inf
    l_g_inf = (lam * p) / (2.0 * lam * p + theta_g)
    l_b_inf = (lam * (1 - p)) / (2.0 * lam * (1 - p) + theta_b)
    w_g_inf = 1.0 / (2.0 * lam * p + theta_g)
    w_b_inf = 1.0 / (2.0 * lam * (1 - p) + theta_b)
    ab_g_inf = theta_g / (2.0 * lam * p + theta_g)
    ab_b_inf = theta_b / (2.0 * lam * (1 - p) + theta_b)
    l_tot_inf = l_g_inf + l_b_inf
    w_tot_inf = l_tot_inf / lam
    ab_tot_inf = p * ab_g_inf + (1 - p) * ab_b_inf

    return {
        "tau_0": {
            "L": l_tot_0, "W": w_tot_0, "cross": cross_0 * 100.0, "ab": ab_tot_0 * 100.0,
            "W_G": w_g_0, "W_B": w_b_0, "ab_G": ab_g_0 * 100.0, "ab_B": ab_b_0 * 100.0,
            "L_G": l_g_0, "L_B": l_b_0
        },
        "tau_inf": {
            "L": l_tot_inf, "W": w_tot_inf, "cross": 0.0, "ab": ab_tot_inf * 100.0,
            "W_G": w_g_inf, "W_B": w_b_inf, "ab_G": ab_g_inf * 100.0, "ab_B": ab_b_inf * 100.0,
            "L_G": l_g_inf, "L_B": l_b_inf
        }
    }


def run_phase2_2_experiments(lam=1.0, p=0.6, tau=3.0, theta_g=0.08, theta_b=0.04,
                             T=20_000, n_reps=5, warmup=1_000.0, plot=False, out_dir="results"):
    os.makedirs(out_dir, exist_ok=True)
    fig_dir = os.path.join(out_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    an = analytical_endpoints_phase2_2(lam=lam, p=p, theta_g=theta_g, theta_b=theta_b)

    print(f"\n==========================================================================")
    print(f"Phase 2.2: Heterojen Terkli Beceri Eşleştirmesi")
    print(f"Parametreler: λ = {lam}, p = {p}, τ = {tau}, θ_G = {theta_g}, θ_B = {theta_b}")
    print(f"Deney Düzeni: {n_reps} replikasyon × T = {T:.0f}, Isınma = {warmup:.0f}")
    print(f"==========================================================================\n")

    R = run_replications_phase2_2(lam=lam, p=p, tau=tau, theta_g=theta_g, theta_b=theta_b,
                                  T=T, n_reps=n_reps, warmup=warmup)

    rows = [
        ["Varış hızı λ_i", f"{lam*p:.2f}", f"{lam*(1-p):.2f}", f"{lam:.2f}"],
        ["Oyuncu sayısı / rep", f"{R[TIER_NAME[GOOD]]['oyuncu sayisi'][0]:.0f}",
         f"{R[TIER_NAME[BAD]]['oyuncu sayisi'][0]:.0f}", f"{R['genel']['toplam oyuncu'][0]:.0f}"],
        ["P(terk_i)", fmt_ci(R[TIER_NAME[GOOD]]["terk orani (%)"], pct=True),
         fmt_ci(R[TIER_NAME[BAD]]["terk orani (%)"], pct=True), fmt_ci(R["genel"]["genel terk orani (%)"], pct=True)],
        ["Çapraz eşleşme oranı", fmt_ci(R[TIER_NAME[GOOD]]["capraz mac orani (%)"], pct=True),
         fmt_ci(R[TIER_NAME[BAD]]["capraz mac orani (%)"], pct=True), fmt_ci(R["genel"]["capraz eslesme orani (%)"], pct=True)],
        ["Ortalama bekleme W_i (tümü)", fmt_ci(R[TIER_NAME[GOOD]]["ort. bekleme (tumu)"]),
         fmt_ci(R[TIER_NAME[BAD]]["ort. bekleme (tumu)"]), fmt_ci(R["genel"]["ort. bekleme (tumu)"])],
        ["Ortalama bekleme W_i (eşleşen)", fmt_ci(R[TIER_NAME[GOOD]]["ort. bekleme (eslesen)"]),
         fmt_ci(R[TIER_NAME[BAD]]["ort. bekleme (eslesen)"]), fmt_ci(R["genel"]["ort. bekleme (eslesen)"])],
        ["Medyan bekleme (eşleşen)", fmt_ci(R[TIER_NAME[GOOD]]["medyan bekleme (eslesen)"], 2),
         fmt_ci(R[TIER_NAME[BAD]]["medyan bekleme (eslesen)"], 2), "–"],
        ["P90 bekleme (eşleşen)", fmt_ci(R[TIER_NAME[GOOD]]["p90 bekleme (eslesen)"], 2),
         fmt_ci(R[TIER_NAME[BAD]]["p90 bekleme (eslesen)"], 2), fmt_ci(R["genel"]["p90 bekleme (eslesen)"], 2)],
        ["Ortalama kuyruk L_i", fmt_ci(R[TIER_NAME[GOOD]]["ort. kuyruk uzunlugu"]),
         fmt_ci(R[TIER_NAME[BAD]]["ort. kuyruk uzunlugu"]), fmt_ci(R["genel"]["ort. toplam kuyruk"])],
        ["Little: λ_i · W_i", f"{lam*p*R[TIER_NAME[GOOD]]['ort. bekleme (tumu)'][0]:.3f}",
         f"{lam*(1-p)*R[TIER_NAME[BAD]]['ort. bekleme (tumu)'][0]:.3f}", f"{lam*R['genel']['ort. bekleme (tumu)'][0]:.3f}"],
    ]
    print("Sınıf Bazlı Performans (Ortalama ± %95 Güven Aralığı)")
    head = ["Metrik", "İyi (Good)", "Kötü (Bad)", "Toplam"]
    print(format_table(head, rows), "\n")

    # tau sweep
    taus = [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 20.0, 50.0]
    sweep_results = []
    for t_val in taus:
        pl, aq, _ = simulate_phase2_2(lam=lam, p=p, tau=t_val, theta_g=theta_g, theta_b=theta_b,
                                      T=T, warmup=warmup, seed=42)
        kp = compute_kpis_phase2_2(pl, aq, warmup)
        sweep_results.append((t_val, kp))

    s_rows = []
    for t_val, kp in sweep_results:
        t_label = "∞" if t_val >= 50.0 else f"{t_val:g}"
        if t_val == tau:
            t_label += " *"
        r = [
            t_label,
            f"{kp['genel']['capraz eslesme orani (%)']:.1f}%",
            f"{kp['genel']['ort. bekleme (tumu)']:.3f}",
            f"{kp[TIER_NAME[GOOD]]['ort. bekleme (tumu)']:.3f}",
            f"{kp[TIER_NAME[BAD]]['ort. bekleme (tumu)']:.3f}",
            f"{kp['genel']['p90 bekleme (eslesen)']:.2f}",
            f"{kp['genel']['ort. toplam kuyruk']:.3f}",
            f"{kp['genel']['genel terk orani (%)']:.1f}%"
        ]
        s_rows.append(r)
    s_head = ["τ", "Çapraz Maç", "W", "W_G", "W_B", "P90", "L", "P(Terk)"]
    print("τ Duyarlılık Analizi (Sweep): Ödünleşim Tablosu (* = varsayılan τ)")
    print(format_table(s_head, s_rows), "\n")

    # Match-Type Matrix
    pl_main, _, _ = simulate_phase2_2(lam=lam, p=p, tau=tau, theta_g=theta_g, theta_b=theta_b,
                                       T=30_000, warmup=warmup, seed=42)
    sel_m = (pl_main["arrival"] >= warmup) & (pl_main["status"] == MATCHED)
    total_m_pairs = (sel_m).sum() // 2
    gg_count = ((pl_main["tier"][sel_m] == GOOD) & (pl_main["match_type"][sel_m] == MATCH_HOMOGENEOUS)).sum() // 2
    bb_count = ((pl_main["tier"][sel_m] == BAD) & (pl_main["match_type"][sel_m] == MATCH_HOMOGENEOUS)).sum() // 2
    gb_count = total_m_pairs - gg_count - bb_count

    print("Maç Tipi Dağılım Matrisi (Tüm maçlardaki oran, T = 30000):")
    m_rows = [
        ["İyi (Good)", f"{100*gg_count/total_m_pairs:.1f}%", f"{100*gb_count/total_m_pairs:.1f}%"],
        ["Kötü (Bad)", "·", f"{100*bb_count/total_m_pairs:.1f}%"]
    ]
    print(format_table(["Maç Tipi", "İyi (Good)", "Kötü (Bad)"], m_rows), "\n")

    # Uç Nokta Doğrulaması
    kp_0 = sweep_results[0][1]
    kp_inf = sweep_results[-1][1]
    rel = lambda x, y: f"{100*abs(x/y - 1):.1f}%" if y > 0 else "–"

    val_rows = [
        ["τ = 0 · L (toplam)", f"{kp_0['genel']['ort. toplam kuyruk']:.3f}", f"{an['tau_0']['L']:.3f}", rel(kp_0['genel']['ort. toplam kuyruk'], an['tau_0']['L'])],
        ["τ = 0 · Çapraz Maç (%)", f"{kp_0['genel']['capraz eslesme orani (%)']:.1f}%", f"{an['tau_0']['cross']:.1f}%", rel(kp_0['genel']['capraz eslesme orani (%)'], an['tau_0']['cross'])],
        ["τ = 0 · P(Terk) (%)", f"{kp_0['genel']['genel terk orani (%)']:.2f}%", f"{an['tau_0']['ab']:.2f}%", rel(kp_0['genel']['genel terk orani (%)'], an['tau_0']['ab'])],
        ["τ = 0 · W_G", f"{kp_0[TIER_NAME[GOOD]]['ort. bekleme (tumu)']:.3f}", f"{an['tau_0']['W_G']:.3f}", rel(kp_0[TIER_NAME[GOOD]]['ort. bekleme (tumu)'], an['tau_0']['W_G'])],
        ["τ = 0 · W_B", f"{kp_0[TIER_NAME[BAD]]['ort. bekleme (tumu)']:.3f}", f"{an['tau_0']['W_B']:.3f}", rel(kp_0[TIER_NAME[BAD]]['ort. bekleme (tumu)'], an['tau_0']['W_B'])],
        ["τ = ∞ · L (toplam)", f"{kp_inf['genel']['ort. toplam kuyruk']:.3f}", f"{an['tau_inf']['L']:.3f}", rel(kp_inf['genel']['ort. toplam kuyruk'], an['tau_inf']['L'])],
        ["τ = ∞ · Çapraz Maç (%)", f"{kp_inf['genel']['capraz eslesme orani (%)']:.1f}%", f"{an['tau_inf']['cross']:.1f}%", "0 (tanım gereği)"],
        ["τ = ∞ · P(Terk) (%)", f"{kp_inf['genel']['genel terk orani (%)']:.2f}%", f"{an['tau_inf']['ab']:.2f}%", rel(kp_inf['genel']['genel terk orani (%)'], an['tau_inf']['ab'])],
        ["τ = ∞ · W_G", f"{kp_inf[TIER_NAME[GOOD]]['ort. bekleme (tumu)']:.3f}", f"{an['tau_inf']['W_G']:.3f}", rel(kp_inf[TIER_NAME[GOOD]]['ort. bekleme (tumu)'], an['tau_inf']['W_G'])],
        ["τ = ∞ · W_B", f"{kp_inf[TIER_NAME[BAD]]['ort. bekleme (tumu)']:.3f}", f"{an['tau_inf']['W_B']:.3f}", rel(kp_inf[TIER_NAME[BAD]]['ort. bekleme (tumu)'], an['tau_inf']['W_B'])],
    ]
    val_head = ["Metrik", "Simülasyon", "Analitik Kapalı Form", "Bağıl Hata"]
    print("Uç Nokta Doğrulaması (τ = 0 Single Pool ve τ = ∞ Strict Separation)")
    print(format_table(val_head, val_rows), "\n")

    # CSV yazımı
    csv_path = os.path.join(out_dir, "tau_sweep.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["tau", "cross_match_ratio", "W_all", "W_good", "W_bad", "P90_matched",
                     "L_total", "P_abandon", "L_good", "L_bad"])
        for t_val, kp in sweep_results:
            wr.writerow([
                t_val,
                kp["genel"]["capraz eslesme orani (%)"] / 100.0,
                kp["genel"]["ort. bekleme (tumu)"],
                kp[TIER_NAME[GOOD]]["ort. bekleme (tumu)"],
                kp[TIER_NAME[BAD]]["ort. bekleme (tumu)"],
                kp["genel"]["p90 bekleme (eslesen)"],
                kp["genel"]["ort. toplam kuyruk"],
                kp["genel"]["genel terk orani (%)"] / 100.0,
                kp[TIER_NAME[GOOD]]["ort. kuyruk uzunlugu"],
                kp[TIER_NAME[BAD]]["ort. kuyruk uzunlugu"]
            ])
    print(f"Sonuçlar CSV dosyasına kaydedildi: {csv_path}")

    if plot:
        plt.style.use("default")
        fig, axs = plt.subplots(1, 2, figsize=(12, 4.5), dpi=150)
        t_arr = [s[0] for s in sweep_results if s[0] < 50.0]
        cross_arr = [s[1]["genel"]["capraz eslesme orani (%)"] for s in sweep_results if s[0] < 50.0]
        w_all_arr = [s[1]["genel"]["ort. bekleme (tumu)"] for s in sweep_results if s[0] < 50.0]
        ab_arr = [s[1]["genel"]["genel terk orani (%)"] for s in sweep_results if s[0] < 50.0]
        w_g_arr = [s[1][TIER_NAME[GOOD]]["ort. bekleme (tumu)"] for s in sweep_results if s[0] < 50.0]
        w_b_arr = [s[1][TIER_NAME[BAD]]["ort. bekleme (tumu)"] for s in sweep_results if s[0] < 50.0]

        axs[0].plot(cross_arr, w_all_arr, "o-", color="#6250d6", lw=1.8, label="Ortalama Bekleme W")
        ax0_tw = axs[0].twinx()
        ax0_tw.plot(cross_arr, ab_arr, "s--", color="#d63b3a", lw=1.5, label="Terk Oranı P(Terk)")
        axs[0].set_xlabel("Çapraz Eşleşme Oranı (%)")
        axs[0].set_ylabel("Ortalama Bekleme Süresi W", color="#6250d6")
        ax0_tw.set_ylabel("Genel Terk Oranı (%)", color="#d63b3a")
        axs[0].set_title("Ödünleşim Eğrisi: Maç Kalitesi vs Bekleme ve Terk")
        axs[0].grid(True, alpha=0.3)

        axs[1].plot(t_arr, w_g_arr, "o-", color="#1d7f4e", lw=1.5, label="İyi (Good) W_G")
        axs[1].plot(t_arr, w_b_arr, "s-", color="#d63b3a", lw=1.5, label="Kötü (Bad) W_B")
        axs[1].plot(t_arr, w_all_arr, "^--", color="#6250d6", lw=1.5, label="Genel W")
        axs[1].axhline(an["tau_inf"]["W_G"], color="#1d7f4e", linestyle=":", label="W_G (τ=∞)")
        axs[1].axhline(an["tau_inf"]["W_B"], color="#d63b3a", linestyle=":", label="W_B (τ=∞)")
        axs[1].set_xlabel("Cross-match Eşiği τ")
        axs[1].set_ylabel("Ortalama Bekleme Süresi")
        axs[1].set_title("Sınıf Bazında Bekleme Süresi Dağılımı")
        axs[1].grid(True, alpha=0.3)
        axs[1].legend()

        plt.tight_layout()
        tr_path = os.path.join(fig_dir, "tradeoff.png")
        plt.savefig(tr_path)
        plt.close(fig)
        print(f"Grafik kaydedildi: {tr_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 2.2: Skill-based matchmaking with heterogeneous abandonment")
    parser.add_argument("--lam", type=float, default=1.0, help="Geliş hızı λ")
    parser.add_argument("--p", type=float, default=0.6, help="Good oranı p")
    parser.add_argument("--tau", type=float, default=3.0, help="Cross-match eşiği τ")
    parser.add_argument("--theta-g", type=float, default=0.08, help="İyi oyuncu terk hızı θ_G")
    parser.add_argument("--theta-b", type=float, default=0.04, help="Kötü oyuncu terk hızı θ_B")
    parser.add_argument("--T", type=float, default=20_000, help="Simülasyon süresi T")
    parser.add_argument("--warmup", type=float, default=1_000.0, help="Isınma süresi")
    parser.add_argument("--reps", type=int, default=5, help="Replikasyon sayısı")
    parser.add_argument("--plot", action="store_true", default=True, help="Grafikleri kaydet")
    parser.add_argument("--out-dir", type=str,
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"),
                        help="Çıktı klasörü")
    args = parser.parse_args()

    run_phase2_2_experiments(lam=args.lam, p=args.p, tau=args.tau,
                             theta_g=args.theta_g, theta_b=args.theta_b,
                             T=args.T, n_reps=args.reps, warmup=args.warmup,
                             plot=args.plot, out_dir=args.out_dir)
