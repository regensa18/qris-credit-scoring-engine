from adapters.input.csv_input import CsvInput


def test_parses_transactions_from_fixture():
    transactions, profile = CsvInput().parse("tests/fixtures/SYN-growing-coffee_shop-UME-3.csv")

    print(f"Parsed {len(transactions)} transactions")
    print(transactions[0])
    print(profile)

    assert len(transactions) > 0
    assert profile.merchant_id == transactions[0].merchant_id
    assert all(t.amount > 0 for t in transactions)