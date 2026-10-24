from domain.models import Features, RuleResult
from adapters.reasoning import messages

RULE_NAME = "trend_direction"
DAYS_PER_MONTH = 30

def evaluate(features: Features, params: dict) -> RuleResult:
    monthly_change = features.trend_slope_daily * DAYS_PER_MONTH
    limit = params["min_monthly_change"]
    passed = monthly_change >= limit
    weight = params["weight_if_passed"] if passed else params["weight_if_failed"]
    return RuleResult(
        rule_name=RULE_NAME,
        passed=passed,
        contribution=weight,
        explanation=messages.trend_direction(passed, monthly_change, limit),
        max_points=params["weight_if_passed"],
    )
