"""Rooftop PV output.

``clear_sky_profile`` is a SIMULATED stand-in (cosine shape, sunrise 06:00, sunset 18:30).
Prompt 3 replaces it with NASA POWER irradiance where available.
"""
import numpy as np


def clear_sky_profile(hours, kwp, sunrise=6.0, sunset=18.5):
    """kW output per kWp for an array of clock hours."""
    hours = np.asarray(hours, dtype=float) % 24
    mid = (sunrise + sunset) / 2
    half = (sunset - sunrise) / 2
    x = (hours - mid) / half
    out = np.where(np.abs(x) < 1, np.cos(x * np.pi / 2), 0.0)
    return kwp * 0.8 * out   # 0.8 performance ratio
