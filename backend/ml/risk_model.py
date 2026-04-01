"""
VARSHA - ML Risk Model
Zone risk scoring, delivery efficiency analysis, and predictive weather risk.
"""
from datetime import date
from sqlalchemy.orm import Session
from backend.models import DeliveryRecordDB


# ── Zone Risk Database (hardcoded for demo) ──────────────────────────────────
ZONE_RISK = {
    "velachery":  {"rain": 1.5, "flood": 1.8, "heat": 1.2, "base": 1.4},
    "madipakkam": {"rain": 1.4, "flood": 1.6, "heat": 1.1, "base": 1.3},
    "adyar":      {"rain": 1.2, "flood": 1.3, "heat": 1.0, "base": 1.15},
    "omr":        {"rain": 0.9, "flood": 0.8, "heat": 1.0, "base": 0.9},
    "tnagar":     {"rain": 1.0, "flood": 0.9, "heat": 1.0, "base": 0.95},
    "annanagar":  {"rain": 0.8, "flood": 0.7, "heat": 0.9, "base": 0.83},
}

SEASON_WEIGHTS = {
    "monsoon":      {"rain": 0.6, "flood": 0.3, "heat": 0.1},
    "post-monsoon": {"rain": 0.4, "flood": 0.4, "heat": 0.2},
    "summer":       {"rain": 0.1, "flood": 0.1, "heat": 0.8},
    "pre-monsoon":  {"rain": 0.3, "flood": 0.2, "heat": 0.5},
}


class RiskModel:

    @staticmethod
    def get_current_season() -> str:
        month = date.today().month
        if month in (10, 11, 12):
            return "monsoon"
        elif month in (1, 2, 3):
            return "post-monsoon"
        elif month in (4, 5, 6):
            return "summer"
        else:
            return "pre-monsoon"

    @staticmethod
    def calculate_zone_risk_factor(zone: str, season: str = None) -> float:
        """Return weighted risk multiplier (0.7–1.8) for zone + season."""
        zone = zone.lower()
        if zone not in ZONE_RISK:
            return 1.0
        if season is None:
            season = RiskModel.get_current_season()

        risks = ZONE_RISK[zone]
        weights = SEASON_WEIGHTS.get(season, SEASON_WEIGHTS["pre-monsoon"])

        factor = (
            risks["rain"] * weights["rain"]
            + risks["flood"] * weights["flood"]
            + risks["heat"] * weights["heat"]
        )
        return round(max(0.7, min(1.8, factor)), 3)

    @staticmethod
    def calculate_delivery_efficiency_factor(partner_id: str, db: Session) -> float:
        """
        Fetch last 30 days delivery data. Higher delivery/km ratio → lower premium.
        >0.35 deliveries/km → 0.9x   (efficient)
        0.25–0.35          → 1.0x   (average)
        <0.25              → 1.1x   (low efficiency)
        """
        from datetime import timedelta
        today = date.today()
        cutoff = today - timedelta(days=30)
        records = (
            db.query(DeliveryRecordDB)
            .filter(
                DeliveryRecordDB.partner_id == partner_id,
                DeliveryRecordDB.date >= cutoff,
            )
            .all()
        )

        if not records:
            return 1.0  # neutral if no history

        total_deliveries = sum(r.deliveries for r in records)
        total_km = sum(r.total_kilometers for r in records)
        efficiency = total_deliveries / total_km if total_km > 0 else 0.0

        if efficiency > 0.35:
            return 0.9
        elif efficiency >= 0.25:
            return 1.0
        else:
            return 1.1

    @staticmethod
    def predict_tomorrow_risk(zone: str) -> dict:
        """
        Simple rule-based tomorrow risk predictor.
        Returns risk factor + human-readable forecast.
        """
        month = date.today().month
        zone = zone.lower()

        if month in (10, 11, 12):
            risk_factor = 1.3
            event = "Heavy monsoon rainfall expected"
            recommendation = "Your shield is building – stay safe during heavy rain"
            icon = "🌧️"
        elif month in (4, 5, 6):
            risk_factor = 1.2
            event = "Extreme heat advisory"
            recommendation = "Stay hydrated – heat stroke risk high"
            icon = "☀️"
        else:
            risk_factor = 1.0
            event = "Normal weather conditions"
            recommendation = "Good riding day – keep building your shield"
            icon = "🌤️"

        zone_risk = ZONE_RISK.get(zone, {}).get("base", 1.0)
        combined_risk = round(risk_factor * zone_risk, 2)

        return {
            "zone": zone,
            "risk_factor": combined_risk,
            "weather_event": event,
            "icon": icon,
            "recommendation": recommendation,
            "season": RiskModel.get_current_season(),
        }

    @staticmethod
    def calculate_dynamic_premium(partner, db: Session) -> dict:
        """
        Full dynamic premium calculation using all three factors.
        Returns per-order premium + all contributing factors.
        """
        season = RiskModel.get_current_season()
        import json
        zones = json.loads(partner.zones) if isinstance(partner.zones, str) else partner.zones
        primary_zone = zones[0] if zones else "velachery"

        zone_factor = RiskModel.calculate_zone_risk_factor(primary_zone, season)
        efficiency_factor = RiskModel.calculate_delivery_efficiency_factor(partner.id, db)
        predict = RiskModel.predict_tomorrow_risk(primary_zone)
        predictive_factor = predict["risk_factor"]

        combined = zone_factor * efficiency_factor * predictive_factor
        combined = round(max(0.7, min(1.8, combined)), 3)

        base = 3.0
        premium_per_order = round(base * combined, 2)

        return {
            "base_premium": base,
            "zone": primary_zone,
            "season": season,
            "zone_factor": zone_factor,
            "efficiency_factor": efficiency_factor,
            "predictive_factor": predictive_factor,
            "combined_factor": combined,
            "premium_per_order": premium_per_order,
            "tomorrow_forecast": predict,
        }
