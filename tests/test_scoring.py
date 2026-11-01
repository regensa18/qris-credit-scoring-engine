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

def _blocker():
    return RuleResult(rule_name="recent_activity", passed=False, contribution=0,
                      explanation="", applicable=True, max_points=0, blocks_approval=True)

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

def test_blocker_caps_eligible_at_manual_review():
    b = _blocker()
    print("applicable:", b.applicable, "blocks_approval:", b.blocks_approval)
    assert decide(100, 80, 50, [_blocker()]) == "manual_review"

def test_blocker_does_not_lift_a_low_decision():
    assert decide(40, 80, 50, [_blocker()]) == "not_eligible"

def test_unblocked_still_eligible():
    assert decide(100, 80, 50, []) == "eligible"
