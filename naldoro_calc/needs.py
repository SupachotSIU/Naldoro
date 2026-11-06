"""คำนวณทุนประกันชีวิตที่ควรมี (Needs Approach และ Human Life Value)."""

from __future__ import annotations

from .finance import pv_growing_annuity


def needs_analysis(
    *,
    annual_family_expense: float,
    years_of_support: int,
    inflation: float = 0.03,
    discount_rate: float = 0.03,
    debts: float = 0.0,
    education_fund: float = 0.0,
    final_expenses: float = 0.0,
    emergency_fund: float = 0.0,
    other_needs: float = 0.0,
    existing_life_cover: float = 0.0,
    liquid_assets: float = 0.0,
) -> dict:
    """ทุนประกันที่ครอบครัวต้องการหากผู้หารายได้เสียชีวิตวันนี้.

    annual_family_expense : ค่าใช้จ่ายครอบครัวต่อปีที่ต้องทดแทน (มูลค่าวันนี้)
    years_of_support      : จำนวนปีที่ต้องดูแล
    discount_rate         : ผลตอบแทนที่คาดว่าครอบครัวนำเงินไปลงทุนได้
    """
    _non_negative(locals())
    income_need = pv_growing_annuity(
        annual_family_expense, discount_rate, inflation, years_of_support, due=True
    )
    lump_sum_needs = debts + education_fund + final_expenses + emergency_fund + other_needs
    total_need = income_need + lump_sum_needs
    resources = existing_life_cover + liquid_assets
    gap = max(0.0, total_need - resources)
    return {
        "method": "needs_approach",
        "income_replacement_need": round(income_need, 2),
        "lump_sum_needs": {
            "debts": debts,
            "education_fund": education_fund,
            "final_expenses": final_expenses,
            "emergency_fund": emergency_fund,
            "other_needs": other_needs,
            "total": round(lump_sum_needs, 2),
        },
        "total_need": round(total_need, 2),
        "existing_resources": {
            "existing_life_cover": existing_life_cover,
            "liquid_assets": liquid_assets,
            "total": round(resources, 2),
        },
        "additional_cover_needed": round(gap, 2),
        "assumptions": {
            "years_of_support": years_of_support,
            "inflation": inflation,
            "discount_rate": discount_rate,
        },
    }


def human_life_value(
    *,
    annual_income: float,
    personal_consumption_ratio: float,
    years_to_retirement: int,
    income_growth: float = 0.03,
    discount_rate: float = 0.04,
) -> dict:
    """มูลค่าทางเศรษฐกิจของชีวิต: PV ของรายได้สุทธิที่ส่งให้ครอบครัวจนเกษียณ."""
    _non_negative(locals())
    if not 0 <= personal_consumption_ratio < 1:
        raise ValueError("personal_consumption_ratio ต้องอยู่ระหว่าง 0 ถึง 1")
    contribution = annual_income * (1 - personal_consumption_ratio)
    hlv = pv_growing_annuity(
        contribution, discount_rate, income_growth, years_to_retirement, due=False
    )
    return {
        "method": "human_life_value",
        "annual_contribution_to_family": round(contribution, 2),
        "human_life_value": round(hlv, 2),
        "multiple_of_income": round(hlv / annual_income, 2) if annual_income else None,
        "assumptions": {
            "years_to_retirement": years_to_retirement,
            "income_growth": income_growth,
            "discount_rate": discount_rate,
            "personal_consumption_ratio": personal_consumption_ratio,
        },
    }


def _non_negative(values: dict) -> None:
    for key, value in values.items():
        if key in ("inflation", "income_growth"):
            continue
        if isinstance(value, (int, float)) and value < 0:
            raise ValueError(f"{key} ต้องไม่ติดลบ")
