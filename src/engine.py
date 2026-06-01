"""Tiny inspectable recommendation engine for the AppliedAI Meta ads assignment.

This is intentionally not an LLM agent. The functions below are pure-ish policy
logic: they accept already-computed metrics and return a recommendation plus an
audit trace. The LLM can explain this trace later, but it cannot change money.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Action = Literal["stop", "decrease", "increase", "hold"]
Confidence = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class AdsetMetrics:
    adset_id: str
    product: str
    stage: Literal["Prospecting", "Retargeting", "Retention"]
    age_days: int
    spend_7d: float
    purchases_7d: int
    raw_roas: float
    expected_roas: float
    marginal_roas: float
    target_roas: float
    frequency: float
    ctr_decline: float
    current_budget: float
    in_learning_phase: bool = False
    stale_data: bool = False
    protected: bool = False
    low_inventory: bool = False
    promo_window: bool = False
    cooldown_active: bool = False
    has_lift_support: bool = False


@dataclass
class Recommendation:
    adset_id: str
    action: Action
    current_budget: float
    new_budget: float
    expected_value: float
    confidence: Confidence
    flags: list[str] = field(default_factory=list)
    fallback_rationale: str = "Recommendation generated from deterministic audit fields."
    audit: dict = field(default_factory=dict)


def maturity_flags(m: AdsetMetrics) -> list[str]:
    flags: list[str] = []
    if m.stale_data:
        flags.append("stale_data")
    if m.age_days < 7:
        flags.append("immature_age")
    if m.spend_7d < max(6500, 2 * max(m.current_budget, 1)):
        flags.append("insufficient_spend")
    if m.purchases_7d < 8:
        flags.append("insufficient_purchases")
    if m.in_learning_phase:
        flags.append("learning_phase")
    if m.cooldown_active:
        flags.append("cooldown")
    if m.protected:
        flags.append("protected")
    if m.low_inventory:
        flags.append("low_inventory")
    if m.promo_window:
        flags.append("promo_window")
    return flags


def confidence_label(m: AdsetMetrics) -> Confidence:
    if m.purchases_7d >= 50 and m.spend_7d >= 25000:
        return "high"
    if m.purchases_7d >= 15 and m.spend_7d >= 10000:
        return "medium"
    return "low"


def recommend(m: AdsetMetrics) -> Recommendation:
    flags = maturity_flags(m)
    conf = confidence_label(m)
    hard_blocks = {"stale_data", "protected", "low_inventory"}
    maturity_blocks = {"immature_age", "insufficient_spend", "insufficient_purchases"}
    blocked = any(f in hard_blocks for f in flags)
    immature = any(f in maturity_blocks for f in flags)

    audit = {
        "raw_roas": round(m.raw_roas, 2),
        "expected_roas": round(m.expected_roas, 2),
        "marginal_roas": round(m.marginal_roas, 2),
        "target_roas": round(m.target_roas, 2),
        "frequency": round(m.frequency, 2),
        "ctr_decline": round(m.ctr_decline, 3),
        "flags": flags,
    }

    if blocked or immature:
        return Recommendation(
            adset_id=m.adset_id,
            action="hold",
            current_budget=m.current_budget,
            new_budget=m.current_budget,
            expected_value=0.0,
            confidence=conf,
            flags=flags,
            fallback_rationale="Held because the engine did not have clean, mature, or permissible data to move money.",
            audit=audit,
        )

    # Stop: mature, weak expected ROAS, fatigue/saturation, no strategic protection.
    if m.expected_roas < 1.00 * m.target_roas and (m.frequency > 3.6 or m.ctr_decline > 0.05):
        return Recommendation(
            adset_id=m.adset_id,
            action="stop",
            current_budget=m.current_budget,
            new_budget=0.0,
            expected_value=max(0.0, m.current_budget * (m.target_roas - m.marginal_roas)),
            confidence=conf,
            flags=flags + ["below_target", "fatigue_or_saturation"],
            fallback_rationale="Mature adset with expected ROAS below target and fatigue/saturation signals.",
            audit=audit,
        )

    # Increase: no learning/cooldown, marginal ROAS above target, and not saturated.
    if (
        not m.in_learning_phase
        and not m.cooldown_active
        and m.marginal_roas > 1.12 * m.target_roas
        and m.frequency < (2.8 if m.stage == "Prospecting" else 4.2)
        and m.ctr_decline < 0.12
    ):
        increase = 0.15 * m.current_budget
        return Recommendation(
            adset_id=m.adset_id,
            action="increase",
            current_budget=m.current_budget,
            new_budget=m.current_budget + increase,
            expected_value=increase * m.marginal_roas,
            confidence=conf,
            flags=flags + ["marginal_roas_above_target"],
            fallback_rationale="Mature adset with marginal ROAS above target, low frequency, and stable creative signal.",
            audit=audit,
        )

    # Decrease: not bad enough to stop, but the next rupee looks inefficient.
    if m.marginal_roas < 0.88 * m.target_roas and m.frequency > 3.2:
        decrease = 0.20 * m.current_budget
        return Recommendation(
            adset_id=m.adset_id,
            action="decrease",
            current_budget=m.current_budget,
            new_budget=m.current_budget - decrease,
            expected_value=max(0.0, decrease * (m.target_roas - m.marginal_roas)),
            confidence=conf,
            flags=flags + ["marginal_roas_below_target", "saturation"],
            fallback_rationale="Adset is not dead, but marginal ROAS is below target and frequency suggests saturation.",
            audit=audit,
        )

    return Recommendation(
        adset_id=m.adset_id,
        action="hold",
        current_budget=m.current_budget,
        new_budget=m.current_budget,
        expected_value=0.0,
        confidence=conf,
        flags=flags,
        fallback_rationale="No safe action: signal is acceptable but not strong enough to move budget today.",
        audit=audit,
    )
