"""ฟังก์ชันคณิตศาสตร์การเงินพื้นฐาน (ใช้ stdlib เท่านั้น)."""

from __future__ import annotations

from typing import Sequence


def pv_growing_annuity(
    payment: float, rate: float, growth: float, periods: int, due: bool = True
) -> float:
    """มูลค่าปัจจุบันของกระแสเงินที่โตขึ้นปีละ ``growth``.

    payment  : จำนวนเงินงวดแรก
    rate     : อัตราคิดลด (ผลตอบแทน) ต่องวด
    growth   : อัตราเติบโตของงวด (เช่น เงินเฟ้อ) ต่องวด
    periods  : จำนวนงวด
    due      : True = จ่ายต้นงวด (annuity due), False = จ่ายปลายงวด
    """
    if periods <= 0:
        return 0.0
    if rate <= -1:
        raise ValueError("rate ต้องมากกว่า -100%")
    ratio = (1 + growth) / (1 + rate)
    if abs(ratio - 1) < 1e-12:
        total = payment * periods
    else:
        total = payment * (1 - ratio**periods) / (1 - ratio)
    return total if due else total / (1 + rate)


def npv(rate: float, cashflows: Sequence[float]) -> float:
    """NPV ของกระแสเงิน โดย cashflows[t] เกิดที่เวลา t (t=0 คือวันนี้)."""
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))


def irr(cashflows: Sequence[float], low: float = -0.99, high: float = 1.0) -> float | None:
    """หา IRR ด้วย bisection; คืน None ถ้าหาไม่ได้ (ไม่มีการเปลี่ยนเครื่องหมาย)."""
    if not any(cf > 0 for cf in cashflows) or not any(cf < 0 for cf in cashflows):
        return None
    f_low, f_high = npv(low, cashflows), npv(high, cashflows)
    while f_low * f_high > 0 and high < 100:
        high *= 2
        f_high = npv(high, cashflows)
    if f_low * f_high > 0:
        return None
    for _ in range(200):
        mid = (low + high) / 2
        f_mid = npv(mid, cashflows)
        if abs(f_mid) < 1e-9 or (high - low) < 1e-12:
            return mid
        if f_low * f_mid < 0:
            high, f_high = mid, f_mid
        else:
            low, f_low = mid, f_mid
    return (low + high) / 2


def monthly_rate(annual_rate: float) -> float:
    """แปลงอัตราต่อปีเป็นอัตราต่อเดือนแบบทบต้น."""
    return (1 + annual_rate) ** (1 / 12) - 1


def payment_for_future_value(target: float, rate: float, periods: int) -> float:
    """เงินออมต่องวด (ปลายงวด) ที่ทำให้ได้มูลค่าอนาคต ``target``."""
    if target <= 0:
        return 0.0
    if periods <= 0:
        raise ValueError("periods ต้องมากกว่า 0")
    if abs(rate) < 1e-12:
        return target / periods
    return target * rate / ((1 + rate) ** periods - 1)
