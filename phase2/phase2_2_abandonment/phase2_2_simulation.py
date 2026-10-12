"""
Phase 2.2: Skill-based Matchmaking with Heterogeneous Abandonment (Terkli Model)
- Oyuncular: Poisson(lambda) varışları.
- Beceri Sınıfları: Good (İyi) olasılığı p, Bad (Kötü) olasılığı 1-p.
- Renk kısıtı yok (1v1 skill-based).
- Farklı Terk Oranları:
    * İyi oyuncu terk hızı: theta_G (ortalama sabır 1/theta_G)
    * Kötü oyuncu terk hızı: theta_B (ortalama sabır 1/theta_B)
- Cross-match Eşiği (tau): Bekleme süresi tau aşılınca esnek moda geçer.
- Etkileşim: Sabır süresi < tau ise oyuncu cross-match göremeden terk edebilir;
  sabır > tau ise esnek havuza girer, yine de eşleşemezse sabrı bitince terk eder.
"""

import heapq
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
                      T=50_000, warmup=1_000, seed=42):
    """
    Phase 2.2 Olay Tabanlı Ayrık Simülasyon (Farklı Terk Oranları)
    """
    rng = np.random.default_rng(seed)
    theta_map = {GOOD: theta_g, BAD: theta_b}

    # Oyuncu kayıtları
    arrival = []
    tier = []
    end = []
    status = []
    partner_id = []
    match_type = []

    queues = {GOOD: deque(), BAD: deque()}
    n_waiting = {GOOD: 0, BAD: 0}

    events = []

    area = {GOOD: 0.0, BAD: 0.0}
    last_t = 0.0
    trace_t = [0.0]
    trace_q_good = [0]
    trace_q_bad = [0]
    trace_q_total = [0]

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
            # 1. Yeni varışı planla
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

            # Eşleşme Adımı 1: Kendi sınıfında bekleyen var mı?
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

            # Eşleşme Adımı 2: Karşı sınıfta FLEXIBLE var mı?
            cross_partner = None
            for candidate in queues[other]:
                if status[candidate] == FLEXIBLE:
                    cross_partner = candidate
                    break

            if cross_partner is not None:
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

            # Eşleşme olmadı -> Kuyruğa ekle
            queues[c].append(curr_id)
            n_waiting[c] += 1

            # tau timeout olayı ekle
            heapq.heappush(events, (evt_t + tau, EVT_TIMEOUT, curr_id))

            # Terk olayı ekle (sabır süresi)
            th = theta_map[c]
            if th > 0:
                patience = rng.exponential(1.0 / th)
                heapq.heappush(events, (evt_t + patience, EVT_ABANDON, curr_id))

            record_trace(evt_t)

        elif evt_type == EVT_TIMEOUT:
            # tau doldu
            if status[pid] == WAITING:
                status[pid] = FLEXIBLE
                c = tier[pid]
                other = 1 - c

                # Karşı tarafta bekleyen herhangi biri var mı?
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
            # Sabır doldu, terk
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


def compute_kpis_phase2_2(players, avg_queue, warmup=1_000):
    kpis = {}

    for c in (GOOD, BAD):
        sel = (players["tier"] == c) & (players["arrival"] >= warmup) & (players["status"] != WAITING) & (players["status"] != FLEXIBLE)
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
        }

    # Genel metrikler
    sel_all = (players["arrival"] >= warmup) & (players["status"].isin([MATCHED, ABANDONED]))
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
        "ort. bekleme (eslesen)": float(w_matched_all.mean()) if len(w_matched_all) > 0 else 0.0,
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


if __name__ == "__main__":
    LAM = 1.0
    P = 0.6
    TAU = 3.0
    THETA_G = 0.08   # İyi oyuncular daha sabırsız
    THETA_B = 0.04   # Kötü oyuncular daha sabırlı
    T = 50_000
    WARMUP = 1_000
    SEED = 42

    print(f"Phase 2.2 Simülasyonu Çalıştırılıyor (theta_G={THETA_G}, theta_B={THETA_B}, tau={TAU})...")
    players, avg_queue, trace = simulate_phase2_2(
        lam=LAM, p=P, tau=TAU, theta_g=THETA_G, theta_b=THETA_B,
        T=T, warmup=WARMUP, seed=SEED
    )
    kpis = compute_kpis_phase2_2(players, avg_queue, warmup=WARMUP)
    print_kpis_phase2_2(kpis)
