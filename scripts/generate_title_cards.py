import os
from PIL import Image, ImageDraw, ImageFont

def create_title_cards():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cards_dir = os.path.join(base_dir, "artifacts", "video", "cards")
    os.makedirs(cards_dir, exist_ok=True)
    
    w, h = 1920, 1080
    bg_color = (8, 12, 21)       # #080C15
    green_color = (61, 205, 88)   # #3DCD58
    cyan_color = (0, 229, 255)    # #00E5FF
    white_color = (241, 245, 249) # #F1F5F9
    gray_color = (148, 163, 184)  # #94A3B8
    card_bg = (18, 27, 44)       # #121B2C
    border_color = (40, 55, 80)
    
    # Try standard fonts
    try:
        font_huge = ImageFont.truetype("arial.ttf", 64)
        font_big = ImageFont.truetype("arial.ttf", 40)
        font_med = ImageFont.truetype("arial.ttf", 26)
        font_small = ImageFont.truetype("arial.ttf", 20)
        font_bold = ImageFont.truetype("arialbd.ttf", 36)
    except Exception:
        font_huge = font_big = font_med = font_small = font_bold = ImageFont.load_default()

    # ----------------------------------------------------
    # 1. OPENING TITLE CARD (0:00 - 0:20)
    # ----------------------------------------------------
    img_open = Image.new("RGB", (w, h), bg_color)
    draw_open = ImageDraw.Draw(img_open)
    
    # Outer decorative glow lines
    draw_open.rectangle([60, 60, w - 60, h - 60], outline=border_color, width=2)
    draw_open.line([60, 60, 260, 60], fill=green_color, width=4)
    draw_open.line([w - 260, h - 60, w - 60, h - 60], fill=cyan_color, width=4)
    
    # Top Tag
    draw_open.text((120, 110), "SCHNEIDER ELECTRIC YUVA YODHA TECH HACKATHON 2026  |  CHALLENGE 03", fill=green_color, font=font_small)
    
    # Main Brand & Title
    draw_open.text((120, 160), "SAANJH", fill=white_color, font=font_huge)
    draw_open.text((120, 245), "Neighbourhood Flexibility Network for Renewable-Deficit Reliability", fill=cyan_color, font=font_big)
    draw_open.text((120, 310), "Sense  →  Forecast  →  Coordinate  →  Dispatch  →  Verify", fill=gray_color, font=font_med)

    # Problem Statement Card (Left)
    draw_open.rounded_rectangle([120, 390, 920, 920], radius=16, fill=card_bg, outline=(255, 70, 70), width=2)
    draw_open.text((150, 420), "THE RENEWABLE INTERMITTENCY CHALLENGE", fill=(255, 100, 100), font=font_bold)
    
    problem_lines = [
        "• Rooftop Solar Drop-Off (Sunset Cliff):",
        "   Midday generation plunges to 0 kW between 16:00 and 18:30.",
        "",
        "• Returning Residential Peak Demand:",
        "   Lighting, cooking, and cooling surge simultaneously.",
        "",
        "• Distribution Transformer Severe Overload:",
        "   Feeder load spikes to 154.1 kW on a 100 kVA asset (115% loading).",
        "   Thermal stress causes 90 minutes of insulation breakdown.",
        "",
        "• Feeder Tail Voltage Collapse:",
        "   Heavy line draw drops tail-end voltage to 218.4V (brownouts)."
    ]
    y_text = 480
    for line in problem_lines:
        draw_open.text((150, y_text), line, fill=white_color if line.startswith("•") else gray_color, font=font_med)
        y_text += 34

    # Solution Card (Right)
    draw_open.rounded_rectangle([980, 390, 1800, 920], radius=16, fill=card_bg, outline=green_color, width=2)
    draw_open.text((1010, 420), "THE SAANJH AUTONOMOUS SOLUTION", fill=green_color, font=font_bold)
    
    sol_lines = [
        "• Aggregated Virtual Community Battery Bank:",
        "   Pools 33 kW / 16.6 kWh of existing household inverter-batteries.",
        "",
        "• Edge AI 1-Step Load Forecasting (XGBoost):",
        "   Predicts the evening deficit 15-45 mins before feeder strain.",
        "",
        "• Autonomous Local Coordination via 865 MHz LoRa Mesh:",
        "   Dispatches 56.25 kW across 39 homes without internet dependency.",
        "",
        "• Invariant Guarantees & Grid Recovery:",
        "   ≥70% SOC floor preserved (0 breaches) | 0 critical load cuts.",
        "   Peak shaved by 44.95 kW (29.2%) | Overload cut by 30 minutes."
    ]
    y_text = 480
    for line in sol_lines:
        draw_open.text((1010, y_text), line, fill=white_color if line.startswith("•") else gray_color, font=font_med)
        y_text += 34

    open_path = os.path.join(cards_dir, "opening_card.png")
    img_open.save(open_path)
    print(f"Generated opening title card at {open_path}")

    # ----------------------------------------------------
    # 2. CLOSING CONCLUSION CARD (4:54 - 5:09)
    # ----------------------------------------------------
    img_close = Image.new("RGB", (w, h), bg_color)
    draw_close = ImageDraw.Draw(img_close)
    
    draw_close.rectangle([60, 60, w - 60, h - 60], outline=border_color, width=2)
    draw_close.line([60, 60, 260, 60], fill=green_color, width=4)
    draw_close.line([w - 260, h - 60, w - 60, h - 60], fill=cyan_color, width=4)

    draw_close.text((120, 110), "SCHNEIDER ELECTRIC YUVA YODHA TECH HACKATHON 2026  |  FINAL SUBMISSION", fill=green_color, font=font_small)
    draw_close.text((120, 155), "SAANJH — VERIFIED GRID RELIABILITY", fill=white_color, font=font_huge)
    draw_close.text((120, 240), "Turning Distributed Neighbourhood Flexibility into Dependable Grid Services", fill=cyan_color, font=font_big)

    # 4 Metric Boxes
    box_w = 380
    box_h = 240
    boxes = [
        {"title": "NET PEAK REDUCTION", "val": "↓ 44.95 kW", "sub": "29.2% Shaved (154.1 → 109.2 kW)", "color": green_color},
        {"title": "OVERLOAD AVOIDANCE", "val": "30 MINS", "sub": "33.3% Cut (90m → 60m duration)", "color": green_color},
        {"title": "VOLTAGE QUALITY", "val": "0 VIOLATIONS", "sub": "100% Eliminated (>226V tail)", "color": cyan_color},
        {"title": "CAPEX EFFICIENCY", "val": "₹7,068 / kW", "sub": "84% Cheaper than Utility BESS", "color": (168, 85, 247)}
    ]
    
    x_start = 120
    for idx, b in enumerate(boxes):
        bx = x_start + idx * (box_w + 33)
        by = 330
        draw_close.rounded_rectangle([bx, by, bx + box_w, by + box_h], radius=14, fill=card_bg, outline=b["color"], width=2)
        draw_close.text((bx + 25, by + 30), b["title"], fill=gray_color, font=font_small)
        draw_close.text((bx + 25, by + 75), b["val"], fill=b["color"], font=font_huge)
        draw_close.text((bx + 25, by + 170), b["sub"], fill=white_color, font=font_med)

    # Bottom Summary Card
    draw_close.rounded_rectangle([120, 620, 1800, 920], radius=16, fill=card_bg, outline=border_color, width=1)
    draw_close.text((150, 650), "ENGINEERING VERIFICATION & REPRODUCIBILITY SUMMARY", fill=green_color, font=font_bold)
    
    summary_items = [
        "✔ 100% PyPSA AC Newton-Raphson Load Flow Convergence (All 72 five-minute snapshots validated).",
        "✔ Real-World XGBoost Forecaster trained on UCI benchmark data with 0 data leakage & early stopping.",
        "✔ Physical Hardware-in-the-Loop demonstrated on RAKwireless WisBlock LoRa 865 MHz telemetry.",
        "✔ Hard Reserve Floor Invariant: All participating batteries maintained ≥70% emergency capacity (min final SOC = 81%).",
        "✔ Complete Open-Source Repository & Live Control Center: https://atharveeee-netizen.github.io/saanjh/"
    ]
    sy = 710
    for it in summary_items:
        draw_close.text((150, sy), it, fill=white_color, font=font_med)
        sy += 36

    close_path = os.path.join(cards_dir, "closing_card.png")
    img_close.save(close_path)
    print(f"Generated closing title card at {close_path}")

if __name__ == "__main__":
    create_title_cards()
