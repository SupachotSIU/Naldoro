import json
import subprocess
import sys
import unittest
from pathlib import Path

from naldoro_calc import (
    analyze_policy,
    compare_plans,
    human_life_value,
    needs_analysis,
    retirement_plan,
    tax_with_insurance,
)
from naldoro_calc.finance import irr, pv_growing_annuity
from naldoro_calc.tax import insurance_deductions, progressive_tax

ROOT = Path(__file__).resolve().parent.parent


class FinanceTest(unittest.TestCase):
    def test_pv_ordinary_annuity(self):
        self.assertAlmostEqual(pv_growing_annuity(100, 0.05, 0, 2, due=False), 185.941, 3)

    def test_pv_growth_equals_rate(self):
        self.assertAlmostEqual(pv_growing_annuity(100, 0.03, 0.03, 10, due=True), 1000)

    def test_irr_simple(self):
        self.assertAlmostEqual(irr([-100, 110]), 0.10, 6)

    def test_irr_none_without_sign_change(self):
        self.assertIsNone(irr([-100, -10]))


class NeedsTest(unittest.TestCase):
    def test_needs_gap(self):
        r = needs_analysis(
            annual_family_expense=300_000, years_of_support=10,
            inflation=0.03, discount_rate=0.03,
            debts=1_000_000, education_fund=500_000,
            existing_life_cover=1_000_000, liquid_assets=500_000,
        )
        self.assertEqual(r["income_replacement_need"], 3_000_000)
        self.assertEqual(r["total_need"], 4_500_000)
        self.assertEqual(r["additional_cover_needed"], 3_000_000)

    def test_gap_never_negative(self):
        r = needs_analysis(annual_family_expense=0, years_of_support=0, liquid_assets=10)
        self.assertEqual(r["additional_cover_needed"], 0)

    def test_hlv(self):
        r = human_life_value(
            annual_income=500_000, personal_consumption_ratio=0.3,
            years_to_retirement=2, income_growth=0, discount_rate=0.05,
        )
        self.assertAlmostEqual(r["human_life_value"], 350_000 * 1.85941, delta=1)

    def test_rejects_negative(self):
        with self.assertRaises(ValueError):
            needs_analysis(annual_family_expense=-1, years_of_support=5)


class TaxTest(unittest.TestCase):
    def test_brackets(self):
        self.assertEqual(progressive_tax(150_000), 0)
        self.assertEqual(progressive_tax(300_000), 7_500)
        self.assertEqual(progressive_tax(1_040_000), 125_000)

    def test_life_premium_saving(self):
        r = tax_with_insurance(salary_income=1_200_000, life_premium=100_000)
        self.assertEqual(r["tax_before_insurance"], 125_000)
        self.assertEqual(r["tax_after_insurance"], 103_000)
        self.assertEqual(r["tax_saving"], 22_000)
        self.assertEqual(r["effective_premium_after_tax"], 78_000)

    def test_health_shares_life_pool(self):
        d = insurance_deductions(
            assessable_income=1_200_000, life_premium=80_000, health_premium=25_000
        )
        self.assertEqual(d["health"], 20_000)
        self.assertEqual(d["unused_premium_not_deductible"], 5_000)

    def test_annuity_uses_life_pool_first(self):
        d = insurance_deductions(
            assessable_income=1_200_000, life_premium=30_000, annuity_premium=250_000
        )
        self.assertEqual(d["annuity_in_life_pool"], 70_000)
        self.assertEqual(d["annuity_own_quota"], 180_000)
        self.assertEqual(d["annuity_total"], 250_000)

    def test_annuity_limited_by_retirement_group(self):
        d = insurance_deductions(
            assessable_income=1_200_000, life_premium=100_000,
            annuity_premium=50_000, other_retirement_funds=480_000,
        )
        self.assertEqual(d["annuity_own_quota"], 20_000)


class RetirementTest(unittest.TestCase):
    def test_zero_rates(self):
        r = retirement_plan(
            current_age=30, retirement_age=60, life_expectancy=80,
            monthly_expense_today=10_000, inflation=0,
            return_before_retirement=0, return_after_retirement=0,
        )
        self.assertEqual(r["corpus_needed_at_retirement"], 2_400_000)
        self.assertAlmostEqual(r["monthly_saving_required"], 6_666.67, 2)

    def test_annuity_reduces_gap(self):
        base = dict(
            current_age=30, retirement_age=60, life_expectancy=80,
            monthly_expense_today=10_000, inflation=0,
            return_before_retirement=0, return_after_retirement=0,
        )
        r = retirement_plan(**base, annuity_annual_payout=60_000, annuity_payout_years=20)
        self.assertEqual(r["gap_at_retirement"], 1_200_000)

    def test_invalid_ages(self):
        with self.assertRaises(ValueError):
            retirement_plan(current_age=60, retirement_age=55, life_expectancy=80,
                            monthly_expense_today=1)


class PolicyTest(unittest.TestCase):
    def test_irr_and_tax_benefit(self):
        r = analyze_policy(
            annual_premium=100_000, premium_years=1,
            benefits=[{"year": 1, "amount": 110_000}], tax_rate=0.2,
        )
        self.assertAlmostEqual(r["irr"], 0.10, 5)
        self.assertAlmostEqual(r["irr_after_tax_benefit"], 0.375, 5)

    def test_compare_sorted(self):
        r = compare_plans(plans=[
            {"name": "A", "annual_premium": 100, "premium_years": 1,
             "benefits": [{"year": 1, "amount": 102}]},
            {"name": "B", "annual_premium": 100, "premium_years": 1,
             "benefits": [{"year": 1, "amount": 105}]},
        ])
        self.assertEqual([p["name"] for p in r["plans"]], ["B", "A"])


class CliTest(unittest.TestCase):
    def test_examples_run(self):
        commands = {
            "needs": "needs.json", "hlv": "hlv.json", "tax": "tax.json",
            "retirement": "retirement.json", "policy": "policy.json",
            "compare": "compare.json",
        }
        for command, filename in commands.items():
            with self.subTest(command=command):
                out = subprocess.run(
                    [sys.executable, "-m", "naldoro_calc", command,
                     str(ROOT / "examples" / filename)],
                    capture_output=True, text=True, cwd=ROOT, check=True,
                )
                self.assertIsInstance(json.loads(out.stdout), dict)


if __name__ == "__main__":
    unittest.main()
