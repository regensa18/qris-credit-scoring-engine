from domain.models import Features, MerchantProfile, RuleResult
from adapters.reasoning.rules import (
    revenue_stability, trend_direction, structural_irregularity, shock_recovery,
)

REGISTRY = {
    module.RULE_NAME: module.evaluate
    for module in (revenue_stability, trend_direction, structural_irregularity, shock_recovery)
}

class RuleBasedEngine:
    """Implements ReasoningPort: runs every rule that appears in the config."""

    def __init__(self, rules_config: dict):
        unknown = [name for name in rules_config if name not in REGISTRY]
        if unknown:
            raise ValueError(f"Aturan tidak dikenal di config: {unknown}")
        self._rules = [(REGISTRY[name], params) for name, params in rules_config.items()]

    def evaluate(self, features: Features, profile: MerchantProfile) -> list[RuleResult]:
        return [rule(features, params) for rule, params in self._rules]

    