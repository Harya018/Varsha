"""
VARSHA - Ring Density Index (Syndicate Detection)
Detects coordinated fraud clusters based on claim patterns.
"""
from datetime import datetime, timedelta
from typing import List


class RingDensityIndex:
    """
    Analyses recent claim patterns to identify potential fraud syndicates.
    High RDI = many claims in same zone/timeframe → flag or quarantine.
    """

    @staticmethod
    def calculate_rdi(claims_in_last_hour: List[dict]) -> dict:
        """
        Input: list of recent claim dicts with keys: partner_id, zone, created_at
        Returns: RDI score and recommended action.
        """
        n = len(claims_in_last_hour)

        if n > 10:
            rdi = round(0.80 + min(0.19, (n - 10) * 0.02), 2)
            action = "CLUSTER_QUARANTINE"
            message = (
                f"{n} claims in 60 min from same zone. "
                "Probable fraud syndicate – quarantine activated."
            )
        elif n > 5:
            rdi = round(0.60 + (n - 5) * 0.04, 2)
            action = "FLAG_REVIEW"
            message = (
                f"{n} claims in 60 min. Elevated cluster activity – flagged for review."
            )
        else:
            rdi = round(max(0.05, n * 0.05), 2)
            action = "NORMAL"
            message = f"{n} claims in last hour – normal traffic."

        # Additional pattern checks (simplified mock)
        risk_signals = {
            "same_zone_cluster": n > 5,
            "rapid_succession": n > 3,  # would check timing in real system
            "identical_amounts": False,   # would compare payout amounts
            "shared_referral": False,     # would check referral codes
        }

        return {
            "rdi": rdi,
            "action": action,
            "message": message,
            "claims_analysed": n,
            "risk_signals": risk_signals,
        }

    @staticmethod
    def get_recent_claims_count(zone: str, db) -> List[dict]:
        """Fetch claims from the last hour for a given zone."""
        from backend.models import ClaimDB
        cutoff = datetime.utcnow() - timedelta(hours=1)
        claims = (
            db.query(ClaimDB)
            .filter(ClaimDB.zone == zone, ClaimDB.created_at >= cutoff)
            .all()
        )
        return [{"partner_id": c.partner_id, "zone": c.zone, "created_at": c.created_at}
                for c in claims]
