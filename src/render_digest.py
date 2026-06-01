"""Render the recommendation digest for Slack / email.

Recommendation-only: the message proposes actions and links to apply them after
human approval. Nothing here writes to Meta. Numbers come from the engine audit
fields. The LLM only phrases rationale. If the LLM fails, the digest still sends.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

try:
    from llm_layer import build_rationale  # optional in this demo package
except Exception:  # pragma: no cover - demo fallback
    build_rationale = None


def _money(x: float) -> str:
    return f"₹{x:,.0f}"


def _safe_flags(r) -> list[str]:
    return list(getattr(r, "flags", []) or [])


def _safe_rationale(r) -> str:
    """LLM failure must not block financial recommendations."""
    fallback = getattr(r, "fallback_rationale", "Recommendation generated from deterministic audit fields.")
    if build_rationale is None:
        return fallback
    try:
        text = build_rationale(r)
        if not text or not isinstance(text, str):
            return fallback
        return text
    except Exception:
        return fallback


def portfolio_summary(recs: Iterable) -> tuple[Counter, float, float, float]:
    recs = list(recs)
    c = Counter(r.action for r in recs)
    acted = [r for r in recs if r.action != "hold"]
    freed = sum(r.current_budget - r.new_budget for r in recs if r.action in ("stop", "decrease"))
    added = sum(r.new_budget - r.current_budget for r in recs if r.action == "increase")
    exp_gain = sum(getattr(r, "expected_value", 0.0) for r in acted)
    return c, freed, added, exp_gain


def render_slack(recs: Iterable, top_n: int = 6, has_margin_data: bool = False) -> str:
    recs = list(recs)
    c, freed, added, exp_gain = portfolio_summary(recs)
    acted = sorted([r for r in recs if r.action != "hold"], key=lambda r: abs(r.expected_value), reverse=True)
    immature = sum(1 for r in recs if any(f.startswith("immature") or f.startswith("insufficient") for f in _safe_flags(r)))
    value_label = "contribution margin" if has_margin_data else "incremental value estimate"

    lines: list[str] = []
    lines.append("*Meta ROAS engine - daily recommendations*")
    lines.append(
        f"Reviewed {len(recs)} adsets · "
        f"{c.get('stop',0)} stop · {c.get('decrease',0)} trim · "
        f"{c.get('increase',0)} scale · {c.get('hold',0)} hold "
        f"({immature} held for insufficient data)"
    )
    lines.append(
        f"Frees {_money(freed)}/day, redeploys {_money(added)}/day · "
        f"est. +{_money(exp_gain)}/day {value_label}"
    )
    lines.append("")
    lines.append(f"*Top {min(top_n, len(acted))} by impact* (review in dashboard; nothing auto-applied):")
    for r in acted[:top_n]:
        tag = {"stop": "STOP", "increase": "SCALE", "decrease": "TRIM"}.get(r.action, "HOLD")
        flags = _safe_flags(r)
        flagtxt = f"  _[{', '.join(flags)}]_" if flags else ""
        lines.append(f"- {tag} `{r.adset_id}` ({r.confidence} confidence){flagtxt}")
        lines.append(f"  {_safe_rationale(r)}")
    lines.append("")
    lines.append("[ Approve low-risk only ]   [ Review high-risk ]   [ Export CSV ]   [ Snooze 24h ]")
    return "\n".join(lines)


def render_email(recs: Iterable, has_margin_data: bool = False) -> str:
    recs = list(recs)
    c, freed, added, exp_gain = portfolio_summary(recs)
    acted = sorted([r for r in recs if r.action != "hold"], key=lambda r: abs(r.expected_value), reverse=True)
    value_label = "margin" if has_margin_data else "value"

    out: list[str] = []
    out.append(f"Subject: Meta ROAS engine - {len(acted)} recommended changes today")
    out.append("")
    out.append("Summary")
    out.append(f"  Adsets reviewed:        {len(recs)}")
    out.append(f"  Stop / Trim / Scale:    {c.get('stop',0)} / {c.get('decrease',0)} / {c.get('increase',0)}")
    out.append(f"  Budget freed per day:   {_money(freed)}")
    out.append(f"  Budget redeployed/day:  {_money(added)}")
    out.append(f"  Est. daily {value_label}:      {_money(exp_gain)}")
    out.append("")
    out.append("All changes require approval. The engine has no write access to Meta in v1.")
    out.append("")
    out.append("Recommended changes")
    out.append(f"  {'adset':<18}{'action':<10}{'current':>10}{'proposed':>11}{'conf':>8}")
    for r in acted:
        nb = "stop" if r.action == "stop" else _money(r.new_budget)
        out.append(f"  {r.adset_id:<18}{r.action:<10}{_money(r.current_budget):>10}{nb:>11}{r.confidence:>8}")
    return "\n".join(out)
