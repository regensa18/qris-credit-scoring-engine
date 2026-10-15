from domain.models import Transaction, ValidationResult

class BasicValidator:
    def __init__(self, config: dict):
        v = config["validation"]
        self.min_months = v["minimum_observation_months"]
        self.min_transactions = v["minimum_transactions"]
        self.reject_on_duplicate_rrn = v.get("reject_on_duplicate_rrn", True)

    def validate(self, transactions: list[Transaction]) -> ValidationResult:
        if not transactions:
            return ValidationResult(
                passed=False,
                reason="Tidak ada data transaksi yang ditemukan.",
            )

        if self.reject_on_duplicate_rrn:
            rrns = [t.rrn for t in transactions if t.rrn]
            duplicates = len(rrns) - len(set(rrns))
            if duplicates > 0:
                return ValidationResult(
                    passed=False,
                    reason=(
                        f"Ditemukan {duplicates} transaksi dengan nomor referensi (RRN) ganda. "
                        f"Data tidak dapat dinilai karena integritasnya tidak terjamin."
                    ),
                )

        if len(transactions) < self.min_transactions:
            return ValidationResult(
                passed=False,
                reason=(
                    f"Jumlah transaksi tidak mencukupi untuk dilakukan penilaian. "
                    f"Ditemukan {len(transactions)} transaksi, minimum yang dibutuhkan "
                    f"adalah {self.min_transactions} transaksi."
                ),
            )

        first = min(t.transaction_date for t in transactions)
        last = max(t.transaction_date for t in transactions)
        window_days = (last - first).days + 1  # inclusive of both ends
        required_days = self.min_months * 30   # approximate 30-day months

        if window_days < required_days:
            return ValidationResult(
                passed=False,
                reason=(
                    f"Riwayat transaksi tidak mencukupi untuk dilakukan penilaian. "
                    f"Periode pengamatan sekitar {window_days / 30:.1f} bulan "
                    f"({first} sampai {last}), minimum yang dibutuhkan adalah "
                    f"{self.min_months} bulan."
                ),
            )

        return ValidationResult(passed=True)