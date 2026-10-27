import pandas as pd
import numpy as np
from domain.models import Transaction, Features

class StatisticalFeatureExtractor:
    def revenue_cv(self, daily: pd.Series) -> float:
        active = daily[daily>0]
        if len(active) < 2 or active.mean() <= 0:
            return 0.0
        return float(active.std() / active.mean())

    def gap_stats(self, daily: pd.Series) -> tuple[int, int]:
        is_zero = (daily == 0).to_numpy()
        gap_days_total = int(is_zero.sum())

        longest = 0
        current = 0
        for zero in is_zero:
            current = current + 1 if zero else 0
            longest = max(longest, current)

        return gap_days_total, longest

    def weekly_pattern_strength(self, daily: pd.Series) -> float:
        if len(daily) < 28 or daily.mean() <= 0:
            return 0.0

        weekday_means = daily.groupby(daily.index.weekday).mean()
        return float(weekday_means.std(ddof=0) / weekday_means.mean())

    # def shock_like_drop_detected(self, daily: pd.Series, 
    #     min_gap_days: int=5, window_days: int=14,  
    #     min_active_ratio: float=0.8) -> bool:
    #     values = daily.to_numpy()
    #     is_zero = values == 0
    #     n = len(values)

    #     i = 0
    #     while i < n:
    #         if not is_zero[i]:
    #             i += 1
    #             continue

    #         start = i
    #         while i < n and is_zero[i]:
    #             i += 1
    #         end = i

    #         if end - start < min_gap_days:
    #             continue

    #         before = values[max(0, start-window_days):start]
    #         after = values[end:end + window_days]

    #         if len(before) < 7 or len(after) < 7:
    #             continue

    #         if (before > 0).mean() >= min_active_ratio and (after > 0).mean() >= min_active_ratio:
    #             return True

    #     return False

    def shock_runs(self, daily, min_gap_days=5, window_days=14, min_active_ratio=0.8):
        """(start, end) index pairs, end exclusive, for each dip-and-recover run."""
        values = np.asarray(daily, dtype=float)
        is_zero = values == 0
        n = len(values)
        runs = []
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
            before = values[max(0, start - window_days):start]
            after = values[end:end + window_days]
            if len(before) < 7 or len(after) < 7:
                continue
            if (before > 0).mean() >= min_active_ratio and (after > 0).mean() >= min_active_ratio:
                runs.append((start, end))
        return runs

    # def gap_stats_outside_shocks(self, daily, runs):
    #     """Same idea as gap_stats, but recognised shock windows don't count as gaps."""
    #     is_zero = daily.to_numpy() == 0
    #     for start, end in runs:
    #         is_zero[start:end] = False
    #     total = int(is_zero.sum())
    #     longest = current = 0
    #     for z in is_zero:
    #         current = current + 1 if z else 0
    #         longest = max(longest, current)
    #     return total, longest

    def shock_like_drop_detected(self, daily, **kwargs) -> bool:
        return len(self.shock_runs(daily, **kwargs)) > 0

    @staticmethod
    def _segment_ids(n, runs):
        seg = np.zeros(n, dtype=int)
        for start, end in runs:
            seg[start:end] = -1     # shock days, zero revenue, excluded by the active mask below
            seg[end:] += 1
        return seg

    @staticmethod
    def _demean_within(values, segments):
        out = values.astype(float).copy()
        for s in np.unique(segments):
            mask = segments == s
            out[mask] -= out[mask].mean()
        return out

    def trend_slope_daily(self, daily, runs=None):
        active = daily.to_numpy() > 0
        if active.sum() < 3:
            return 0.0
        y = daily.to_numpy()[active]
        if y.mean() <= 0:
            return 0.0
        x = np.arange(len(daily))[active].astype(float)
        seg = self._segment_ids(len(daily), runs or [])[active]
        xc, yc = self._demean_within(x, seg), self._demean_within(y, seg)
        denom = (xc ** 2).sum()
        return float((xc * yc).sum() / denom / y.mean()) if denom > 0 else 0.0

    def revenue_cv_residual(self, daily, runs=None):
        active = daily.to_numpy() > 0
        if active.sum() < 14:
            return 0.0
        x = np.arange(len(daily))[active].astype(float)
        log_y = np.log(daily.to_numpy()[active])
        seg = self._segment_ids(len(daily), runs or [])[active]
        xc, lc = self._demean_within(x, seg), self._demean_within(log_y, seg)
        denom = (xc ** 2).sum()
        slope = (xc * lc).sum() / denom if denom > 0 else 0.0
        resid = pd.Series(lc - slope * xc, index=daily.index[active])
        resid = resid - resid.groupby(resid.index.weekday).transform("mean")
        return float(resid.std())

    def shock_recovery_ratio(self, daily, runs, window_days=28):
        """Mean active-day revenue after a shock / before it. None if no shock."""
        if not runs:
            return None
        v = daily.to_numpy()
        ratios = []
        for start, end in runs:
            before = v[max(0, start - window_days):start]
            after = v[end:end + window_days]
            before, after = before[before > 0], after[after > 0]
            if len(before) and len(after):
                ratios.append(after.mean() / before.mean())
        return float(min(ratios)) if ratios else None

    def gap_stats_outside_shocks(self, daily, runs):
        """Same idea as gap_stats, but recognised shock windows don't count as gaps."""
        is_zero = daily.to_numpy() == 0
        for start, end in runs:
            is_zero[start:end] = False
        total = int(is_zero.sum())
        longest = current = 0
        for z in is_zero:
            current = current + 1 if z else 0
            longest = max(longest, current)
        return total, longest

    def gap_stats_unexplained(self, daily, runs, min_weeks=8, closed_ratio=0.9):
        """Zero days not explained by a recognised shock or a regular weekly closure.
        Returns (total, longest, regular_closed_weekdays); weekday 0 = Monday."""
        zero = daily.to_numpy() == 0
        in_shock = np.zeros(len(zero), dtype=bool)
        for start, end in runs:
            in_shock[start:end] = True
        weekday = np.asarray(daily.index.weekday)
        closed = []
        for d in range(7):
            mask = (weekday == d) & ~in_shock
            if mask.sum() >= min_weeks and zero[mask].mean() >= closed_ratio:
                closed.append(d)
        gap = zero & ~(in_shock | np.isin(weekday, closed))
        total = int(gap.sum())
        longest = current = 0
        for g in gap:
            current = current + 1 if g else 0
            longest = max(longest, current)
        return total, longest, closed

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

        runs = self.shock_runs(daily)

        revenue_cv_residual = self.revenue_cv_residual(daily, runs)
        weekly_pattern_strength = self.weekly_pattern_strength(daily)

        gaps_out_total, gaps_out_longest = self.gap_stats_outside_shocks(daily, runs)
        unexp_total, unexp_longest, closed_days = self.gap_stats_unexplained(daily, runs)

        return Features(
            total_transactions=total_transactions,
            active_days=active_days,
            total_days_span=total_days_span,
            revenue_cv=revenue_cv,
            gap_days_total=gap_total,
            longest_gap_days=longest_gap,
            weekly_pattern_strength=weekly_pattern_strength,
            daily_revenue={pd.Timestamp(d).strftime("%Y-%m-%d"): float(v) for d, v in daily.items()},
            revenue_cv_residual=revenue_cv_residual,
            trend_slope_daily=self.trend_slope_daily(daily, runs),
            shock_like_drop_detected=len(runs) > 0,
            shock_count=len(runs),
            shock_days_total=sum(e - s for s, e in runs),
            shock_recovery_ratio=self.shock_recovery_ratio(daily, runs),
            gap_days_outside_shocks=gaps_out_total,
            longest_gap_outside_shocks=gaps_out_longest,
            unexplained_gap_days=unexp_total,
            longest_unexplained_gap=unexp_longest,
            regular_closed_weekdays=closed_days
        )
