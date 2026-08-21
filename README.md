# Solomon's Sword

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ITAA 1936](https://img.shields.io/badge/Legislation-ITAA%201936%20Division%206-002B49)](https://www.legislation.gov.au/Details/C2024C00036)

**Trust distribution allocation, Section 100A / 99B risk evaluation, and Division 6 ITAA 1936 compliance for Australian trusts.**

Named for the judgement of Solomon, where the threat of dividing the child in proportion is what reveals who the true claimant is. This library does both halves of that: Division 6 allocates trust income by proportionate entitlement following *Bamford*, and Section 100A asks who actually ended up with the benefit.

Installed as the `solomons-sword` distribution, imported as `solomonssword`, and run as `trust-allocate`.

---

## 🔍 Core Features

- **Division 6 Proportionate Allocation (*Bamford v FCT*)**: Calculates present entitlement proportions and allocates *s 95(1) ITAA 1936* taxable net income, franking credits, and streamed capital gains (*Subdivision 115-220*) / franked dividends (*Subdivision 207-B*).
- **Section 100A Reimbursement Agreement Matrix**: Evaluates arrangements against **ATO PCG 2022/2** risk zones (Green / Blue / Red), ordinary family dealing exclusions (*s 100A(13)*), and circular flow triggers.
- **Section 99B Foreign Trust Receipt Assessment**: Computes assessable amounts under *s 99B(1)* after corpus exemptions (*s 99B(2)(a)*) and prior-taxed income.
- **Trust Resolution 30 June Schedule Verifier**: Verifies timing, deed powers, execution, and percentage completeness.

---

## 🚀 Quickstart

### CLI Usage
```bash
# Evaluate Section 100A risk zone
trust-allocate s100a-check --beneficiary "Adult Child" --amount 40000 --adult-child --retained-by-parents

# Assess Section 99B receipt from foreign trust with corpus deduction
trust-allocate s99b-check --beneficiary "Jane Doe" --gross 150000 --corpus 50000
```

---

## ⚖️ License
MIT License. Created by Ryan Duguid.