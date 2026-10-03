import os
import time
import glob
import subprocess
from playwright.sync_api import sync_playwright

def smooth_move_mouse(page, start_x, start_y, end_x, end_y, steps=25, delay=0.02):
    for i in range(1, steps + 1):
        x = start_x + (end_x - start_x) * (i / float(steps))
        y = start_y + (end_y - start_y) * (i / float(steps))
        page.mouse.move(x, y)
        time.sleep(delay)

def record_walkthrough():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vid_raw_dir = os.path.join(base_dir, "artifacts", "video", "raw_walkthrough")
    os.makedirs(vid_raw_dir, exist_ok=True)
    
    # Clean previous raw webm recordings
    for f in glob.glob(os.path.join(vid_raw_dir, "*.webm")):
        try:
            os.remove(f)
        except Exception:
            pass

    html_file = os.path.join(base_dir, "docs", "index.html")
    file_uri = "file:///" + html_file.replace("\\", "/")

    print(f"Opening browser to record master walkthrough from {file_uri}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir=vid_raw_dir,
            record_video_size={"width": 1920, "height": 1080},
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        page.goto(file_uri)
        page.wait_for_timeout(3000)

        # ----------------------------------------------------
        # STORYBOARD 1 & 2: LANDING / OVERVIEW & TOPOLOGY (0-20s)
        # ----------------------------------------------------
        print("Recording Step 1 & 2: Landing, Overview & System Parameters...")
        # Hover brand & status badge
        smooth_move_mouse(page, 960, 540, 200, 30, steps=20, delay=0.03)
        page.wait_for_timeout(3000)
        smooth_move_mouse(page, 200, 30, 1600, 30, steps=25, delay=0.03)
        page.wait_for_timeout(3000)
        
        # Hover Hero Title and System Tags
        smooth_move_mouse(page, 1600, 30, 450, 120, steps=20, delay=0.03)
        page.wait_for_timeout(4000)
        smooth_move_mouse(page, 450, 120, 1100, 130, steps=25, delay=0.03)
        page.wait_for_timeout(4000)

        # ----------------------------------------------------
        # STORYBOARD 3, 4, 5: KPI CARDS INSPECTION (20-60s)
        # ----------------------------------------------------
        print("Recording Step 3-5: Inspecting 6 Core KPI Cards...")
        # Card 1: Feeder Peak
        smooth_move_mouse(page, 1100, 130, 160, 220, steps=20, delay=0.03)
        page.wait_for_timeout(4000)
        # Card 2: Flexibility
        smooth_move_mouse(page, 160, 220, 400, 220, steps=20, delay=0.03)
        page.wait_for_timeout(4000)
        # Card 3: Overload
        smooth_move_mouse(page, 400, 220, 640, 220, steps=20, delay=0.03)
        page.wait_for_timeout(4000)
        # Card 4: Voltage Violations
        smooth_move_mouse(page, 640, 220, 880, 220, steps=20, delay=0.03)
        page.wait_for_timeout(4000)
        # Card 5: Resistive Losses
        smooth_move_mouse(page, 880, 220, 1120, 220, steps=20, delay=0.03)
        page.wait_for_timeout(4000)
        # Card 6: CapEx Efficiency
        smooth_move_mouse(page, 1120, 220, 1360, 220, steps=20, delay=0.03)
        page.wait_for_timeout(5000)

        # ----------------------------------------------------
        # STORYBOARD 6, 7, 8: TAB 1 - FEEDER DEMAND & SOLAR CLIFF (60-100s)
        # ----------------------------------------------------
        print("Recording Step 6-8: Tab 1 Feeder Demand & Solar Cliff...")
        # Hover Tab 1 Button
        smooth_move_mouse(page, 1360, 220, 150, 310, steps=20, delay=0.03)
        page.wait_for_timeout(2000)
        
        # Move across the load curve chart (showing tooltips)
        chart_x_start = 120
        chart_x_end = 850
        chart_y = 520
        for x in range(chart_x_start, chart_x_end, 75):
            smooth_move_mouse(page, x, chart_y, x + 75, chart_y, steps=8, delay=0.02)
            page.wait_for_timeout(1000)
            
        page.wait_for_timeout(3000)
        # Inspect Right Side Stat Panel (Intermittency Dynamics)
        smooth_move_mouse(page, chart_x_end, chart_y, 1150, 420, steps=20, delay=0.03)
        page.wait_for_timeout(3500)
        smooth_move_mouse(page, 1150, 420, 1150, 520, steps=15, delay=0.03)
        page.wait_for_timeout(3500)
        smooth_move_mouse(page, 1150, 520, 1150, 680, steps=15, delay=0.03)
        page.wait_for_timeout(5000)

        # ----------------------------------------------------
        # STORYBOARD 9, 10: TAB 2 - AC VOLTAGE & POWER QUALITY (100-135s)
        # ----------------------------------------------------
        print("Recording Step 9-10: Tab 2 AC Voltage & Power Quality (PyPSA)...")
        # Click Tab 2
        smooth_move_mouse(page, 1150, 680, 340, 310, steps=25, delay=0.03)
        page.click("#btn-tab-voltage")
        page.wait_for_timeout(2500)

        # Inspect Voltage chart curve
        for x in range(chart_x_start, chart_x_end, 90):
            smooth_move_mouse(page, x, chart_y, x + 90, chart_y, steps=8, delay=0.02)
            page.wait_for_timeout(1000)

        page.wait_for_timeout(3000)
        # Inspect Voltage Quality Metrics panel & Local Inverter Reactive Support
        smooth_move_mouse(page, chart_x_end, chart_y, 1150, 430, steps=20, delay=0.03)
        page.wait_for_timeout(4000)
        smooth_move_mouse(page, 1150, 430, 1150, 680, steps=15, delay=0.03)
        page.wait_for_timeout(5000)

        # ----------------------------------------------------
        # STORYBOARD 11, 12, 13: TAB 3 - ASSET FLEXIBILITY & BATTERY VPP (135-170s)
        # ----------------------------------------------------
        print("Recording Step 11-13: Tab 3 Asset Flexibility & Battery VPP...")
        # Click Tab 3
        smooth_move_mouse(page, 1150, 680, 570, 310, steps=25, delay=0.03)
        page.click("#btn-tab-flexibility")
        page.wait_for_timeout(2500)

        # Inspect Flexibility chart
        for x in range(chart_x_start, chart_x_end, 90):
            smooth_move_mouse(page, x, chart_y, x + 90, chart_y, steps=8, delay=0.02)
            page.wait_for_timeout(1000)

        page.wait_for_timeout(3000)
        # Inspect Fleet Invariants: 81% SOC, 0 cuts, 0 overrides
        smooth_move_mouse(page, chart_x_end, chart_y, 1150, 430, steps=20, delay=0.03)
        page.wait_for_timeout(4000)
        smooth_move_mouse(page, 1150, 430, 1150, 680, steps=15, delay=0.03)
        page.wait_for_timeout(5000)

        # ----------------------------------------------------
        # STORYBOARD 14, 15: TAB 4 - AI FORECASTER & TRAINING AUDIT (170-205s)
        # ----------------------------------------------------
        print("Recording Step 14-15: Tab 4 AI Forecaster & Training Audit...")
        # Click Tab 4
        smooth_move_mouse(page, 1150, 680, 800, 310, steps=25, delay=0.03)
        page.click("#btn-tab-forecaster")
        page.wait_for_timeout(2500)

        # Inspect XGBoost Loss curve
        for x in range(chart_x_start, chart_x_end, 90):
            smooth_move_mouse(page, x, chart_y, x + 90, chart_y, steps=8, delay=0.02)
            page.wait_for_timeout(1000)

        page.wait_for_timeout(3000)
        # Inspect Benchmark table and Scientific Integrity Note
        smooth_move_mouse(page, chart_x_end, chart_y, 1150, 440, steps=20, delay=0.03)
        page.wait_for_timeout(4000)
        smooth_move_mouse(page, 1150, 440, 1150, 680, steps=15, delay=0.03)
        page.wait_for_timeout(5000)

        # ----------------------------------------------------
        # STORYBOARD 16, 17: TAB 5 - DISCOM DIRECTIVES & ECONOMICS (205-235s)
        # ----------------------------------------------------
        print("Recording Step 16-17: Tab 5 DISCOM Directives & Economics...")
        # Click Tab 5
        smooth_move_mouse(page, 1150, 680, 1030, 310, steps=25, delay=0.03)
        page.click("#btn-tab-discom")
        page.wait_for_timeout(2500)

        # Hover Execution Directive Banner
        smooth_move_mouse(page, 1030, 310, 400, 440, steps=20, delay=0.03)
        page.wait_for_timeout(5000)

        # Hover Sensitivity table
        smooth_move_mouse(page, 400, 440, 400, 620, steps=15, delay=0.03)
        page.wait_for_timeout(4000)

        # Hover Stakeholder Value Stack
        smooth_move_mouse(page, 400, 620, 1150, 450, steps=20, delay=0.03)
        page.wait_for_timeout(4000)
        smooth_move_mouse(page, 1150, 450, 1150, 680, steps=15, delay=0.03)
        page.wait_for_timeout(5000)

        # ----------------------------------------------------
        # STORYBOARD 18: RETURN TO HERO OVERVIEW & SUMMARY (235-245s)
        # ----------------------------------------------------
        print("Recording Step 18: Return to Hero Overview...")
        smooth_move_mouse(page, 1150, 680, 150, 310, steps=25, delay=0.03)
        page.click("#btn-tab-demand")
        page.wait_for_timeout(2500)
        smooth_move_mouse(page, 150, 310, 960, 220, steps=25, delay=0.03)
        page.wait_for_timeout(7500)

        print("Recording finished. Closing browser context...")
        context.close()
        browser.close()

    # Locate raw webm and transcode to master mp4
    raw_files = glob.glob(os.path.join(vid_raw_dir, "*.webm"))
    if not raw_files:
        print("Error: No raw webm video found!")
        return False
        
    raw_video = raw_files[0]
    out_master_mp4 = os.path.join(base_dir, "artifacts", "video", "saanjh_website_walkthrough_master.mp4")
    
    print(f"Transcoding raw recording {raw_video} to {out_master_mp4} (1080p 30FPS H.264, no audio)...")
    ffmpeg_exe = r"C:\Users\noobg\AppData\Local\Microsoft\WinGet\Packages\yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-N-124279-g0f6ba39122-win64-gpl\bin\ffmpeg.exe"
    
    cmd = [
        ffmpeg_exe, "-y",
        "-i", raw_video,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-an",
        out_master_mp4
    ]
    
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        print(f"Successfully generated: {out_master_mp4}")
        return True
    else:
        print(f"FFmpeg transcode failed:\n{res.stderr}")
        return False

if __name__ == "__main__":
    record_walkthrough()
