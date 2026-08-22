import pytest
from datetime import date
from decimal import Decimal
from louisgoldberg.division6 import TrustIncomeAssessment, BeneficiaryEntitlement, calculate_proportionate_share
from louisgoldberg.section100a import evaluate_section100a_risk, Section100ARiskZone
from louisgoldberg.section99b import ForeignTrustReceipt, evaluate_section99b_liability
from louisgoldberg.trust_resolution import TrustResolutionSchedule, validate_trust_resolution

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
    # s 207-35 already includes the gross-up in the trust's s 95 net income, so
    # the share is the net income share alone and the credit is reported
    # separately for the s 207-45 offset.
    assert shares[0].total_taxable_component == Decimal("60000.00")

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
    # PCG 2022/2's green zone is a compliance-resourcing stance; it does not
    # decide the s 100A(13) ordinary family dealing exception.
    assert green_res.is_ordinary_family_dealing is None

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

def test_section100a_does_not_default_to_green():
    result = evaluate_section100a_risk(
        beneficiary_name="Unspecified",
        distribution_amount=Decimal("10000.00"),
    )
    assert result.risk_zone == Section100ARiskZone.OUTSIDE_GREEN
    assert result.is_ordinary_family_dealing is False


def test_division6_rejects_percentages_that_do_not_total_100():
    assessment = TrustIncomeAssessment(
        financial_year=2025,
        trust_name="Overallocated Trust",
        trust_accounting_income=Decimal("100000.00"),
        section95_net_taxable_income=Decimal("100000.00"),
        beneficiaries=[
            BeneficiaryEntitlement(beneficiary_name="A", percentage_entitlement=Decimal("60.00")),
            BeneficiaryEntitlement(beneficiary_name="B", percentage_entitlement=Decimal("60.00")),
        ],
    )
    try:
        calculate_proportionate_share(assessment)
    except ValueError as exc:
        assert "not 100" in str(exc)
    else:
        raise AssertionError("over-allocation must be refused")


def test_trust_resolution_rejects_zero_percent_and_missing_deed_facts():
    schedule = TrustResolutionSchedule(
        trust_name="Smith Family Trust",
        financial_year=2025,
        resolution_date=date(2025, 6, 25),
        is_signed_by_trustee=True,
        streaming_powers_in_deed=False,
        default_beneficiary_clause_exists=False,
        allocated_percentages_total=Decimal("0.00"),
    )
    is_valid, issues = validate_trust_resolution(schedule)
    assert is_valid is False
    assert any("100%" in issue for issue in issues)
    assert any("streaming" in issue for issue in issues)
    assert any("default beneficiary" in issue for issue in issues)


def test_streamed_amounts_are_refused_not_misallocated():
    # Streaming previously allocated 150% of the franking credit pool.
    t = TrustIncomeAssessment(
        financial_year=2025, trust_name="T",
        trust_accounting_income=Decimal("100000.00"),
        section95_net_taxable_income=Decimal("130000.00"),
        franked_dividends=Decimal("70000.00"), franking_credits=Decimal("30000.00"),
        beneficiaries=[
            BeneficiaryEntitlement("A", percentage_entitlement=Decimal("50.00"),
                                   specifically_streamed_franked_dividends=Decimal("70000.00")),
            BeneficiaryEntitlement("B", percentage_entitlement=Decimal("50.00")),
        ],
    )
    with pytest.raises(ValueError, match="Division 6E"):
        calculate_proportionate_share(t)


def test_shares_reconcile_to_the_net_income():
    t = TrustIncomeAssessment(
        financial_year=2025, trust_name="T",
        trust_accounting_income=Decimal("100000.00"),
        section95_net_taxable_income=Decimal("100000.00"),
        beneficiaries=[
            BeneficiaryEntitlement("A", fixed_entitlement_amount=Decimal("33333.33")),
            BeneficiaryEntitlement("B", fixed_entitlement_amount=Decimal("33333.33")),
            BeneficiaryEntitlement("C", fixed_entitlement_amount=Decimal("33333.34")),
        ],
    )
    shares = calculate_proportionate_share(t)
    assert sum(s.section95_net_income_share for s in shares) == Decimal("100000.00")


def test_franking_credits_are_not_added_on_top_of_the_net_income_share():
    # s 207-35 already includes the gross-up in the trust's s 95 net income.
    t = TrustIncomeAssessment(
        financial_year=2025, trust_name="T",
        trust_accounting_income=Decimal("100000.00"),
        section95_net_taxable_income=Decimal("130000.00"),
        franked_dividends=Decimal("70000.00"), franking_credits=Decimal("30000.00"),
        beneficiaries=[BeneficiaryEntitlement("A", percentage_entitlement=Decimal("100.00"))],
    )
    share = calculate_proportionate_share(t)[0]
    assert share.section95_net_income_share == Decimal("130000.00")
    assert share.franking_credit_grossup == Decimal("30000.00")
    assert share.total_taxable_component == Decimal("130000.00")


def test_unmodelled_cases_fail_closed():
    base = dict(financial_year=2025, trust_name="T",
                trust_accounting_income=Decimal("100000.00"),
                section95_net_taxable_income=Decimal("100000.00"))
    with pytest.raises(ValueError, match="s 99 or s 99A"):
        calculate_proportionate_share(TrustIncomeAssessment(beneficiaries=[], **base))
    with pytest.raises(ValueError, match="s 99 or s 99A"):
        calculate_proportionate_share(TrustIncomeAssessment(
            beneficiaries=[BeneficiaryEntitlement("A", percentage_entitlement=Decimal("100.00"))],
            financial_year=2025, trust_name="T",
            trust_accounting_income=Decimal("0.00"),
            section95_net_taxable_income=Decimal("50000.00")))
    with pytest.raises(ValueError, match="non-resident"):
        calculate_proportionate_share(TrustIncomeAssessment(
            beneficiaries=[BeneficiaryEntitlement("NR", is_resident=False, percentage_entitlement=Decimal("100.00"))],
            **base))
    with pytest.raises(ValueError, match="at most 100 per cent"):
        calculate_proportionate_share(TrustIncomeAssessment(
            beneficiaries=[BeneficiaryEntitlement("A", percentage_entitlement=Decimal("150.00")),
                           BeneficiaryEntitlement("B", percentage_entitlement=Decimal("-50.00"))],
            **base))


def test_minor_beneficiary_is_assessed_to_the_trustee():
    t = TrustIncomeAssessment(
        financial_year=2025, trust_name="T",
        trust_accounting_income=Decimal("100000.00"),
        section95_net_taxable_income=Decimal("100000.00"),
        beneficiaries=[BeneficiaryEntitlement("Minor", is_under_legal_disability=True,
                                              percentage_entitlement=Decimal("100.00"))],
    )
    assert "s 98" in calculate_proportionate_share(t)[0].assessed_under_section


def test_s99b_corpus_proviso_and_residency():
    from louisgoldberg.section99b import ForeignTrustReceipt, evaluate_section99b_liability
    r = evaluate_section99b_liability(ForeignTrustReceipt(
        "A", Decimal("100000.00"), corpus_amount_aud=Decimal("20000.00"),
        corpus_attributable_to_notional_assessable_income_aud=Decimal("5000.00")))
    assert r.corpus_exemption == Decimal("15000.00")
    assert r.assessable_income_under_s99b == Decimal("85000.00")
    with pytest.raises(ValueError, match="resident"):
        evaluate_section99b_liability(ForeignTrustReceipt(
            "B", Decimal("100000.00"), beneficiary_was_resident_during_year=False))
    with pytest.raises(ValueError, match="non-negative"):
        evaluate_section99b_liability(ForeignTrustReceipt("C", Decimal("100000.00"),
                                                          corpus_amount_aud=Decimal("-1.00")))


def test_green_zone_does_not_claim_the_ordinary_family_dealing_exception():
    from louisgoldberg.section100a import evaluate_section100a_risk, Section100ARiskZone
    res = evaluate_section100a_risk(
        beneficiary_name="A", distribution_amount=Decimal("50000.00"),
        beneficiary_actually_received_funds=True)
    assert res.risk_zone == Section100ARiskZone.GREEN
    assert res.is_ordinary_family_dealing is None
    assert "not a determination" in res.tax_consequence_summary
