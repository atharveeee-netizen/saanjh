# Transformer
TRANSFORMER_RATING_KVA = 100
TRANSFORMER_RATED_TEMP_C = 65
TRANSFORMER_AMBIENT_C = 35
VOLTAGE_NOMINAL = 230

# Neighbourhood
NUM_HOMES = 60
HOMES_WITH_INVERTER_BATTERY = 42  # 70% penetration (realistic for urban India)
HOMES_WITH_SOLAR = 15             # 25% penetration

# Household load profiles (watts, by category)
# These represent TYPICAL Indian urban evening loads
LOAD_PROFILES = {
    "lighting": {"base": 100, "peak_add": 80, "deferrable": False},
    "fans": {"base": 150, "peak_add": 0, "deferrable": False},
    "tv": {"base": 120, "peak_add": 0, "deferrable": False},
    "refrigerator": {"base": 200, "peak_add": 0, "deferrable": False},
    "cooking": {"base": 0, "peak_add": 800, "deferrable": False},  # induction/mixer
    "water_heater": {"base": 0, "peak_add": 2000, "deferrable": True, "duration_min": 20},
    "ac": {"base": 0, "peak_add": 1500, "deferrable": True, "duration_min": 60},
    "washing_machine": {"base": 0, "peak_add": 500, "deferrable": True, "duration_min": 45},
    "ev_charger": {"base": 0, "peak_add": 1500, "deferrable": True, "duration_min": 120},
    "water_pump": {"base": 0, "peak_add": 750, "deferrable": True, "duration_min": 30},
}

# Probabilities of having specific high-load appliances
PROB_AC = 0.55          # 55% homes have AC (urban India summer)
PROB_EV = 0.08          # 8% homes have EV
PROB_WATER_HEATER = 0.6 # 60% homes use geyser in evening
PROB_WATER_PUMP = 0.3   # 30% homes run pump in evening

# Inverter battery
BATTERY_CAPACITY_WH = 1800  # typical 150Ah/12V
BATTERY_INVERTER_RATING_W = 800
BATTERY_RESERVE_SOC = 0.70
BATTERY_AVAILABLE_SOC = 0.22  # 92% - 70% reserve = ~400 Wh available

# Solar
SOLAR_PANEL_RATING_W = 1000  # 1 kW rooftop

# SAANJH dispatch
MAX_EVENT_DURATION_MIN = 120
DISPATCH_STAGGER_GROUPS = 4
REBOUND_RECOVERY_MIN = 30
