# IE492 - A Stochastic Matching Problem

This repository contains the simulation models, analytical queueing formulations, numerical experiments, and interactive reports for the **IE492 Senior Design Project** (Bogazici University, Department of Industrial Engineering).

## Project Team
- Bünyamin Selçuk İmre
- Dilara Belibağlı
- Edanur Bozkurt
- Erdoğan Kocabaş
- **Supervisor:** Prof. Aybek Korugan

---

## 🚀 Interactive Model Reports

Interactive web applications and simulation dashboards are located in [`model_reports/`](model_reports/):
- **Dashboard:** [`model_reports/index.html`](model_reports/index.html)
- **Model 1 (Chess · White vs Black):** [`model_reports/m1_chess/report.html`](model_reports/m1_chess/report.html)
- **Model 2 (Skill-based · Good vs Bad):** [`model_reports/m2_good_bad/report.html`](model_reports/m2_good_bad/report.html)
- **Model 3 (Multi-tier · Good–Medium–Bad):** [`model_reports/m3_good_medium_bad/report.html`](model_reports/m3_good_medium_bad/report.html)

---

## Repository Structure

```
├── model_reports/                # Interactive HTML reports & common simulation engine
│   ├── index.html                # Unified dashboard linking all models
│   ├── common/                   # Event-driven engine (matching_sim.py, skill_report.py)
│   ├── m1_chess/                 # Model 1 report & CLI simulation script
│   ├── m2_good_bad/              # Model 2 report & CLI simulation script
│   └── m3_good_medium_bad/       # Model 3 report & CLI simulation script
├── results/                      # Centralized numerical datasets (CSV) and high-res plots
│   ├── m1_chess/                 # p-sweep datasets & steady-state plots
│   ├── m2_good_bad/              # tau-sweep datasets & trade-off curves
│   └── m3_good_medium_bad/       # 3-tier tau-sweep datasets & waiting time plots
├── phase1/                       # Phase 1: 1v1 Chess FCFS with abandonment
│   ├── stage1_chess_fcfs.py      # Simulation script (replications, 95% CI, CTMC)
│   ├── stage1_chess_fcfs.ipynb   # Interactive analysis & visualizations
│   ├── results/                  # Local sweep CSV and figures
│   └── README.md                 # Mathematical formulation & CTMC validation
├── phase2/                       # Phase 2: 1v1 Skill-based Matchmaking
│   ├── phase2_1_no_abandonment/  # Phase 2.1: Skill-based with tau threshold, θ = 0
│   ├── phase2_2_abandonment/     # Phase 2.2: Skill-based with heterogeneous abandonment
│   ├── phase2_3_multi_tier/      # Phase 2.3: 3-tier expanding pool (Good–Medium–Bad)
│   └── README.md                 # Summary of Phase 2 models & trade-off findings
├── docs/
│   └── project_proposal.md       # Project proposal and literature review
└── README.md
```

---

## Phases Overview

- **Phase 1:** 1v1 FCFS bilateral queue with color preference (White/Black) and exponential abandonment. Validated against a 1D birth-death Continuous-Time Markov Chain (CTMC) within $\pm 2\%$ error.
- **Phase 2:** 1v1 Skill-based matching with homogeneous priority and expanding threshold ($\tau$):
  - **Phase 2.1 (No Abandonment):** Zero-abandonment ($\theta = 0$), quantifying the trade-off between waiting delay ($W$) and match quality ($\text{cross-match ratio}$). Validated at closed-form analytical limits ($\tau = 0$ single pool and $\tau = \infty$ strict separation).
  - **Phase 2.2 (Heterogeneous Abandonment):** Asymmetric abandonment ($\theta_G \neq \theta_B$), analyzing the power of cross-matching to prevent churn in minority tiers.
  - **Phase 2.3 (Multi-Tier Expansion):** 3-tier hierarchy (Good–Medium–Bad) with neighbor threshold $\tau$ and distant threshold $2\tau$, highlighting the buffering role of the Medium class.
- **Phase 3 (Next):** Multi-player team formation ($n=2$ / 2v2 and $n=3$ / 3v3), combinatorial team partitioning, and multi-dimensional skill vectors.
- **Phase 4:** Policy evaluation, Pareto frontiers (waiting time vs match quality), and sensitivity analysis.
