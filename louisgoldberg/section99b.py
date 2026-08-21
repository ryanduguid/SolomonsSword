"""
Section 99B ITAA 1936 Assessment for receipts from non-resident / foreign trusts.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class ForeignTrustReceipt:
    beneficiary_name: str
    gross_amount_received_aud: Decimal
    corpus_amount_aud: Decimal = Decimal("0.00")  # Original capital settlement not from accumulated income
    already_assessed_under_div6_aud: Decimal = Decimal("0.00")
    source_country: str = "Foreign"


@dataclass(frozen=True)
class Section99BAssessment:
    beneficiary_name: str
    gross_receipt: Decimal
    corpus_exemption: Decimal
    prior_assessed_exemption: Decimal
    assessable_income_under_s99b: Decimal
    statutory_basis: str


def evaluate_section99b_liability(receipt: ForeignTrustReceipt) -> Section99BAssessment:
    """
    Calculate assessable amount under s 99B(1) less exemptions under s 99B(2)(a)-(c).
    """
    gross = receipt.gross_amount_received_aud
    corpus = receipt.corpus_amount_aud
    prior_taxed = receipt.already_assessed_under_div6_aud

    exemptions = corpus + prior_taxed
    assessable = max(Decimal("0.00"), gross - exemptions)

    basis = (
        f"s 99B(1) ITAA 1936: Gross receipt ${gross:,.2f} less corpus exemption ${corpus:,.2f} "
        f"(s 99B(2)(a)) and prior-taxed income ${prior_taxed:,.2f} (s 99B(2)(c)). Assessable: ${assessable:,.2f}."
    )

    return Section99BAssessment(
        beneficiary_name=receipt.beneficiary_name,
        gross_receipt=gross,
        corpus_exemption=corpus,
        prior_assessed_exemption=prior_taxed,
        assessable_income_under_s99b=assessable,
        statutory_basis=basis,
    )