"""
VARSHA - Main FastAPI Application
All API endpoints for Registration, Policy, ML, Claims, and Triggers.
"""
import json
import uuid
import random
from datetime import datetime, date
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database import get_db, init_db
from backend.models import (
    DeliveryPartnerDB, PolicyDB, ClaimDB, DeductionLogDB,
    RegistrationRequest, RegistrationResponse,
    OTPVerifyRequest, OTPVerifyResponse,
    SimulateDeliveryRequest, SimulateDeliveryResponse,
)
from backend.premium_engine import PremiumEngine
from backend.ml.risk_model import RiskModel
from backend.triggers.weather_trigger import WeatherTrigger
from backend.fraud.coherence_score import CoherenceScore
from backend.fraud.ring_density import RingDensityIndex

# ── App Setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="VARSHA – AI Parametric Insurance for Delivery Partners",
    version="2.0.0",
    description="DEVTrails 2026 Phase 2 – Chennai Delivery Partner Insurance Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Constants ────────────────────────────────────────────────────────────────
VALID_ZONES = ["velachery", "adyar", "madipakkam", "omr", "tnagar", "annanagar"]
VALID_PLATFORMS = ["swiggy", "zomato", "zepto", "blinkit"]
MOCK_OTP = "123456"

ZONE_H3 = {
    "velachery": "8c2a8a1a",
    "madipakkam": "8c2a8a1b",
    "adyar": "8c2a8a1c",
    "omr": "8c2a8a1d",
    "tnagar": "8c2a8a1e",
    "annanagar": "8c2a8a1f",
}

PAYOUT_TIERS = [
    (300, 2000),
    (250, 1500),
    (200, 1200),
    (150, 900),
    (100, 600),
    (50, 300),
    (0, 0),
]


@app.on_event("startup")
async def startup_event():
    init_db()


# ── Helper Utilities ─────────────────────────────────────────────────────────
def make_partner_id(zone: str) -> str:
    prefix = zone[:3].upper()
    ts = datetime.utcnow().strftime("%H%M%S")
    rand = random.randint(1000, 9999)
    return f"VRS-{prefix}-{ts}-{rand}"


def get_partner_or_404(partner_id: str, db: Session) -> DeliveryPartnerDB:
    p = db.query(DeliveryPartnerDB).filter(DeliveryPartnerDB.id == partner_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Partner {partner_id} not found")
    return p


def calculate_payout(shield_balance: int) -> int:
    for threshold, amount in PAYOUT_TIERS:
        if shield_balance >= threshold:
            return amount
    return 0


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1 – REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/register", response_model=RegistrationResponse, tags=["Registration"])
def register_partner(payload: RegistrationRequest, db: Session = Depends(get_db)):
    """Step 1: Register a new delivery partner and send mock OTP."""
    # Validate mobile
    if not payload.mobile.isdigit() or len(payload.mobile) != 10:
        raise HTTPException(status_code=400, detail="Mobile must be exactly 10 digits")

    # Check duplicate mobile
    existing = db.query(DeliveryPartnerDB).filter(
        DeliveryPartnerDB.mobile == payload.mobile
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Mobile number already registered")

    # Validate zones
    for z in payload.zones:
        if z.lower() not in VALID_ZONES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid zone '{z}'. Valid: {VALID_ZONES}"
            )

    # Validate platforms
    for p in payload.platforms:
        if p.lower() not in VALID_PLATFORMS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform '{p}'. Valid: {VALID_PLATFORMS}"
            )

    primary_zone = payload.zones[0].lower()
    partner_id = make_partner_id(primary_zone)

    db_partner = DeliveryPartnerDB(
        id=partner_id,
        mobile=payload.mobile,
        name=payload.name,
        zones=json.dumps([z.lower() for z in payload.zones]),
        upi_id=payload.upi_id,
        platforms=json.dumps([p.lower() for p in payload.platforms]),
        registered_at=datetime.utcnow(),
        shield_balance=0,
        shield_target=300,
        weekly_deduction_total=0,
        last_deduction_reset=date.today(),
        is_active=False,  # Activated after OTP verification
    )
    db.add(db_partner)
    db.commit()

    return RegistrationResponse(
        partner_id=partner_id,
        message=f"OTP sent to {payload.mobile} (demo OTP: 123456)",
        success=True,
    )


@app.post("/api/verify-otp", response_model=OTPVerifyResponse, tags=["Registration"])
def verify_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    """Step 2: Verify OTP and activate the partner account."""
    partner = db.query(DeliveryPartnerDB).filter(
        DeliveryPartnerDB.mobile == payload.mobile
    ).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Mobile not found. Please register first.")

    if payload.otp != MOCK_OTP:
        raise HTTPException(status_code=400, detail="Invalid OTP. Use 123456 for demo.")

    partner.is_active = True
    db.add(partner)

    # Create policy
    existing_policy = db.query(PolicyDB).filter(
        PolicyDB.partner_id == partner.id
    ).first()
    if not existing_policy:
        policy = PolicyDB(
            id=str(uuid.uuid4()),
            partner_id=partner.id,
            status="active",
            shield_balance=0,
            shield_target=300,
            weekly_cap=75,
            per_order_deduction=3,
            current_week_deductions=0,
            last_week_reset=date.today(),
            created_at=datetime.utcnow(),
        )
        db.add(policy)

    db.commit()

    zones = json.loads(partner.zones)
    h3_ids = [ZONE_H3.get(z, "unknown") for z in zones]

    return OTPVerifyResponse(
        success=True,
        partner_id=partner.id,
        name=partner.name,
        message=f"Welcome to VARSHA, {partner.name}! Your Universal Worker ID: {partner.id}",
    )


@app.get("/api/partner/{partner_id}", tags=["Registration"])
def get_partner(partner_id: str, db: Session = Depends(get_db)):
    """Fetch partner profile by ID."""
    p = get_partner_or_404(partner_id, db)
    return {
        "id": p.id,
        "name": p.name,
        "mobile": p.mobile,
        "zones": json.loads(p.zones),
        "upi_id": p.upi_id,
        "platforms": json.loads(p.platforms),
        "registered_at": p.registered_at,
        "shield_balance": p.shield_balance,
        "shield_target": p.shield_target,
        "is_active": p.is_active,
    }


@app.get("/api/partners", tags=["Registration"])
def list_partners(db: Session = Depends(get_db)):
    """List all registered partners (for demo picker)."""
    partners = db.query(DeliveryPartnerDB).filter(
        DeliveryPartnerDB.is_active == True
    ).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "zones": json.loads(p.zones),
            "shield_balance": p.shield_balance,
            "platforms": json.loads(p.platforms),
        }
        for p in partners
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2 – POLICY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/policy/{partner_id}", tags=["Policy"])
def get_policy(partner_id: str, db: Session = Depends(get_db)):
    """Get insurance policy / shield status for a partner."""
    p = get_partner_or_404(partner_id, db)
    PremiumEngine.reset_weekly_deductions(db)

    shield = PremiumEngine.get_shield_status(p)
    pct = shield["percentage"]

    if p.shield_balance >= p.shield_target:
        status = "Shield Full – No Deductions"
    elif p.shield_balance >= 200:
        status = "Building Shield – Nearly There!"
    else:
        status = "Building Shield"

    # Last 5 deduction logs
    logs = (
        db.query(DeductionLogDB)
        .filter(DeductionLogDB.partner_id == partner_id)
        .order_by(DeductionLogDB.id.desc())
        .limit(5)
        .all()
    )
    last_5 = [
        {
            "amount": l.deduction_amount,
            "zone_factor": l.zone_factor,
            "efficiency_factor": l.efficiency_factor,
            "predictive_factor": l.predictive_factor,
            "timestamp": l.created_at.isoformat(),
        }
        for l in logs
    ]

    return {
        "partner_id": partner_id,
        "shield_balance": p.shield_balance,
        "shield_target": p.shield_target,
        "percentage": pct,
        "weekly_deductions_this_week": p.weekly_deduction_total,
        "weekly_cap": 75,
        "status": status,
        "last_5_deductions": last_5,
    }


@app.post("/api/policy/simulate-delivery", tags=["Policy"])
def simulate_delivery(payload: SimulateDeliveryRequest, db: Session = Depends(get_db)):
    """Simulate a day's deliveries and apply premium deductions."""
    p = get_partner_or_404(payload.partner_id, db)
    zones = json.loads(p.zones) if isinstance(p.zones, str) else p.zones
    primary_zone = zones[0] if zones else "velachery"

    zone_factor = RiskModel.calculate_zone_risk_factor(primary_zone)
    efficiency_factor = RiskModel.calculate_delivery_efficiency_factor(p.id, db)
    predict = RiskModel.predict_tomorrow_risk(primary_zone)
    predictive_factor = predict["risk_factor"]

    result = PremiumEngine.calculate_deduction(
        partner=p,
        orders_today=payload.deliveries_today,
        total_kilometers=payload.total_kilometers,
        zone_factor=zone_factor,
        efficiency_factor=efficiency_factor,
        predictive_factor=predictive_factor,
        db=db,
    )

    return {
        "partner_id": payload.partner_id,
        "deliveries_processed": payload.deliveries_today,
        "total_deduction": result["deduction"],
        "new_shield_balance": p.shield_balance,
        "premium_per_order": result.get("premium_per_order"),
        "capped": result.get("capped", False),
        "deduction_details": [result],
        "message": result["message"],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3 – ML / DYNAMIC PREMIUM
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/ml/zone-risk/{zone}", tags=["ML"])
def get_zone_risk(zone: str):
    """Return zone risk factor for the current season."""
    if zone.lower() not in VALID_ZONES:
        raise HTTPException(status_code=400, detail=f"Unknown zone: {zone}")
    season = RiskModel.get_current_season()
    factor = RiskModel.calculate_zone_risk_factor(zone, season)
    from backend.ml.risk_model import ZONE_RISK
    zone_risks = ZONE_RISK.get(zone.lower(), {})
    return {
        "zone": zone,
        "season": season,
        "risk_factor": factor,
        "risk_breakdown": zone_risks,
        "message": f"Zone {zone.title()} has risk factor {factor}x for {season} season",
    }


@app.get("/api/ml/predict-tomorrow/{partner_id}", tags=["ML"])
def predict_tomorrow(partner_id: str, db: Session = Depends(get_db)):
    """Get tomorrow's risk prediction for a partner's primary zone."""
    p = get_partner_or_404(partner_id, db)
    premium_calc = RiskModel.calculate_dynamic_premium(p, db)
    return {
        "partner_id": partner_id,
        "name": p.name,
        **premium_calc,
    }


@app.get("/api/ml/premium/{partner_id}", tags=["ML"])
def get_dynamic_premium(partner_id: str, db: Session = Depends(get_db)):
    """Get full explainable dynamic premium breakdown for a partner."""
    p = get_partner_or_404(partner_id, db)
    return RiskModel.calculate_dynamic_premium(p, db)


@app.post("/api/ml/update-risk-model", tags=["ML"])
def update_risk_model():
    """Simulate model retraining (mock endpoint)."""
    return {
        "success": True,
        "message": "Risk model retrained with latest 30-day delivery data",
        "model_version": "v2.1.0",
        "retrained_at": datetime.utcnow().isoformat(),
        "zones_updated": VALID_ZONES,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4 – TRIGGERS & CLAIMS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/triggers/check/{zone}", tags=["Triggers"])
def check_triggers(zone: str):
    """Run all parametric triggers for a given zone."""
    if zone.lower() not in VALID_ZONES:
        raise HTTPException(status_code=400, detail=f"Unknown zone: {zone}")
    return WeatherTrigger.check_all_triggers(zone)


@app.get("/api/triggers/status", tags=["Triggers"])
def all_trigger_status():
    """Return current trigger status for all Chennai zones."""
    results = {}
    for zone in VALID_ZONES:
        results[zone] = WeatherTrigger.check_all_triggers(zone)
    return {"zones": results, "checked_at": datetime.utcnow().isoformat()}


@app.post("/api/triggers/simulate", tags=["Triggers"])
def simulate_trigger(zone: str, trigger_type: str, active: bool = True):
    """Demo endpoint: force-activate a specific trigger in a zone."""
    if zone.lower() not in VALID_ZONES:
        raise HTTPException(status_code=400, detail=f"Unknown zone: {zone}")
    valid_types = ["rain", "heat", "flood", "aqi", "curfew"]
    if trigger_type.lower() not in valid_types:
        raise HTTPException(status_code=400, detail=f"Unknown trigger: {trigger_type}")
    WeatherTrigger.set_override(zone, trigger_type, active)
    return {
        "success": True,
        "zone": zone,
        "trigger_type": trigger_type,
        "activated": active,
        "message": f"{'Activated' if active else 'Deactivated'} {trigger_type} trigger in {zone}",
    }


@app.post("/api/claims/auto/{partner_id}", tags=["Claims"])
def auto_claim(partner_id: str, db: Session = Depends(get_db)):
    """
    Zero-touch claim: checks triggers, runs fraud gate, and auto-processes if eligible.
    """
    p = get_partner_or_404(partner_id, db)
    zones = json.loads(p.zones) if isinstance(p.zones, str) else p.zones
    primary_zone = zones[0]
    platforms = json.loads(p.platforms) if isinstance(p.platforms, str) else p.platforms

    # Check if shield has any balance
    if p.shield_balance < 50:
        raise HTTPException(
            status_code=400,
            detail="Shield balance too low (< ₹50). Keep collecting to unlock payouts."
        )

    # Run triggers
    trigger_result = WeatherTrigger.check_all_triggers(primary_zone, platforms)
    if not trigger_result["any_triggered"]:
        return {
            "partner_id": partner_id,
            "triggered": False,
            "message": f"No active triggers in {primary_zone.title()} right now. Stay safe!",
            "trigger_details": trigger_result["trigger_details"],
        }

    active = trigger_result["active_triggers"]
    trigger_type = active[0]["type"] if active else "unknown"

    # Ring Density Check (fraud syndicate detection)
    recent_claims = RingDensityIndex.get_recent_claims_count(primary_zone, db)
    rdi_result = RingDensityIndex.calculate_rdi(recent_claims)
    if rdi_result["action"] == "CLUSTER_QUARANTINE":
        claim_id = str(uuid.uuid4())
        claim = ClaimDB(
            id=claim_id,
            partner_id=partner_id,
            trigger_type=trigger_type,
            payout_amount=0,
            status="quarantined",
            coherence_score=0.0,
            created_at=datetime.utcnow(),
            zone=primary_zone,
        )
        db.add(claim)
        db.commit()
        return {
            "partner_id": partner_id,
            "claim_id": claim_id,
            "status": "quarantined",
            "message": "Unusual claim cluster detected. Under enhanced review.",
            "rdi": rdi_result,
        }

    # Coherence Score (6-signal fraud gate)
    coherence = CoherenceScore.calculate_score(partner_id, primary_zone)
    payout = calculate_payout(p.shield_balance)
    claim_id = str(uuid.uuid4())

    if coherence["action"] == "AUTO_APPROVE":
        # Immediate payout
        old_balance = p.shield_balance
        p.shield_balance = 0
        db.add(p)
        claim = ClaimDB(
            id=claim_id,
            partner_id=partner_id,
            trigger_type=trigger_type,
            payout_amount=payout,
            status="auto_approved",
            coherence_score=coherence["score"],
            created_at=datetime.utcnow(),
            processed_at=datetime.utcnow(),
            zone=primary_zone,
        )
        db.add(claim)
        db.commit()
        return {
            "partner_id": partner_id,
            "claim_id": claim_id,
            "trigger_type": trigger_type,
            "status": "auto_approved",
            "payout_amount": payout,
            "coherence_score": coherence["score"],
            "action": "AUTO_APPROVE",
            "processing_time": "90 seconds",
            "signal_breakdown": coherence["signal_breakdown"],
            "message": f"₹{payout:,} credited to {p.upi_id} in {coherence['processing_time']}! 🎉",
            "rdi": rdi_result,
        }

    elif coherence["action"] == "OTP_SELFIE":
        claim = ClaimDB(
            id=claim_id,
            partner_id=partner_id,
            trigger_type=trigger_type,
            payout_amount=payout,
            status="otp_required",
            coherence_score=coherence["score"],
            created_at=datetime.utcnow(),
            zone=primary_zone,
        )
        db.add(claim)
        db.commit()
        return {
            "partner_id": partner_id,
            "claim_id": claim_id,
            "trigger_type": trigger_type,
            "status": "otp_required",
            "payout_amount": payout,
            "coherence_score": coherence["score"],
            "action": "OTP_SELFIE",
            "processing_time": "60 seconds after verification",
            "message": f"One more step: Enter OTP (123456) and upload selfie to claim ₹{payout:,}",
            "rdi": rdi_result,
        }

    else:
        claim = ClaimDB(
            id=claim_id,
            partner_id=partner_id,
            trigger_type=trigger_type,
            payout_amount=payout,
            status="manual_review",
            coherence_score=coherence["score"],
            created_at=datetime.utcnow(),
            zone=primary_zone,
        )
        db.add(claim)
        db.commit()
        return {
            "partner_id": partner_id,
            "claim_id": claim_id,
            "trigger_type": trigger_type,
            "status": "manual_review",
            "payout_amount": payout,
            "coherence_score": coherence["score"],
            "action": "MANUAL_REVIEW",
            "processing_time": "Up to 24 hours",
            "message": "Claim under manual review. You'll be notified within 24 hours.",
            "rdi": rdi_result,
        }


@app.post("/api/claims/verify-otp-selfie", tags=["Claims"])
def verify_otp_selfie(
    claim_id: str,
    otp: str,
    selfie_base64: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Verify OTP + selfie for medium-confidence claims and process payout."""
    claim = db.query(ClaimDB).filter(ClaimDB.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status != "otp_required":
        raise HTTPException(status_code=400, detail=f"Claim is not pending verification (status: {claim.status})")

    if otp != MOCK_OTP:
        raise HTTPException(status_code=400, detail="Invalid OTP. Use 123456 for demo.")

    # Mock selfie check: accepted if provided
    selfie_ok = selfie_base64 is not None and len(selfie_base64) > 10

    partner = db.query(DeliveryPartnerDB).filter(
        DeliveryPartnerDB.id == claim.partner_id
    ).first()

    old_balance = partner.shield_balance if partner else 0
    if partner:
        partner.shield_balance = 0
        db.add(partner)

    claim.status = "paid"
    claim.processed_at = datetime.utcnow()
    db.add(claim)
    db.commit()

    return {
        "success": True,
        "claim_id": claim_id,
        "payout_amount": claim.payout_amount,
        "old_shield_balance": old_balance,
        "selfie_verified": selfie_ok,
        "message": f"✅ ₹{claim.payout_amount:,} will be credited to your UPI in 60 seconds!",
    }


@app.get("/api/claims/history/{partner_id}", tags=["Claims"])
def claim_history(partner_id: str, db: Session = Depends(get_db)):
    """Return claims history for a partner."""
    get_partner_or_404(partner_id, db)
    claims = (
        db.query(ClaimDB)
        .filter(ClaimDB.partner_id == partner_id)
        .order_by(ClaimDB.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "partner_id": partner_id,
        "total_claims": len(claims),
        "claims": [
            {
                "id": c.id,
                "trigger_type": c.trigger_type,
                "payout_amount": c.payout_amount,
                "status": c.status,
                "coherence_score": c.coherence_score,
                "zone": c.zone,
                "created_at": c.created_at.isoformat(),
                "processed_at": c.processed_at.isoformat() if c.processed_at else None,
            }
            for c in claims
        ],
    }


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "service": "VARSHA – AI Parametric Insurance Platform",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
