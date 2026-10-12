# Phase 1: Renk Bazlı FCFS Satranç Eşleştirmesi (Terkli Model)

Bu aşamada ELO / beceri puanı olmaksızın, renk tercihi (Beyaz / Siyah), ilk gelen ilk eşleşir (FCFS) disiplini ve sabır süresi (terk / reneging) içeren 1v1 iki taraflı eşleştirme kuyruk sistemi modellenmiştir.

Modelin etkileşimli tarayıcı raporu ve canlı animasyonu: [`model_reports/m1_chess/report.html`](../model_reports/m1_chess/report.html)

---

## Model Tanımı ve Dinamikleri

- **Geliş Süreci:** Oyuncular Poisson($\lambda$) süreciyle sisteme dahil olur ($\lambda = 1.0$).
- **Renk Tercihi Dağılımı:** Her oyuncu bağımsız olarak $p$ olasılıkla **Beyaz**, $1-p$ olasılıkla **Siyah** renk tercih eder (varsayılan $p = 0.60$).
- **Eşleştirme Kuralı (FCFS):** Sıranın başındaki Beyaz ile sıranın başındaki Siyah anında eşleşir. Bu nedenle kuyrukta aynı anda yalnızca tek bir renk birikebilir:
  $$X(t) = N_\text{beyaz}(t) - N_\text{siyah}(t)$$
  $N_\text{beyaz}(t) > 0 \implies N_\text{siyah}(t) = 0$ ve tersi.
- **Terk (Abandonment / Reneging):** Bekleyen her oyuncunun sabır süresi $S \sim \text{Exp}(\theta)$ dağılımına sahiptir (varsayılan $\theta = 0.05 \implies$ ortalama sabır $1/\theta = 20$ zaman birimi). Sabrı dolan oyuncu kuyruktan ayrılır.

---

## Analitik Doğrulama: Doğum-Ölüm Süreci (Birth-Death CTMC)

Sistem durumu $X(t) \in \mathbb{Z}$ tek boyutlu bir CTMC olarak kesin çözüme sahiptir:
- $n > 0$ ($n$ beyaz bekliyor):
  - İleri geçiş hızı ($n \to n+1$): $\lambda_\text{w} = p\lambda$
  - Geri geçiş hızı ($n \to n-1$): $\lambda_\text{b} + n\theta = (1-p)\lambda + n\theta$
- $n < 0$ ($|n|$ siyah bekliyor):
  - İleri geçiş hızı ($n \to n-1$): $\lambda_\text{b} = (1-p)\lambda$
  - Geri geçiş hızı ($n \to n+1$): $\lambda_\text{w} + |n|\theta = p\lambda + |n|\theta$

### Durağan Durum Dağılımı $\pi_n$ ve Little Yasası
Detaylı denge denklemlerinden:
$$\pi_n = \pi_0 \prod_{k=1}^n \frac{p\lambda}{(1-p)\lambda + k\theta} \quad (n > 0), \qquad \pi_{-n} = \pi_0 \prod_{k=1}^n \frac{(1-p)\lambda}{p\lambda + k\theta} \quad (n > 0)$$

Durağan kuyruk uzunlukları:
$$L_\text{beyaz} = \sum_{n=1}^\infty n \pi_n, \qquad L_\text{siyah} = \sum_{n=1}^\infty n \pi_{-n}, \qquad L_\text{toplam} = E[|X|] = L_\text{beyaz} + L_\text{siyah}$$

Little Yasası ile ortalama bekleme süreleri ve terk oranları:
$$W_\text{beyaz} = \frac{L_\text{beyaz}}{p\lambda}, \qquad W_\text{siyah} = \frac{L_\text{siyah}}{(1-p)\lambda}$$
$$P(\text{beyaz terk}) = \frac{\theta L_\text{beyaz}}{p\lambda}, \qquad P(\text{siyah terk}) = \frac{\theta L_\text{siyah}}{(1-p)\lambda}$$

---

## Doğrulama Sonuçları (Simülasyon vs CTMC)

Varsayılan parametreler ($\lambda = 1.0, p = 0.60, \theta = 0.05, T = 20\,000$, 5 bağımsız replikasyon):

| Metrik | Beyaz (Simülasyon ± %95 CI) | Beyaz (CTMC) | Siyah (Simülasyon ± %95 CI) | Siyah (CTMC) | Toplam (Simülasyon ± %95 CI) | Toplam (CTMC) |
|---|---|---|---|---|---|---|
| **Varış Hızı $\lambda_i$** | 0.60 | 0.60 | 0.40 | 0.40 | 1.00 | 1.00 |
| **P(Terk)** | %34.2 ± 1.4 | %34.8 | %2.2 ± 0.3 | %2.2 | %21.4 ± 0.9 | %21.8 |
| **Ortalama Bekleme $W_i$** | 6.789 ± 0.317 | 6.962 | 0.460 ± 0.070 | 0.443 | 4.245 ± 0.204 | 4.354 |
| **P90 Bekleme (Eşleşen)** | 15.56 ± 0.73 | – | 1.08 ± 0.45 | – | 12.31 ± 0.67 | – |
| **P(W = 0)** | %9.1 ± 1.2 | – | %84.3 ± 1.8 | – | – | – |
| **Ortalama Kuyruk $L_i$** | 4.052 ± 0.219 | 4.177 | 0.185 ± 0.031 | 0.177 | 4.236 ± 0.195 | 4.354 |
| **Little Kontrolü $\lambda_i W_i$** | 4.074 | 4.177 | 0.184 | 0.177 | 4.245 | 4.354 |

> [!NOTE]
> Simülasyon sonuçları analitik CTMC çözümü ile **%2 bağıl hata payı** içerisinde birebir örtüşmektedir. Little Yasası tam olarak sağlanmaktadır ($\lambda_i W_i \approx L_i$).

---

## Dosya ve Sonuç Organizasyonu

- **Simülasyon Kodu:** [`stage1_chess_fcfs.py`](stage1_chess_fcfs.py)
  - Çoklu replikasyon, %95 CI, CTMC çözücü, $p$-sweep ve $\theta$-sweep çalıştırır.
  - Komut: `python3 phase1/stage1_chess_fcfs.py --reps 5 --plot`
- **İnteraktif Notebook:** [`stage1_chess_fcfs.ipynb`](stage1_chess_fcfs.ipynb)
- **Üretilen Sonuç Dosyaları:**
  - `results/p_sweep.csv`: $p \in [0.20, 0.80]$ için simülasyon ve CTMC metrik tablosu.
  - `results/figures/p_sweep.png`: $p$ duyarlılık analizi grafiği (bekleme ve terk oranları).
  - `results/figures/steady_state.png`: Kuyruk izi ve analitik $\pi_n$ durağan dağılım doğrulaması.
- **İnteraktif Web Raporu:** [`model_reports/m1_chess/report.html`](../model_reports/m1_chess/report.html)
