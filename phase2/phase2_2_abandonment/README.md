# Phase 2.2: Skill-Based Matchmaking With Heterogeneous Abandonment (Terkli Model)

Bu aşamada 1v1 beceri (skill) temelli eşleştirmeye oyuncuların sabır süreleri (terk etme / reneging) dahil edilmiştir. Gerçekçi bir oyun ekosisteminde olduğu gibi **İyi (Good)** ve **Kötü (Bad)** oyuncuların terk parametreleri birbirinden farklıdır ($\theta_G \neq \theta_B$).

Modelin etkileşimli tarayıcı raporu: [`model_reports/m2_good_bad/report.html`](../../model_reports/m2_good_bad/report.html)

---

## Model Dinamikleri

- **Geliş Süreci:** Oyuncular Poisson($\lambda$) hızıyla gelir ($\lambda = 1.0$).
- **Beceri Dağılımı:**
  - $p$ olasılıkla: **İyi (Good)** ($p = 0.60$)
  - $1-p$ olasılıkla: **Kötü (Bad)** ($1-p = 0.40$)
- **Heterojen Sabır Dağılımı:**
  - İyi oyuncu sabrı: $S_G \sim \text{Exp}(\theta_G)$ ($\theta_G = 0.08 \implies E[S_G] = 12.5$ birim zaman).
  - Kötü oyuncu sabrı: $S_B \sim \text{Exp}(\theta_B)$ ($\theta_B = 0.04 \implies E[S_B] = 25.0$ birim zaman).

### $\tau$ Eşiği ve Terk Etme Etkileşimi
1. **Sabır Süresi $< \tau$:** Oyuncu $\tau$ süresi dolmadan önce sabrını tüketirse doğrudan sistemden terk eder (`ABANDONED`). Çapraz eşleşme şansı bulamaz.
2. **Sabır Süresi $\ge \tau$:** Oyuncu $\tau$ süresine ulaştığında "esnek" (`FLEXIBLE`) moda geçer ve karşı sınıfla eşleşebilir hale gelir. Eğer yine de karşı sınıftan eşleşme bulamazsa sabrı bittiğinde terk eder.

---

## Analitik Uç Nokta Doğrulaması

Sistem iki uç noktada kapalı form Markov Zinciri çözümlerine sahiptir:

### 1. $\tau = 0$ (Single Pool / Tek Havuz Eşleştirme)
Herkes herkesle eşleşir. Sistemde sırada en fazla 1 kişi bekleyebilir (durum 0, durum Good bekliyor, durum Bad bekliyor).
Detaylı denge denklemlerinden:
$$w_c = \frac{\lambda p_c}{\lambda + \theta_c}, \quad Z = 1 + w_G + w_B, \quad \pi_c = \frac{w_c}{Z}$$
$$L_c = \pi_c, \quad W_c = \frac{L_c}{\lambda p_c}, \quad P(\text{terk}_c) = \theta_c W_c$$
$$L = L_G + L_B = 0.485, \quad \text{Cross-match Rate} = 48.2\%, \quad P(\text{terk}) = 3.08\%$$

### 2. $\tau = \infty$ (Strict Separation / Ayrık Sınıflar)
İki sınıf bağımsız kuyruklardır. Her sınıfın sırada en fazla 1 oyuncusu olabilir:
$$L_G = \frac{\lambda p}{2\lambda p + \theta_G} = \frac{0.60}{1.20 + 0.08} = 0.469, \quad W_G = 0.781, \quad P(\text{terk}_G) = 6.25\%$$
$$L_B = \frac{\lambda(1-p)}{2\lambda(1-p) + \theta_B} = \frac{0.40}{0.80 + 0.04} = 0.476, \quad W_B = 1.190, \quad P(\text{terk}_B) = 4.76\%$$
$$L_\text{toplam} = 0.945, \quad \text{Cross-match Rate} = 0.0\%, \quad P(\text{terk}) = 5.65\%$$

---

## Simülasyon Doğrulama Tablosu

5 bağımsız replikasyon ($\lambda = 1.0, p = 0.60, \tau = 3.0, \theta_G = 0.08, \theta_B = 0.04, T = 20\,000$):

| Metrik | İyi (Good) | Kötü (Bad) | Toplam Simülasyon | Analitik Referans | Bağıl Hata |
|---|---|---|---|---|---|
| **Varış Hızı $\lambda_i$** | 0.60 | 0.40 | 1.00 | 1.00 | – |
| **P(Terk) ($\tau=3.0$)** | %5.6 ± 0.3 | %3.7 ± 0.3 | %4.8 ± 0.3 | – | – |
| **Ortalama Bekleme $W$ ($\tau=3.0$)** | 0.705 ± 0.010 | 0.994 ± 0.017 | 0.821 ± 0.006 | – | – |
| **Çapraz Eşleşme Oranı ($\tau=3.0$)** | %10.8 ± 0.2 | %16.2 ± 0.4 | %13.6 ± 0.3 | – | – |
| **Kuyruk Uzunluğu $L$ ($\tau=3.0$)** | 0.423 ± 0.006 | 0.399 ± 0.006 | 0.822 ± 0.007 | – | – |
| **Little Kontrolü $\lambda_i W_i$** | 0.423 | 0.398 | 0.821 | – | – |
| **$\tau = 0$ Limit Kuyruk $L$** | 0.283 | 0.202 | 0.484 | 0.485 | %0.2 |
| **$\tau = 0$ Çapraz Maç Oranı** | – | – | %48.0 | %48.2 | %0.3 |
| **$\tau = 0$ Terk Oranı** | %3.78 | %2.02 | %3.34 | %3.08 | %8.3 |
| **$\tau = \infty$ Limit Kuyruk $L$** | 0.475 | 0.476 | 0.951 | 0.945 | %0.7 |
| **$\tau = \infty$ Limit Bekleme $W_G$** | 0.792 | – | – | 0.781 | %1.4 |
| **$\tau = \infty$ Limit Bekleme $W_B$** | – | 1.190 | – | 1.190 | %0.0 |
| **$\tau = \infty$ Terk Oranı** | %6.33 | %4.76 | %5.48 | %5.65 | %3.0 |

---

## Maç Tipi Dağılım Matrisi ($\tau = 3.0, T = 30\,000$)

| Maç Tipi | İyi (Good) | Kötü (Bad) |
|---|---|---|
| **İyi (Good)** | %52.6 | %13.7 (Çapraz G-B) |
| **Kötü (Bad)** | · | %33.6 |

---

## Dosya ve Sonuç Organizasyonu

- **Simülasyon Kodu:** [`phase2_2_simulation.py`](phase2_2_simulation.py)
  - Çoklu replikasyon, %95 CI, uç nokta analitik doğrulayıcı, maç matrisi ve $\tau$-sweep içerir.
  - Çalıştırma: `python3 phase2/phase2_2_abandonment/phase2_2_simulation.py --tau 3.0 --plot`
- **İnteraktif Notebook:** [`phase2_2_simulation.ipynb`](phase2_2_simulation.ipynb)
- **Üretilen Sonuç Dosyaları:**
  - `results/tau_sweep.csv`: $\tau \in [0, 50]$ sweep metrik tablosu.
  - `results/figures/tradeoff.png`: Bekleme süresi, terk oranı ve maç kalitesi ödünleşim grafiği.
