import os
import glob
import subprocess

def compile_digital_twin():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frames_dir = os.path.join(base_dir, "artifacts", "video", "frames")
    out_video = os.path.join(base_dir, "artifacts", "video", "saanjh_blender_digital_twin_30s.mp4")
    ffmpeg_exe = r"C:\Users\noobg\AppData\Local\Microsoft\WinGet\Packages\yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-N-124279-g0f6ba39122-win64-gpl\bin\ffmpeg.exe"

    frames = sorted(glob.glob(os.path.join(frames_dir, "frame_*.jpg")))
    print(f"Found {len(frames)} rendered Blender frames in {frames_dir}")
    if len(frames) < 10:
        print("Error: Too few frames to compile.")
        return False

    # Concat file: each frame displayed for 1.0 second, with 36 frames = 36.0 seconds
    concat_file = os.path.join(frames_dir, "concat_30s.txt")
    with open(concat_file, "w") as f:
        for frame in frames:
            p = frame.replace("\\", "/")
            f.write(f"file '{p}'\n")
            f.write("duration 1.0\n")
        # repeat last frame to ensure ffmpeg captures full duration
        f.write(f"file '{frames[-1].replace(chr(92), '/')}'\n")

    cmd = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-an",
        out_video
    ]

    print("Compiling Blender frames into 30-40s digital twin MP4...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        print(f"Successfully generated: {out_video}")
        return True
    else:
        print(f"FFmpeg error:\n{res.stderr}")
        return False

if __name__ == "__main__":
    compile_digital_twin()
