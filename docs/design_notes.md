# Design notes

## Core thesis

Do not optimize historical average ROAS in isolation. Estimate whether the next rupee of spend is likely to work, then apply maturity, confidence, attribution, fatigue, inventory, learning-phase, and approval guardrails before moving budget.

## Why this is not an LLM media buyer

The LLM is useful for creative interpretation and explanation. It is not reliable enough to control budget movement directly. Budget decisions are made through deterministic rules and stored with an audit trail.

## Assumed ad universe

The assignment did not provide a real customer dataset, so the simulator assumes a multi-category consumer brand running Meta ads across skincare, apparel, beauty, home/lifestyle, and electronics accessories. Campaign stages include prospecting, retargeting, and retention. Creative formats include UGC reels, static ads, carousel ads, demos, testimonials, and offer-led ads.

## Production validation needed

Simulator results are not live lift claims. A production deployment would need account backtesting, margin data, inventory data, CAPI quality checks, and eventually online holdout or conversion lift testing.
