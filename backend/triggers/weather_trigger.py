"""
VARSHA - Weather & Platform Triggers
Parametric trigger checks for auto-claim activation (all mock data for demo).
"""
import random
from datetime import datetime


# ── Mock data generators (realistic Chennai ranges) ──────────────────────────
def get_mock_rainfall_data(zone: str) -> float:
    """Simulate IMD API. Returns rainfall in mm for zone."""
    base_ranges = {
        "velachery": (5, 38),
        "madipakkam": (3, 35),
        "adyar": (2, 28),
        "omr": (1, 20),
        "tnagar": (2, 25),
        "annanagar": (1, 18),
    }
    lo, hi = base_ranges.get(zone.lower(), (1, 25))
    return round(random.uniform(lo, hi), 1)


def get_mock_temperature_data(zone: str) -> float:
    """Simulate temperature API. Returns Celsius."""
    return round(random.uniform(30.0, 44.5), 1)


def get_mock_aqi_data(zone: str) -> int:
    """Simulate CPCB API. Returns AQI value."""
    base_aqi = {
        "velachery": (80, 380),
        "madipakkam": (70, 350),
        "adyar": (60, 300),
        "omr": (40, 200),
        "tnagar": (70, 340),
        "annanagar": (50, 260),
    }
    lo, hi = base_aqi.get(zone.lower(), (50, 300))
    return random.randint(lo, hi)


# ── Trigger Classes ──────────────────────────────────────────────────────────
class WeatherTrigger:

    # Zones that can be overridden by the demo "Simulate" buttons
    _simulated_overrides: dict = {}

    @classmethod
    def set_override(cls, zone: str, trigger_type: str, active: bool):
        """Allow frontend demo to force-activate a trigger for a zone."""
        key = f"{zone.lower()}:{trigger_type}"
        cls._simulated_overrides[key] = active

    @classmethod
    def check_rain_trigger(cls, zone: str) -> dict:
        """Trigger if rainfall >= 20 mm."""
        override_key = f"{zone.lower()}:rain"
        if cls._simulated_overrides.get(override_key):
            return {
                "triggered": True,
                "rainfall_mm": 28.5,
                "duration_hours": 6,
                "source": "simulated",
                "message": "Heavy rainfall ≥ 20mm – trigger activated (demo)"
            }
        rainfall = get_mock_rainfall_data(zone)
        triggered = rainfall >= 20
        return {
            "triggered": triggered,
            "rainfall_mm": rainfall,
            "duration_hours": 6 if triggered else 0,
            "source": "imd_mock",
            "message": f"Rainfall {rainfall}mm {'≥ 20mm – TRIGGER ACTIVE' if triggered else '< 20mm'}"
        }

    @classmethod
    def check_heat_trigger(cls, zone: str) -> dict:
        """Trigger if temperature >= 40°C."""
        override_key = f"{zone.lower()}:heat"
        if cls._simulated_overrides.get(override_key):
            return {
                "triggered": True,
                "temperature_c": 42.1,
                "source": "simulated",
                "message": "Extreme heat ≥ 40°C – trigger activated (demo)"
            }
        temp = get_mock_temperature_data(zone)
        triggered = temp >= 40.0
        return {
            "triggered": triggered,
            "temperature_c": temp,
            "source": "temp_mock",
            "message": f"Temperature {temp}°C {'≥ 40°C – TRIGGER ACTIVE' if triggered else '< 40°C'}"
        }

    @classmethod
    def check_flood_trigger(cls, zone: str) -> dict:
        """Trigger for designated Chennai flood-prone zones."""
        override_key = f"{zone.lower()}:flood"
        if cls._simulated_overrides.get(override_key):
            return {
                "triggered": True,
                "water_level": "2.1m",
                "source": "simulated",
                "message": "Flood sensor activated (demo)"
            }
        flood_zones = ["velachery", "madipakkam"]
        triggered = zone.lower() in flood_zones
        return {
            "triggered": triggered,
            "water_level": "1.8m" if triggered else "0.2m",
            "source": "corporation_sensor_mock",
            "message": f"Zone {'is' if triggered else 'is not'} in flood-risk list"
        }

    @classmethod
    def check_aqi_trigger(cls, zone: str) -> dict:
        """Trigger if AQI >= 400."""
        override_key = f"{zone.lower()}:aqi"
        if cls._simulated_overrides.get(override_key):
            return {
                "triggered": True,
                "aqi": 445,
                "duration_hours": 4,
                "source": "simulated",
                "message": "Severe AQI ≥ 400 – trigger activated (demo)"
            }
        aqi = get_mock_aqi_data(zone)
        triggered = aqi >= 400
        return {
            "triggered": triggered,
            "aqi": aqi,
            "duration_hours": 4 if triggered else 0,
            "source": "cpcb_mock",
            "message": f"AQI {aqi} {'≥ 400 – TRIGGER ACTIVE' if triggered else '< 400'}"
        }

    @classmethod
    def check_curfew_trigger(cls, zone: str) -> dict:
        """Trigger if a curfew is declared in the zone."""
        curfew_zones = []  # Empty for demo; add "omr" to test
        triggered = zone.lower() in curfew_zones
        return {
            "triggered": triggered,
            "source": "news_api_mock",
            "message": "Curfew active" if triggered else "No curfew declared"
        }

    @classmethod
    def check_platform_trigger(cls, platform: str, zone: str) -> dict:
        """Trigger if delivery platform is down in zone > 60 min."""
        # Mock: Zepto is down in Velachery for demo
        if platform.lower() == "zepto" and zone.lower() == "velachery":
            return {
                "triggered": True,
                "duration_minutes": 75,
                "source": "platform_status_mock",
                "message": "Zepto platform downtime > 60 min in Velachery"
            }
        return {
            "triggered": False,
            "duration_minutes": 0,
            "source": "platform_status_mock",
            "message": f"{platform} operational in {zone}"
        }

    @classmethod
    def check_all_triggers(cls, zone: str, platforms: list = None) -> dict:
        """Run all triggers for a zone and return combined status."""
        rain = cls.check_rain_trigger(zone)
        heat = cls.check_heat_trigger(zone)
        flood = cls.check_flood_trigger(zone)
        aqi = cls.check_aqi_trigger(zone)
        curfew = cls.check_curfew_trigger(zone)

        platform_status = {}
        if platforms:
            for p in platforms:
                platform_status[p] = cls.check_platform_trigger(p, zone)

        active_triggers = []
        if rain["triggered"]:
            active_triggers.append({"type": "rain", "details": rain})
        if heat["triggered"]:
            active_triggers.append({"type": "heat", "details": heat})
        if flood["triggered"]:
            active_triggers.append({"type": "flood", "details": flood})
        if aqi["triggered"]:
            active_triggers.append({"type": "aqi", "details": aqi})
        if curfew["triggered"]:
            active_triggers.append({"type": "curfew", "details": curfew})
        for p, s in platform_status.items():
            if s["triggered"]:
                active_triggers.append({"type": f"platform_{p}", "details": s})

        return {
            "zone": zone,
            "checked_at": datetime.utcnow().isoformat(),
            "any_triggered": len(active_triggers) > 0,
            "active_triggers": active_triggers,
            "trigger_details": {
                "rain": rain,
                "heat": heat,
                "flood": flood,
                "aqi": aqi,
                "curfew": curfew,
            },
            "platform_status": platform_status,
        }
