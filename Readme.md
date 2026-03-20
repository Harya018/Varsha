# VARSHA
## AI-Powered Parametric Insurance for Swiggy/Zomato Delivery Partners

**DEVTrails 2026 | Phase 1 Submission**
**Team:** [Your Team Name]
**Location:** Chennai, Tamil Nadu
**GitHub:** https://github.com/[team-name]/varsha
**Demo Video:** https://youtu.be/[link]

---

## Persona & Workflow

We chose food delivery partners on Swiggy and Zomato in Chennai.

**Persona: Karthik, 32, Velachery**

Karthik delivers 25-30 orders per week, earning ₹600-800 daily. During Northeast Monsoon, Velachery floods within 2 hours of heavy rain. He loses 2-3 days of work each time it rains. Traditional insurance requires ₹400-500 upfront—a full day's earnings he can't spare.

**Workflow:**

1. Karthik signs up with mobile number, selects Velachery zone, registers UPI ID
2. Each delivery → ₹3 deducted automatically (weekly cap ₹75)
3. After 100 deliveries (₹300), deductions stop—shield full
4. IMD detects 20mm rain in 6 hours in Velachery
5. System verifies his location, Swiggy order history, cell tower
6. ₹2,000 credited to his UPI within 90 seconds
7. Policy ends, next delivery starts new ₹3 deductions
8. First 3 orders after rain pay double (RainBoost)
9. Customer tips during rain → earns points for next order; partner gets full tip instantly
10. Cash tips verified via customer confirmation

---

## Weekly Premium Model

| Component | Value |
|-----------|-------|
| Per-order deduction | ₹3 |
| Weekly maximum | ₹75 (25 orders) |
| Shield target | ₹300 |
| Payout | ₹2,000 |
| Risk multiplier | 0.8x - 1.5x based on zone |

Partner pays only when working. After shield reaches ₹300, deductions stop completely. After payout, new cycle starts automatically.

---

## Parametric Triggers

| Trigger | Threshold | Data Source |
|---------|-----------|-------------|
| Heavy rain | >20mm in 6 hours | IMD Chennai |
| Extreme heat | >40°C | IMD Chennai |
| Urban flooding | Water level > danger mark | Chennai Corporation |
| Curfew/strike | Government notification | Official alerts + news APIs |

---

## Platform Choice

We chose Progressive Web App (PWA) because:
- Works on feature phones and smartphones
- No app store download required
- Minimal data usage
- Single codebase for faster development

---

## AI/ML Integration

**Risk Scoring (Random Forest / XGBoost)**
- Inputs: historical rainfall by zone, flood incidence, partner order history, time of year
- Output: zone risk factor (0.8x - 1.5x) applied to ₹3 base rate
- Trained on 10 years of IMD Chennai weather data

**Fraud Detection (5-Signal Coherence)**
- Signals: GPS + cell tower + IP + motion + IMD weather
- All five must align for auto-approval
- Storm Coherence Score: >0.80 auto-approve, <0.40 auto-reject

**Ring Density Index**
- Detects syndicates: same WiFi BSSID, same onboarding IP, same referral chain
- Score >0.70 triggers cluster quarantine

**Predictive Disruption (LSTM)**
- Inputs: IMD 7-day forecast, historical flood patterns
- Output: "85% chance of rain tomorrow in Velachery"

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React + Tailwind CSS (PWA) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Cache/Queue | Redis + Celery |
| ML | scikit-learn, XGBoost, TensorFlow |
| APIs | IMD, OpenWeatherMap, MapMyIndia |
| Payments | Razorpay (mock) |
| Deployment | Docker + GitHub Actions |

---

## Development Plan

**Phase 1 (Weeks 1-2) - Completed**
- Week 1: Chennai weather data collection, flood zone mapping, partner interviews
- Week 2: Architecture design, ML prototype planning, this README

**Phase 2 (Weeks 3-4)**
- Week 3: PWA registration, zone selection, UPI linking, basic dashboard
- Week 4: ₹3/order deduction logic, weekly cap enforcement, shield accumulation, mock payouts

**Phase 3 (Weeks 5-6)**
- Week 5: 5-signal fraud detection, ML models, ring density engine
- Week 6: RainBoost, TipPoints, full dashboards, final demo video

---

## Analytics Dashboard

**Partner View:** Shield status, weekly deductions, payout history, weather forecast, RainBoost remaining

**Admin View:** Active policies, daily triggers by zone, fraud alerts, loss ratio, ML model accuracy

---

## Repository Link

https://github.com/[team-name]/varsha

---

## Demo Video Link

https://youtu.be/[link]