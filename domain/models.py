from dataclasses import dataclass
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


