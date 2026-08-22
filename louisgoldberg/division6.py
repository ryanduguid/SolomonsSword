"""
Division 6 ITAA 1936 trust net income allocation on the proportionate approach
from Commissioner of Taxation v Bamford [2010] HCA 10; (2010) 240 CLR 481.

Scope: this module allocates s 95 net income by each beneficiary's share of the
income of the trust estate. It does NOT model the Division 6E streaming
carve-out, s 98(2A)/(3) non-resident trustee assessment, or s 99/99A trustee
assessment, and refuses inputs that would engage them rather than returning a
number the model cannot stand behind. Outputs are review aids, not advice.
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
    proportionate approach (Commissioner of Taxation v Bamford [2010] HCA 10).

    Refuses, rather than guesses, the cases this model does not implement:
    nil income of the trust estate, no presently entitled beneficiary,
    non-resident beneficiaries, specifically streamed capital gains or franked
    dividends (Division 6E with Subdivisions 115-C and 207-B), and entitlements
    outside the 0 to 100 per cent range.
    """
    total_trust_inc = assessment.trust_accounting_income
    s95_net = assessment.section95_net_taxable_income
    shares: List[BeneficiaryTaxShare] = []

    if not assessment.beneficiaries:
        raise ValueError(
            "no presently entitled beneficiary: the trustee is assessed under "
            "s 99 or s 99A ITAA 1936, which this module does not compute"
        )
    if total_trust_inc <= Decimal("0.00"):
        raise ValueError(
            "income of the trust estate is nil or negative: with no income to be "
            "presently entitled to, the proportionate approach cannot allocate the "
            "s 95 net income and the trustee is assessed under s 99 or s 99A"
        )
    for b in assessment.beneficiaries:
        if not b.is_resident:
            raise ValueError(
                f"{b.beneficiary_name} is a non-resident: the trustee is assessed "
                "under s 98(2A) or s 98(3) ITAA 1936, which this module does not compute"
            )
        if b.specifically_streamed_capital_gains > Decimal("0.00") or b.specifically_streamed_franked_dividends > Decimal("0.00"):
            raise ValueError(
                f"{b.beneficiary_name} has specifically streamed amounts: the Division 6E "
                "carve-out with Subdivisions 115-C and 207-B is not implemented, so the "
                "proportionate allocation would be wrong"
            )

    # Unrounded ratios: quantising each share's percentage before multiplying it
    # into the s 95 pool loses cents that never reach any beneficiary.
    ratios: list[Decimal] = []
    implied: list[Decimal] = []
    for b in assessment.beneficiaries:
        if b.percentage_entitlement is not None:
            if not (Decimal("0.00") < b.percentage_entitlement <= Decimal("100.00")):
                raise ValueError(
                    f"{b.beneficiary_name} has a {b.percentage_entitlement}% entitlement; "
                    "a present entitlement must be above 0 and at most 100 per cent"
                )
            ratios.append(b.percentage_entitlement / Decimal("100.00"))
            implied.append(b.percentage_entitlement)
        elif b.fixed_entitlement_amount is not None:
            if b.fixed_entitlement_amount <= Decimal("0.00"):
                raise ValueError(
                    f"{b.beneficiary_name} has a fixed entitlement of "
                    f"{b.fixed_entitlement_amount}; it must be positive"
                )
            ratios.append(b.fixed_entitlement_amount / total_trust_inc)
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

    # Allocate on the unrounded ratios, then hand the rounding residual to the
    # largest share so the allocated total reconciles to the s 95 net income.
    residual = s95_net.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    for b, ratio, pct in zip(assessment.beneficiaries, ratios, implied):
        entitlement_dollar = (total_trust_inc * ratio).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Proportionate share of s 95 net income (Bamford).
        s95_share = (s95_net * ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        residual -= s95_share

        # Franking credits ride the same proportionate share. Streamed
        # dividends are refused above, so there is one allocation basis here.
        fc_share = (assessment.franking_credits * ratio).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if b.is_under_legal_disability:
            section_ref = "s 98 ITAA 1936 (Trustee assessed on behalf of beneficiary under legal disability)"
        else:
            section_ref = "s 97 ITAA 1936 (Beneficiary presently entitled and not under legal disability)"

        # The franking credit gross-up is already inside the s 95 net income
        # (s 207-35 ITAA 1997), so it is reported for the s 207-45 offset and
        # never added to the share again.
        total_taxable = s95_share

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

    if residual and shares:
        largest = max(range(len(shares)), key=lambda i: shares[i].section95_net_income_share)
        adjusted = shares[largest]
        shares[largest] = BeneficiaryTaxShare(
            beneficiary_name=adjusted.beneficiary_name,
            trust_income_entitlement=adjusted.trust_income_entitlement,
            proportion_percentage=adjusted.proportion_percentage,
            section95_net_income_share=adjusted.section95_net_income_share + residual,
            streamed_capital_gains=adjusted.streamed_capital_gains,
            streamed_franked_dividends=adjusted.streamed_franked_dividends,
            franking_credit_grossup=adjusted.franking_credit_grossup,
            total_taxable_component=adjusted.total_taxable_component + residual,
            assessed_under_section=adjusted.assessed_under_section,
        )

    return shares