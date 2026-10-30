from domain.models import Features, RuleResult
from adapters.reasoning import messages

RULE_NAME = "recent_activity"

def evaluate(features: Features, params: dict) -> RuleResult:
    days = features.days_since_last_transaction
    limit = params["max_days_without_sales"]
    passed = days <= limit
    return RuleResult(
        rule_name=RULE_NAME, passed=passed, contribution=0,
        explanation=messages.recent_activity(passed, days, limit),
        max_points=0, blocks_approval=not passed,
    )
