"""วางแผนเงินเกษียณ และประเมินบทบาทของประกันบำนาญ."""

from __future__ import annotations

from .finance import monthly_rate, payment_for_future_value, pv_growing_annuity


def retirement_plan(
    *,
    current_age: int,
    retirement_age: int,
    life_expectancy: int,
    monthly_expense_today: float,
    inflation: float = 0.03,
    return_before_retirement: float = 0.05,
    return_after_retirement: float = 0.03,
    current_savings: float = 0.0,
    other_monthly_income_today: float = 0.0,
    annuity_annual_payout: float = 0.0,
    annuity_payout_years: int = 0,
) -> dict:
    """เงินก้อนที่ต้องมีตอนเกษียณ และเงินออมต่อเดือนที่ต้องเก็บเพิ่ม.

    monthly_expense_today       : ค่าใช้จ่ายหลังเกษียณต่อเดือน คิดเป็นมูลค่าวันนี้
    other_monthly_income_today  : รายได้อื่นหลังเกษียณ (บำนาญประกันสังคม ฯลฯ) มูลค่าวันนี้
                                  โตตามเงินเฟ้อ
    annuity_annual_payout       : เงินบำนาญรายปีจากประกันบำนาญ (ตัวเลขตายตัวตามกรมธรรม์
                                  ไม่โตตามเงินเฟ้อ) เริ่มจ่ายตอนเกษียณ
    """
    if not current_age < retirement_age < life_expectancy:
        raise ValueError("ต้องเป็น current_age < retirement_age < life_expectancy")
    years_to_retire = retirement_age - current_age
    years_in_retirement = life_expectancy - retirement_age
    inflate = (1 + inflation) ** years_to_retire

    net_monthly_today = max(0.0, monthly_expense_today - other_monthly_income_today)
    first_year_need = net_monthly_today * 12 * inflate
    corpus_needed = pv_growing_annuity(
        first_year_need, return_after_retirement, inflation, years_in_retirement, due=True
    )
    annuity_value = pv_growing_annuity(
        annuity_annual_payout,
        return_after_retirement,
        0.0,
        min(annuity_payout_years, years_in_retirement),
        due=True,
    )
    fv_savings = current_savings * (1 + return_before_retirement) ** years_to_retire
    gap = max(0.0, corpus_needed - annuity_value - fv_savings)
    monthly_saving = payment_for_future_value(
        gap, monthly_rate(return_before_retirement), years_to_retire * 12
    )
    return {
        "years_to_retirement": years_to_retire,
        "years_in_retirement": years_in_retirement,
        "monthly_expense_at_retirement": round(monthly_expense_today * inflate, 2),
        "net_annual_need_first_year": round(first_year_need, 2),
        "corpus_needed_at_retirement": round(corpus_needed, 2),
        "annuity_value_at_retirement": round(annuity_value, 2),
        "current_savings_future_value": round(fv_savings, 2),
        "gap_at_retirement": round(gap, 2),
        "monthly_saving_required": round(monthly_saving, 2),
        "assumptions": {
            "inflation": inflation,
            "return_before_retirement": return_before_retirement,
            "return_after_retirement": return_after_retirement,
        },
    }
