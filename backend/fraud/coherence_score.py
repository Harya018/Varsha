"""
VARSHA - Coherence Score (6-Signal Anti-Fraud Validation)
Validates claim authenticity using a weighted signal model.
"""
import random
from datetime import datetime


class CoherenceScore:
    """
    6-signal fraud gate for claim verification.
    Each signal returns 0.0–1.0.
    """

    SIGNAL_WEIGHTS = {
        "gps":                  0.15,
        "cell_tower":           0.20,
        "battery_drain":        0.10,
        "platform_activity":    0.20,
        "network_degradation":  0.20,
        "accelerometer":        0.15,
    }

    @staticmethod
    def check_gps_match(partner_id: str, trigger_zone: str) -> float:
        """Was partner's GPS near the trigger zone at claim time? (mock)"""
        return round(random.uniform(0.65, 1.0), 2)

    @staticmethod
    def check_tower_match(partner_id: str, trigger_zone: str) -> float:
        """Did cell tower pings place partner in claimed zone? (mock)"""
        return round(random.uniform(0.60, 1.0), 2)

    @staticmethod
    def check_battery_pattern(partner_id: str) -> float:
        """Battery drain pattern consistent with active riding? (mock)"""
        return round(random.uniform(0.55, 1.0), 2)

    @staticmethod
    def check_platform_activity(partner_id: str, claim_time: datetime) -> float:
        """Was partner active on delivery platform near claim time? (mock)"""
        return round(random.uniform(0.50, 1.0), 2)

    @staticmethod
    def check_network_quality(partner_id: str) -> float:
        """
        INVERTED SIGNAL: Poor connectivity = proof of outdoor presence.
        Low network quality (outdoors) → high fraud score.
        """
        raw_quality = round(random.uniform(0.2, 0.8), 2)
        return round(1.0 - raw_quality, 2)  # invert

    @staticmethod
    def check_motion_pattern(partner_id: str) -> float:
        """Accelerometer patterns consistent with two-wheeler riding? (mock)"""
        return round(random.uniform(0.60, 1.0), 2)

    @classmethod
    def calculate_score(cls, partner_id: str, trigger_zone: str,
                         claim_time: datetime = None) -> dict:
        """
        Compute the weighted coherence score and decide action tier.

        Score >= 0.80 → AUTO_APPROVE (90 seconds)
        Score >= 0.60 → OTP_SELFIE  (60 seconds)
        Score  < 0.60 → MANUAL_REVIEW (24 hours)
        """
        if claim_time is None:
            claim_time = datetime.utcnow()

        signals = {
            "gps":                cls.check_gps_match(partner_id, trigger_zone),
            "cell_tower":         cls.check_tower_match(partner_id, trigger_zone),
            "battery_drain":      cls.check_battery_pattern(partner_id),
            "platform_activity":  cls.check_platform_activity(partner_id, claim_time),
            "network_degradation": cls.check_network_quality(partner_id),
            "accelerometer":      cls.check_motion_pattern(partner_id),
        }

        score = sum(
            signals[sig] * cls.SIGNAL_WEIGHTS[sig]
            for sig in signals
        )
        score = round(score, 3)

        if score >= 0.80:
            action = "AUTO_APPROVE"
            processing_time = "90 seconds"
            tier_label = "High Confidence"
        elif score >= 0.60:
            action = "OTP_SELFIE"
            processing_time = "60 seconds after verification"
            tier_label = "Medium Confidence"
        else:
            action = "MANUAL_REVIEW"
            processing_time = "Up to 24 hours"
            tier_label = "Low Confidence – Manual Review"

        return {
            "score": score,
            "action": action,
            "processing_time": processing_time,
            "tier_label": tier_label,
            "signal_breakdown": signals,
        }
