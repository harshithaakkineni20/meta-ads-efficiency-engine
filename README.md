# Meta ads efficiency engine

A simulated decision engine for improving Meta ads efficiency across a high-volume account. The system recommends which ads to stop, trim, scale, hold, or use as the basis for new creative briefs.

This repo was built for the AppliedAI Studio AI Builder assignment.

## What this project does

The assignment describes a customer running roughly 10,000 Facebook and Instagram campaigns per month and asks for a system to improve ROAS. Because no real account dataset was provided, this repo includes a simulator that creates Meta-style ad data and hidden ground truth.

The engine only sees observed attributed performance, similar to what an operator would see from Meta. The evaluator sees hidden future and marginal ROAS, which makes it possible to test whether recommendations are directionally right.

## Core idea

Do not sort by historical ROAS alone. Historical ROAS can be noisy, delayed, inflated by retargeting, or distorted by promotions. The engine estimates whether the next rupee of spend is likely to return above target, then applies maturity, attribution, fatigue, inventory, learning-phase, and approval guardrails.

AI is used for creative interpretation and explanation. AI is not used to decide budget movement.

## Repo structure

```text
meta-ads-efficiency-engine/
├── README.md
├── requirements.txt
├── configs/
│   └── thresholds.yaml
├── docs/
│   ├── Meta_Ads_Efficiency_Engine_Report.pdf
│   ├── design_notes.md
│   ├── report_source.html
│   └── test_cases.md
├── assets/
│   └── diagrams/
│       ├── algorithm_flow.png
│       ├── architecture.png
│       ├── decision_flow.png
│       ├── failover.png
│       └── process_overview.png
├── outputs/
│   ├── sample_output.md
│   ├── sim_examples.csv
│   └── sim_summary.csv
├── src/
│   ├── engine.py
│   ├── llm_eval.py
│   ├── render_digest.py
│   └── simulate_meta_ads_demo.py
└── tests/
    └── test_engine_cases.py
```

## How to run

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/simulate_meta_ads_demo.py
python src/llm_eval.py
python tests/test_engine_cases.py
```

The simulator writes outputs to `outputs/sim_summary.csv`, `outputs/sim_examples.csv`, and `outputs/sample_output.md`.

## Current simulator readout

| Metric | Naive ROAS rule | Guarded engine | Readout |
|---|---:|---:|---|
| False pause rate | 16.2% | 1.7% | Safer about killing ads that would have recovered. |
| Wrong scale rate | 8.7% | 5.7% | Reduces scaling of noisy or inflated winners. |
| Missed scale rate | 10.1% | 34.5% | Conservative v1; waits for stronger evidence. |

The higher missed-scale rate is intentional in v1. The engine is tuned to avoid expensive false positives before it becomes aggressive about upside capture.

## What the engine recommends

- `stop`: mature underperformance with fatigue or saturation.
- `decrease`: not dead, but marginal ROAS suggests the next rupee is better used elsewhere.
- `increase`: mature signal, marginal ROAS above target, healthy frequency, and no blocking constraints.
- `hold`: immature, stale, protected, constrained, or unclear cases.
- `create`: represented in the design layer as creative-brief generation from winning/fatiguing patterns.

## Where AI is used

AI can classify creative patterns, write creative briefs from proven patterns, and generate readable rationale from structured audit fields. AI cannot move budgets, invent metrics, override guardrails, or write to Meta.

## Important limitation

The simulator is not proof of live revenue lift. It is a test harness for failure modes: noisy ROAS, delayed attribution, fatigue, saturation, and retargeting inflation. A production version would need real account backtests, margin data, inventory data, and online holdout or conversion lift testing.
