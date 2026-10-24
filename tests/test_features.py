import pandas as pd
from pytest import approx
from adapters.features.statistical_features import StatisticalFeatureExtractor
from adapters.input.csv_input import CsvInput

FULL = "SYN-steady-warung_sembako_18_days_shock"
PARTIAL = "SYN-steady-coffee_shop_7_day_shock"
NONE = "SYN-seasonal-fried_chicken_5_days_shock"

def _series(values):
    index = pd.date_range("2025-01-01", periods=len(values), freq="D")
    return pd.Series(values, index=index, dtype= float)

def _load(name):
    transactions, _ = CsvInput().parse(f"tests/fixtures/{name}.csv")
    return transactions, StatisticalFeatureExtractor().extract(transactions)

f = StatisticalFeatureExtractor()

# --- revenue_cv ---
def test_cv_is_zero_when_all_active_days_identical():
    assert f.revenue_cv(_series([100, 100, 100, 100])) == 0.0

def test_cv_known_value():
    # [90, 110]: mean 100, sample std sqrt(200) = 14.142 -> cv 0.1414
    assert f.revenue_cv(_series([90, 110])) == approx(0.1414, abs=1e-3)

def test_cv_ignores_zero_days():
    # zeros are gaps, not low-revenue days, so the CV should not change
    assert f.revenue_cv(_series([90, 0, 0, 110])) == approx(0.1414, abs=1e-3)

def test_cv_returns_zero_with_fewer_than_two_active_days():
    assert f.revenue_cv(_series([0, 0, 100])) == 0.0

# --- trend_slope_daily ---
def test_slope_is_zero_for_flat_series():
    assert f.trend_slope_daily(_series([100, 100, 100, 100, 100])) == approx(0.0, abs=1e-9)

def test_slope_positive_for_rising_series():
    # +10 per day, mean 120 -> 10/120
    assert f.trend_slope_daily(_series([100, 110, 120, 130, 140])) == approx(10 / 120)

def test_slope_negative_for_falling_series():
    assert f.trend_slope_daily(_series([140, 130, 120, 110, 100])) < 0

def test_slope_returns_zero_with_fewer_than_three_active_days():
    assert f.trend_slope_daily(_series([100, 0, 120])) == 0.0

# --- gap_stats ---
def test_gap_stats_counts_total_and_longest():
    # zeros at positions 1,2,4 -> total 3, longest run 2
    assert f.gap_stats(_series([100, 0, 0, 100, 0, 100])) == (3, 2)

def test_gap_stats_no_gaps():
    assert f.gap_stats(_series([100, 100, 100])) == (0, 0)


def test_extract_on_growing_fixture():
    transactions, _ = CsvInput().parse("tests/fixtures/SYN-growing-coffee_shop-UME-3.csv")
    features = f.extract(transactions)

    assert features.total_transactions == len(transactions)
    assert features.active_days > 150
    # assert features.revenue_cv < 0.3
    assert features.longest_gap_days == 0
    assert type(features.active_days) is int
    assert type(features.revenue_cv) is float

def test_residual_cv_is_small_for_clean_growing_merchant():
    transactions, _ = CsvInput().parse("tests/fixtures/SYN-growing-coffee_shop-UME-3.csv")
    df = pd.DataFrame([{"date": pd.Timestamp(t.transaction_date), "amount": t.amount} for t in transactions])
    daily = df.groupby("date")["amount"].sum().sort_index()

    full_index = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = daily.reindex(full_index, fill_value=0.0)
    assert 0.05 < f.revenue_cv_residual(daily) < 0.15

def test_residual_cv_is_small_for_volatile_merchant():
    transactions, _ = CsvInput().parse("tests/fixtures/SYN-volatile-fried_chicken_stall-UKE-5.csv")
    df = pd.DataFrame([{"date": pd.Timestamp(t.transaction_date), "amount": t.amount} for t in transactions])
    daily = df.groupby("date")["amount"].sum().sort_index()

    full_index = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = daily.reindex(full_index, fill_value=0.0)
    assert 0.4 < f.revenue_cv_residual(daily) < 0.5

def test_weekly_strength_known_value():
    daily = _series([100, 100, 100, 100, 100, 200, 200] * 4)
    assert f.weekly_pattern_strength(daily) == approx(0.3514, abs=1e-3)

def test_weekly_strength_zero_for_flat_series():
    assert f.weekly_pattern_strength(_series([100] * 14)) == 0.0

def test_weekly_strength_zero_when_series_too_short():
    assert f.weekly_pattern_strength(_series([100, 200, 300])) == 0.0

def test_shock_detected_for_dip_and_recover():
    assert f.shock_like_drop_detected(_series([100] * 30 + [0] * 10 + [100] * 30)) is True

def test_shock_detected_with_partial_recovery():
    assert f.shock_like_drop_detected(_series([100] * 30 + [0] * 10 + [60] * 30)) is True

def test_no_shock_in_flat_series():
    assert f.shock_like_drop_detected(_series([100] * 70)) is False

def test_weekly_closure_is_not_a_shock():
    assert f.shock_like_drop_detected(_series(([100] * 6 + [0]) * 10)) is False

def test_gap_at_end_is_not_a_shock():
    # no recovery observed
    assert f.shock_like_drop_detected(_series([100] * 30 + [0] * 10)) is False

def test_bazaar_pattern_is_not_a_shock():
    assert f.shock_like_drop_detected(_series(([0] * 25 + [100] * 3) * 5)) is False

def test_fixture_has_no_transactions_during_shock():
    # checks the fixture itself: the closed days (Apr 10 to Apr 27) are empty
    transactions, _ = _load(FULL)
    shocked = set(pd.date_range("2025-04-10", periods=18).date)
    assert not any(t.transaction_date in shocked for t in transactions)

def test_full_recovery_shock_is_detected():
    _, f = _load(FULL)
    assert f.shock_like_drop_detected is True

def test_full_recovery_gap_features():
    _, f = _load(FULL)
    assert f.total_days_span == 365
    assert f.gap_days_total == 18
    assert f.longest_gap_days == 18
    assert f.active_days == 347 # 365 - 18

def test_partial_recovery_shock_is_detected():
    _, f = _load(PARTIAL)
    assert f.shock_like_drop_detected is True


def test_partial_recovery_gap_features():
    _, f = _load(PARTIAL)
    assert f.gap_days_total == 7
    assert f.longest_gap_days == 7
    assert f.active_days == 358 # 365 - 7

def test_permanent_closure_is_not_visible_as_a_shock():
    # Known limitation: with recovery="none" the series just ends on Oct 10,
    # so there is no dip-and-recover shape to find.
    transactions, f = _load(NONE)
    assert max(t.transaction_date for t in transactions).isoformat() == "2025-10-10"
    assert f.total_days_span == 283      # Jan 1 to Oct 10 inclusive
    assert f.gap_days_total == 0
    assert f.shock_like_drop_detected is False

def _shock_series(after_level, extra_zero_days=()):
    vals = [100.0] * 30 + [0.0] * 6 + [after_level] * 30
    for i in extra_zero_days:
        vals[i] = 0.0
    return pd.Series(vals, index=pd.date_range("2026-01-01", periods=66))

def test_shock_runs_finds_the_closure():
    assert StatisticalFeatureExtractor().shock_runs(_shock_series(100.0)) == [(30, 36)]

def test_recovery_ratio_full_and_partial():
    f = StatisticalFeatureExtractor()
    s_full, s_part = _shock_series(100.0), _shock_series(60.0)
    assert f.shock_recovery_ratio(s_full, f.shock_runs(s_full)) == approx(1.0)
    assert f.shock_recovery_ratio(s_part, f.shock_runs(s_part)) == approx(0.6)

def test_no_shock_gives_none():
    f = StatisticalFeatureExtractor()
    flat = pd.Series([100.0] * 40, index=pd.date_range("2026-01-01", periods=40))
    assert f.shock_recovery_ratio(flat, f.shock_runs(flat)) is None

def test_gap_outside_shocks_ignores_the_shock():
    f = StatisticalFeatureExtractor()
    s = _shock_series(100.0, extra_zero_days=(10, 11))   # 2-day gap, too short to be a shock
    runs = f.shock_runs(s)
    assert f.gap_stats_outside_shocks(s, runs) == (2, 2)
    assert f.gap_stats(s) == (8, 6) 

