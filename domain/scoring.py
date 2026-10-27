def compute_score(results, scale_max: int = 100) -> int:
    applicable = [r for r in results if r.applicable]
    best = sum(r.max_points for r in applicable)
    if best <= 0:
        raise ValueError("Tidak ada aturan yang berlaku untuk dinilai")
    total = sum(r.contribution for r in applicable)
    score = round(scale_max * (total + best) / (2 * best))
    return max(0, min(scale_max, score))

def decide(score: int, eligible_threshold: int, review_threshold: int) -> str:
    if score >= eligible_threshold:
        return "eligible"
    if score >= review_threshold:
        return "manual_review"
    return "not_eligible"

