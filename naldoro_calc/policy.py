"""วิเคราะห์ผลตอบแทนกรมธรรม์ (IRR) และเปรียบเทียบหลายแบบประกัน.

แบบจำลองเวลา: ปีกรมธรรม์ที่ 1 เริ่มที่ t=0
  - เบี้ยประกันจ่ายต้นปีกรมธรรม์ -> ปีที่ k จ่ายที่ t = k-1
  - เงินคืน/เงินครบสัญญา "สิ้นปีกรมธรรม์ที่ y" -> เกิดที่ t = y
"""

from __future__ import annotations

from .finance import irr


def policy_cashflows(
    *,
    annual_premium: float,
    premium_years: int,
    benefits: list[dict],
    tax_rate: float = 0.0,
    deductible_per_year: float | None = None,
) -> list[float]:
    """สร้างกระแสเงินรายปี (ลบ = จ่ายเบี้ย, บวก = รับเงิน).

    benefits            : [{"year": 5, "amount": 10000}, ...] จ่าย ณ สิ้นปีกรมธรรม์
    tax_rate            : อัตราภาษีส่วนเพิ่ม ใช้ลดต้นทุนเบี้ยจากสิทธิลดหย่อน
    deductible_per_year : เบี้ยที่ลดหย่อนได้ต่อปี (ค่าเริ่มต้น = เบี้ยทั้งหมด)
    """
    if annual_premium < 0 or premium_years < 0:
        raise ValueError("annual_premium และ premium_years ต้องไม่ติดลบ")
    if deductible_per_year is None:
        deductible_per_year = annual_premium
    tax_saving = min(annual_premium, deductible_per_year) * tax_rate
    last_benefit_year = max((int(b["year"]) for b in benefits), default=0)
    length = max(premium_years, last_benefit_year + 1)
    flows = [0.0] * length
    for k in range(premium_years):
        flows[k] -= annual_premium - tax_saving
    for b in benefits:
        year = int(b["year"])
        if year < 1:
            raise ValueError("ปีของผลประโยชน์ต้องเริ่มที่ 1")
        flows[year] += float(b["amount"])
    return flows


def analyze_policy(
    *,
    name: str = "plan",
    annual_premium: float,
    premium_years: int,
    benefits: list[dict],
    sum_assured: float = 0.0,
    coverage_years: int | None = None,
    tax_rate: float = 0.0,
    deductible_per_year: float | None = None,
) -> dict:
    """สรุปตัวเลขสำคัญของกรมธรรม์ 1 แบบ."""
    flows = policy_cashflows(
        annual_premium=annual_premium,
        premium_years=premium_years,
        benefits=benefits,
    )
    total_premium = annual_premium * premium_years
    total_benefit = sum(float(b["amount"]) for b in benefits)
    rate = irr(flows)
    result = {
        "name": name,
        "total_premium": round(total_premium, 2),
        "total_benefit": round(total_benefit, 2),
        "net_gain": round(total_benefit - total_premium, 2),
        "irr": None if rate is None else round(rate, 6),
        "sum_assured": sum_assured,
        "coverage_years": coverage_years,
        "sum_assured_per_annual_premium": (
            round(sum_assured / annual_premium, 2) if annual_premium else None
        ),
        "cashflows": [round(x, 2) for x in flows],
    }
    if tax_rate:
        flows_tax = policy_cashflows(
            annual_premium=annual_premium,
            premium_years=premium_years,
            benefits=benefits,
            tax_rate=tax_rate,
            deductible_per_year=deductible_per_year,
        )
        rate_tax = irr(flows_tax)
        result["tax_rate"] = tax_rate
        result["irr_after_tax_benefit"] = None if rate_tax is None else round(rate_tax, 6)
    return result


def compare_plans(*, plans: list[dict], tax_rate: float = 0.0) -> dict:
    """วิเคราะห์หลายแบบประกันแล้วเรียงตาม IRR (หลังสิทธิภาษีถ้ามี)."""
    results = []
    for plan in plans:
        params = dict(plan)
        params.setdefault("tax_rate", tax_rate)
        results.append(analyze_policy(**params))
    key = "irr_after_tax_benefit" if tax_rate else "irr"
    results.sort(key=lambda r: (r.get(key) is None, -(r.get(key) or 0)))
    return {"ranked_by": key, "plans": results}
