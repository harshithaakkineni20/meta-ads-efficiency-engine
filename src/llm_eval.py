"""Small LLM output guard for creative brief generation.

The eval here is intentionally boring: schema, claims, duplication, and metric
truthfulness. For this assignment, boring guards are the point. The LLM can write
briefs and summaries, but the system rejects malformed or unsafe output.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

BANNED_CLAIMS = ["cures", "removes pigmentation", "guaranteed", "in 7 days", "medical grade"]
REQUIRED_BRIEF_FIELDS = {"hook", "visual_direction", "script_outline", "cta", "why_this_works"}
ALLOWED_METRICS = {"raw_roas", "expected_roas", "marginal_roas", "target_roas", "frequency", "ctr_decline", "spend_7d", "purchases_7d"}


@dataclass
class EvalResult:
    passed: bool
    reason: str


def validate_creative_briefs(raw: str, expected_product: str, existing_hooks: set[str]) -> EvalResult:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return EvalResult(False, "malformed_json")

    briefs = payload.get("briefs")
    if not isinstance(briefs, list) or not briefs:
        return EvalResult(False, "missing_briefs")

    seen_hooks = set(existing_hooks)
    for brief in briefs:
        if not isinstance(brief, dict):
            return EvalResult(False, "brief_not_object")
        if set(brief.keys()) < REQUIRED_BRIEF_FIELDS:
            return EvalResult(False, "missing_required_field")
        text = json.dumps(brief).lower()
        if expected_product.lower() not in text:
            return EvalResult(False, "wrong_product_context")
        if any(claim in text for claim in BANNED_CLAIMS):
            return EvalResult(False, "unsafe_or_unsubstantiated_claim")
        hook = brief["hook"].strip().lower()
        if hook in seen_hooks:
            return EvalResult(False, "duplicate_hook")
        seen_hooks.add(hook)
    return EvalResult(True, "ok")


def validate_summary_metrics(summary: str, audit: dict[str, Any]) -> EvalResult:
    """Reject summaries that mention metrics not present in deterministic audit data."""
    mentioned_metricish_tokens = {m for m in ALLOWED_METRICS if m in summary}
    missing = [m for m in mentioned_metricish_tokens if m not in audit]
    if missing:
        return EvalResult(False, f"metric_not_in_audit:{','.join(missing)}")
    return EvalResult(True, "ok")


if __name__ == "__main__":
    bad_json = "{briefs: [not valid]}"
    print("malformed json:", validate_creative_briefs(bad_json, "Vitamin C Serum", set()))

    bad_claim = json.dumps({"briefs": [{
        "hook": "Vitamin C Serum removes pigmentation in 7 days",
        "visual_direction": "Creator holds the product",
        "script_outline": "Show routine and claim fast results",
        "cta": "Shop now",
        "why_this_works": "Vitamin C Serum solves a sharp pain point"
    }]})
    print("unsafe claim:", validate_creative_briefs(bad_claim, "Vitamin C Serum", set()))
