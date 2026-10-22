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

        slope, intercept = np.polyfit(x, log_y.to_numpy(), 1)
        detrended = log_y - (slope * x + intercept)

        detrended = detrended - detrended.groupby(detrended.index.weekday).transform("mean")

        return float(detrended.std())

    def weekly_pattern_strength(self, daily: pd.Series) -> float:
        if len(daily) < 28 or daily.mean() <= 0:
            return 0.0

        weekday_means = daily.groupby(daily.index.weekday).mean()
        return float(weekday_means.std(ddof=0) / weekday_means.mean())

    def shock_like_drop_detected(self, daily: pd.Series, 
        min_gap_days: int=5, window_days: int=14,  
        min_active_ratio: float=0.8) -> bool:
        values = daily.to_numpy()
        is_zero = values == 0
        n = len(values)

        i = 0
        while i < n:
            if not is_zero[i]:
                i += 1
                continue

            start = i
            while i < n and is_zero[i]:
                i += 1
            end = i

            if end - start < min_gap_days:
                continue

            before = values[max(0, start-window_days):start]
            after = values[end:end + window_days]

            if len(before) < 7 or len(after) < 7:
                continue

            if (before > 0).mean() >= min_active_ratio and (after > 0).mean() >= min_active_ratio:
                return True

        return False

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
        weekly_pattern_strength = self.weekly_pattern_strength(daily)

        shock_like_drop = self.shock_like_drop_detected(daily)

        return Features(
            total_transactions=total_transactions,
            active_days=active_days,
            total_days_span=total_days_span,
            revenue_cv=revenue_cv,
            trend_slope_daily=trend,
            gap_days_total=gap_total,
            longest_gap_days=longest_gap,
            weekly_pattern_strength=weekly_pattern_strength,
            shock_like_drop_detected=shock_like_drop,
            revenue_cv_residual=revenue_cv_residual,
            daily_revenue={pd.Timestamp(d).strftime("%Y-%m-%d"): float(v) for d, v in daily.items()},
        )
