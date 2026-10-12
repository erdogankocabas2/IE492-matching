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
└── README.md
```

---

## Phases Overview
- **Phase 1 (Completed):** 1v1 FCFS bilateral queue with color preference (White/Black) and exponential abandonment. CTMC birth-death validation.
- **Phase 2 (Next):** 1v1 with Skill/ELO ratings, expanding matching window (Chess.com / Lichess policies), and abandonment trade-offs.
- **Phase 3:** Multi-player team formation ($n=2$ / 2v2 and $n=3$ / 3v3), combinatorial team partitioning, and multi-dimensional skill vectors.
- **Phase 4:** Policy evaluation, Pareto frontiers (waiting time vs match quality), and sensitivity analysis.
