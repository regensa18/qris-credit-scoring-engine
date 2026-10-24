import dataclasses
from adapters.validation.basic_validator import BasicValidator
from adapters.input.csv_input import CsvInput
from config.loader import load_config

def _validator():
    return BasicValidator(load_config("config.json"))

def test_sufficient_history_passes():
    transactions, _ = CsvInput().parse("tests/fixtures/SYN-growing-coffee_shop-UME-3.csv")
    assert _validator().validate(transactions).passed is True

def test_short_history_fails_with_specific_reason():
    transactions, _ = CsvInput().parse("tests/fixtures/fixture_short.csv")
    result = _validator().validate(transactions)
    assert result.passed is False
    assert "transaksi" in result.reason

def test_empty_fails():
    assert _validator().validate([]).passed is False

def test_duplicate_rrn_fails():
    transactions, _ = CsvInput().parse("tests/fixtures/SYN-growing-coffee_shop-UME-3.csv")
    transactions[1] = dataclasses.replace(transactions[1], rrn=transactions[0].rrn)
    result = _validator().validate(transactions)
    assert result.passed is False
    assert "RRN" in result.reason

def test_event_based_merchant_is_still_assessable():
    transactions, _ = CsvInput().parse("tests/fixtures/SYN-event_based-bazaar_vendor-UMI-7.csv")
    assert _validator().validate(transactions).passed is True