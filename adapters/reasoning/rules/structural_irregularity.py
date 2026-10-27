from domain.models import Features, RuleResult
from adapters.reasoning import messages

RULE_NAME = "structural_irregularity_handling"

def evaluate(features: Features, params: dict) -> RuleResult:
    span = max(features.total_days_span, 1)
    share = features.unexplained_gap_days / span
    longest = features.longest_unexplained_gap
    limit = params["max_unexplained_gap_share"]
    max_longest = params["max_unexplained_longest_gap_days"]

    share_bad = share > limit
    longest_bad = longest > max_longest
    passed = not (share_bad or longest_bad)

    if passed:
        weight = params["weight_if_passed"]
        text = messages.irregularity_passed(share, limit, longest, max_longest)
    else:
        weight = params["weight_if_failed"]
        text = messages.irregularity_failed(share, limit, longest, max_longest, share_bad, longest_bad)

    return RuleResult(rule_name=RULE_NAME, passed=passed, contribution=weight,
                      explanation=text, max_points=params["weight_if_passed"])
