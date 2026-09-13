# Goldman Sachs India Hackathon 2026 — Solution Showcase

Personal solution repository for the **Goldman Sachs India Hackathon 2026 (Computer Science Track)** conducted on HackerRank.

This repository is intended as a **portfolio and technical showcase** of the solutions developed for the three CS-track problem statements. It contains the corresponding problem statements, the submitted implementations, sample inputs/outputs, algorithmic reasoning, complexity analysis, and design trade-offs used in the solutions.

> **Finalist Achievement**
>
> Selected as a **finalist in the Goldman Sachs India Hackathon 2026 (Computer Science Track)**, ranking in the **top 0.3% among 16,000+ participants nationwide**. Advanced to the **in-person finals at the Goldman Sachs Bengaluru campus**, where I presented my solution architecture, design decisions, and technical implementation to senior Goldman Sachs engineers.

## Hackathon

The Goldman Sachs India Hackathon is a competitive coding challenge covering real-world technical and quantitative problems. The 2026 Computer Science track consisted of three problems that tested deterministic parsing, recursive type inference, combinatorial optimization, simulation, and multi-agent routing under dynamic constraints.

**Official:** [Goldman Sachs India Hackathon 2026](https://www.goldmansachs.com/careers/students/programs-and-internships/india/hackathon)  
**HackerRank CS Contest:** [Goldman Sachs India Hackathon 2026 — CS](https://www.hackerrank.com/goldman-sachs-india-hackathon-2026-cs)

## Solutions

| # | Problem | Difficulty | Core Concepts | Solution |
|---|---|---|---|---|
| 01 | **JSON → TypeScript Type Generator** | Medium | Recursive parsing, type inference, object merging, deterministic formatting | [View solution](./01-json-to-typescript/README.md) |
| 02 | **Group Trip Planner** | Medium | Constraint optimization, meet-in-the-middle, bitmasks, replanning, tie-breaking | [View solution](./02-group-trip-planner/README.md) |
| 03 | **Multi-Agent Drone Routing in a Temporal Urban Grid** | Advanced | Computational geometry, temporal constraints, battery simulation, charging, multi-agent scheduling | [View solution](./03-multi-agent-drone-routing/README.md) |

Each solution directory follows the same documentation pattern: a concise problem overview and challenge link, the implementation link, then the algorithm, design decisions, complexity analysis, and supporting examples.

## Repository Structure

```text
GSIH_2026_Solutions/
├── README.md
├── .gitignore
├── 01-json-to-typescript/
│   ├── README.md
│   ├── problem.md
│   ├── solution.py
│   └── examples/
│       ├── input.txt
│       └── output.txt
├── 02-group-trip-planner/
│   ├── README.md
│   ├── problem.md
│   ├── solution.py
│   └── examples/
│       ├── input.txt
│       └── output.txt
└── 03-multi-agent-drone-routing/
    ├── README.md
    ├── problem.md
    ├── solution.py
    └── examples/
        ├── input.json
        └── output.json
```

## Running the Solutions

All implementations use **Python 3** and the Python standard library only.

### 01 — JSON → TypeScript

```bash
python3 01-json-to-typescript/solution.py < 01-json-to-typescript/examples/input.txt
```

### 02 — Group Trip Planner

```bash
python3 02-group-trip-planner/solution.py < 02-group-trip-planner/examples/input.txt
```

### 03 — Multi-Agent Drone Routing

```bash
python3 03-multi-agent-drone-routing/solution.py < 03-multi-agent-drone-routing/examples/input.json
```

## What This Repository Showcases

The goal of this repository is not only to preserve the code submissions, but to make the reasoning behind them easy to inspect.

**Deterministic problem solving** — strict ordering, tie-breaking, reproducible output, and stable naming decisions.

**Algorithmic optimization** — subset optimization and meet-in-the-middle techniques for constrained planning.

**Simulation and systems reasoning** — time-dependent obstacles, battery and payload constraints, resource contention, and multi-agent scheduling.

**Engineering clarity** — each solution separates the problem statement, implementation, examples, algorithmic explanation, and complexity discussion.

## Disclaimer

The supplied dataset and problem statement remain subject to the HackerRank challenge terms. The implementation in this repository is provided for portfolio and educational use.

## Author

**Adhvaith G V**
