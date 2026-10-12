"""
Phase 2.3: Multi-Tier Skill-based Matchmaking (Good - Medium - Bad)
- Oyuncular: Poisson(λ) varışları (varsayılan λ = 1.0).
- 3 Beceri Sınıfı: Good (p_G = 0.20), Medium (p_M = 0.50), Bad (p_B = 0.30).
- Mesafe / Eşik Matrisi d[i][j]:
    * Aynı sınıf: 0 (anında homojen eşleşme)
    * Komşu sınıflar (G-M, M-B): τ eşiği
    * Uzak sınıflar (G-B): 2τ eşiği (--no-far ile ∞ yapılarak G-B kapatılabilir)
- Heterojen Terk Oranları: θ_G = 0.08, θ_M = 0.06, θ_B = 0.04
- Analitik Uç Nokta Doğrulaması:
    * τ = 0: 3 sınıflı tek havuz (pool_one)
    * τ = ∞: 3 bağımsız sınıf (separate)
"""

import argparse
import csv
import math
import os
import sys

# Ortak model modülünü içe aktar
HERE = os.path.dirname(os.path.abspath(__file__))
COMMON_DIR = os.path.join(HERE, "..", "..", "model_reports", "common")
if os.path.exists(COMMON_DIR):
    sys.path.insert(0, COMMON_DIR)
    import matching_sim as M
    import skill_report
else:
    raise ImportError("model_reports/common modülü bulunamadı.")


def run_phase2_3_experiments(lam=1.0, pg=0.2, pb=0.3, tau=3.0, far=True,
                             theta_g=0.08, theta_m=0.06, theta_b=0.04,
                             abandon=True, T=20_000, n_reps=5, plot=False, out_dir="results"):
    os.makedirs(out_dir, exist_ok=True)
    pm = 1.0 - pg - pb
    probs = [pg, pm, pb]
    names = ["Good", "Medium", "Bad"]
    letters = ["G", "M", "B"]
    thetas = [theta_g, theta_m, theta_b] if abandon else [0.0, 0.0, 0.0]

    def build_d(t):
        f = 2.0 * t if far else M.INF
        return [[0.0, t, f], [t, 0.0, t], [f, t, 0.0]]

    extra_desc = f", G-B {'2τ' if far else 'kapalı (∞)'}"
    skill_report.analyse(
        title="Phase 2.3 · Multi-Tier (Good–Medium–Bad)",
        names=names,
        letters=letters,
        lam=lam,
        probs=probs,
        build_d=build_d,
        theta=thetas,
        tau=tau,
        abandon=abandon,
        pool_at_zero=far,
        out_dir=out_dir,
        T=T,
        n_reps=n_reps,
        plot=plot,
        extra=extra_desc
    )


def main():
    ap = argparse.ArgumentParser(description="Phase 2.3: 3-Tier Skill-based Matchmaking")
    ap.add_argument("--lam", type=float, default=1.0, help="Varış hızı λ")
    ap.add_argument("--pg", type=float, default=0.2, help="Good oranı p_G")
    ap.add_argument("--pb", type=float, default=0.3, help="Bad oranı p_B (p_M = 1 - p_G - p_B)")
    ap.add_argument("--tau", type=float, default=3.0, help="Komşu eşiği τ")
    ap.add_argument("--no-far", action="store_true", help="G-B maçını tamamen kapat (eşik = ∞)")
    ap.add_argument("--theta-g", type=float, default=0.08)
    ap.add_argument("--theta-m", type=float, default=0.06)
    ap.add_argument("--theta-b", type=float, default=0.04)
    ap.add_argument("--no-abandon", action="store_true", help="Terk mekanizmasını kapat")
    ap.add_argument("--T", type=float, default=20_000)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--plot", action="store_true", default=True)
    ap.add_argument("--out-dir", type=str,
                    default=os.path.join(HERE, "results"),
                    help="Çıktı klasörü")
    a = ap.parse_args()

    if a.pg + a.pb >= 1.0:
        ap.error("p_G + p_B < 1 olmalıdır")

    run_phase2_3_experiments(
        lam=a.lam, pg=a.pg, pb=a.pb, tau=a.tau, far=not a.no_far,
        theta_g=a.theta_g, theta_m=a.theta_m, theta_b=a.theta_b,
        abandon=not a.no_abandon, T=a.T, n_reps=a.reps, plot=a.plot, out_dir=a.out_dir
    )


if __name__ == "__main__":
    main()
