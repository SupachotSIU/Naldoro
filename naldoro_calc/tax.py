"""ภาษีเงินได้บุคคลธรรมดาไทย และสิทธิลดหย่อนจากเบี้ยประกัน.

อ้างอิงเกณฑ์กรมสรรพากรสำหรับปีภาษี 2568 (2025). ก่อนใช้กับปีภาษีอื่น
ให้ตรวจสอบค่าคงที่ด้านล่างกับประกาศล่าสุดของกรมสรรพากรทุกครั้ง.

ข้อจำกัด: ไม่คำนวณภาษีวิธีที่ 2 (0.5% ของเงินได้อื่นนอกจากเงินเดือน),
ไม่ตรวจเพดานรายกองทุน (PVD/RMF/SSF/กอช.) — ผู้ใช้ต้องใส่ยอดที่ผ่านเพดานรายตัวแล้ว.
"""

from __future__ import annotations

import math

TAX_YEAR = "2568 (2025)"

BRACKETS = [
    (150_000, 0.00),
    (300_000, 0.05),
    (500_000, 0.10),
    (750_000, 0.15),
    (1_000_000, 0.20),
    (2_000_000, 0.25),
    (5_000_000, 0.30),
    (math.inf, 0.35),
]

PERSONAL_ALLOWANCE = 60_000
EMPLOYMENT_EXPENSE_RATE = 0.50
EMPLOYMENT_EXPENSE_CAP = 100_000

LIFE_POOL_CAP = 100_000          # เบี้ยประกันชีวิต + ประกันสุขภาพตนเอง รวมกันไม่เกิน
HEALTH_CAP = 25_000              # ประกันสุขภาพตนเอง
PARENTS_HEALTH_CAP = 15_000      # ประกันสุขภาพบิดามารดา
SPOUSE_LIFE_CAP = 10_000         # ประกันชีวิตคู่สมรสที่ไม่มีเงินได้
ANNUITY_RATE_CAP = 0.15          # ประกันบำนาญ 15% ของเงินได้พึงประเมิน
ANNUITY_AMOUNT_CAP = 200_000
RETIREMENT_GROUP_CAP = 500_000   # บำนาญ + PVD/กบข. + RMF + SSF + กอช. รวมกัน


def progressive_tax(net_income: float) -> float:
    """ภาษีตามอัตราก้าวหน้าจากเงินได้สุทธิ."""
    tax, lower = 0.0, 0.0
    for upper, rate in BRACKETS:
        if net_income <= lower:
            break
        tax += (min(net_income, upper) - lower) * rate
        lower = upper
    return tax


def marginal_rate(net_income: float) -> float:
    lower = 0.0
    for upper, rate in BRACKETS:
        if net_income <= upper:
            return rate if net_income > lower else 0.0
        lower = upper
    return BRACKETS[-1][1]


def insurance_deductions(
    *,
    assessable_income: float,
    life_premium: float = 0.0,
    health_premium: float = 0.0,
    parents_health_premium: float = 0.0,
    spouse_life_premium: float = 0.0,
    annuity_premium: float = 0.0,
    other_retirement_funds: float = 0.0,
) -> dict:
    """คำนวณยอดลดหย่อนจากเบี้ยประกันแต่ละประเภทตามเพดาน.

    ประกันบำนาญจะใช้สิทธิในโควตาประกันชีวิต 100,000 ที่เหลือก่อน (ซึ่งให้ผลลดหย่อนรวม
    สูงสุด) แล้วส่วนที่เหลือจึงใช้โควตา 15%/200,000 ซึ่งต้องรวมกับกองทุนเกษียณอื่น
    ไม่เกิน 500,000.
    """
    life = min(life_premium, LIFE_POOL_CAP)
    health = min(health_premium, HEALTH_CAP, LIFE_POOL_CAP - life)
    annuity_in_life_pool = min(annuity_premium, LIFE_POOL_CAP - life - health)
    annuity_own_cap = min(assessable_income * ANNUITY_RATE_CAP, ANNUITY_AMOUNT_CAP)
    annuity_own = min(annuity_premium - annuity_in_life_pool, annuity_own_cap)
    group_room = max(0.0, RETIREMENT_GROUP_CAP - other_retirement_funds)
    annuity_own = min(annuity_own, group_room)
    parents = min(parents_health_premium, PARENTS_HEALTH_CAP)
    spouse = min(spouse_life_premium, SPOUSE_LIFE_CAP)
    annuity_total = annuity_in_life_pool + annuity_own
    total = life + health + annuity_total + parents + spouse
    return {
        "life": life,
        "health": health,
        "annuity_in_life_pool": annuity_in_life_pool,
        "annuity_own_quota": annuity_own,
        "annuity_total": annuity_total,
        "parents_health": parents,
        "spouse_life": spouse,
        "total": total,
        "unused_premium_not_deductible": round(
            life_premium + health_premium + parents_health_premium
            + spouse_life_premium + annuity_premium - total,
            2,
        ),
    }


def tax_with_insurance(
    *,
    salary_income: float = 0.0,
    other_assessable_income: float = 0.0,
    other_income_expense_deduction: float = 0.0,
    other_deductions: float = 0.0,
    other_retirement_funds: float = 0.0,
    life_premium: float = 0.0,
    health_premium: float = 0.0,
    parents_health_premium: float = 0.0,
    spouse_life_premium: float = 0.0,
    annuity_premium: float = 0.0,
) -> dict:
    """เปรียบเทียบภาษีก่อน/หลังใช้สิทธิลดหย่อนเบี้ยประกัน.

    other_deductions       : ลดหย่อนอื่นที่ไม่ใช่ประกันและกองทุนเกษียณ (บุตร, ประกันสังคม,
                             ดอกเบี้ยบ้าน, บริจาค ฯลฯ) ไม่รวมลดหย่อนส่วนตัว 60,000
    other_retirement_funds : PVD/กบข. + RMF + SSF + กอช. (ผ่านเพดานรายตัวแล้ว)
    """
    for key, value in list(locals().items()):
        if value < 0:
            raise ValueError(f"{key} ต้องไม่ติดลบ")
    assessable = salary_income + other_assessable_income
    expense = min(salary_income * EMPLOYMENT_EXPENSE_RATE, EMPLOYMENT_EXPENSE_CAP)
    expense += other_income_expense_deduction
    retirement_funds = min(other_retirement_funds, RETIREMENT_GROUP_CAP)
    base_deductions = PERSONAL_ALLOWANCE + other_deductions + retirement_funds

    net_before = max(0.0, assessable - expense - base_deductions)
    ins = insurance_deductions(
        assessable_income=assessable,
        life_premium=life_premium,
        health_premium=health_premium,
        parents_health_premium=parents_health_premium,
        spouse_life_premium=spouse_life_premium,
        annuity_premium=annuity_premium,
        other_retirement_funds=retirement_funds,
    )
    net_after = max(0.0, net_before - ins["total"])
    tax_before = progressive_tax(net_before)
    tax_after = progressive_tax(net_after)
    total_premium = (
        life_premium + health_premium + parents_health_premium
        + spouse_life_premium + annuity_premium
    )
    saving = tax_before - tax_after
    return {
        "tax_year": TAX_YEAR,
        "assessable_income": assessable,
        "expense_deduction": expense,
        "net_income_before_insurance": net_before,
        "insurance_deductions": ins,
        "net_income_after_insurance": net_after,
        "tax_before_insurance": round(tax_before, 2),
        "tax_after_insurance": round(tax_after, 2),
        "tax_saving": round(saving, 2),
        "marginal_rate_before": marginal_rate(net_before),
        "total_premium": total_premium,
        "effective_premium_after_tax": round(total_premium - saving, 2),
    }
