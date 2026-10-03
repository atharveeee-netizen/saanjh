from simulation.config import MAX_EVENT_DURATION_MIN

class SAANJHDispatcher:
    def __init__(self, target_transformer_limit_kw):
        self.target_limit_kw = target_transformer_limit_kw
        
    def calculate_required_flexibility(self, forecast_load_kw):
        return max(0, forecast_load_kw - self.target_limit_kw)
        
    def dispatch(self, households, required_flex_kw, duration_min):
        if required_flex_kw <= 0:
            return 0, 0
            
        # Sort households by available flexibility (descending) and participation count (ascending)
        available_homes = [h for h in households if not h.is_dispatched and h.get_available_flexibility() > 0]
        available_homes.sort(key=lambda h: (-h.get_available_flexibility(), h.participation_count))
        
        dispatched_flex_w = 0
        homes_dispatched = 0
        
        for h in available_homes:
            if dispatched_flex_w >= required_flex_kw * 1000:
                break
                
            flex_w = h.get_available_flexibility()
            h.dispatch(duration_min)
            dispatched_flex_w += flex_w
            homes_dispatched += 1
            
        return dispatched_flex_w / 1000.0, homes_dispatched
