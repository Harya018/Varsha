"""
VARSHA - Dynamic Premium Engine
Calculates per-order insurance deductions using zone risk, delivery efficiency, and predictive factors.
"""
import json
from datetime import date
from sqlalchemy.orm import Session
from backend.models import DeliveryPartnerDB, DeliveryRecordDB, DeductionLogDB


class PremiumEngine:

    BASE_DEDUCTION = 3.0  # ₹3 per order base
    WEEKLY_CAP = 75       # max ₹75 per week

    @staticmethod
    def calculate_deduction(partner: DeliveryPartnerDB, orders_today: int,
                             total_kilometers: float, zone_factor: float,
                             efficiency_factor: float, predictive_factor: float,
                             db: Session) -> dict:
        """
        Calculate and apply a single batched deduction for today's deliveries.
        Returns deduction breakdown dict.
        """
        combined_factor = zone_factor * efficiency_factor * predictive_factor
        combined_factor = max(0.7, min(1.8, combined_factor))  # clamp

        premium_per_order = round(PremiumEngine.BASE_DEDUCTION * combined_factor, 2)
        total_deduction = round(premium_per_order * orders_today, 2)

        # Check weekly cap
        remaining_cap = PremiumEngine.WEEKLY_CAP - partner.weekly_deduction_total
        if remaining_cap <= 0:
            return {
                "deduction": 0,
                "capped": True,
                "premium_per_order": premium_per_order,
                "message": "Weekly cap reached – no deduction this week",
            }

        actual_deduction = min(total_deduction, remaining_cap)
        actual_deduction = round(actual_deduction, 2)

        # Update partner balances
        new_balance = min(partner.shield_balance + int(actual_deduction), partner.shield_target)
        partner.shield_balance = new_balance
        partner.weekly_deduction_total = min(
            partner.weekly_deduction_total + int(actual_deduction),
            PremiumEngine.WEEKLY_CAP
        )
        partner.last_deduction_reset = date.today()
        db.add(partner)

        # Log deduction
        log = DeductionLogDB(
            partner_id=partner.id,
            platform="delivery",
            deduction_amount=actual_deduction,
            zone_factor=zone_factor,
            efficiency_factor=efficiency_factor,
            predictive_factor=predictive_factor,
        )
        db.add(log)
        db.commit()

        return {
            "deduction": actual_deduction,
            "capped": actual_deduction < total_deduction,
            "premium_per_order": premium_per_order,
            "zone_factor": zone_factor,
            "efficiency_factor": efficiency_factor,
            "predictive_factor": predictive_factor,
            "combined_factor": round(combined_factor, 3),
            "message": f"Collected ₹{actual_deduction} for {orders_today} deliveries",
        }

    @staticmethod
    def get_shield_status(partner: DeliveryPartnerDB) -> dict:
        """Return shield percentage and fullness flag."""
        pct = round((partner.shield_balance / partner.shield_target) * 100, 1)
        return {
            "percentage": pct,
            "is_full": partner.shield_balance >= partner.shield_target,
            "shield_balance": partner.shield_balance,
            "shield_target": partner.shield_target,
        }

    @staticmethod
    def reset_weekly_deductions(db: Session):
        """Reset weekly totals if a new week has started (called on startup/cron)."""
        today = date.today()
        partners = db.query(DeliveryPartnerDB).all()
        reset_count = 0
        for p in partners:
            if p.last_deduction_reset and (today - p.last_deduction_reset).days >= 7:
                p.weekly_deduction_total = 0
                p.last_deduction_reset = today
                db.add(p)
                reset_count += 1
        if reset_count:
            db.commit()
            print(f"[PremiumEngine] Reset weekly deductions for {reset_count} partners.")
