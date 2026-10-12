# Phase 1: Renk Bazlı FCFS Satranç Eşleştirmesi (Terkli Model)

Bu aşamada ELO / skill puanı olmaksızın, renk tercihi (Beyaz / Siyah) ve sabır süresi (terk / reneging) içeren temel 1v1 eşleştirme kuyruk sistemi modellenmiştir.

## Model Özeti
- **Geliş Süreci:** Oyuncular Poisson($\lambda$) süreciyle sisteme dahil olur.
- **Renk Dağılımı:** Her oyuncu $p$ olasılıkla **Beyaz**, $1-p$ olasılıkla **Siyah** renk ister.
- **Eşleştirme Kuralı (FCFS):** Sıranın başındaki Beyaz ile sıranın başındaki Siyah anında eşleşir. Bu nedenle kuyrukta aynı anda yalnızca tek bir renk birikebilir ($X(t) = \#\text{Beyaz} - \#\text{Siyah}$).
- **Terk (Abandonment / Reneging):** Bekleyen her oyuncunun sabrı $\text{Exp}(\theta)$ dağılımına sahiptir. Sabrı biten oyuncu sistemden ayrılır.

## Analitik Model (CTMC)
$X(t) = \#\text{beyaz} - \#\text{siyah}$ tek boyutlu bir Doğum-Ölüm Süreci (Birth-Death Process / CTMC) olarak modellenmiştir:
- $n > 0$ iken ($n$ beyaz bekliyor): $n \to n+1$ geçiş hızı $p\lambda$, $n \to n-1$ geçiş hızı $(1-p)\lambda + n\theta$.
- $n < 0$ iken ($|n|$ siyah bekliyor): simetrik yapı.

### Anlık ve Zaman Ortalamalı Toplam Kuyruk
FCFS eşleşme kuralı gereğince sistemde aynı anda iki renkten de oyuncu bulunamaz ($N_\text{beyaz}(t) > 0 \implies N_\text{siyah}(t) = 0$). Bu nedenle herhangi bir $t$ anında sistemde sırada bekleyen **toplam oyuncu sayısı (anlık kuyruk)**:
$$Q(t) = N_\text{beyaz}(t) + N_\text{siyah}(t) = |N_\text{beyaz}(t) - N_\text{siyah}(t)| = |X(t)|$$
Zaman ortalamalı toplam kuyruk uzunluğu ise renk bazlı kuyrukların toplamına eşittir:
$$L_\text{toplam} = E[|X|] = L_\text{beyaz} + L_\text{siyah}$$

Durağan dağılımdan Little Yasası yardımıyla:
$$E[W_\text{beyaz}] = \frac{L_\text{beyaz}}{p\lambda}, \qquad P(\text{beyaz terk}) = \frac{\theta L_\text{beyaz}}{p\lambda}$$

## Dosyalar
- `stage1_chess_fcfs.py`: Ayrık olay simülasyonu, CTMC analitik çözücü ve duyarlılık analizi kodu.
- `stage1_chess_fcfs.ipynb`: Grafik görselleştirmeleri ve interaktif analizler içeren Jupyter Notebook.
