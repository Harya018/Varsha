"""
VARSHA - SQLAlchemy Models & Pydantic Schemas
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Date, DateTime, Text
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date


# ── SQLAlchemy Base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── SQLAlchemy ORM Models ────────────────────────────────────────────────────
class DeliveryPartnerDB(Base):
    __tablename__ = "delivery_partners"

    id = Column(String, primary_key=True)
    mobile = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    zones = Column(Text, nullable=False)           # JSON-serialised list
    upi_id = Column(String, nullable=False)
    platforms = Column(Text, nullable=False)        # JSON-serialised list
    registered_at = Column(DateTime, default=datetime.utcnow)
    shield_balance = Column(Integer, default=0)
    shield_target = Column(Integer, default=300)
    weekly_deduction_total = Column(Integer, default=0)
    last_deduction_reset = Column(Date, default=date.today)
    is_active = Column(Boolean, default=False)


class DeliveryRecordDB(Base):
    __tablename__ = "delivery_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    partner_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    deliveries = Column(Integer, nullable=False)
    total_kilometers = Column(Float, nullable=False)
    earnings = Column(Integer, nullable=False)


class PolicyDB(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True)
    partner_id = Column(String, nullable=False)
    status = Column(String, default="active")       # active|paused|expired|claimed
    shield_balance = Column(Integer, default=0)
    shield_target = Column(Integer, default=300)
    weekly_cap = Column(Integer, default=75)
    per_order_deduction = Column(Integer, default=3)
    current_week_deductions = Column(Integer, default=0)
    last_week_reset = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_payout_date = Column(DateTime, nullable=True)


class ClaimDB(Base):
    __tablename__ = "claims"

    id = Column(String, primary_key=True)
    partner_id = Column(String, nullable=False)
    trigger_type = Column(String, nullable=False)
    payout_amount = Column(Integer, default=0)
    status = Column(String, default="pending")      # auto_approved|otp_required|manual_review|paid
    coherence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    zone = Column(String, nullable=False)


class DeductionLogDB(Base):
    __tablename__ = "deduction_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    partner_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    deduction_amount = Column(Float, nullable=False)
    zone_factor = Column(Float, nullable=False)
    efficiency_factor = Column(Float, nullable=False)
    predictive_factor = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Pydantic Request/Response Schemas ────────────────────────────────────────
class RegistrationRequest(BaseModel):
    mobile: str
    name: str
    zones: List[str]
    upi_id: str
    platforms: List[str]


class RegistrationResponse(BaseModel):
    partner_id: str
    message: str
    success: bool


class OTPVerifyRequest(BaseModel):
    mobile: str
    otp: str


class OTPVerifyResponse(BaseModel):
    success: bool
    partner_id: Optional[str] = None
    name: Optional[str] = None
    message: str


class PolicyResponse(BaseModel):
    partner_id: str
    shield_balance: int
    shield_target: int
    percentage: float
    weekly_deductions_this_week: int
    weekly_cap: int
    status: str
    last_5_deductions: List[dict]


class SimulateDeliveryRequest(BaseModel):
    partner_id: str
    platform: str
    deliveries_today: int
    total_kilometers: float


class SimulateDeliveryResponse(BaseModel):
    partner_id: str
    deliveries_processed: int
    total_deduction: float
    new_shield_balance: int
    deduction_details: List[dict]


class ClaimResponse(BaseModel):
    partner_id: str
    trigger_type: str
    status: str
    payout_amount: int
    coherence_score: float
    action: str
    message: str
    claim_id: str
