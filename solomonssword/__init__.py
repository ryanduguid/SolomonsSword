"""
SolomonsSword: Trust Distribution & Section 100A / 99B Risk Engine
Named for the judgement of Solomon, where the threat of proportionate division is what reveals the true claimant.
"""

__version__ = "0.1.0"
__author__ = "Ryan Duguid"

from .division6 import (
    TrustIncomeAssessment,
    BeneficiaryEntitlement,
    calculate_proportionate_share,
)
from .section100a import (
    Section100ARiskZone,
    Section100AAssessment,
    evaluate_section100a_risk,
)
from .section99b import (
    ForeignTrustReceipt,
    Section99BAssessment,
    evaluate_section99b_liability,
)
from .trust_resolution import (
    TrustResolutionSchedule,
    validate_trust_resolution,
)

__all__ = [
    "TrustIncomeAssessment",
    "BeneficiaryEntitlement",
    "calculate_proportionate_share",
    "Section100ARiskZone",
    "Section100AAssessment",
    "evaluate_section100a_risk",
    "ForeignTrustReceipt",
    "Section99BAssessment",
    "evaluate_section99b_liability",
    "TrustResolutionSchedule",
    "validate_trust_resolution",
]