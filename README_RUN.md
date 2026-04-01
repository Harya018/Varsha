# VARSHA – Run Instructions

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Backend
```bash
uvicorn backend.main:app --reload --port 8000
```
API docs available at: **http://localhost:8000/docs**

### 3. Open Frontend
Open `frontend/index.html` in your browser, **or** serve it:
```bash
python -m http.server 8080
```
Then visit: **http://localhost:8080/frontend/**

---

## Demo Credentials
| Field | Value |
|-------|-------|
| Mobile | Any 10-digit number |
| OTP | `123456` |
| Platforms | Swiggy / Zomato / Zepto / Blinkit |

---

## Demo Flow

### Registration
1. Enter any 10-digit mobile → Send OTP
2. Enter `123456` → Verify
3. Fill name, zone, UPI, platforms → Submit
4. Copy your Universal Worker ID (`VRS-VEL-...`)

### Policy Dashboard
- Select a pre-seeded partner (Arjun, Priya, Ravi, Sowmya, Karthik)
- View shield progress bar and balance
- Set deliveries + KM → click **Simulate & Collect Premium**
- Watch shield balance rise with dynamic per-order deduction

### Dynamic Premium (ML Tab)
- Select any partner to see AI-computed premium
- Zone risk × Efficiency × Tomorrow's Weather = Final rate
- Velachery during monsoon = ~1.5x multiplier

### Claims (Zero-Touch Demo)
1. Select a trigger zone (e.g. Velachery)
2. Click **Simulate Rain** to force-activate trigger
3. Select a partner → **Check My Eligibility**
4. Score ≥ 80% → AUTO-APPROVED in 90 seconds
5. Score 60–79% → Enter OTP `123456` + tap selfie → Verify & Claim
6. View claim history table

---

## Payout Tiers
| Shield Balance | Payout |
|---------------|--------|
| ₹300 (Full)   | ₹2,000 |
| ₹250–299      | ₹1,500 |
| ₹200–249      | ₹1,200 |
| ₹150–199      | ₹900   |
| ₹100–149      | ₹600   |
| ₹50–99        | ₹300   |
| < ₹50         | ₹0     |

---

## Project Structure
```
Varsha/
├── backend/
│   ├── main.py           # FastAPI app (20+ endpoints)
│   ├── models.py         # SQLAlchemy + Pydantic models
│   ├── database.py       # DB setup + mock data seed
│   ├── premium_engine.py # Weekly-capped deduction logic
│   ├── ml/
│   │   └── risk_model.py # Zone risk + efficiency + predict
│   ├── triggers/
│   │   └── weather_trigger.py  # Rain/Heat/Flood/AQI/Curfew/Platform
│   └── fraud/
│       ├── coherence_score.py  # 6-signal fraud gate
│       └── ring_density.py     # Syndicate detection
├── frontend/
│   └── index.html        # Single-page app (4 tabs)
├── data/
│   └── chennai_zones.json
└── requirements.txt
```

## Notes
- No real payments — UPI payout is mocked
- No real OTP — always use `123456`
- No external APIs — all weather/AQI data is realistic mock
- Database: SQLite file (`varsha_demo.db`) created on first run
