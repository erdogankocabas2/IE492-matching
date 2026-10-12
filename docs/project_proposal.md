# IE492 Project Proposal: A Stochastic Matching Problem

**Supervisor:** Aybek Korugan  
**Date:** 05.10.2026  

**Prepared by:**
- Bünyamin Selçuk İmre (2021402180)
- Dilara Belibağlı (2021402066)
- Edanur Bozkurt (2021402009)
- Erdoğan Kocabaş (2021402183)

---

## 1. Problem Description
Online multiplayer games rely on matchmaking systems that assign players who are searching for a game at the same time into competitive sessions. The quality of a matchmaking system is mainly determined by two conflicting objectives: how long players wait before a game starts and how balanced the resulting match is. Using strict matching criteria may improve match quality, but it can significantly increase waiting times, especially when the number of suitable players in the system is limited. On the other hand, relaxing the matching criteria may reduce waiting times at the cost of creating less balanced games.

This project considers a stochastic matchmaking system in which players arrive randomly over time. Players may arrive individually or as groups, which may not be allowed to separate. Each game consists of two teams of equal size $n$, so every completed match removes $2n$ players from the waiting pool. Each player is characterized by a skill vector containing $k$ skill-related attributes, such as overall rating, experience, offensive ability, defensive ability, or other game-specific performance measures. The matchmaking system may use all or only a selected subset $S \subseteq \{1, \dots, k\}$ of these characteristics when evaluating potential matches.

For every matching decision, the system must determine:
1. Which skill characteristics should be taken into account,
2. When a match should be formed from the current pool of waiting players,
3. Which $2n$ players should be included in that match,
4. How those players should be divided into two teams.

The system therefore has three main performance objectives:
- Minimizing player waiting time,
- Minimizing skill differences among players assigned to the same team (within-team balance),
- Minimizing skill differences between the two opposing teams (between-team balance).

A fundamental trade-off arises between these objectives. Using a larger number of skill characteristics or imposing stricter similarity requirements may produce more homogeneous and balanced matches, but it also reduces the effective pool of compatible players and may increase waiting times. Similarly, waiting longer before forming a match may allow the system to find a better combination of players, whereas matching immediately reduces delay but may produce lower-quality matches.

The problem can therefore be formulated as a stochastic multi-objective optimization problem. The aim of the project is to develop and evaluate matchmaking policies that balance expected waiting time and match quality under different system conditions.

---

## 2. Proposed Approach
- **Arrival Process:** Player arrivals will initially be modeled as a Poisson process with rate $\lambda$. The analysis will focus particularly on how system performance changes with player arrival rate $\lambda$, team size $n$, the number and subset of skill characteristics used, and the strictness of the matching policy.
- **Model Progression:** The model will first be studied for small team sizes, particularly $n=2$ and $n=3$. Analytical approaches may be possible for simplified or discretized cases, while larger instances will require discrete-event simulation.
- **Team Formation & Combinatorial Optimization:** Team formation introduces a combinatorial optimization problem, since the selected $2n$ players must be divided into two balanced teams. Different policies for selecting players from the waiting pool and assigning them to teams will be developed and compared based on their effects on waiting time, within-team skill differences, and between-team skill differences.
- **Data & Calibration:** Since detailed real-world matchmaking data is rarely publicly available, synthetic arrival and skill distributions will initially be used and, where possible, calibrated using publicly available game data.

---

## 3. Literature Review
- **Véron, Marin, and Monnet (2014):** Analyzed more than 28 million League of Legends sessions, reporting average matchmaking time close to 90 seconds (target was 30s). 7.9% of ranked requests took $>5$ minutes, and high-rank queue times reached 45 minutes due to player scarcity at the distribution tails. Relaxing rating difference increased abandonment/leavers. Adding games played as an extra criterion increased average wait by ~50%.
- **Chess Platforms (Chess.com & Lichess):**
  - *Chess.com (2025):* Applies an initially narrow rating range and progressively widens acceptable range over time. High-rated matchmaking times increase accordingly.
  - *Lichess:* Batch/periodic matching using weighted graph matching where edge weights reflect rating distance and accumulated wait time.
- **Xu, Yu, and Wu (2021):** Model online matchmaking as a stochastic queueing problem for 2v2 games using continuous-time Markov chains (CTMCs). Shows that side-choice / queuing rules divide player pools and significantly affect delays, while choice-free flexible players improve overall throughput. However, assumes homogeneous player skills.

---

## 4. References
1. Chess.com. (2025). *How does matchmaking work in Live Chess?* Chess.com Help Center.
2. Lichess. (n.d.). *lila: Lichess source code, pool module.* GitHub.
3. Véron, M., Marin, O., & Monnet, S. (2014). *Matchmaking in multi-player on-line games: Studying user traces to improve the user experience.* Proceedings of NOSSDAV ’14, ACM.
4. Xu, M., Yu, Y., & Wu, C. (2021). *Rule designs for optimal online game matchmaking.* Proceedings of the 40th Chinese Control Conference, 1055–1062.
