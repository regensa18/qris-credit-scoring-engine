from typing import Protocol
from domain.models import Transaction, MerchantProfile, ValidationResult, Features, RuleResult

class InputPort(Protocol):
    def parse(self, source: str) -> tuple[list[Transaction], MerchantProfile]:
        """Parse a raw source (e.g. a CSV file path) into domain models."""
        ...

class ValidationPort(Protocol):
    def validate(self, transactions: list[Transaction]) -> ValidationResult:
        ...

class FeatureExtractionPort(Protocol):
    def extract(self, transactions: list[Transaction]) -> Features:
        ...

class ReasoningPort(Protocol):
    """THE swappable boundary. Today: RuleBasedEngine.
    Later: a neurosymbolic/knowledge-graph engine. Same interface either way."""
    def evaluate(self, features: Features, profile: MerchantProfile) -> list[RuleResult]:
        ...

class OutputPort(Protocol):
    def format(self, merchant_id: str, results: list[RuleResult]) -> dict:
        ...

    def format_not_assessed(self, merchant_id: str, reason: str) -> dict:
        ...
