"""Essential-band load limiting through the smart meter's load-limit function.

Instead of disconnecting a home, the DISCOM's smart meter caps it at an essential power
band (default 500 W). Within the band a home can run lights, fans, a fridge and phone
charging. Homes flagged as critical (a registered medical device, or a small enterprise
that depends on refrigeration) get a higher band.

Smart-meter load limiting trips the supply if the limit is exceeded for longer than a
set delay; a short grace window stops fridge and fan motor inrush (a few times running
current for well under a second) from tripping it. ``meter_trips`` models that logic on
a high-resolution trace. The 15-minute simulation works with average power, so a banded
home's average draw is simply capped at its band: the household is assumed to switch
off heavier appliances (as Eskom's load-limiting customers are asked to) rather than
trip repeatedly.
"""
import numpy as np


class EssentialBand:
    def __init__(self, cfg, critical_mask):
        self.band_w = cfg["band_w"]
        self.critical_band_w = cfg["critical_band_w"]
        self.ladder_w = sorted({*cfg.get("ladder_w", []), self.band_w}, reverse=True)
        self.ladder_w = [w for w in self.ladder_w if w >= self.band_w]
        self.grace_s = cfg["grace_s"]
        self.critical = np.asarray(critical_mask, dtype=bool)

    def limits_kw(self, level_w):
        """Per-home limit in kW for a band level; critical homes keep their higher band."""
        return np.where(self.critical, max(level_w, self.critical_band_w), level_w) / 1000.0

    def reduction_kw(self, draw_kw, level_w, homes=None):
        """kW removed if ``homes`` (default all) are capped at ``level_w``."""
        cut = np.maximum(0.0, draw_kw - self.limits_kw(level_w))
        if homes is not None:
            cut = np.where(homes, cut, 0.0)
        return cut

    @staticmethod
    def meter_trips(trace_w, dt_s, limit_w, grace_s):
        """True if ``trace_w`` stays above ``limit_w`` for longer than ``grace_s``."""
        over = np.asarray(trace_w) > limit_w
        run = 0.0
        for o in over:
            run = run + dt_s if o else 0.0
            if run > grace_s:
                return True
        return False
