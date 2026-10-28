from domain.models import ScoreResult
from domain.scoring import compute_score, decide

def assess_merchant(source, *, input_port, validator, extractor, engine, output, scoring_cfg):
    transactions, profile = input_port.parse(source)

    validation = validator.validate(transactions)
    if not validation.passed:
        return output.format_not_assessed(profile.merchant_id, validation.reason)

    features = extractor.extract(transactions)
    results = engine.evaluate(features, profile)

    score = compute_score(results, scoring_cfg["scale_max"])
    decision = decide(score, scoring_cfg["eligible_threshold"], scoring_cfg["review_threshold"])

    return output.format(ScoreResult(
        merchant_id=profile.merchant_id, score=score,
        decision=decision, rule_results=results,
    ))
