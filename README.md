# Solomon's Sword

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![tests](https://github.com/ryanduguid/SolomonsSword/actions/workflows/ci.yml/badge.svg)](https://github.com/ryanduguid/SolomonsSword/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ITAA 1936](https://img.shields.io/badge/Legislation-ITAA%201936%20Division%206-002B49)](https://www.legislation.gov.au/C1936A00027/latest/text)

**Trust distribution allocation, Section 100A / 99B risk evaluation, and Division 6 ITAA 1936 review helpers for Australian trusts.**

The repository name is the public project identity; the `louisgoldberg` distribution and `louisgoldberg` command remain compatibility identifiers.

Named for the judgement of Solomon, where the threat of dividing the child in proportion is what reveals who the true claimant is. Division 6 allocates trust income by proportionate entitlement following *Bamford*; Section 100A asks who actually ended up with the benefit. The name is a tribute only.

---

## Core Features

- **Division 6 Proportionate Allocation (*Bamford v FCT*)**: Calculates present entitlement proportions and allocates *s 95(1) ITAA 1936* taxable net income, franking credits, and streamed capital gains (*Subdivision 115-C*, including s 115-220) / franked dividends (*Subdivision 207-B*).
- **Section 100A Reimbursement Agreement Matrix**: Classifies supplied facts against **ATO PCG 2022/2** as Green, Red, or outside those zones. The final guideline has white, green and red; the draft blue zone did not survive. White zone (income years ending before 1 July 2014) is out of scope because the function does not take an income year.
- **Section 99B Foreign Trust Receipt Assessment**: Computes assessable amounts under *s 99B(1)* after corpus exemptions (*s 99B(2)(a)*) and prior-taxed income.
- **Trust Resolution 30 June Schedule Verifier**: Checks timing, deed-power and percentage-completeness facts the caller supplies.

---

## Quickstart

### CLI Usage
```bash
# Evaluate Section 100A risk zone
louisgoldberg s100a-check --beneficiary "Adult Child" --amount 40000 --adult-child --retained-by-parents

# Assess Section 99B receipt from foreign trust with corpus deduction
louisgoldberg s99b-check --beneficiary "Jane Doe" --gross 150000 --corpus 50000
```

---

## Statutory Ground Truth & Test Harness

All allocation and threshold algorithms use exact `decimal.Decimal` calculations to prevent rounding discrepancies in trust tax schedules.

| Statutory Domain | Primary Authority | What the code actually does |
| :--- | :--- | :--- |
| **Proportionate Entitlement** | *ITAA 1936* s 95, s 97 (*Bamford v FCT*) | `Beneficiary Share = (Accounting Entitlement / Total Accounting Income) * s95 Net Income`. |
| **Section 100A Risk Matrix** | *ITAA 1936* s 100A, *ATO PCG 2022/2* | Returns GREEN, RED or OUTSIDE_GREEN from the supplied flags. It does not decide the white zone. |
| **Foreign Trust Distributions** | *ITAA 1936* s 99B(1), s 99B(2)(a) | Subtracts settled corpus and previously taxed income prior to assessable inclusion. |
| **Trust Resolution Timing** | Caller-supplied deed and execution facts | Refuses incomplete percentages and missing deed facts. This is not a substitute for current ATO guidance. |

### Automated Test Suite
- Run the suite: `pytest tests/`
- The suite covers proportionate streaming, Section 100A zones the engine implements, Section 99B corpus deductions, and resolution gates. Do not treat a badge as a live coverage certificate.

---

## Licence
MIT License. Created by Ryan Duguid.
