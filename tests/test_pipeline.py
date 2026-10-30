import json, datetime
from main import build_pipeline
from domain.assess import assess_merchant

START_DATE = datetime.date(2025, 1, 1)     # the start_date you passed to the generator
DAYS = 365                                  # the days you passed to the generator
AS_OF = START_DATE + datetime.timedelta(days=DAYS - 1)    # last day of the generated period
# ENDED = "tests/fixtures/SYN-seasonal-fried_chicken_5_days_shock.csv"

FIXTURES = "tests/fixtures/"
STEADY = FIXTURES + "SYN-steady-warung_sembako-UMI-1.csv"
SHOCK_FULL_RECOVERY = FIXTURES + "SYN-steady-warung_sembako_18_days_shock.csv"    # 18-day shock, full recovery
SEASONAL_OK = FIXTURES + "SYN-growing-coffee_shop-UME-3.csv"     # full year, no closure
ENDED = FIXTURES + "SYN-seasonal-fried_chicken_5_days_shock.csv"           # stops on 2025-10-10
TOO_SHORT = FIXTURES + "fixture_short.csv"

def run(path, as_of=None):
    return json.loads(assess_merchant(path, as_of=as_of, **build_pipeline()))

def rule(out, name):
    return next(e for e in out["explanations"] if e["rule"] == name)

# def test_steady_merchant_is_scored_with_explanations():
#     out = run("tests/fixtures/SYN-steady-warung_sembako-UMI-1.csv")
#     assert out["decision"] == "eligible"
#     assert 0 <= out["score"] <= 100
#     assert all(e["explanation"] for e in out["explanations"])
#     assert any(e["rule"] == "shock_recovery" and not e["applicable"] for e in out["explanations"])

# def test_shocked_merchant_with_full_recovery_matches_steady_decision():
#     steady = run("tests/fixtures/SYN-steady-warung_sembako-UMI-1.csv")
#     shocked = run("tests/fixtures/SYN-steady-warung_sembako_18_days_shock.csv")
#     assert shocked["decision"] == steady["decision"]

# def test_too_short_history_is_not_assessed():
#     out = run("tests/fixtures/fixture_short.csv")
#     assert out["decision"] == "not_assessed" and out["score"] is None and out["reason"]

# def test_ended_business_is_not_auto_approved():
#     out = run(ENDED, as_of=AS_OF)
#     print("out explanations")
#     print(out["explanations"])
#     assert "recent_activity" in out["approval_blocked_by"]
#     assert out["decision"] in ("manual_review", "not_eligible")
#     recent = next(e for e in out["explanations"] if e["rule"] == "recent_activity")
#     assert not recent["passed"]

# def test_same_merchant_not_blocked_without_as_of():
#     out = run(ENDED)                      # as_of defaults to the last transaction date
#     assert out["approval_blocked_by"] == []

def test_steady_merchant_is_scored_with_explanations():
    out = run(STEADY)                                   # as_of=None -> last transaction date
    assert out["decision"] == "eligible"
    assert 0 <= out["score"] <= 100
    assert out["approval_blocked_by"] == []
    assert all(e["explanation"] for e in out["explanations"])
    assert not rule(out, "shock_recovery")["applicable"]


def test_seasonal_full_year_merchant_is_eligible():
    out = run(SEASONAL_OK, as_of=AS_OF)                 # file ends on AS_OF, so 0 days silent
    assert out["decision"] == "eligible"
    assert out["approval_blocked_by"] == []

def test_shocked_merchant_with_full_recovery_matches_steady_decision():
    steady = run(STEADY)
    shocked = run(SHOCK_FULL_RECOVERY)
    assert rule(shocked, "shock_recovery")["applicable"]
    assert rule(shocked, "shock_recovery")["passed"]
    assert shocked["decision"] == steady["decision"]

def test_ended_business_is_not_auto_approved_when_as_of_is_given():
    out = run(ENDED, as_of=AS_OF)
    assert "recent_activity" in out["approval_blocked_by"]
    assert out["decision"] in ("manual_review", "not_eligible")
    assert not rule(out, "recent_activity")["passed"]
    assert "82 hari" in rule(out, "recent_activity")["explanation"]    # 2025-10-10 -> 2025-12-31


def test_same_ended_business_is_not_blocked_without_as_of():
    out = run(ENDED)                                    # as_of=None -> 0 days silent
    assert out["approval_blocked_by"] == []
    assert rule(out, "recent_activity")["passed"]


def test_as_of_before_last_transaction_does_not_crash():
    out = run(STEADY, as_of=datetime.date(2000, 1, 1))  # nonsense date: treated as 0 days silent
    assert out["decision"] != "not_assessed"

def test_too_short_history_is_not_assessed():
    out = run(TOO_SHORT)
    assert out["decision"] == "not_assessed"
    assert out["score"] is None
    assert out["reason"]
