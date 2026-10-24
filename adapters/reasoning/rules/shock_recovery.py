from domain.models import Features, RuleResult
from adapters.reasoning import messages

RULE_NAME = "shock_recovery"

def evaluate(features: Features, params: dict) -> RuleResult:
    if features.shock_count == 0:
        return RuleResult(
            rule_name=RULE_NAME, passed=True, contribution=0,
            explanation=messages.shock_not_applicable(),
            applicable=False, max_points=0,
        )

    max_shocks = params["max_excusable_shocks"]
    min_ratio = params["min_recovery_ratio"]
    ratio = features.shock_recovery_ratio

    too_many = features.shock_count > max_shocks
    low_recovery = ratio is not None and ratio < min_ratio
    passed = not (too_many or low_recovery)

    if passed:
        weight = params["weight_if_passed"]
        text = messages.shock_recovery_passed(features.shock_count, ratio)
    else:
        weight = params["weight_if_failed"]
        text = messages.shock_recovery_failed(
            features.shock_count, max_shocks, ratio, min_ratio, too_many, low_recovery)

    return RuleResult(
        rule_name=RULE_NAME, passed=passed, contribution=weight,
        explanation=text, max_points=params["weight_if_passed"],
    )
