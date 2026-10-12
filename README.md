# IE492 - A Stochastic Matching Problem

This repository contains the simulation models, analytical queueing formulations, and matchmaking policy evaluations for the **IE492 Senior Design Project** (Bogazici University, Department of Industrial Engineering).

## Project Team
- Bünyamin Selçuk İmre
- Dilara Belibağlı
- Edanur Bozkurt
- Erdoğan Kocabaş
- **Supervisor:** Prof. Aybek Korugan

---

## Repository Structure
```
├── docs/
│   └── project_proposal.md       # Full project proposal and literature review
├── phase1/                       # Phase 1: 1v1 Chess FCFS with abandonment (No ELO)
│   ├── stage1_chess_fcfs.py      # Discrete-event simulation & CTMC analytical model
│   ├── stage1_chess_fcfs.ipynb   # Interactive analysis & visualizations
│   └── README.md                 # Mathematical formulation and KPI descriptions
├── phase2/                       # Phase 2: 1v1 Skill-based Matchmaking (Good vs Bad)
│   ├── phase2_1_no_abandonment/  # Phase 2.1: Skill-based with tau threshold, no abandonment
│   │   ├── phase2_1_simulation.py
│   │   ├── phase2_1_simulation.ipynb
│   │   └── README.md
│   └── phase2_2_abandonment/     # Phase 2.2: Skill-based with heterogeneous abandonment
│       ├── phase2_2_simulation.py
│       ├── phase2_2_simulation.ipynb
│       └── README.md
└── README.md
```

---

## Phases Overview
- **Phase 1 (Completed):** 1v1 FCFS bilateral queue with color preference (White/Black) and exponential abandonment. CTMC birth-death validation.
- **Phase 2 (Completed):** 1v1 Skill-based matching (Good vs Bad) with homogeneous priority and cross-match tolerance window ($\tau$).
  - **Phase 2.1:** Zero-abandonment ($\theta = 0$), trade-off between delay and match quality (cross-match ratio).
  - **Phase 2.2:** Heterogeneous abandonment ($\theta_G \neq \theta_B$), analyzing the power of cross-matching to prevent user churn.
- **Phase 3 (Next):** Multi-player team formation ($n=2$ / 2v2 and $n=3$ / 3v3), combinatorial team partitioning, and multi-dimensional skill vectors.
- **Phase 4:** Policy evaluation, Pareto frontiers (waiting time vs match quality), and sensitivity analysis.
