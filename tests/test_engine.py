import pytest
from domain.models import Features
from adapters.reasoning.rule_based_engine import RuleBasedEngine

RULES = {
    "revenue_stability": {"weight_if_passed": 20, "weight_if_failed": -20, "max_residual_cv": 0.30},
    "trend_direction": {"weight_if_passed": 15, "weight_if_failed": -15, "min_monthly_change": -0.05},
    "structural_irregularity_handling": {"weight_if_passed": 15, "weight_if_failed": -15,
        "max_unexplained_gap_share": 0.10, "max_unexplained_longest_gap_days": 7},
    "shock_recovery": {"weight_if_passed": 10, "weight_if_failed": -10,
        "min_recovery_ratio": 0.8, "max_excusable_shocks": 2},
}

def _features():
    return Features(
        total_transactions=500, active_days=180, total_days_span=190,
        revenue_cv=0.2, revenue_cv_residual=0.10, trend_slope_daily=0.0,
        gap_days_total=0, longest_gap_days=0, weekly_pattern_strength=0.1,
        shock_like_drop_detected=False, daily_revenue={},
    )

def test_engine_runs_all_configured_rules():
    results = RuleBasedEngine(RULES).evaluate(_features(), profile=None)
    assert [r.rule_name for r in results] == list(RULES)

def test_unknown_rule_in_config_is_rejected():
    with pytest.raises(ValueError):
        RuleBasedEngine({"seasonality_awareness": {}})
