class Transformer:
    def __init__(self, rating_kva, power_factor):
        self.rating_kva = rating_kva
        self.power_factor = power_factor

    @property
    def rating_kw(self):
        return self.rating_kva * self.power_factor

    def loading_pct(self, load_kw):
        """Apparent-power loading. Reverse flow (net export) also loads the transformer."""
        return abs(load_kw) / self.power_factor / self.rating_kva * 100.0
