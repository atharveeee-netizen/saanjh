import os
import yaml

# Path to the new configuration file
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'saanjh.yaml')

with open(config_path, 'r') as f:
    _cfg = yaml.safe_load(f)

# Transformer
TRANSFORMER_RATING_KVA = _cfg['transformer']['rating_kva']
TRANSFORMER_RATED_TEMP_C = _cfg['transformer']['rated_temp_c']
TRANSFORMER_AMBIENT_C = _cfg['transformer']['ambient_c']
VOLTAGE_NOMINAL = _cfg['transformer']['voltage_nominal']

# Neighbourhood
NUM_HOMES = _cfg['neighbourhood']['num_homes']
HOMES_WITH_INVERTER_BATTERY = _cfg['neighbourhood']['homes_with_inverter_battery']
HOMES_WITH_SOLAR = _cfg['neighbourhood']['homes_with_solar']

# Probabilities
PROB_AC = _cfg['probabilities']['ac']
PROB_EV = _cfg['probabilities']['ev']
PROB_WATER_HEATER = _cfg['probabilities']['water_heater']
PROB_WATER_PUMP = _cfg['probabilities']['water_pump']

# Battery
BATTERY_CAPACITY_WH = _cfg['battery']['capacity_wh']
BATTERY_INVERTER_RATING_W = _cfg['battery']['inverter_rating_w']
BATTERY_RESERVE_SOC = _cfg['battery']['reserve_soc']
BATTERY_AVAILABLE_SOC = _cfg['battery']['available_soc']

# Solar
SOLAR_PANEL_RATING_W = _cfg['solar']['panel_rating_w']

# SAANJH dispatch
MAX_EVENT_DURATION_MIN = _cfg['dispatch']['max_event_duration_min']
DISPATCH_STAGGER_GROUPS = _cfg['dispatch']['stagger_groups']
REBOUND_RECOVERY_MIN = _cfg['dispatch']['rebound_recovery_min']

# Load profiles
LOAD_PROFILES = _cfg['load_profiles']
