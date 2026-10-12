# Phase 2.3: Multi-Tier Skill-Based Matchmaking (Good – Medium – Bad)

Bu aşamada 2 sınıflı model (İyi - Kötü), modern rekabetçi oyunlardaki kademeli eşleştirme yapılarını temsil eden **3 sınıflı (Good - Medium - Bad)** hiyerarşik sisteme genişletilmiştir.

Modelin etkileşimli tarayıcı raporu: [`model_reports/m3_good_medium_bad/report.html`](../../model_reports/m3_good_medium_bad/report.html)

---

## Model Dinamikleri

- **Geliş Süreci:** Oyuncular Poisson($\lambda$) hızıyla gelir ($\lambda = 1.0$).
- **Beceri Dağılımı:**
  - $p_G = 0.20$ (İyi / Good)
  - $p_M = 0.50$ (Orta / Medium — çoğunluk köprü sınıf)
  - $p_B = 0.30$ (Kötü / Bad)
- **Heterojen Sabır Dağılımı:**
  - $\theta_G = 0.08 \implies E[S_G] = 12.5$ birim zaman
  - $\theta_M = 0.06 \implies E[S_M] = 16.7$ birim zaman
  - $\theta_B = 0.04 \implies E[S_B] = 25.0$ birim zaman

### Eşik Matrisi ($d_{ij}$) ve Öncelik Hiyerarşisi
Oyuncular bekleme sürelerine göre aşamalı olarak daha uzak beceri sınıflarıyla eşleşebilir:
$$d = \begin{pmatrix} 0 & \tau & 2\tau \\ \tau & 0 & \tau \\ 2\tau & \tau & 0 \end{pmatrix}$$
- **Aynı Sınıf ($d=0$):** $G-G, M-M, B-B$ anında homojen eşleşir.
- **Komşu Sınıf ($d=\tau$):** Bekleme süresi $\ge \tau$ olunca $G-M$ ve $M-B$ maçları açılır.
- **Uç Sınıflar ($d=2\tau$):** Bekleme süresi $\ge 2\tau$ olunca en son çare olarak $G-B$ maçına izin verilir (`--no-far` ile $d=\infty$ yapılarak tamamen kapatılabilir).

---

## Önemli Bulgular

1. **Medium Sınıfının Tampon Rolü:** Çoğunluk olan Medium sınıfı ($p_M = 0.50$), Good ve Bad sınıfları arasında bir köprü görevi görerek genel bekleme süresini ($W_M = 0.738$) ve terk oranını düşürür.
2. **Bedeli Azınlık Öder:** En küçük sınıf olan Good ($p_G = 0.20$), kendi sınıfından oyuncu bulmakta zorlandığı için en yüksek terk oranına ($\%12.1$) ve bekleme süresine ($W_G = 1.534$) maruz kalır.
3. **Uç Nokta Doğrulaması:** $\tau = 0$ (tek havuz) ve $\tau = \infty$ (ayrık sınıflar) analitik Markov zincirleri ile bağıl hata $<\%1$ düzeyindedir.

---

## Dosyalar

- **Simülasyon Kodu:** [`phase2_3_simulation.py`](phase2_3_simulation.py)
  - Komut: `python3 phase2/phase2_3_multi_tier/phase2_3_simulation.py --tau 3.0 --plot`
- **Üretilen Sonuç Dosyaları:**
  - `results/tau_sweep.csv`: $\tau \in [0, \infty]$ metrik tablosu.
  - `results/figures/tradeoff.png`: Bekleme süresi ve çapraz eşleşme ödünleşim grafiği.
  - `results/figures/waiting_by_class.png`: Sınıf bazında bekleme süreleri.
