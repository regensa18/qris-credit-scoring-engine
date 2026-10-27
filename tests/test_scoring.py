import pytest
from domain.models import RuleResult
from domain.scoring import compute_score, decide

def _r(passed, weight, applicable=True):
    return RuleResult(
        rule_name="x", passed=passed,
        contribution=(weight if passed else -weight) if applicable else 0,
        explanation="", applicable=applicable,
        max_points=weight if applicable else 0,
    )

def test_all_pass_is_100():
    assert compute_score([_r(True, 20), _r(True, 15), _r(True, 15), _r(True, 10)]) == 100

def test_not_applicable_rule_does_not_lower_the_score():
    with_shock = [_r(True, 20), _r(True, 15), _r(True, 15), _r(True, 10)]
    no_shock = [_r(True, 20), _r(True, 15), _r(True, 15), _r(True, 10, applicable=False)]
    assert compute_score(with_shock) == compute_score(no_shock) == 100

def test_one_failure_scores():
    assert compute_score([_r(True, 20), _r(False, 15), _r(True, 15), _r(True, 10)]) == 75

def test_even_split_is_midpoint():
    assert compute_score([_r(True, 10), _r(False, 10)]) == 50

def test_no_applicable_rules_raises():
    with pytest.raises(ValueError):
        compute_score([_r(True, 10, applicable=False)])

def test_decision_boundaries():
    assert decide(80, 80, 50) == "eligible"
    assert decide(79, 80, 50) == "manual_review"
    assert decide(50, 80, 50) == "manual_review"
    assert decide(49, 80, 50) == "not_eligible"
