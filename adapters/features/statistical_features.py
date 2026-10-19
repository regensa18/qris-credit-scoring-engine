import pandas as pd
import numpy as np
from domain.models import Transaction, Features

class StatisticalFeatureExtractor:
    def revenue_cv(self, daily: pd.Series) -> float:
        active = daily[daily>0]
        if len(active) < 2 or active.mean() <= 0:
            return 0.0
        return float(active.std() / active.mean())

    def trend_slope_daily(self, daily: pd.Series) -> float:
        active = daily[daily > 0]
        if len(active) < 3 or active.mean() <= 0 :
            return 0.0
        x = (active.index - daily.index[0]).days.to_numpy()
        y = active.to_numpy()
        slope = np.polyfit(x, y, 1)[0]
        return float(slope / active.mean())

    def gap_stats(self, daily: pd.Series) -> tuple[int, int]:
        is_zero = (daily == 0).to_numpy()
        gap_days_total = int(is_zero.sum())

        longest = 0
        current = 0
        for zero in is_zero:
            current = current + 1 if zero else 0
            longest = max(longest, current)

        return gap_days_total, longest

    def revenue_cv_residual(self, daily: pd.Series) -> float:
        active = daily[daily > 0]
        if len(active) < 14 or active.mean() <= 0:
            return 0.0

        x = (active.index - daily.index[0]).days.to_numpy()
        log_y = pd.Series(np.log(active.to_numpy()), index=active.index)

        # 1. remove the trend (a straight line in log space = compounding growth)
        slope, intercept = np.polyfit(x, log_y.to_numpy(), 1)
        detrended = log_y - (slope * x + intercept)

        # 2. remove the weekday effect (subtract each weekday's average)
        detrended = detrended - detrended.groupby(detrended.index.weekday).transform("mean")

        # 3. what remains is the unpredictable swing
        return float(detrended.std())

    def extract(self, transactions: list[Transaction]) -> Features:
        df = pd.DataFrame([{"date": pd.Timestamp(t.transaction_date), "amount": t.amount} for t in transactions])
        daily = df.groupby("date")["amount"].sum().sort_index()

        full_index = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
        daily = daily.reindex(full_index, fill_value=0.0)

        total_transactions = len(transactions)
        active_days = int((daily>0).sum())
        total_days_span = len(daily)

        revenue_cv = self.revenue_cv(daily)
        trend = self.trend_slope_daily(daily)
        gap_total, longest_gap = self.gap_stats(daily)

        revenue_cv_residual = self.revenue_cv_residual(daily)

        return Features(
            total_transactions=total_transactions,
            active_days=active_days,
            total_days_span=total_days_span,
            revenue_cv=revenue_cv,
            trend_slope_daily=trend,
            gap_days_total=gap_total,
            longest_gap_days=longest_gap,
            weekly_pattern_strength=0.0,
            shock_like_drop_detected=False,
            revenue_cv_residual=revenue_cv_residual,
            daily_revenue={pd.Timestamp(d).strftime("%Y-%m-%d"): float(v) for d, v in daily.items()},
        )
