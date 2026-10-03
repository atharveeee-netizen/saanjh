from playwright.sync_api import sync_playwright
import time
import os
import glob

def record():
    vid_dir = os.path.abspath("artifacts/video")
    os.makedirs(vid_dir, exist_ok=True)
    
    # Remove old webm files to ensure we grab the right one
    for f in glob.glob(os.path.join(vid_dir, "*.webm")):
        try:
            os.remove(f)
        except:
            pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir=vid_dir,
            record_video_size={"width": 1920, "height": 1080},
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        print("Navigating to dashboard...")
        page.goto("http://localhost:8501")
        
        # Wait for the main container to load
        page.wait_for_timeout(5000)
        
        print("Scrolling through the dashboard...")
        # Scroll down slowly to show the graphs
        for _ in range(8):
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(2000)
            
        print("Recording complete.")
        context.close()
        browser.close()
        
    # rename the output to dashboard_recording.webm
    webm_files = glob.glob(os.path.join(vid_dir, "*.webm"))
    if webm_files:
        os.rename(webm_files[0], os.path.join(vid_dir, "dashboard_recording.webm"))
        print("Dashboard recording saved as dashboard_recording.webm")

if __name__ == "__main__":
    record()
