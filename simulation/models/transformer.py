from simulation.config import TRANSFORMER_RATING_KVA, TRANSFORMER_RATED_TEMP_C, TRANSFORMER_AMBIENT_C

class Transformer:
    def __init__(self):
        self.rating_kva = TRANSFORMER_RATING_KVA
        self.ambient_c = TRANSFORMER_AMBIENT_C
        self.rated_rise_c = TRANSFORMER_RATED_TEMP_C - TRANSFORMER_AMBIENT_C
        
    def get_loading_percent(self, load_kw):
        # Assuming PF = 0.95
        apparent_power_kva = load_kw / 0.95
        return (apparent_power_kva / self.rating_kva) * 100
        
    def get_temperature(self, loading_percent):
        # Simplified thermal model
        return self.ambient_c + self.rated_rise_c * (loading_percent / 100.0)**2
