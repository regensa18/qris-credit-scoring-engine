import json
from domain.models import ScoreResult

ENGINE_NAME = "rule_based_v1"

class JsonOutput:
    """Implements OutputPort. JSON with Bahasa Indonesia explanations."""

    def format(self, result: ScoreResult) -> str:
        payload = {
            "merchant_id": result.merchant_id,
            "engine": ENGINE_NAME,
            "score": result.score,
            "decision": result.decision,
            "explanations": [
                {
                    "rule": r.rule_name,
                    "applicable": r.applicable,
                    "passed": r.passed,
                    "points": r.contribution,
                    "explanation": r.explanation,
                }
                for r in result.rule_results
            ],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def format_not_assessed(self, merchant_id: str, reason: str) -> str:
        payload = {
            "merchant_id": merchant_id,
            "engine": ENGINE_NAME,
            "score": None,
            "decision": "not_assessed",
            "reason": reason,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
