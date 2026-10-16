import pandas as pd
import numpy as np
from datetime import datetime
from domain.models import Transaction, Features

class StatisticalFeatures:
    def revenue_cv(self, daily: pd.Series) -> float:
        active = daily[daily>0]
        if len(active) < 2 or active.mean() <= 0:
            return 0.0
        return float(active.std() / active.mean())

    def extract(self, transactions: list[Transaction]) -> Features:
        df = pd.DataFrame([{"date": t.transaction_date, "amount": t.amount} for t in transactions])
        daily = df.groupby("date")["amount"].sum().sort_index()

        full_index = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
        daily = daily.reindex(full_index, fill_value=0.0)

        total_transactions = len(transactions)
        active_days = int((daily>0).sum())
        total_days_span = len(daily)
