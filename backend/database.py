"""
VARSHA - In-Memory SQLite Database Setup with Mock Data Population
"""
import json
import uuid
import random
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import (
    Base, DeliveryPartnerDB, DeliveryRecordDB, PolicyDB
)

# ── Engine: in-memory SQLite ─────────────────────────────────────────────────
DATABASE_URL = "sqlite:///./varsha_demo.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency for DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Seed Mock Data ───────────────────────────────────────────────────────────
SAMPLE_PARTNERS = [
    {
        "name": "Arjun Kumar",
        "mobile": "9876543210",
        "zones": ["velachery"],
        "upi_id": "arjun@okaxis",
        "platforms": ["swiggy", "zomato"],
        "shield_balance": 187,
        "weekly_deduction_total": 42,
    },
    {
        "name": "Priya Devi",
        "mobile": "9876543211",
        "zones": ["adyar"],
        "upi_id": "priya@oksbi",
        "platforms": ["zomato", "blinkit"],
        "shield_balance": 300,
        "weekly_deduction_total": 0,
    },
    {
        "name": "Ravi Shankar",
        "mobile": "9876543212",
        "zones": ["madipakkam"],
        "upi_id": "ravi@okhdfc",
        "platforms": ["swiggy", "zepto"],
        "shield_balance": 65,
        "weekly_deduction_total": 55,
    },
    {
        "name": "Sowmya Krishnan",
        "mobile": "9876543213",
        "zones": ["omr"],
        "upi_id": "sowmya@ybl",
        "platforms": ["zomato", "swiggy", "blinkit"],
        "shield_balance": 245,
        "weekly_deduction_total": 30,
    },
    {
        "name": "Karthik Raj",
        "mobile": "9876543214",
        "zones": ["annanagar"],
        "upi_id": "karthik@paytm",
        "platforms": ["swiggy"],
        "shield_balance": 120,
        "weekly_deduction_total": 63,
    },
]

ZONE_H3_MAP = {
    "velachery": "8c2a8a1a",
    "madipakkam": "8c2a8a1b",
    "adyar": "8c2a8a1c",
    "omr": "8c2a8a1d",
    "tnagar": "8c2a8a1e",
    "annanagar": "8c2a8a1f",
}


def _make_partner_id(zone: str) -> str:
    prefix = zone[:3].upper()
    ts = datetime.utcnow().strftime("%H%M%S")
    rand = random.randint(1000, 9999)
    return f"VRS-{prefix}-{ts}-{rand}"


def init_db():
    """Create all tables and populate with mock data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Skip if already seeded
        if db.query(DeliveryPartnerDB).count() > 0:
            return

        today = date.today()
        for p in SAMPLE_PARTNERS:
            partner_id = _make_partner_id(p["zones"][0])
            db_partner = DeliveryPartnerDB(
                id=partner_id,
                mobile=p["mobile"],
                name=p["name"],
                zones=json.dumps(p["zones"]),
                upi_id=p["upi_id"],
                platforms=json.dumps(p["platforms"]),
                registered_at=datetime.utcnow() - timedelta(days=random.randint(30, 90)),
                shield_balance=p["shield_balance"],
                shield_target=300,
                weekly_deduction_total=p["weekly_deduction_total"],
                last_deduction_reset=today,
                is_active=True,
            )
            db.add(db_partner)
            db.flush()

            # Create corresponding policy
            policy = PolicyDB(
                id=str(uuid.uuid4()),
                partner_id=partner_id,
                status="active" if p["shield_balance"] < 300 else "full",
                shield_balance=p["shield_balance"],
                shield_target=300,
                weekly_cap=75,
                per_order_deduction=3,
                current_week_deductions=p["weekly_deduction_total"],
                last_week_reset=today,
                created_at=datetime.utcnow(),
            )
            db.add(policy)

            # Generate 30 days of synthetic delivery history
            platforms = p["platforms"]
            for day_offset in range(30):
                record_date = today - timedelta(days=day_offset)
                deliveries = random.randint(12, 35)
                km = round(deliveries * random.uniform(2.2, 4.5), 1)
                earnings = deliveries * random.randint(35, 55)
                record = DeliveryRecordDB(
                    partner_id=partner_id,
                    platform=random.choice(platforms),
                    date=record_date,
                    deliveries=deliveries,
                    total_kilometers=km,
                    earnings=earnings,
                )
                db.add(record)

        db.commit()
        print("[VARSHA DB] Mock data seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"[VARSHA DB] Seed error: {e}")
    finally:
        db.close()
