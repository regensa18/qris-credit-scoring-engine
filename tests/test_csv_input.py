import json
import pytest

from main import build_pipeline
from domain.assess import assess_merchant
from adapters.input.csv_input import CsvInput

HEADER = "merchant_id,date,amount,type,rrn,mcc,business_type,merchant_business_scale\n"
ROW = "M1,2025-01-01,50000,credit,R1,5814,warung_sembako,UMI\n"

def test_parses_transactions_from_fixture():
    transactions, profile = CsvInput().parse("tests/fixtures/SYN-growing-coffee_shop-UME-3.csv")

    print(f"Parsed {len(transactions)} transactions")
    print(transactions[0])
    print(profile)

    assert len(transactions) > 0
    assert profile.merchant_id == transactions[0].merchant_id
    assert all(t.amount > 0 for t in transactions)

@pytest.mark.parametrize("content, expected_reason", [
    ("", "kosong"),
    (HEADER, "tidak berisi transaksi"),
    ("merchant_id,date,type,rrn\nM1,2025-01-01,credit,R1\n", "Kolom wajib tidak ditemukan: amount"),
    (HEADER + "M1,2025-01-01,abc,credit,R1,5814,warung_sembako,UMI\n", "bukan angka"),
    (HEADER + "M1,2025-01-01,-500,credit,R1,5814,warung_sembako,UMI\n", "lebih dari 0"),
    (HEADER + "M1,31/02/2025,50000,credit,R1,5814,warung_sembako,UMI\n", "tanggal"),
    (HEADER + ROW + "M2,2025-01-02,50000,credit,R2,5814,warung_sembako,UMI\n", "lebih dari satu merchant"),
])
def test_bad_input_is_not_assessed_with_a_clear_reason(tmp_path, content, expected_reason):
    f = tmp_path / "input.csv"
    f.write_text(content)
    out = json.loads(assess_merchant(str(f), **build_pipeline()))
    assert out["decision"] == "not_assessed"
    assert out["score"] is None
    assert expected_reason in out["reason"]


def test_error_reason_names_the_line_number(tmp_path):
    f = tmp_path / "input.csv"
    f.write_text(HEADER + ROW + "M1,2025-01-02,abc,credit,R2,5814,warung_sembako,UMI\n")
    out = json.loads(assess_merchant(str(f), **build_pipeline()))
    assert "Baris 3" in out["reason"]          # header is line 1, first row line 2, bad row line 3
