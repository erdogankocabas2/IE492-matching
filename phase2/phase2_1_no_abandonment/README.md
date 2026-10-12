# Phase 2.1: Skill-Based Matchmaking Without Abandonment (Terk Yok)

Bu aşamada 1v1 maçlar için beceri (skill) temelli eşleştirme mekanizması modellenmiştir. Oyuncular **İyi (Good)** ve **Kötü (Bad)** olmak üzere iki gruba ayrılır. Terk etme (abandonment) henüz yoktur ($\theta = 0$).

## Model Dinamikleri

- **Geliş Süreci:** Oyuncular Poisson($\lambda$) hızıyla gelir.
- **Beceri Dağılımı:**
  - $p$ olasılıkla: **İyi (Good)**
  - $1-p$ olasılıkla: **Kötü (Bad)**
- **Renk Kısıtı:** Yoktur (1v1 skill-based).

### Eşleşme Mantığı ve $\tau$ Eşiği
1. **Homojen Öncelik:** Yeni gelen oyuncu öncelikle kendi sınıfından bekleyen varsa onunla anında eşleşir ($G-G$ veya $B-B$).
2. **Eşikli Çapraz Eşleşme ($\tau$):** Kendi sınıfında kimse yoksa, karşı sınıfta bekleme süresi $\ge \tau$ olan ("esnek") bir oyuncu varsa, onunla anında çapraz eşleşme ($G-B$) gerçekleşir.
3. **Olay Tabanlı Zaman Aşımı (Timeout Event):** Kuyrukta bekleyen bir oyuncunun bekleme süresi $\tau$ eşiğine ulaştığı anda, karşı sınıfta bekleyen biri varsa **anında** çapraz eşleşme yapılır. Karşıda kimse yoksa oyuncu esnek moda geçer ve karşı sınıftan gelecek ilk oyuncuyla eşleşir.

### Temel Trade-off (Ödünleşim)
- $\tau \to 0$: Oyuncular hiç beklemeden karşı sınıfla eşleşir. Bekleme süreleri minimumdur ancak maçların kalitesi düşüktür (çapraz maç oranı yüksek).
- $\tau \to \infty$: Oyuncular sadece kendi sınıflarıyla eşleşir (katı ayrım). Maç kalitesi %100 homojendir ancak azınlık olan sınıf daha uzun süre bekler ve kuyruklar büyür.

## KPI'lar
- **Sınıf Bazında Bekleme Süresi:** Ortalama, medyan, P90 bekleme süreleri ($W_G, W_B$).
- **Kuyruk Uzunlukları:** Zaman ortalamalı $L_G, L_B$ ve toplam kuyruk $L_\text{toplam}$.
- **Çapraz Eşleşme Oranı:** Toplam eşleşenler içinde $G-B$ maçlarının oranı (%).
