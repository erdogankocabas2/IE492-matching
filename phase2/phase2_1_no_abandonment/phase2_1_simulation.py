"""
Phase 2.1: Skill-based Matchmaking without Abandonment (Terk Yok)
- Oyuncular: Poisson(lambda) varışları.
- Beceri Sınıfları: Good (İyi) olasılığı p, Bad (Kötü) olasılığı 1-p.
- Renk kısıtı yok (1v1 skill-based).
- Homojen Öncelik: Good-Good, Bad-Bad.
- Cross-match Eşiği (tau): Bekleme süresi tau aşılınca esnek (flexible) moda geçer,
  karşı sınıfla eşleşebilir (Good-Bad).
- Terk etme yok (theta = 0).
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

# Olay tipleri
EVT_ARRIVAL = 1
EVT_TIMEOUT = 2

# Maç tipleri
MATCH_HOMOGENEOUS = 0  # G-G veya B-B
MATCH_CROSS = 1        # G-B


def simulate_phase2_1(lam=1.0, p=0.6, tau=3.0, T=50_000, warmup=1_000, seed=42):
    """
    Phase 2.1 Olay Tabanlı Ayrık Simülasyon
    """
    rng = np.random.default_rng(seed)

    # Oyuncu kayıtları
    arrival = []
    tier = []
    end = []
    status = []
    partner_id = []
    match_type = []

    # Kuyruklar (indeksler)
    queues = {GOOD: deque(), BAD: deque()}
    n_waiting = {GOOD: 0, BAD: 0}

    # Olay kuyruğu (event_time, event_type, player_id)
    events = []

    # Zaman ortalamalı kuyruk alanı
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

    # İlk varış olayını ekle
    t_first = rng.exponential(1.0 / lam)
    heapq.heappush(events, (t_first, EVT_ARRIVAL, -1))

    while events:
        evt_t, evt_type, pid = heapq.heappop(events)

        if evt_t > T:
            advance(T)
            break

        advance(evt_t)

        if evt_type == EVT_ARRIVAL:
            # 1. Yeni bir sonraki varışı planla
            t_next = evt_t + rng.exponential(1.0 / lam)
            if t_next <= T:
                heapq.heappush(events, (t_next, EVT_ARRIVAL, -1))

            # 2. Yeni gelen oyuncuyu oluştur
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
                # Homojen eşleşme!
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

            # Eşleşme Adımı 2: Kendi sınıfında yok. Karşı sınıfta FLEXIBLE (>= tau beklemiş) var mı?
            cross_partner = None
            # Karşı sınıftaki esnek oyuncuyu bulmak için baştan tara
            for candidate in queues[other]:
                if status[candidate] == FLEXIBLE:
                    cross_partner = candidate
                    break

            if cross_partner is not None:
                # Çapraz eşleşme!
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

            # Eşleşme olmadı -> Kuyruğa gir
            queues[c].append(curr_id)
            n_waiting[c] += 1
            # tau süresi sonrası için timeout olayı planla
            heapq.heappush(events, (evt_t + tau, EVT_TIMEOUT, curr_id))
            record_trace(evt_t)

        elif evt_type == EVT_TIMEOUT:
            # Oyuncunun tau süresi doldu, esnek duruma geçiş
            if status[pid] == WAITING:
                status[pid] = FLEXIBLE
                c = tier[pid]
                other = 1 - c

                # Karşı tarafta bekleyen herhangi biri var mı?
                # Varsa ANINDA çapraz eşleşme gerçekleşir!
                cross_partner = None
                while queues[other]:
                    candidate = queues[other].popleft()
                    if status[candidate] in (WAITING, FLEXIBLE):
                        cross_partner = candidate
                        break

                if cross_partner is not None:
                    # pid kuyruğundan da çıkar
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
                else:
                    # Karşıda kimse yok, kuyrukta FLEXIBLE olarak beklemeye devam eder
                    pass

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


def compute_kpis_phase2_1(players, avg_queue, warmup=1_000):
    kpis = {}
    total_matches = 0
    cross_matches = 0

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
        }

    # Genel maç metrikleri
    sel_all = (players["arrival"] >= warmup) & (players["status"] == MATCHED)
    w_all = players["end"][sel_all] - players["arrival"][sel_all]
    mt_all = players["match_type"][sel_all]

    total_matched_players = len(w_all)
    cross_matched_players = int((mt_all == MATCH_CROSS).sum())
    cross_match_ratio = cross_matched_players / total_matched_players if total_matched_players > 0 else 0.0

    kpis["genel"] = {
        "toplam eslesen oyuncu": total_matched_players,
        "ort. bekleme (genel)": float(w_all.mean()) if len(w_all) > 0 else 0.0,
        "ort. toplam kuyruk": avg_queue["total"],
        "capraz eslesme orani (%)": cross_match_ratio * 100.0,
        "homojen eslesme orani (%)": (1.0 - cross_match_ratio) * 100.0,
    }

    return kpis


def print_kpis_phase2_1(kpis):
    print("=" * 60)
    print(f"{'KPI':<30}{'İyi (Good)':>14}{'Kötü (Bad)':>14}")
    print("-" * 60)
    for k in ["oyuncu sayisi", "ort. bekleme", "medyan bekleme", "p90 bekleme",
              "beklemeden eslesme orani", "ort. kuyruk uzunlugu", "capraz mac sayisi"]:
        print(f"{k:<30}{kpis[TIER_NAME[GOOD]][k]:>14.3f}{kpis[TIER_NAME[BAD]][k]:>14.3f}")
    print("-" * 60)
    print(f"Genel Ortalama Bekleme Süresi : {kpis['genel']['ort. bekleme (genel)']:>10.3f}")
    print(f"Genel Ortalama Toplam Kuyruk  : {kpis['genel']['ort. toplam kuyruk']:>10.3f}")
    print(f"Çapraz Eşleşme Oranı (G-B)    : %{kpis['genel']['capraz eslesme orani (%)']:>9.2f}")
    print(f"Homojen Eşleşme Oranı (G-G,B-B): %{kpis['genel']['homojen eslesme orani (%)']:>8.2f}")
    print("=" * 60)


if __name__ == "__main__":
    LAM = 1.0
    P = 0.6
    TAU = 3.0
    T = 50_000
    WARMUP = 1_000
    SEED = 42

    print(f"Phase 2.1 Simülasyonu Çalıştırılıyor (lambda={LAM}, p={P}, tau={TAU})...")
    players, avg_queue, trace = simulate_phase2_1(lam=LAM, p=P, tau=TAU, T=T, warmup=WARMUP, seed=SEED)
    kpis = compute_kpis_phase2_1(players, avg_queue, warmup=WARMUP)
    print_kpis_phase2_1(kpis)
