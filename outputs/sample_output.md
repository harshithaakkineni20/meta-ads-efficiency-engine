# Sample simulator output
This output is simulated. It is a failure-mode test harness, not proof of live-account lift.
## Generated data
- Campaigns: 10,000
- Ads: 120,000
- Mature ads eligible for hard decisions: 84,852
## Policy comparison
| Metric | Naive ROAS rule | Guarded engine | Readout |
|---|---:|---:|---|
| False pause rate | 16.2% | 1.7% | Engine is safer about killing ads that would have recovered. |
| Wrong scale rate | 8.7% | 5.7% | Engine reduces scaling of noisy or inflated winners. |
| Missed scale rate | 10.1% | 34.5% | Engine is deliberately conservative in v1. |

## Example rows

### Stop mature fatigued ad
- Ad: `ad_000000`
- Product / format / stage: Beauty / UGC Reel / Prospecting
- Age: 7 days
- Spend 7d: INR 161,607
- Purchases: 81
- Raw ROAS: 0.73
- Estimated marginal ROAS: 0.59
- Hidden true marginal ROAS: 0.70
- Target ROAS: 1.90
- Frequency: 11.50
- Engine action: **STOP**
- What this shows: Mature underperformance with saturation and weak marginal ROAS.

### Failed naive scale case
- Ad: `ad_006520`
- Product / format / stage: Electronics accessories / UGC Reel / Prospecting
- Age: 2 days
- Spend 7d: INR 2,484
- Purchases: 5
- Raw ROAS: 6.29
- Estimated marginal ROAS: 4.97
- Hidden true marginal ROAS: 2.33
- Target ROAS: 2.39
- Frequency: 0.85
- Engine action: **ENGINE HOLDS**
- What this shows: A simple ROAS rule would scale, but hidden marginal ROAS is below target.

### Increase mature scalable ad
- Ad: `ad_000002`
- Product / format / stage: Beauty / Product Demo / Retargeting
- Age: 36 days
- Spend 7d: INR 9,859
- Purchases: 11
- Raw ROAS: 2.49
- Estimated marginal ROAS: 3.07
- Hidden true marginal ROAS: 2.08
- Target ROAS: 1.90
- Frequency: 0.70
- Engine action: **INCREASE**
- What this shows: Marginal ROAS is above target, frequency is healthy, and signal is mature.

### Failed naive scale case
- Ad: `ad_000004`
- Product / format / stage: Home / Product Demo / Retargeting
- Age: 20 days
- Spend 7d: INR 48,703
- Purchases: 36
- Raw ROAS: 4.50
- Estimated marginal ROAS: 3.05
- Hidden true marginal ROAS: 1.72
- Target ROAS: 2.62
- Frequency: 6.09
- Engine action: **ENGINE HOLDS**
- What this shows: A simple ROAS rule would scale, but hidden marginal ROAS is below target.
