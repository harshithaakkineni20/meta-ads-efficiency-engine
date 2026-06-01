"""Small executable test cases for the decision engine.

Run with:
    python tests/test_engine_cases.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from engine import AdsetMetrics, recommend


def test_stop_mature_fatigued_ad() -> None:
    rec = recommend(AdsetMetrics(
        adset_id="ad_stop_001",
        product="Home",
        stage="Prospecting",
        age_days=21,
        spend_7d=150_000,
        purchases_7d=70,
        raw_roas=1.2,
        expected_roas=1.8,
        marginal_roas=0.9,
        target_roas=2.6,
        frequency=8.5,
        ctr_decline=0.45,
        current_budget=20_000,
    ))
    assert rec.action == "stop"


def test_hold_immature_high_roas_ad() -> None:
    rec = recommend(AdsetMetrics(
        adset_id="ad_hold_001",
        product="Apparel",
        stage="Retargeting",
        age_days=4,
        spend_7d=4_000,
        purchases_7d=3,
        raw_roas=7.5,
        expected_roas=5.8,
        marginal_roas=4.2,
        target_roas=2.1,
        frequency=0.9,
        ctr_decline=-0.10,
        current_budget=2_000,
    ))
    assert rec.action == "hold"
    assert "immature_age" in rec.flags or "insufficient_spend" in rec.flags


def test_increase_mature_healthy_ad() -> None:
    rec = recommend(AdsetMetrics(
        adset_id="ad_scale_001",
        product="Beauty",
        stage="Retargeting",
        age_days=30,
        spend_7d=35_000,
        purchases_7d=35,
        raw_roas=3.2,
        expected_roas=3.4,
        marginal_roas=3.1,
        target_roas=1.9,
        frequency=1.2,
        ctr_decline=0.02,
        current_budget=5_000,
        has_lift_support=True,
    ))
    assert rec.action == "increase"
    assert rec.new_budget > rec.current_budget


def test_block_scale_when_inventory_is_low() -> None:
    rec = recommend(AdsetMetrics(
        adset_id="ad_inventory_001",
        product="Skincare",
        stage="Prospecting",
        age_days=25,
        spend_7d=45_000,
        purchases_7d=50,
        raw_roas=4.1,
        expected_roas=4.0,
        marginal_roas=3.7,
        target_roas=1.9,
        frequency=1.1,
        ctr_decline=0.01,
        current_budget=6_000,
        low_inventory=True,
    ))
    assert rec.action == "hold"
    assert "low_inventory" in rec.flags


def run() -> None:
    tests = [
        test_stop_mature_fatigued_ad,
        test_hold_immature_high_roas_ad,
        test_increase_mature_healthy_ad,
        test_block_scale_when_inventory_is_low,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")


if __name__ == "__main__":
    run()
