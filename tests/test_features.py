import pandas as pd
from pytest import approx
from adapters.features.statistical_features import StatisticalFeatureExtractor
from adapters.input.csv_input import CsvInput

def _series(values):
    index = pd.date_range("2025-01-01", periods=len(values), freq="D")
    return pd.Series(values, index=index, dtype= float)

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
