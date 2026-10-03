import math
from simulation.config import SOLAR_PANEL_RATING_W

class SolarPanel:
    @staticmethod
    def get_generation(hour):
        # Simplified curve peaking at 12:00, dropping to zero by 18:30
        if hour >= 18.5 or hour <= 6:
            return 0
        
        # Scale hour to range [-pi/2, pi/2] around noon
        # 6 AM = -pi/2, 12 PM = 0, 18 PM = pi/2
        normalized_time = (hour - 12) / 6
        if normalized_time > 1 or normalized_time < -1:
            return 0
            
        return SOLAR_PANEL_RATING_W * math.cos(normalized_time * math.pi / 2)
