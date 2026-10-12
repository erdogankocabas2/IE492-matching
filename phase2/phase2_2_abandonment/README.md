# Phase 2.2: Skill-Based Matchmaking With Heterogeneous Abandonment (Terkli Model)

Bu aşamada 1v1 beceri (skill) temelli eşleştirmeye oyuncuların sabır süreleri (terk etme / reneging) eklenmiştir. Gerçekçi bir senaryo olarak **İyi (Good)** ve **Kötü (Bad)** oyuncuların sabır seviyeleri birbirinden farklıdır ($\theta_G \neq \theta_B$).

## Model Dinamikleri

- **Geliş Süreci:** Oyuncular Poisson($\lambda$) hızıyla gelir.
- **Beceri Dağılımı:**
  - $p$ olasılıkla: **İyi (Good)**
  - $1-p$ olasılıkla: **Kötü (Bad)**
- **Heterojen Sabır Süresi:**
  - İyi oyuncu sabrı: $S_G \sim \text{Exp}(\theta_G)$ (örn. $\theta_G = 0.08 \implies$ ortalama sabır 12.5 birim zaman).
  - Kötü oyuncu sabrı: $S_B \sim \text{Exp}(\theta_B)$ (örn. $\theta_B = 0.04 \implies$ ortalama sabır 25.0 birim zaman).

### $\tau$ Eşiği ve Terk Etme Etkileşimi
1. **Sabır $< \tau$:** Oyuncu $\tau$ süresi dolmadan sabırsızlanırsa sistemden terk eder (`ABANDONED`). Çapraz eşleşme fırsatı bulamaz.
2. **Sabır $\ge \tau$:** Oyuncu $\tau$ süresine ulaştığında "esnek" (`FLEXIBLE`) moda geçer ve karşı sınıfla eşleşebilir hale gelir. Eğer yine de karşı taraftan uygun eşleşme çıkmazsa, sabrı dolduğu anda sistemden terk eder.

### Temel Trade-off ve Politika Kararı
- Eğer $\tau$ çok yüksek tutulursa: Maçlar homojen kalır fakat azınlık grubun terk oranı fırlar (oyuncular cross-match göremeden sistemi terk eder).
- Eğer $\tau$ dengeli tutulursa: Cross-match sayesinde oyuncular terk etmeden oyuna sokulur; terk oranı belirgin şekilde düşer, ancak maç kalitesi (% G-B oranı) dengelenmelidir.

## KPI'lar
- **Eşleşme ve Terk Oranları:** Sınıf bazında ve genel terk yüzdesi.
- **Bekleme Süresi Dağılımı:** Eşleşenlerin ve tüm oyuncuların ortalama/medyan/P90 süreleri.
- **Kuyruk Uzunlukları:** Zaman ortalamalı $L_G, L_B$ ve $L_\text{toplam}$.
- **Çapraz Eşleşme Oranı:** Gerçekleşen maçlar içinde $G-B$ maçlarının yüzdesi.
