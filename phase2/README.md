# Phase 2: 1v1 Beceri Bazlı Eşleştirme (Skill-Based Matchmaking)

Bu aşamada 1v1 oyunlarda beceri (skill/ELO) farklarını yönetmek için eşik tabanlı dinamik havuz genişletme mekanizması (**Flexible / Expanding Pool Matching Policy**) geliştirilmiş ve analiz edilmiştir.

Etkileşimli web simülasyonları ve canlı deney raporları:
- 2 Sınıflı Model (İyi – Kötü): [`model_reports/m2_good_bad/report.html`](../model_reports/m2_good_bad/report.html)
- 3 Sınıflı Model (İyi – Orta – Kötü): [`model_reports/m3_good_medium_bad/report.html`](../model_reports/m3_good_medium_bad/report.html)

---

## Alt Aşamalar

```
phase2/
├── phase2_1_no_abandonment/   # Aşama 2.1: Terk yok (θ = 0), τ eşiği ile gecikme/kalite ödünleşimi
├── phase2_2_abandonment/      # Aşama 2.2: Heterojen terk (θ_G ≠ θ_B), kullanıcı kaybı ve çapraz maçlar
├── phase2_3_multi_tier/       # Aşama 2.3: Çok sınıflı yapı (Good–Medium–Bad), mesafe matrisi d_ij
└── README.md
```

| Alt Aşama | Sınıflar | Terk Oranları | Eşik Mekanizması | Odak Noktası |
|---|---|---|---|---|
| **Phase 2.1** | Good, Bad | Yok ($\theta = 0$) | $\tau$ cross-match eşiği | Bekleme süresi ($W$) ile maç kalitesi ($\text{cross-match}$) arasındaki temel ödünleşim. |
| **Phase 2.2** | Good, Bad | Heterojen ($\theta_G=0.08, \theta_B=0.04$) | $\tau$ cross-match eşiği | Çapraz eşleşmenin azınlık gruptaki terk oranını önleme gücü. |
| **Phase 2.3** | Good, Medium, Bad | Heterojen ($\theta_G=0.08, \theta_M=0.06, \theta_B=0.04$) | Komşu $\tau$, Uzak $2\tau$ | Çok sınıflı liglerde Medium sınıfının tampon görevi ve uç maçların ($G-B$) etkisi. |

---

## Temel Analitik Sonuçlar ve Uç Nokta Doğrulaması

Her model, $\tau = 0$ (tek havuz / single pool) ve $\tau = \infty$ (ayrık sınıflar / strict separation) uç noktalarında kapalı form Markov Zinciri çözümleri ile doğrulanmıştır:

1. **Tek Havuz Limiti ($\tau = 0$):**
   - Bekleme süreleri asgari düzeye iner ($W \to 0.48 - 0.50$).
   - Kuyrukta ortalama $\le 1$ oyuncu bulunur ($L \to 0.48 - 0.50$).
   - Ancak maçların $\%48 - \%62$'si farklı sınıflar arasında gerçekleşir (düşük maç kalitesi).
2. **Katı Ayrım Limiti ($\tau = \infty$):**
   - Maçlar $\%100$ homojendir (çapraz maç $\%0$).
   - Ancak özellikle azınlık sınıflar için kuyruk ve bekleme süresi sert şekilde yükselir ($W_B \to 1.19 - 1.25$, $W_G \to 1.5 - 2.0$).
   - Terk mekanizması açıkken oyuncu kaybı tavan yapar.

---

## Sonuç Dosyaları ve Organizasyon

Tüm simülasyon çıktıları ve grafikler kendi klasörlerinde ve merkezi `results/` altında toplanmıştır:
- `phase2_1_no_abandonment/results/tau_sweep.csv` & `figures/tradeoff.png`
- `phase2_2_abandonment/results/tau_sweep.csv` & `figures/tradeoff.png`
- `phase2_3_multi_tier/results/tau_sweep.csv` & `figures/tradeoff.png`
