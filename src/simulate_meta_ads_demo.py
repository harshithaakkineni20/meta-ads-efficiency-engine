"""Generate a simulated Meta ads account and score recommendation policies.

The assignment did not include a real Meta dataset, so this simulator creates
an account-like dataset with hidden ground truth. The engine sees observed
attributed performance. The evaluator sees hidden future/marginal ROAS, which
lets us test whether a recommendation was directionally right.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

N_CAMPAIGNS = 10_000
N_ADS = 120_000

product_categories = np.array(["Skincare", "Apparel", "Home", "Beauty", "Electronics accessories"])
formats = np.array(["UGC Reel", "Static", "Carousel", "Product Demo", "Testimonial", "Offer-led"])
funnel = np.array(["Prospecting", "Retargeting", "Retention"])

campaign_id = rng.integers(1, N_CAMPAIGNS + 1, size=N_ADS)
product = rng.choice(product_categories, size=N_ADS, p=[0.26, 0.24, 0.17, 0.20, 0.13])
fmt = rng.choice(formats, size=N_ADS, p=[0.34, 0.20, 0.18, 0.12, 0.09, 0.07])
stage = rng.choice(funnel, size=N_ADS, p=[0.68, 0.24, 0.08])

margin_map = {
    "Skincare": 0.60,
    "Apparel": 0.52,
    "Home": 0.42,
    "Beauty": 0.58,
    "Electronics accessories": 0.46,
}
margin = np.array([margin_map[p] for p in product])
target_roas = (1 / margin) * 1.10

age_days = rng.integers(1, 45, size=N_ADS)
daily_budget = np.clip(rng.lognormal(mean=8.1, sigma=0.9, size=N_ADS), 300, 90_000)
spend_7d = daily_budget * np.minimum(age_days, 7) * rng.uniform(0.75, 1.05, size=N_ADS)

creative_quality = rng.beta(2.2, 4.5, size=N_ADS)
audience_fit = rng.beta(2.5, 3.2, size=N_ADS)
saturation = rng.beta(2.0, 2.2, size=N_ADS)

base_mroas = target_roas * (0.45 + 2.1 * creative_quality + 1.25 * audience_fit)
base_mroas *= np.where(fmt == "UGC Reel", 1.13, np.where(fmt == "Static", 0.92, 1.0))
base_mroas *= np.where(stage == "Retargeting", 0.88, np.where(stage == "Retention", 0.82, 1.0))

frequency = np.clip(
    (spend_7d / np.percentile(spend_7d, 65)) * (0.9 + 4.5 * saturation) + rng.normal(0, 0.35, N_ADS),
    0.7,
    11.5,
)
fatigue_penalty = 1 / (1 + 0.22 * np.maximum(0, frequency - 3.0) ** 1.4)
true_marginal_roas = base_mroas * fatigue_penalty
true_future_roas = true_marginal_roas * rng.lognormal(mean=0, sigma=0.35, size=N_ADS)

cpc = rng.lognormal(mean=4.25, sigma=0.45, size=N_ADS)
clicks = np.maximum(1, (spend_7d / cpc).astype(int))
ctr = np.clip(rng.normal(0.014 + 0.018 * creative_quality, 0.005, N_ADS), 0.002, 0.065)
impressions = np.maximum(1_000, (clicks / ctr).astype(int))

aov = np.where(product == "Home", rng.normal(2400, 450, N_ADS), rng.normal(1450, 300, N_ADS))
aov = np.where(product == "Electronics accessories", rng.normal(1800, 380, N_ADS), aov)
aov = np.clip(aov, 450, 4200)
expected_revenue = spend_7d * true_future_roas
expected_purchases = np.clip(expected_revenue / aov, 0.1, 5000)
purchases = np.maximum(0, rng.poisson(expected_purchases))

delay_factor = np.where(
    age_days < 4,
    rng.uniform(0.45, 0.78, N_ADS),
    np.where(age_days < 7, rng.uniform(0.75, 0.95, N_ADS), 1.0),
)
luck = rng.lognormal(mean=0, sigma=np.clip(1.2 / np.sqrt(np.maximum(purchases, 1)), 0.12, 0.85), size=N_ADS)
overlap_factor = np.where(stage == "Retargeting", rng.uniform(1.15, 1.85, N_ADS), np.where(stage == "Retention", rng.uniform(1.05, 1.55, N_ADS), 1.0))
observed_revenue = purchases * aov * delay_factor * luck * overlap_factor
raw_roas = np.divide(observed_revenue, spend_7d, out=np.zeros_like(observed_revenue), where=spend_7d > 0)

ctr_decline = np.clip((frequency - 2.1) * 0.12 + rng.normal(0, 0.12, N_ADS), -0.25, 0.65)
cpm_increase = np.clip((frequency - 3.0) * 0.06 + rng.normal(0, 0.07, N_ADS), -0.15, 0.45)

mature = (age_days >= 7) & (spend_7d >= 6500) & (impressions >= 5000) & (purchases >= 8)
peer_key = pd.Series(product + "|" + fmt + "|" + stage)
df_tmp = pd.DataFrame({"peer": peer_key, "raw": raw_roas / target_roas})
peer_mean_norm = df_tmp.groupby("peer")["raw"].transform("mean").to_numpy()
w = purchases / (purchases + 24)
expected_norm_roas = w * (raw_roas / target_roas) + (1 - w) * peer_mean_norm
expected_roas = expected_norm_roas * target_roas
confidence = np.clip(0.45 + 0.12 * np.log1p(purchases) + 0.10 * np.log1p(spend_7d / 10000), 0.35, 0.96)
estimated_marginal_roas = expected_roas * np.clip(1.12 - 0.08 * np.maximum(0, frequency - 2.5), 0.45, 1.15)
estimated_marginal_roas *= np.where(stage == "Retargeting", 0.78, np.where(stage == "Retention", 0.85, 1.0))

naive_stop = raw_roas < (0.70 * target_roas)
naive_increase = raw_roas > (1.00 * target_roas)

engine_stop = mature & (expected_roas < 1.00 * target_roas) & (confidence > 0.65) & ((ctr_decline > 0.05) | (frequency > 3.6))
engine_increase = mature & (estimated_marginal_roas > 1.12 * target_roas) & (confidence > 0.72) & (frequency < np.where(stage == "Prospecting", 2.8, 4.2)) & (ctr_decline < 0.12)
engine_decrease = mature & (~engine_stop) & (estimated_marginal_roas < 0.88 * target_roas) & (frequency > 3.2) & (confidence > 0.65)
engine_hold = ~(engine_stop | engine_increase | engine_decrease)

false_pause_naive = naive_stop & (true_future_roas >= target_roas)
false_pause_engine = engine_stop & (true_future_roas >= target_roas)
wrong_scale_naive = naive_increase & (true_marginal_roas < target_roas)
wrong_scale_engine = engine_increase & (true_marginal_roas < target_roas)
scaleable_truth = (true_marginal_roas > 1.25 * target_roas) & mature
missed_scale_naive = (~naive_increase) & scaleable_truth
missed_scale_engine = (~engine_increase) & scaleable_truth

def pct(num: float, den: float) -> float:
    return 100 * num / den if den else 0.0

summary = {
    "campaigns": N_CAMPAIGNS,
    "ads": N_ADS,
    "mature_ads": int(mature.sum()),
    "naive_stop_count": int(naive_stop.sum()),
    "engine_stop_count": int(engine_stop.sum()),
    "naive_increase_count": int(naive_increase.sum()),
    "engine_increase_count": int(engine_increase.sum()),
    "engine_decrease_count": int(engine_decrease.sum()),
    "naive_false_pause_rate": pct(false_pause_naive.sum(), naive_stop.sum()),
    "engine_false_pause_rate": pct(false_pause_engine.sum(), engine_stop.sum()),
    "naive_wrong_scale_rate": pct(wrong_scale_naive.sum(), naive_increase.sum()),
    "engine_wrong_scale_rate": pct(wrong_scale_engine.sum(), engine_increase.sum()),
    "naive_missed_scale_rate": pct(missed_scale_naive.sum(), scaleable_truth.sum()),
    "engine_missed_scale_rate": pct(missed_scale_engine.sum(), scaleable_truth.sum()),
    "engine_skip_rate": pct(engine_hold.sum(), N_ADS),
}

example_df = pd.DataFrame({
    "ad_id": [f"ad_{i:06d}" for i in range(N_ADS)],
    "campaign_id": campaign_id,
    "product": product,
    "format": fmt,
    "stage": stage,
    "age_days": age_days,
    "spend_7d": spend_7d,
    "impressions": impressions,
    "clicks": clicks,
    "purchases": purchases,
    "revenue": observed_revenue,
    "raw_roas": raw_roas,
    "expected_roas": expected_roas,
    "estimated_marginal_roas": estimated_marginal_roas,
    "true_marginal_roas": true_marginal_roas,
    "true_future_roas": true_future_roas,
    "target_roas": target_roas,
    "frequency": frequency,
    "ctr_decline": ctr_decline,
    "cpm_increase": cpm_increase,
    "engine_stop": engine_stop,
    "engine_increase": engine_increase,
    "engine_decrease": engine_decrease,
    "mature": mature,
    "naive_stop": naive_stop,
    "naive_increase": naive_increase,
    "false_pause_naive": false_pause_naive,
    "false_pause_engine": false_pause_engine,
    "wrong_scale_naive": wrong_scale_naive,
    "wrong_scale_engine": wrong_scale_engine,
})

ex_stop = example_df[example_df.engine_stop & (example_df.raw_roas < 0.6 * example_df.target_roas)].head(1)
ex_hold = example_df[(example_df.raw_roas > 2.3 * example_df.target_roas) & (~example_df.engine_increase) & (example_df.true_marginal_roas < example_df.target_roas) & (example_df.age_days < 7)].head(1)
ex_inc = example_df[example_df.engine_increase & (example_df.estimated_marginal_roas > 1.2 * example_df.target_roas)].head(1)
ex_naive_fail = example_df[example_df.wrong_scale_naive & (~example_df.engine_increase)].head(1)
examples = pd.concat([ex_stop, ex_hold, ex_inc, ex_naive_fail]).drop_duplicates("ad_id")

pd.DataFrame([summary]).T.to_csv(OUTPUT_DIR / "sim_summary.csv", header=["value"])
examples.to_csv(OUTPUT_DIR / "sim_examples.csv", index=False)

rows = []
rows.append("# Sample simulator output\n")
rows.append("This output is simulated. It is a failure-mode test harness, not proof of live-account lift.\n")
rows.append("## Generated data\n")
rows.append(f"- Campaigns: {N_CAMPAIGNS:,}\n- Ads: {N_ADS:,}\n- Mature ads eligible for hard decisions: {int(mature.sum()):,}\n")
rows.append("## Policy comparison\n")
rows.append("| Metric | Naive ROAS rule | Guarded engine | Readout |\n|---|---:|---:|---|\n")
rows.append(f"| False pause rate | {summary['naive_false_pause_rate']:.1f}% | {summary['engine_false_pause_rate']:.1f}% | Engine is safer about killing ads that would have recovered. |\n")
rows.append(f"| Wrong scale rate | {summary['naive_wrong_scale_rate']:.1f}% | {summary['engine_wrong_scale_rate']:.1f}% | Engine reduces scaling of noisy or inflated winners. |\n")
rows.append(f"| Missed scale rate | {summary['naive_missed_scale_rate']:.1f}% | {summary['engine_missed_scale_rate']:.1f}% | Engine is deliberately conservative in v1. |\n")
rows.append("\n## Example rows\n")
for _, r in examples.iterrows():
    if bool(r.engine_stop):
        label = "Stop mature fatigued ad"
        action = "STOP"
        why = "Mature underperformance with saturation and weak marginal ROAS."
    elif bool(r.engine_increase):
        label = "Increase mature scalable ad"
        action = "INCREASE"
        why = "Marginal ROAS is above target, frequency is healthy, and signal is mature."
    elif bool(r.wrong_scale_naive):
        label = "Failed naive scale case"
        action = "ENGINE HOLDS"
        why = "A simple ROAS rule would scale, but hidden marginal ROAS is below target."
    else:
        label = "Hold exciting but immature ad"
        action = "HOLD / WATCHLIST"
        why = "Raw ROAS looks high, but the ad is young or noisy."
    rows.append(f"\n### {label}\n")
    rows.append(f"- Ad: `{r.ad_id}`\n")
    rows.append(f"- Product / format / stage: {r['product']} / {r['format']} / {r['stage']}\n")
    rows.append(f"- Age: {int(r.age_days)} days\n")
    rows.append(f"- Spend 7d: INR {r.spend_7d:,.0f}\n")
    rows.append(f"- Purchases: {int(r.purchases)}\n")
    rows.append(f"- Raw ROAS: {r.raw_roas:.2f}\n")
    rows.append(f"- Estimated marginal ROAS: {r.estimated_marginal_roas:.2f}\n")
    rows.append(f"- Hidden true marginal ROAS: {r.true_marginal_roas:.2f}\n")
    rows.append(f"- Target ROAS: {r.target_roas:.2f}\n")
    rows.append(f"- Frequency: {r.frequency:.2f}\n")
    rows.append(f"- Engine action: **{action}**\n")
    rows.append(f"- What this shows: {why}\n")

(OUTPUT_DIR / "sample_output.md").write_text("".join(rows))

print(pd.DataFrame([summary]).T)
print("\nWrote outputs to", OUTPUT_DIR)


if __name__ == "__main__":
    pass
