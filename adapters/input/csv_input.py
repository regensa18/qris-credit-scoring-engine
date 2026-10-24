import pandas as pd
from datetime import datetime
from domain.models import Transaction, MerchantProfile

class CsvInput:
    def parse(self, source: str) -> tuple[list[Transaction], MerchantProfile]:
        df = pd.read_csv(source)

        transactions = []
        for _, row in df.iterrows():
            transaction = Transaction(
                merchant_id = str(row["merchant_id"]),
                transaction_date=datetime.strptime(str(row["date"]), "%Y-%m-%d").date(),
                amount=float(row["amount"]),
                type=str(row.get("type", "credit")),
                mcc=str(row.get("mcc", "")),
                business_type=str(row.get("business_type", "")),
                merchant_business_scale=str(row.get("merchant_business_scale", "")),
                rrn=str(row.get("rrn", ""))
            )
            transactions.append(transaction)

        merchant = MerchantProfile(
            merchant_id=df.iloc[0]["merchant_id"],
            years_operated=0.0,
            location="test"
        )
        
        return transactions, merchant
