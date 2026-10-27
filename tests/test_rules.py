from dataclasses import replace

from domain.models import Features
from adapters.reasoning.rules import revenue_stability, trend_direction, shock_recovery, structural_irregularity

PARAMS = {"weight_if_passed": 20, "weight_if_failed": -20, "max_residual_cv": 0.30}
TREND_PARAMS = {"weight_if_passed": 15, "weight_if_failed": -15, "min_monthly_change": -0.05}
SHOCK_PARAMS = {"weight_if_passed": 10, "weight_if_failed": -10,
                "min_recovery_ratio": 0.8, "max_excusable_shocks": 2}
IRR_PARAMS = {"weight_if_passed": 15, "weight_if_failed": -15,
              "max_unexplained_gap_share": 0.10, "max_unexplained_longest_gap_days": 7}

def _features(**overrides):
    base = Features(
        total_transactions=500, active_days=180, total_days_span=190,
        revenue_cv=0.2, revenue_cv_residual=0.10, trend_slope_daily=0.0,
        gap_days_total=0, longest_gap_days=0, weekly_pattern_strength=0.1,
        shock_like_drop_detected=False, daily_revenue={},
    )
    return replace(base, **overrides)

def test_stable_merchant_passes():
    r = revenue_stability.evaluate(_features(revenue_cv_residual=0.10), PARAMS)
    assert r.passed and r.contribution == 20 and r.max_points == 20

def test_unstable_merchant_fails():
    r = revenue_stability.evaluate(_features(revenue_cv_residual=0.45), PARAMS)
    assert not r.passed and r.contribution == -20 and r.max_points == 20

def test_exactly_at_limit_passes():
    assert revenue_stability.evaluate(_features(revenue_cv_residual=0.30), PARAMS).passed

def test_explanation_is_indonesian_and_has_numbers():
    r = revenue_stability.evaluate(_features(revenue_cv_residual=0.45), PARAMS)
    assert "45%" in r.explanation and "30%" in r.explanation

def test_flat_trend_passes():
    r = trend_direction.evaluate(_features(trend_slope_daily=0.0), TREND_PARAMS)
    assert r.passed and r.contribution == 15

def test_growth_passes_without_bonus():
    r = trend_direction.evaluate(_features(trend_slope_daily=0.004), TREND_PARAMS)
    assert r.passed and r.contribution == 15      # same points as flat

def test_steep_decline_fails():
    r = trend_direction.evaluate(_features(trend_slope_daily=-0.003), TREND_PARAMS)   # -9% per month
    assert not r.passed and r.contribution == -15 and r.max_points == 15

def test_trend_explanation_has_numbers():
    r = trend_direction.evaluate(_features(trend_slope_daily=-0.003), TREND_PARAMS)
    assert "-9.0%" in r.explanation and "5%" in r.explanation

def test_no_shock_is_not_applicable():
    r = shock_recovery.evaluate(_features(shock_count=0), SHOCK_PARAMS)
    assert not r.applicable and r.contribution == 0 and r.max_points == 0

def test_full_recovery_passes():
    r = shock_recovery.evaluate(_features(shock_count=1, shock_recovery_ratio=1.0), SHOCK_PARAMS)
    assert r.applicable and r.passed and r.contribution == 10

def test_partial_recovery_fails():
    r = shock_recovery.evaluate(_features(shock_count=1, shock_recovery_ratio=0.6), SHOCK_PARAMS)
    assert not r.passed and r.contribution == -10 and "60%" in r.explanation

def test_two_shocks_allowed_three_not():
    ok = shock_recovery.evaluate(_features(shock_count=2, shock_recovery_ratio=1.0), SHOCK_PARAMS)
    bad = shock_recovery.evaluate(_features(shock_count=3, shock_recovery_ratio=1.0), SHOCK_PARAMS)
    assert ok.passed and not bad.passed

def test_ratio_exactly_at_minimum_passes():
    assert shock_recovery.evaluate(_features(shock_count=1, shock_recovery_ratio=0.8), SHOCK_PARAMS).passed

# def test_both_reasons_penalised_once():
#     r = shock_recovery.evaluate(_features(shock_count=3, shock_recovery_ratio=0.5), SHOCK_PARAMS)
#     assert r.contribution == -10 and "3 kali" in r.explanation and "50%" in r.explanation

def test_continuous_merchant_passes():
    r = structural_irregularity.evaluate(
        _features(total_days_span=180, unexplained_gap_days=15, longest_unexplained_gap=3), IRR_PARAMS)
    assert r.passed and r.contribution == 15                     # 8%

def test_too_many_gap_days_fails():
    r = structural_irregularity.evaluate(
        _features(total_days_span=180, unexplained_gap_days=45, longest_unexplained_gap=4), IRR_PARAMS)
    assert not r.passed and "25%" in r.explanation               # 45/180

def test_long_dead_stretch_fails():
    r = structural_irregularity.evaluate(
        _features(total_days_span=180, unexplained_gap_days=10, longest_unexplained_gap=9), IRR_PARAMS)
    assert not r.passed and "9 hari" in r.explanation

def test_both_reasons_penalised_once():
    r = structural_irregularity.evaluate(
        _features(total_days_span=180, unexplained_gap_days=60, longest_unexplained_gap=12), IRR_PARAMS)
    assert r.contribution == -15
