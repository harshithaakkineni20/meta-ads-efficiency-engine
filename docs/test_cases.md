# Test cases and what they prove

The simulator creates observed Meta-style ad data and hidden ground truth. The engine only sees observed data. The evaluator uses hidden true marginal ROAS and future ROAS to score whether a recommendation was directionally right.

## Passing cases

| Case | Expected behavior | What it proves |
|---|---|---|
| Mature fatigued ad below target | Stop | The engine can identify real underperformance when signal is mature and fatigue is visible. |
| Young high-ROAS ad with low spend | Hold / watchlist | The engine does not scale noisy early winners just because ROAS looks good. |
| Mature ad with marginal ROAS above target and low frequency | Increase with cap | The engine can scale, but only when signal quality and saturation checks pass. |
| Low inventory product with strong ROAS | Hold / block scale | Business constraints override pure performance metrics. |
| Stale Meta API snapshot | Exclude / annotate | Data-quality failures do not create fake confidence. |

## Failed or intentionally conservative cases

| Case | What fails | What it shows |
|---|---|---|
| Naive ROAS rule scales a retargeting winner | Hidden true marginal ROAS is below target | Platform ROAS can overstate incrementality, especially in retargeting. |
| Engine misses a true scale opportunity | The engine waits for more signal | V1 is conservative by design; false positives are treated as more expensive than missed upside. |
| LLM returns malformed JSON | Creative brief output is rejected | The LLM cannot break the recommendation workflow. |
| LLM mentions a metric not present in the audit log | Summary is rejected | Explanations must be grounded in deterministic fields. |
| Promo window inflates observed ROAS | Confidence is reduced | The system should not confuse sale effects with ad quality. |

## Why failed cases matter

The failed cases are not embarrassing edge cases. They are the point of the simulator. A useful ads engine should expose where it is conservative, where naive rules break, and where business context is missing. This is safer than presenting a clean demo that only shows success paths.
