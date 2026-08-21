"""
Division 6 ITAA 1936 Trust Net Income allocation and proportionate approach
grounded in Bamford v FCT [2012] HCA 11.
"""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict


@dataclass(frozen=True)
class BeneficiaryEntitlement:
    beneficiary_name: str
    is_resident: bool = True
    is_under_legal_disability: bool = False  # e.g., minor (s 98) vs adult (s 97)
    fixed_entitlement_amount: Optional[Decimal] = None
    percentage_entitlement: Optional[Decimal] = None
    specifically_streamed_capital_gains: Decimal = Decimal("0.00")
    specifically_streamed_franked_dividends: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class BeneficiaryTaxShare:
    beneficiary_name: str
    trust_income_entitlement: Decimal
    proportion_percentage: Decimal
    section95_net_income_share: Decimal
    streamed_capital_gains: Decimal
    streamed_franked_dividends: Decimal
    franking_credit_grossup: Decimal
    total_taxable_component: Decimal
    assessed_under_section: str  # e.g., "s 97 (Beneficiary direct)", "s 98 (Trustee on behalf of minor)"


@dataclass
class TrustIncomeAssessment:
    financial_year: int
    trust_name: str
    trust_accounting_income: Decimal      # Income of the trust estate under trust deed
    section95_net_taxable_income: Decimal  # s 95(1) ITAA 1936 net income
    net_capital_gains: Decimal = Decimal("0.00")
    franked_dividends: Decimal = Decimal("0.00")
    franking_credits: Decimal = Decimal("0.00")
    beneficiaries: List[BeneficiaryEntitlement] = field(default_factory=list)


def calculate_proportionate_share(assessment: TrustIncomeAssessment) -> List[BeneficiaryTaxShare]:
    """
    Calculate each beneficiary's assessable share of s 95 net income under the
    proportionate approach (Bamford v FCT) and Subdivisions 115-220 & 207-B ITAA 1997.
    """
    total_trust_inc = assessment.trust_accounting_income
    s95_net = assessment.section95_net_taxable_income
    shares: List[BeneficiaryTaxShare] = []

    if total_trust_inc <= Decimal("0.00") or not assessment.beneficiaries:
        return shares

    implied: list[Decimal] = []
    for b in assessment.beneficiaries:
        if b.percentage_entitlement is not None:
            implied.append(b.percentage_entitlement)
        elif b.fixed_entitlement_amount is not None:
            implied.append(
                ((b.fixed_entitlement_amount / total_trust_inc) * Decimal("100.00")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            )
        else:
            raise ValueError(
                f"{b.beneficiary_name} has neither a percentage nor a fixed entitlement"
            )
    total_pct = sum(implied, Decimal("0.00"))
    if abs(total_pct - Decimal("100.00")) > Decimal("0.01"):
        raise ValueError(
            f"beneficiary entitlements sum to {total_pct}%, not 100%"
        )

    # Calculate base income proportions
    for b in assessment.beneficiaries:
        if b.percentage_entitlement is not None:
            entitlement_dollar = (total_trust_inc * (b.percentage_entitlement / Decimal("100.00"))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            pct = b.percentage_entitlement
        elif b.fixed_entitlement_amount is not None:
            entitlement_dollar = b.fixed_entitlement_amount
            pct = ((entitlement_dollar / total_trust_inc) * Decimal("100.00")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            entitlement_dollar = Decimal("0.00")
            pct = Decimal("0.00")

        # Proportionate share of s 95 net income
        s95_share = (s95_net * (pct / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Franking credit share attached
        if assessment.franked_dividends > Decimal("0.00") and b.specifically_streamed_franked_dividends > Decimal("0.00"):
            frank_ratio = b.specifically_streamed_franked_dividends / assessment.franked_dividends
            fc_share = (assessment.franking_credits * frank_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            fc_share = (assessment.franking_credits * (pct / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if b.is_under_legal_disability:
            section_ref = "s 98 ITAA 1936 (Trustee assessed on behalf of beneficiary under legal disability)"
        else:
            section_ref = "s 97 ITAA 1936 (Beneficiary presently entitled and not under legal disability)"

        total_taxable = s95_share + fc_share

        shares.append(
            BeneficiaryTaxShare(
                beneficiary_name=b.beneficiary_name,
                trust_income_entitlement=entitlement_dollar,
                proportion_percentage=pct,
                section95_net_income_share=s95_share,
                streamed_capital_gains=b.specifically_streamed_capital_gains,
                streamed_franked_dividends=b.specifically_streamed_franked_dividends,
                franking_credit_grossup=fc_share,
                total_taxable_component=total_taxable,
                assessed_under_section=section_ref,
            )
        )

    return shares