import os
import subprocess
import glob
import sys

def compile_video(fps, output_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    frames_dir = os.path.join(base_dir, 'artifacts', 'video', 'frames')
    output_path = os.path.join(base_dir, 'artifacts', 'video', output_name)
    
    frames = sorted(glob.glob(os.path.join(frames_dir, 'frame_*.jpg')))
    if not frames:
        print("No frames found!")
        sys.exit(1)
        
    print(f"Found {len(frames)} frames. Compiling...")
    
    # Write a concat file for ffmpeg
    concat_file = os.path.join(frames_dir, 'concat.txt')
    with open(concat_file, 'w') as f:
        for frame in frames:
            # ffmpeg concat needs relative paths or absolute with forward slashes
            path = frame.replace('\\', '/')
            f.write(f"file '{path}'\n")
            f.write(f"duration {1.0 / fps}\n")
            
    # Run ffmpeg
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        output_path
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        print(f"Successfully compiled {output_name}")
    else:
        print(f"FFmpeg failed:\n{result.stderr}")

if __name__ == "__main__":
    is_preview = "--preview" in sys.argv
    fps = 30
    if is_preview:
        # Since we skipped frames, we might want it to play faster or same fps
        fps = 10 # play it out slowly to inspect
        compile_video(fps, "saanjh_digital_twin_preview.mp4")
    else:
        compile_video(fps, "saanjh_digital_twin.mp4")
