# Phase 2.1: Skill-Based Matchmaking Without Abandonment (Terk Yok)

Bu aşamada 1v1 maçlar için beceri (skill) temelli eşleştirme mekanizması modellenmiştir. Oyuncular **İyi (Good)** ve **Kötü (Bad)** olmak üzere iki gruba ayrılır. Terk etme (abandonment) henüz yoktur ($\theta = 0$).

Modelin etkileşimli tarayıcı raporu: [`model_reports/m2_good_bad/report.html`](../../model_reports/m2_good_bad/report.html) (Abandonment kapalıyken `Phase 2.1` rejimi)

---

## Model Dinamikleri

- **Geliş Süreci:** Oyuncular Poisson($\lambda$) hızıyla gelir ($\lambda = 1.0$).
- **Beceri Dağılımı:**
  - $p$ olasılıkla: **İyi (Good)** ($p = 0.60$)
  - $1-p$ olasılıkla: **Kötü (Bad)** ($1-p = 0.40$)
- **Renk Kısıtı:** Yoktur (1v1 beceri tabanlı).

### Eşleşme Mantığı ve $\tau$ Eşiği
1. **Homojen Öncelik:** Yeni gelen oyuncu öncelikle kendi sınıfından bekleyen varsa onunla anında eşleşir ($G-G$ veya $B-B$).
2. **Eşikli Çapraz Eşleşme ($\tau$):** Kendi sınıfında kimse yoksa, karşı sınıfta bekleme süresi $\ge \tau$ olan ("esnek") bir oyuncu varsa, onunla anında çapraz eşleşme ($G-B$) gerçekleşir.
3. **Zaman Aşımı Olayı (Timeout Event):** Kuyrukta bekleyen bir oyuncunun bekleme süresi $\tau$ eşiğine ulaştığı anda, karşı sınıfta bekleyen biri varsa **anında** çapraz eşleşme yapılır.

---

## Analitik Uç Nokta Doğrulaması

Sistem iki uç noktada kapalı form analitik çözüme sahiptir:

### 1. $\tau = 0$ (Single Pool / Tek Havuz Eşleştirme)
Tüm oyuncular beceri farkı gözetilmeksizin FCFS sırasına göre eşleşir. Sistemde sırada en fazla 1 oyuncu bekleyebilir (durum 0 veya durum 1):
$$\pi_0 = 0.5, \quad \pi_1 = 0.5 \implies L = 0.500, \quad W = \frac{L}{\lambda} = 0.500$$
Çapraz eşleşme oranı:
$$\text{Cross-match Rate} = 2p(1-p) = 2 \times 0.60 \times 0.40 = 48.0\%$$

### 2. $\tau = \infty$ (Strict Separation / Katı Ayrım)
İki sınıf birbirinden tamamen bağımsız iki eşleştirme kuyruğudur. Her sınıf kendi içinde en fazla 1 bekleyen oyuncuya sahiptir:
$$L_G = 0.500, \quad W_G = \frac{1}{2\lambda p} = \frac{1}{2(0.60)} = 0.833$$
$$L_B = 0.500, \quad W_B = \frac{1}{2\lambda (1-p)} = \frac{1}{2(0.40)} = 1.250$$
$$L_\text{toplam} = L_G + L_B = 1.000, \quad W_\text{genel} = 1.000, \quad \text{Cross-match Rate} = 0.0\%$$

---

## Simülasyon Doğrulama Tablosu

5 bağımsız replikasyon ($\lambda = 1.0, p = 0.60, \tau = 3.0, T = 20\,000$):

| Metrik | İyi (Good) | Kötü (Bad) | Toplam Simülasyon | Analitik Referans | Bağıl Hata |
|---|---|---|---|---|---|
| **Varış Hızı $\lambda_i$** | 0.60 | 0.40 | 1.00 | 1.00 | – |
| **Ortalama Bekleme $W$ ($\tau=3.0$)** | 0.725 ± 0.013 | 1.000 ± 0.028 | 0.836 ± 0.018 | – | – |
| **Çapraz Eşleşme Oranı ($\tau=3.0$)** | %12.2 ± 0.7 | %18.1 ± 1.1 | %14.6 ± 0.9 | – | – |
| **Kuyruk Uzunluğu $L$ ($\tau=3.0$)** | 0.436 ± 0.005 | 0.405 ± 0.007 | 0.841 ± 0.011 | – | – |
| **$\tau = 0$ Limit Kuyruk $L$** | – | – | 0.493 | 0.500 | %1.3 |
| **$\tau = 0$ Çapraz Maç Oranı** | – | – | %48.0 | %48.0 | %0.1 |
| **$\tau = \infty$ Limit Kuyruk $L$** | 0.500 | 0.500 | 1.000 | 1.000 | %0.0 |
| **$\tau = \infty$ Limit Bekleme $W_G$** | 0.837 | – | – | 0.833 | %0.5 |
| **$\tau = \infty$ Limit Bekleme $W_B$** | – | 1.230 | – | 1.250 | %1.6 |

---

## Dosya ve Sonuç Organizasyonu

- **Simülasyon Kodu:** [`phase2_1_simulation.py`](phase2_1_simulation.py)
  - Çoklu replikasyon, %95 CI, uç nokta doğrulayıcı ve $\tau$-sweep içerir.
  - Çalıştırma: `python3 phase2/phase2_1_no_abandonment/phase2_1_simulation.py --tau 3.0 --plot`
- **İnteraktif Notebook:** [`phase2_1_simulation.ipynb`](phase2_1_simulation.ipynb)
- **Üretilen Sonuç Dosyaları:**
  - `results/tau_sweep.csv`: $\tau \in [0, 50]$ sweep metrik tablosu.
  - `results/figures/tradeoff.png`: Bekleme süresi ve çapraz eşleşme ödünleşim grafiği.
