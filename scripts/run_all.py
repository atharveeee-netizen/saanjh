"""Regenerate and verify every SAANJH deliverable with one command.

    python scripts/run_all.py --quick     # contracts, replay evidence, docs, tests
    python scripts/run_all.py             # analyses + replay + docs + tests
    python scripts/run_all.py --annual    # also re-run the 30-seed annual simulation

The stages are ordered so each one verifies the previous output. Everything is
invoked through the current Python interpreter, so it works from a fresh clone
inside the project's virtual environment.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def run(label: str, command: list[str], allow_missing: bool = False) -> bool:
    print(f"\n=== {label} ===", flush=True)
    print("$ " + " ".join(command), flush=True)
    started = time.time()
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except FileNotFoundError:
        if allow_missing:
            print(f"SKIP {label}: {command[0]} not installed", flush=True)
            return False
        raise
    except subprocess.CalledProcessError as exc:
        print(f"FAIL {label} (exit {exc.returncode})", flush=True)
        raise
    print(f"OK {label} ({time.time() - started:.1f} s)", flush=True)
    return True


def platformio() -> list[str] | None:
    if shutil.which("pio"):
        return ["pio"]
    try:
        subprocess.run([PY, "-m", "platformio", "--version"],
                       cwd=ROOT, check=True, capture_output=True)
        return [PY, "-m", "platformio"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true",
                        help="skip the analysis rebuild; keep contracts, replay, docs and tests")
    parser.add_argument("--annual", action="store_true",
                        help="also re-run the 30-seed annual simulation (slow)")
    parser.add_argument("--firmware", action="store_true",
                        help="build the three RAK4631 images and run the native tests")
    parser.add_argument("--skip-tests", action="store_true", help="skip pytest")
    args = parser.parse_args(argv)

    if not args.quick:
        run("analysis bundles", [PY, "simulation/run_analysis.py"])

    if args.annual:
        run("annual simulation", [PY, "simulation/run_year.py"])

    # Schemas are derived from the contracts, so regenerate after the bundles.
    run("result contracts + schemas", [PY, "-m", "simulation.contracts", "--write-schemas"])

    run("gateway replay evidence", [
        PY, "-m", "gateway.service",
        "--mode", "replay", "--nodes", "3", "--hours", "6",
        "--duration-min", "45", "--packet-loss", "0.02",
    ])
    run("contracts after replay", [PY, "-m", "simulation.contracts"])
    run("docs match results.json", [PY, "scripts/render_results.py", "--check"])

    if args.firmware:
        pio = platformio()
        if pio is None:
            print("\nSKIP firmware: PlatformIO is not installed "
                  "(python -m pip install platformio)", flush=True)
        else:
            run("firmware images", pio + ["run", "-e", "node101", "-e", "node102", "-e", "node103"])
            run("native firmware tests", pio + ["test", "-e", "native"], allow_missing=True)

    if not args.skip_tests:
        run("python test suite", [PY, "-m", "pytest", "-q"])

    print("\nAll requested stages completed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
