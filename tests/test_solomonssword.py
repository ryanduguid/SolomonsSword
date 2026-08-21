from datetime import date
from decimal import Decimal
from solomonssword.division6 import TrustIncomeAssessment, BeneficiaryEntitlement, calculate_proportionate_share
from solomonssword.section100a import evaluate_section100a_risk, Section100ARiskZone
from solomonssword.section99b import ForeignTrustReceipt, evaluate_section99b_liability
from solomonssword.trust_resolution import TrustResolutionSchedule, validate_trust_resolution

def test_division6_proportionate_approach():
    # Trust with $100k accounting income, $120k s95 taxable net income (due to non-deductible adjustments)
    assessment = TrustIncomeAssessment(
        financial_year=2025,
        trust_name="Smith Family Trust",
        trust_accounting_income=Decimal("100000.00"),
        section95_net_taxable_income=Decimal("120000.00"),
        franking_credits=Decimal("15000.00"),
        beneficiaries=[
            BeneficiaryEntitlement(
                beneficiary_name="Alice Smith",
                percentage_entitlement=Decimal("50.00"),
            ),
            BeneficiaryEntitlement(
                beneficiary_name="Bob Smith",
                percentage_entitlement=Decimal("50.00"),
            ),
        ],
    )

    shares = calculate_proportionate_share(assessment)
    assert len(shares) == 2
    # 50% of $120,000 = $60,000
    assert shares[0].section95_net_income_share == Decimal("60000.00")
    # 50% of $15,000 = $7,500
    assert shares[0].franking_credit_grossup == Decimal("7500.00")
    assert shares[0].total_taxable_component == Decimal("67500.00")

def test_section100a_risk_zones():
    # Red Zone: Adult child distribution retained by parents without loan
    red_res = evaluate_section100a_risk(
        beneficiary_name="Charlie (Adult Child)",
        distribution_amount=Decimal("45000.00"),
        beneficiary_is_adult_child=True,
        funds_retained_by_parents_without_loan=True,
    )
    assert red_res.risk_zone == Section100ARiskZone.RED
    assert red_res.is_ordinary_family_dealing is False

    # Green Zone: Beneficiary receives and retains funds
    green_res = evaluate_section100a_risk(
        beneficiary_name="David (Adult Child)",
        distribution_amount=Decimal("30000.00"),
        beneficiary_is_adult_child=True,
        funds_retained_by_parents_without_loan=False,
        beneficiary_actually_received_funds=True,
    )
    assert green_res.risk_zone == Section100ARiskZone.GREEN
    assert green_res.is_ordinary_family_dealing is True

def test_section99b_corpus_exemption():
    # $100k foreign trust distribution, $40k is original settled corpus
    receipt = ForeignTrustReceipt(
        beneficiary_name="Emma Resident",
        gross_amount_received_aud=Decimal("100000.00"),
        corpus_amount_aud=Decimal("40000.00"),
    )
    res = evaluate_section99b_liability(receipt)
    assert res.corpus_exemption == Decimal("40000.00")
    assert res.assessable_income_under_s99b == Decimal("60000.00")

def test_trust_resolution_validation():
    # Valid timely resolution
    valid_sched = TrustResolutionSchedule(
        trust_name="Smith Family Trust",
        financial_year=2025,
        resolution_date=date(2025, 6, 25),
        is_signed_by_trustee=True,
        streaming_powers_in_deed=True,
        default_beneficiary_clause_exists=True,
        allocated_percentages_total=Decimal("100.00"),
    )
    is_valid, issues = validate_trust_resolution(valid_sched)
    assert is_valid is True
    assert len(issues) == 0

    # Late resolution after 30 June
    late_sched = TrustResolutionSchedule(
        trust_name="Smith Family Trust",
        financial_year=2025,
        resolution_date=date(2025, 7, 5),
        is_signed_by_trustee=True,
        streaming_powers_in_deed=True,
        default_beneficiary_clause_exists=True,
        allocated_percentages_total=Decimal("100.00"),
    )
    is_valid_late, issues_late = validate_trust_resolution(late_sched)
    assert is_valid_late is False
    assert any("after 30 June" in issue for issue in issues_late)