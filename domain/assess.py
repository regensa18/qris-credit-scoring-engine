import datetime

from domain.errors import InvalidInputError
from domain.models import ScoreResult
from domain.scoring import compute_score, decide

def assess_merchant(source, *, input_port, validator, extractor, engine, 
                    output, scoring_cfg, as_of: datetime.date | None = None):
    try:
        transactions, profile = input_port.parse(source)
    except InvalidInputError as e:
        return output.format_not_assessed("UNKNOWN", str(e))

    validation = validator.validate(transactions)
    if not validation.passed:
        return output.format_not_assessed(profile.merchant_id, validation.reason)

    features = extractor.extract(transactions, as_of)
    results = engine.evaluate(features, profile)

    score = compute_score(results, scoring_cfg["scale_max"])
    decision = decide(score, scoring_cfg["eligible_threshold"], scoring_cfg["review_threshold"], results)

    return output.format(ScoreResult(
        merchant_id=profile.merchant_id, score=score,
        decision=decision, rule_results=results,
    ))
