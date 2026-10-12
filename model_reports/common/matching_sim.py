"""
Ortak 1v1 eşleştirme simülasyon motoru (Model 1, 2 ve 3).

Raporlardaki (report.html) tarayıcı simülasyonuyla aynı kuralları uygular.
Üç model tek bir threshold matrix d[i][j] ile tanımlanır:
  i ve j sınıfından iki oyuncu, en az biri d[i][j] kadar beklemişse eşleşebilir.
    - M1 Chess:            d = [[inf, 0], [0, inf]]          (yalnızca karşı renk, FCFS)
    - M2 Good-Bad:         d = [[0, tau], [tau, 0]]
    - M3 Good-Medium-Bad:  d = [[0, tau, 2tau], [tau, 0, tau], [2tau, tau, 0]]  (G-B kapalıysa inf)

Politika:
  - Arrival: eşiği en küçük sınıftan başlanır; o sınıfın sıra başı (en uzun bekleyen)
    eşiği geçmişse onunla eşleşir. Aynı eşikte en uzun bekleyen seçilir.
  - Timeout: bekleyen oyuncu bir eşiğe ulaşınca o eşiğin açtığı sınıfların sıra başıyla eşleşir.
  - Abandonment: sabır ~ Exp(theta_i); sabrı biten oyuncu kuyruktan ayrılır.

Ölçütler (warm-up sonrası gelen, run sonunda beklemeyen oyuncular):
  W_i  : mean waiting time (eşleşen + terk eden)      L_i : zaman ortalamalı queue length
  P(abandon_i), cross-match rate, medyan / P90 W (eşleşenler), P(W = 0), match-type matrix.
"""

import heapq
import math
from collections import deque

import numpy as np

INF = math.inf
ARRIVAL, TIMEOUT, ABANDON = 0, 1, 2
WAITING, MATCHED, ABANDONED = 0, 1, 2


class Sim:
    def __init__(self, lam, probs, d, theta, seed=42, warmup=0.0):
        self.lam, self.probs, self.d, self.theta = lam, list(probs), d, list(theta)
        self.K = K = len(probs)
        self.rng = np.random.default_rng(seed)
        self.warmup = warmup
        self.t = 0.0
        self.last_t = 0.0
        self.heap = []
        self.seq = 0
        self.queues = [deque() for _ in range(K)]
        self.n_wait = [0] * K
        self.area = [0.0] * K
        self.cum = np.cumsum(self.probs)
        # her sınıf için eşleşebileceği sınıflar (eşiğe göre sıralı) ve pozitif eşikler
        self.order, self.thresholds = [], []
        for i in range(K):
            js = sorted([j for j in range(K) if math.isfinite(d[i][j])], key=lambda j: d[i][j])
            self.order.append(js)
            th = []
            for j in js:
                if d[i][j] > 0 and d[i][j] not in th:
                    th.append(d[i][j])
            self.thresholds.append(th)
        self.arr, self.cls, self.end, self.st, self.mate = [], [], [], [], []
        self._push(self._exp(lam), ARRIVAL, -1)

    # --- yardımcılar ---
    def _exp(self, rate):
        return self.rng.exponential(1.0 / rate)

    def _push(self, t, kind, pid, v=None):
        self.seq += 1
        heapq.heappush(self.heap, (t, self.seq, kind, pid, v))

    def _advance(self, to):
        s = max(self.last_t, self.warmup)
        if to > s:
            for i in range(self.K):
                self.area[i] += self.n_wait[i] * (to - s)
        self.last_t = to

    def head(self, c):
        q = self.queues[c]
        while q and self.st[q[0]] != WAITING:
            q.popleft()
        return q[0] if q else -1

    def _match(self, a, b, t):
        self.st[a] = self.st[b] = MATCHED
        self.end[a] = self.end[b] = t
        self.mate[a], self.mate[b] = b, a

    # --- bir olay ---
    def step(self):
        t, _, kind, pid, v = heapq.heappop(self.heap)
        self._advance(t)
        self.t = t
        if kind == ARRIVAL:
            self._push(t + self._exp(self.lam), ARRIVAL, -1)
            c = int(np.searchsorted(self.cum, self.rng.random(), side='right'))
            c = min(c, self.K - 1)
            pid = len(self.arr)
            self.arr.append(t); self.cls.append(c); self.end.append(math.nan); self.st.append(WAITING); self.mate.append(-1)
            best, best_d, best_arr = -1, INF, INF
            for j in self.order[c]:
                dj = self.d[c][j]
                if dj > best_d:
                    break
                h = self.head(j)
                if h >= 0 and t - self.arr[h] >= dj - 1e-12:
                    if dj < best_d or self.arr[h] < best_arr:
                        best, best_d, best_arr = h, dj, self.arr[h]
            if best >= 0:
                self.n_wait[self.cls[best]] -= 1
                self._match(best, pid, t)
                return
            self.queues[c].append(pid)
            self.n_wait[c] += 1
            for th in self.thresholds[c]:
                self._push(t + th, TIMEOUT, pid, th)
            if self.theta[c] > 0:
                self._push(t + self._exp(self.theta[c]), ABANDON, pid)
        elif kind == TIMEOUT:
            if self.st[pid] != WAITING:
                return
            ci, best, ba = self.cls[pid], -1, INF
            for j in range(self.K):
                if j == ci or self.d[ci][j] != v:
                    continue
                h = self.head(j)
                if h >= 0 and self.arr[h] < ba:
                    best, ba = h, self.arr[h]
            if best >= 0:
                self.n_wait[ci] -= 1
                self.n_wait[self.cls[best]] -= 1
                self._match(pid, best, t)
        else:  # ABANDON
            if self.st[pid] != WAITING:
                return
            self.st[pid] = ABANDONED
            self.end[pid] = t
            self.n_wait[self.cls[pid]] -= 1

    def run(self, T, hist=None, trace=None):
        """T'ye kadar koşar. hist(sim) -> anahtar verilirse zaman ağırlıklı durum dağılımı döner.
        trace=(t0, t1) verilirse o aralıktaki (t, N_1..N_K) kayıtlarını döner."""
        H = {} if hist else None
        tr = [] if trace else None
        while self.heap and self.heap[0][0] <= T:
            if H is not None:
                tn, s0 = self.heap[0][0], max(self.t, self.warmup)
                if tn > s0:
                    key = hist(self)
                    H[key] = H.get(key, 0.0) + tn - s0
            self.step()
            if tr is not None and trace[0] <= self.t <= trace[1]:
                tr.append((self.t, *self.n_wait))
        if H is not None:
            s1 = max(self.t, self.warmup)
            if T > s1:
                key = hist(self)
                H[key] = H.get(key, 0.0) + T - s1
            span = T - self.warmup
            H = {k: x / span for k, x in H.items()}
        self._advance(T)
        self.t = T
        return H, tr


def kpis(sim, T):
    """Sınıf bazında ve toplam ölçütler."""
    K, wu, span = sim.K, sim.warmup, T - sim.warmup
    arr, cls, end, st, mate = (np.array(x) for x in (sim.arr, sim.cls, sim.end, sim.st, sim.mate))
    done = (arr >= wu) & (st != WAITING)
    w = end - arr
    out = {'cls': [], 'pairs': np.zeros((K, K), dtype=int)}
    matched = done & (st == MATCHED)
    mcls = np.where(mate >= 0, cls[np.clip(mate, 0, None)], -1)
    for c in range(K):
        sel = done & (cls == c)
        wm = w[sel & (st == MATCHED)]
        n = int(sel.sum())
        m = int((sel & (st == MATCHED)).sum())
        cross = int((sel & matched & (mcls != c)).sum())
        out['cls'].append({
            'n': n,
            'matchRate': m / n if n else math.nan,
            'abRate': int((sel & (st == ABANDONED)).sum()) / n if n else math.nan,
            'wAll': float(w[sel].mean()) if n else math.nan,
            'wM': float(wm.mean()) if len(wm) else math.nan,
            'wMed': float(np.median(wm)) if len(wm) else math.nan,
            'wP90': float(np.percentile(wm, 90)) if len(wm) else math.nan,
            'zeroRate': float((w[sel] == 0).mean()) if n else math.nan,
            'L': sim.area[c] / span,
            'crossRate': cross / m if m else math.nan,
            'wMatched': wm,
        })
    # maç tipi matrisi: her maç bir kez (ikinci oyuncu ya da ısınma öncesi partner üzerinden)
    for i in np.where(matched)[0]:
        j = mate[i]
        if j > i or arr[j] < wu:
            a, b = sorted((cls[i], cls[j]))
            out['pairs'][a, b] += 1
    n_pairs = int(out['pairs'].sum())
    cross_pairs = n_pairs - int(np.trace(out['pairs']))
    wd, wmd = w[done], w[matched]
    out['total'] = {
        'n': int(done.sum()),
        'matchRate': float((st[done] == MATCHED).mean()),
        'abRate': float((st[done] == ABANDONED).mean()),
        'wAll': float(wd.mean()),
        'wM': float(wmd.mean()) if len(wmd) else math.nan,
        'wP90': float(np.percentile(wmd, 90)) if len(wmd) else math.nan,
        'L': sum(sim.area) / span,
        'crossRate': cross_pairs / n_pairs if n_pairs else 0.0,
    }
    out['n_pairs'] = n_pairs
    return out


def run(lam, probs, d, theta, T, seed=42, warmup=1000.0, hist=None, trace=None):
    sim = Sim(lam, probs, d, theta, seed=seed, warmup=warmup)
    H, tr = sim.run(T, hist=hist, trace=trace)
    return kpis(sim, T), H, tr


T975 = [math.nan, 12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262]


def flat(k):
    o = {}
    for i, c in enumerate(k['cls']):
        for m in ('n', 'matchRate', 'abRate', 'wAll', 'wM', 'wMed', 'wP90', 'zeroRate', 'L', 'crossRate'):
            o[f'{m}{i}'] = c[m]
    for m in ('n', 'matchRate', 'abRate', 'wAll', 'wM', 'wP90', 'L', 'crossRate'):
        o['T_' + m] = k['total'][m]
    return o


def reps(lam, probs, d, theta, T=20000, n=5, warmup=1000.0, seed0=1000):
    """n bağımsız replikasyon: her ölçüt için (ortalama, %95 CI yarı genişliği)."""
    vals = [flat(run(lam, probs, d, theta, T, seed=seed0 + r, warmup=warmup)[0]) for r in range(n)]
    out = {}
    for key in vals[0]:
        xs = np.array([v[key] for v in vals], dtype=float)
        m = float(np.mean(xs))
        h = T975[n - 1] * float(np.std(xs, ddof=1)) / math.sqrt(n) if n > 1 else math.nan
        out[key] = (m, h)
    return out


# ---------- analitik referanslar ----------

def ctmc_chess(lam, p, theta, N=500):
    """M1: X = N_w - N_b birth-death CTMC. theta = 0 ise None (durağan dağılım yok)."""
    if not theta > 0:
        return None
    a, b = p * lam, (1 - p) * lam
    lp = {0: 0.0}
    for n in range(1, N):
        lp[n] = lp[n - 1] + math.log(a) - math.log(b + n * theta)
        lp[-n] = lp[-(n - 1)] + math.log(b) - math.log(a + n * theta)
    m = max(lp.values())
    pi = {n: math.exp(v - m) for n, v in lp.items()}
    Z = sum(pi.values())
    pi = {n: v / Z for n, v in pi.items()}
    Lw = sum(n * v for n, v in pi.items() if n > 0)
    Lb = sum(-n * v for n, v in pi.items() if n < 0)
    return {'dist': pi, 'Lw': Lw, 'Lb': Lb, 'L': Lw + Lb, 'Ww': Lw / a, 'Wb': Lb / b,
            'abW': theta * Lw / a, 'abB': theta * Lb / b}


def pool_one(lam, probs, theta):
    """tau = 0 (single pool): toplam kuyruk <= 1. Durum 0 ya da 'c sınıfından biri bekliyor'."""
    w = [lam * p / (lam + th) for p, th in zip(probs, theta)]
    Z = 1 + sum(w)
    pi = [x / Z for x in w]
    cls = [{'L': pc, 'W': pc / (lam * p), 'ab': th * pc / (lam * p)} for pc, p, th in zip(pi, probs, theta)]
    L = sum(pi)
    cross = sum(pc * (lam - lam * p) for pc, p in zip(pi, probs)) / (lam * L)
    return {'cls': cls, 'L': L, 'W': L / lam, 'cross': cross, 'ab': sum(c['ab'] * p for c, p in zip(cls, probs))}


def separate(lam, probs, theta):
    """tau = inf (strict separation): her sınıf ayrı 0/1 zinciri."""
    cls = []
    for p, th in zip(probs, theta):
        lc = lam * p
        cls.append({'L': lc / (2 * lc + th), 'W': 1 / (2 * lc + th), 'ab': th / (2 * lc + th)})
    L = sum(c['L'] for c in cls)
    return {'cls': cls, 'L': L, 'W': L / lam, 'cross': 0.0, 'ab': sum(c['ab'] * p for c, p in zip(cls, probs))}


# ---------- çıktı yardımcıları ----------

def fmt_ci(mh, digits=3, pct=False):
    m, h = mh
    if pct:
        return f'{100 * m:.1f}% ± {100 * h:.1f}'
    return f'{m:.{digits}f} ± {h:.{digits}f}'


def table(head, rows):
    """Basit hizalı metin tablosu."""
    w = [max(len(str(x)) for x in col) for col in zip(head, *rows)]
    line = '  '.join(str(h).ljust(w[i]) if i == 0 else str(h).rjust(w[i]) for i, h in enumerate(head))
    out = [line, '-' * len(line)]
    for r in rows:
        out.append('  '.join(str(x).ljust(w[i]) if i == 0 else str(x).rjust(w[i]) for i, x in enumerate(r)))
    return '\n'.join(out)
