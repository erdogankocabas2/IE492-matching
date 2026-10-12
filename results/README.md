# IE492 Simülasyon ve Analiz Sonuçları (Simulation Results)

Bu klasör, tüm aşamalara ait sayısal deney sonuçlarını, parametre tarama (sweep) veri setlerini (CSV) ve üretilen yüksek çözünürlüklü grafikleri içermektedir.

Tüm modeller için etkileşimli web simülasyonları ve canlı dashboard: [`model_reports/index.html`](../model_reports/index.html)

---

## Dizin Yapısı

```
results/
├── README.md
├── m1_chess/                         # Phase 1 / Model 1: Renk Bazlı FCFS Satranç
│   ├── p_sweep.csv                   # p ∈ [0.20, 0.80] için simülasyon ve CTMC metrikleri
│   └── figures/
│       ├── p_sweep.png               # Beyaz/Siyah bekleme süresi ve terk oranı sweep grafiği
│       └── steady_state.png          # Kuyruk izi ve CTMC π_n durağan dağılım doğrulaması
├── m2_good_bad/                      # Phase 2 / Model 2: 2 Sınıflı Beceri Eşleştirmesi (İyi - Kötü)
│   ├── tau_sweep.csv                 # τ ∈ [0, ∞] için bekleme, kuyruk ve terk metrikleri
│   └── figures/
│       ├── tradeoff.png              # Çapraz eşleşme oranı vs bekleme süresi ve terk oranı
│       └── waiting_by_class.png      # τ eşiğine göre sınıf bazlı ortalama bekleme süreleri
└── m3_good_medium_bad/               # Phase 2 / Model 3: 3 Sınıflı Beceri Eşleştirmesi (İyi - Orta - Kötü)
    ├── tau_sweep.csv                 # 3 sınıf için τ ∈ [0, ∞] sweep tablosu
    └── figures/
        ├── tradeoff.png              # Çok sınıflı ligde maç kalitesi vs bekleme ödünleşimi
        └── waiting_by_class.png      # Good, Medium ve Bad sınıflarının bekleme süreleri
```

---

## Veri Seti Açıklamaları (CSV Şemaları)

### 1. `m1_chess/p_sweep.csv`
- `p`: Beyaz renk tercihi olasılığı ($p \in [0.20, 0.80]$).
- `W_w_sim`, `W_b_sim`: Beyaz ve Siyah oyuncular için simülasyon ortalama bekleme süresi.
- `L_w_sim`, `L_b_sim`: Zaman ortalamalı kuyruk uzunlukları.
- `P_ab_w_sim`, `P_ab_b_sim`: Renk bazlı terk oranları.
- `W_w_ctmc`, `W_b_ctmc`, `L_w_ctmc`, `L_b_ctmc`, `P_ab_w_ctmc`, `P_ab_b_ctmc`: Birth-death CTMC analitik modelinden elde edilen teorik değerler.

### 2. `m2_good_bad/tau_sweep.csv`
- `tau`: Çapraz eşleşme bekleme eşiği ($\tau \in [0, 20, \infty]$).
- `cross_match`: Gerçekleşen maçlar içerisinde farklı sınıfların eşleştiği ($G-B$) maçların oranı.
- `W`: Genel ortalama bekleme süresi.
- `W_G`, `W_B`: İyi ve Kötü oyuncuların ortalama bekleme süreleri.
- `P90`: Eşleşen oyuncuların 90. yüzdelik bekleme süresi.
- `L`: Ortalama toplam kuyruk uzunluğu.
- `P_abandon`: Genel terk oranı.
- `L_G`, `L_B`: Sınıf bazlı kuyruk uzunlukları.

### 3. `m3_good_medium_bad/tau_sweep.csv`
- `tau`: Komşu eşiği $\tau$ (uç eşik $2\tau$).
- `cross_match`: Toplam maçlar içinde homojen olmayan ($G-M, M-B, G-B$) maçların oranı.
- `W_G`, `W_M`, `W_B`: Good, Medium ve Bad oyuncularının bekleme süreleri.
- `L_G`, `L_M`, `L_B`: Sınıf bazlı kuyruk uzunlukları.
