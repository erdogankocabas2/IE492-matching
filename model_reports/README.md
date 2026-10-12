# Model Reports

Üç 1v1 eşleştirme modeli için etkileşimli HTML raporları ve bu raporların sonuçlarını üreten Python simülasyon kodu.

```
model_reports/
├── index.html                    # üç raporun listesi
├── common/
│   ├── matching_sim.py           # ortak event-driven simülasyon motoru + analitik çözümler
│   └── skill_report.py           # M2 / M3 için ortak analiz akışı (tablolar, τ sweep, validation)
├── m1_chess/
│   ├── report.html               # M1 · Chess: White–Black
│   └── simulation.py
├── m2_good_bad/
│   ├── report.html               # M2 · Good–Bad
│   └── simulation.py
└── m3_good_medium_bad/
    ├── report.html               # M3 · Good–Medium–Bad
    └── simulation.py
```

## Raporlar

`report.html` dosyalarını tarayıcıda açmak yeterli (yazı tipleri ve Chart.js için internet gerekli). Her raporda:

1. **Model tanımı:** arrivals, policy, abandonment, state, metrics.
2. **§1 Simulation:** canlı animasyon ve altında parametre paneli. Parametre değişince bütün sonuçlar tarayıcıda yeniden hesaplanır.
3. **§2 Results:** KPI kutuları (toplam + sınıf kırılımı), önem sırasına göre grafikler, en sonda detay tabloları.
4. **§3 Analytical model & validation:** M1'de birth–death CTMC; M2/M3'te τ = 0 ve τ = ∞ uçlarının kapalı formu.
5. **§4 Conclusion:** güncel parametrelerle bulgular.

## Simülasyon kodu

Gereksinim: Python 3, numpy (grafikler için matplotlib).

```bash
python3 model_reports/m1_chess/simulation.py                    # rapordaki varsayılanlar
python3 model_reports/m1_chess/simulation.py --p 0.7 --theta 0.1
python3 model_reports/m2_good_bad/simulation.py --tau 5 --no-abandon
python3 model_reports/m3_good_medium_bad/simulation.py --no-far --plot
```

Her script raporun tablolarını terminale yazar, sweep tablosunu CSV olarak kaydeder (`p_sweep.csv` / `tau_sweep.csv`) ve `--plot` ile `figures/` altına grafik üretir. Parametreler için `--help`.

| Script | Çıktılar |
|---|---|
| `m1_chess/simulation.py` | per-colour performance (± 95% CI, CTMC), p sweep (sim vs CTMC), patience trade-off (θ sweep) |
| `m2_good_bad/simulation.py` | per-class performance, τ sweep (cross-match, W, W_G, W_B, P90, L, P(abandon)), match-type matrix, validation at τ = 0 / ∞ |
| `m3_good_medium_bad/simulation.py` | M2 ile aynı, üç sınıf için; `--no-far` ile G–B maçı kapalı |

### Motor

`common/matching_sim.py` üç modeli tek bir threshold matrix `d[i][j]` ile tanımlar: i ve j sınıfından iki oyuncu, en az biri `d[i][j]` kadar beklemişse eşleşebilir.

- M1: `[[∞, 0], [0, ∞]]` (yalnızca karşı renk, FCFS)
- M2: `[[0, τ], [τ, 0]]`
- M3: `[[0, τ, 2τ], [τ, 0, τ], [2τ, τ, 0]]` (G–B kapalıysa ∞)

Arrival'da en küçük eşikten başlanır ve sıra başı (en uzun bekleyen) seçilir; timeout olayında oyuncu yeni açılan sınıfın sıra başıyla eşleşir; sabır ~ Exp(θ_i).

Doğrulama:
- Aynı seed ile M2 sonuçları `phase2_2_simulation.py` ile birebir aynı (P(abandon) %4,83, W eşleşen 0,798, L 0,819, cross-match %13,8).
- M1 simülasyonu CTMC ile ±%2 içinde; M2/M3'te τ = 0 ve τ = ∞ uçları kapalı formla örtüşüyor.
- Rapordaki tarayıcı simülasyonu aynı kuralları uygular; farklı rassal sayı üreteci kullandığı için sayılar istatistiksel olarak aynı, birebir değil.

## Gösterim

W_i ve W: mean waiting time (sınıf i ve toplam; eşleşen + terk eden). L_i ve L: mean queue length, L = Σ L_i. Little's law: L_i = λ_i·W_i. Terimler İngilizce, açıklamalar Türkçe.

## Not

`phase2/phase2_2_abandonment/phase2_2_simulation.py` içindeki `compute_kpis_phase2_2` fonksiyonu `players["status"].isin(...)` çağırıyor; numpy dizilerinde `isin` metodu olmadığı için hata veriyor. `np.isin(players["status"], [MATCHED, ABANDONED])` ile düzeltilebilir.
