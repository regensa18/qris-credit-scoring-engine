import json
from main import build_pipeline
from domain.assess import assess_merchant

def run(path):
    return json.loads(assess_merchant(path, **build_pipeline()))

def test_steady_merchant_is_scored_with_explanations():
    out = run("tests/fixtures/SYN-steady-warung_sembako-UMI-1.csv")
    assert out["decision"] == "eligible"
    assert 0 <= out["score"] <= 100
    assert all(e["explanation"] for e in out["explanations"])
    assert any(e["rule"] == "shock_recovery" and not e["applicable"] for e in out["explanations"])

def test_shocked_merchant_with_full_recovery_matches_steady_decision():
    steady = run("tests/fixtures/SYN-steady-warung_sembako-UMI-1.csv")
    shocked = run("tests/fixtures/SYN-steady-warung_sembako_18_days_shock.csv")
    assert shocked["decision"] == steady["decision"]

def test_too_short_history_is_not_assessed():
    out = run("tests/fixtures/fixture_short.csv")
    assert out["decision"] == "not_assessed" and out["score"] is None and out["reason"]
