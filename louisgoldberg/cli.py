"""
CLI interface for LouisGoldberg.
"""

import argparse
import sys
from decimal import Decimal
from .decimal_args import decimal_type
from .division6 import TrustIncomeAssessment, BeneficiaryEntitlement, calculate_proportionate_share
from .section100a import evaluate_section100a_risk
from .section99b import ForeignTrustReceipt, evaluate_section99b_liability


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="louisgoldberg",
        description="LouisGoldberg: Trust Distribution & Section 100A / 99B Compliance Engine",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: s100a-check
    s100a_parser = subparsers.add_parser("s100a-check", help="Evaluate Section 100A reimbursement agreement risk")
    s100a_parser.add_argument("--beneficiary", type=str, required=True, help="Beneficiary name")
    s100a_parser.add_argument("--amount", type=decimal_type, required=True, help="Distribution amount ($)")
    s100a_parser.add_argument("--adult-child", action="store_true", help="Beneficiary is an adult child")
    s100a_parser.add_argument("--retained-by-parents", action="store_true", help="Funds retained by parents without loan")
    s100a_parser.add_argument("--circular", action="store_true", help="Circular flow of funds present")
    received = s100a_parser.add_mutually_exclusive_group()
    received.add_argument("--received-funds", action="store_true", help="Beneficiary received and retained the funds")
    received.add_argument("--funds-not-received", action="store_true", help="Beneficiary did not receive the funds")

    # Command: s99b-check
    s99b_parser = subparsers.add_parser("s99b-check", help="Evaluate Section 99B foreign trust distribution")
    s99b_parser.add_argument("--beneficiary", type=str, required=True, help="Beneficiary name")
    s99b_parser.add_argument("--gross", type=decimal_type, required=True, help="Gross amount received AUD ($)")
    s99b_parser.add_argument("--corpus", type=decimal_type, default=Decimal("0.00"), help="Corpus / capital settlement ($)")

    args = parser.parse_args()

    if args.command == "s100a-check":
        res = evaluate_section100a_risk(
            beneficiary_name=args.beneficiary,
            distribution_amount=args.amount,
            beneficiary_is_adult_child=args.adult_child,
            funds_retained_by_parents_without_loan=args.retained_by_parents,
            circular_flow_of_funds=args.circular,
            beneficiary_actually_received_funds=(
                True if args.received_funds else False if args.funds_not_received else None
            ),
        )
        print("=" * 60)
        print(f"Section 100A Risk Evaluation — {res.beneficiary_name}")
        print("=" * 60)
        print(f"Distribution Amount:     ${res.distribution_amount:,.2f}")
        print(f"Risk Zone:               {res.risk_zone.value}")
        print(f"Ordinary Family Dealing: {res.is_ordinary_family_dealing}")
        if res.risk_factors_identified:
            print(f"Risk Factors:            {', '.join(res.risk_factors_identified)}")
        print(f"Consequence:             {res.tax_consequence_summary}")
        print("=" * 60)
        return 0

    elif args.command == "s99b-check":
        receipt = ForeignTrustReceipt(
            beneficiary_name=args.beneficiary,
            gross_amount_received_aud=args.gross,
            corpus_amount_aud=args.corpus,
        )
        res = evaluate_section99b_liability(receipt)
        print("=" * 60)
        print(f"Section 99B Assessment — {res.beneficiary_name}")
        print("=" * 60)
        print(f"Gross Receipt:           ${res.gross_receipt:,.2f}")
        print(f"Corpus Exemption:        ${res.corpus_exemption:,.2f}")
        print(f"Assessable under s99B:   ${res.assessable_income_under_s99b:,.2f}")
        print(f"Basis:                   {res.statutory_basis}")
        print("=" * 60)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())