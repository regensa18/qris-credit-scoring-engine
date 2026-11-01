import math
import pandas as pd
from datetime import datetime

from domain.errors import InvalidInputError
from domain.models import Transaction, MerchantProfile

REQUIRED_COLUMNS = ["merchant_id", "date", "amount"]


class CsvInput:
    def parse(self, source: str) -> tuple[list[Transaction], MerchantProfile]:
        try:
            df = pd.read_csv(source)
        except pd.errors.EmptyDataError:
            raise InvalidInputError("File kosong atau tidak memiliki header.") from None
        except (pd.errors.ParserError, UnicodeDecodeError):
            raise InvalidInputError("File tidak dapat dibaca sebagai CSV yang valid.") from None

        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise InvalidInputError(f"Kolom wajib tidak ditemukan: {', '.join(missing)}.")

        if df.empty:
            raise InvalidInputError("File tidak berisi transaksi.")

        if df["merchant_id"].isna().any():
            raise InvalidInputError("Terdapat baris tanpa merchant_id.")

        if df["merchant_id"].nunique() > 1:
            raise InvalidInputError(
                "File berisi lebih dari satu merchant; satu file hanya boleh untuk satu merchant."
            )

        transactions = []
        for line, (_, row) in enumerate(df.iterrows(), start=2):   # line 1 is the header
            try:
                transaction_date = datetime.strptime(str(row["date"]), "%Y-%m-%d").date()
            except ValueError:
                raise InvalidInputError(
                    f"Baris {line}: tanggal '{row['date']}' tidak valid, gunakan format YYYY-MM-DD."
                ) from None

            try:
                amount = float(row["amount"])
            except (TypeError, ValueError):
                raise InvalidInputError(f"Baris {line}: jumlah '{row['amount']}' bukan angka.") from None
            if not math.isfinite(amount) or amount <= 0:
                raise InvalidInputError(f"Baris {line}: jumlah harus berupa angka lebih dari 0.")

            transactions.append(Transaction(
                merchant_id=str(row["merchant_id"]),
                transaction_date=transaction_date,
                amount=amount,
                type=str(row.get("type", "credit")),
                mcc=str(row.get("mcc", "")),
                business_type=str(row.get("business_type", "")),
                merchant_business_scale=str(row.get("merchant_business_scale", "")),
                rrn=str(row.get("rrn", "")),
            ))

        merchant = MerchantProfile(
            merchant_id=str(df.iloc[0]["merchant_id"]),
            years_operated=0.0,
            location="test",
        )
        return transactions, merchant
