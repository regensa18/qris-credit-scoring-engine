from domain.models import Features, RuleResult
from adapters.reasoning import messages

RULE_NAME = "revenue_stability"

def evaluate(features: Features, params: dict) -> RuleResult:
    cv = features.revenue_cv_residual
    limit = params["max_residual_cv"]
    passed = cv <= limit
    weight = params["weight_if_passed"] if passed else params["weight_if_failed"]
    return RuleResult(
        rule_name=RULE_NAME,
        passed=passed,
        contribution=weight,
        explanation=messages.revenue_stability(passed, cv, limit),
        max_points=params["weight_if_passed"],
    )
