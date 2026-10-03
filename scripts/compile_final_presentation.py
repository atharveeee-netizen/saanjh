import os
import subprocess

def compile_presentation():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    vid_dir = os.path.join(base_dir, 'artifacts', 'video')
    
    # 1. Hardware Video
    hardware_vid = r"C:\Users\noobg\Downloads\WhatsApp Video 2026-09-20 at 11.00.02 PM.mp4"
    if not os.path.exists(hardware_vid):
        print(f"Error: Could not find hardware video at {hardware_vid}")
        return
        
    # 2. Dashboard Video
    dashboard_vid = os.path.join(vid_dir, 'dashboard_recording.webm')
    if not os.path.exists(dashboard_vid):
        print(f"Error: Could not find dashboard video at {dashboard_vid}")
        return
        
    # 3. Blender Video
    blender_vid = os.path.join(vid_dir, 'saanjh_digital_twin.mp4')
    if not os.path.exists(blender_vid):
        blender_vid = os.path.join(vid_dir, 'saanjh_digital_twin_preview.mp4')
        print(f"Using blender preview video: {blender_vid}")
    else:
        print(f"Using full blender video: {blender_vid}")
        
    output_vid = os.path.join(vid_dir, 'saanjh_final_presentation.mp4')
    
    print("Stitching the videos into a 1920x1080 30FPS final cut...")
    
    # We will use ffmpeg filter_complex to scale/pad everything to 1920x1080, format the audio (or add silent audio if missing), and concat.
    
    # Assuming hardware video has audio, dashboard doesn't, blender doesn't.
    # We generate silent audio for dashboard and blender.
    cmd = [
        'ffmpeg', '-y',
        '-i', hardware_vid,
        '-i', dashboard_vid,
        '-i', blender_vid,
        '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100', # dummy audio
        '-filter_complex',
        (
            "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v0];"
            "[1:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v1];"
            "[2:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v2];"
            
            # map audio (hardware has audio [0:a], dummy for others)
            "[v0][0:a][v1][3:a][v2][3:a]concat=n=3:v=1:a=1[v][a]"
        ),
        '-map', '[v]',
        '-map', '[a]',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
        '-c:a', 'aac', '-shortest',
        output_vid
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        print(f"Successfully compiled {output_vid}")
    else:
        print(f"FFmpeg failed:\n{result.stderr}")

if __name__ == "__main__":
    compile_presentation()
