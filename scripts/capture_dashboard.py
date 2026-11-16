"""Capture 1080p screenshots of every dashboard tab for the demo video.

Optional tooling, not part of the runtime dependencies:

    pip install playwright
    python scripts/capture_dashboard.py --url http://localhost:8501

Uses the system Chrome by default. Pass ``--channel msedge`` for Edge. The
Streamlit server must already be running. The screenshots land in
``docs/figures/dashboard/`` and are committed as recording assets.
"""
import argparse
import os

from playwright.sync_api import sync_playwright

TABS = [
    ("1_reliability", "Reliability"),
    ("2_energy_balance", "Energy balance"),
    ("3_low_income", "Low-income economics"),
    ("4_robustness", "Overload & robustness"),
    ("5_calibration", "India calibration"),
    ("6_hil_gateway", "HIL gateway"),
    ("7_discom_dispatch", "DISCOM dispatch"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://localhost:8501")
    ap.add_argument("--channel", default="chrome")
    ap.add_argument("--out", default=os.path.join("docs", "figures", "dashboard"))
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=args.channel, headless=True)
        page = browser.new_page(viewport={"width": args.width, "height": args.height})
        page.goto(args.url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("[role='tab']", timeout=60000)
        page.wait_for_timeout(2500)
        page.add_style_tag(content="""
            header[data-testid="stHeader"] {display: none;}
            [data-testid="stToolbar"] {display: none;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
        """)

        tabs = page.get_by_role("tab")
        labels = [tabs.nth(i).inner_text() for i in range(tabs.count())]
        print("tabs:", labels)
        if len(labels) != len(TABS):
            raise SystemExit(f"expected {len(TABS)} tabs, found {len(labels)}")

        for index, (name, needle) in enumerate(TABS):
            match = next((i for i, label in enumerate(labels) if needle in label), None)
            if match is None:
                raise SystemExit(f"tab not found: {needle}")
            tabs.nth(match).click()
            page.wait_for_timeout(1800)
            path = os.path.join(args.out, f"{name}.png")
            page.screenshot(path=path)
            print("wrote", path)

        browser.close()


if __name__ == "__main__":
    main()
