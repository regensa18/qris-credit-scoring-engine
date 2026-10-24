from dataclasses import dataclass, field
from datetime import date

@dataclass
class Transaction:
    merchant_id: str
    transaction_date: date
    amount: float
    type: str
    rrn: str
    mcc: str=""
    business_type: str=""
    merchant_business_scale: str=""

@dataclass
class MerchantProfile:
    merchant_id: str
    years_operated: float
    location: str

@dataclass
class ValidationResult:
    passed: bool
    reason: str=""

@dataclass
class Features:
    total_transactions: int
    active_days: int
    total_days_span: int
    revenue_cv: float
    trend_slope_daily: float
    weekly_pattern_strength: float
    gap_days_total: int
    longest_gap_days: int
    shock_like_drop_detected: bool
    revenue_cv_residual: float
    daily_revenue: dict[str, float] = field(default_factory=dict)
    shock_count: int = 0
    shock_days_total: int = 0
    shock_recovery_ratio: float | None = None   # None = no shock
    gap_days_outside_shocks: int = 0
    longest_gap_outside_shocks: int = 0

