"""AC power-flow check of a feeder load profile with PyPSA.

Model: the DT low-voltage bus is the slack bus at nominal voltage; one lumped, balanced
three-phase LT line feeds a load-centre bus carrying the whole neighbourhood load at the
configured power factor. Results are tail-end phase voltage and line losses. This is a
simplified feeder (no per-phase imbalance, no distributed loads along the line); every
result that uses it states so.
"""
import logging
import warnings

import numpy as np
import pandas as pd

logging.getLogger("pypsa").setLevel(logging.WARNING)
logging.getLogger("linopy").setLevel(logging.WARNING)


def run_power_flow(load_kw, cfg):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        return _run_power_flow(load_kw, cfg)


def _run_power_flow(load_kw, cfg):
    import pypsa

    elec = cfg["electrical"]
    v_phase = elec["voltage_nominal_v"]
    v_ll_kv = v_phase * np.sqrt(3) / 1000.0
    pf = elec["power_factor"]
    line = elec["lt_feeder"]

    load_kw = np.asarray(load_kw, dtype=float)
    n = pypsa.Network()
    n.set_snapshots(pd.RangeIndex(len(load_kw)))
    n.add("Bus", "dt_lv", v_nom=v_ll_kv)
    n.add("Generator", "dt_secondary", bus="dt_lv", control="Slack")
    n.add("Bus", "load_centre", v_nom=v_ll_kv)
    n.add("Line", "lt_feeder", bus0="dt_lv", bus1="load_centre",
          r=line["r_ohm"], x=line["x_ohm"], s_nom=line["s_nom_mva"])
    p_mw = load_kw / 1000.0
    q_mvar = p_mw * np.tan(np.arccos(pf))
    n.add("Load", "neighbourhood", bus="load_centre", p_set=p_mw, q_set=q_mvar)
    n.pf()

    v_pu = n.buses_t.v_mag_pu["load_centre"].to_numpy()
    loss_kw = (n.lines_t.p0["lt_feeder"].to_numpy() + n.lines_t.p1["lt_feeder"].to_numpy()) * 1000.0
    return pd.DataFrame({
        "voltage_pu": v_pu,
        "voltage_v": v_pu * v_phase,
        "line_loss_kw": np.maximum(0.0, loss_kw),
    })
