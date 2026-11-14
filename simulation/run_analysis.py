"""Regenerate every analysis deliverable in one command.

    python simulation/run_analysis.py                 # default reduced Monte Carlo
    python simulation/run_analysis.py --only reliability energy_balance

Outputs (committed so a fresh clone and the dashboard work without re-running):
    simulation/results/reliability.json
    simulation/results/energy_balance.json
    simulation/results/low_income.json
    simulation/results/overload.json
    simulation/results/robustness.json
    simulation/results/calibration.json

The annual ``results.json`` is produced separately by ``simulation/run_year.py``.
These analyses use fewer seeds than the annual run so the repository stays reproducible
on a laptop; the seed counts are written into every JSON file.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simulation.calibration_cases as calibration_cases
import simulation.energy_balance as energy_balance
import simulation.low_income as low_income
import simulation.overload as overload
import simulation.reliability as reliability
import simulation.robustness as robustness

STEPS = {
    "energy_balance": lambda a: energy_balance.build(),
    "calibration": lambda a: calibration_cases.build(),
    "reliability": lambda a: reliability.build(seeds=a.reliability_seeds, workers=a.workers),
    "low_income": lambda a: low_income.build(seeds=a.scenario_seeds, workers=a.workers),
    "overload": lambda a: overload.build(seeds=a.scenario_seeds, workers=a.workers),
    "robustness": lambda a: robustness.build(seeds=a.robustness_seeds, workers=a.workers),
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", choices=list(STEPS), default=list(STEPS))
    ap.add_argument("--reliability-seeds", type=int, default=5)
    ap.add_argument("--scenario-seeds", type=int, default=2)
    ap.add_argument("--robustness-seeds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args(argv)
    t0 = time.time()
    for name in a.only:
        t = time.time()
        _, path = STEPS[name](a)
        print(f"{name:15s} {time.time() - t:7.1f} s -> {path}", flush=True)
    print(f"Done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
