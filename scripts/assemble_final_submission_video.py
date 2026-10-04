import os
import subprocess

def assemble_master_video():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vid_dir = os.path.join(base_dir, "artifacts", "video")
    cards_dir = os.path.join(vid_dir, "cards")
    ffmpeg_exe = r"C:\Users\noobg\AppData\Local\Microsoft\WinGet\Packages\yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-N-124279-g0f6ba39122-win64-gpl\bin\ffmpeg.exe"

    open_card = os.path.join(cards_dir, "opening_card.png")
    close_card = os.path.join(cards_dir, "closing_card.png")
    walkthrough_vid = os.path.join(vid_dir, "saanjh_website_walkthrough_master.mp4")
    hardware_vid = os.path.join(vid_dir, "hardware_demonstration.mp4")
    blender_vid = os.path.join(vid_dir, "saanjh_blender_digital_twin_30s.mp4")
    output_vid = os.path.join(vid_dir, "saanjh_final_5min_submission.mp4")

    # Verify input existence
    for path, name in [
        (open_card, "Opening Card"),
        (close_card, "Closing Card"),
        (walkthrough_vid, "Website Walkthrough Master"),
        (hardware_vid, "Hardware Demonstration"),
        (blender_vid, "Blender Digital Twin 30s")
    ]:
        if not os.path.exists(path):
            print(f"Error: Missing input asset {name} at {path}")
            return False

    temp_parts_dir = os.path.join(vid_dir, "temp_assembly_parts")
    os.makedirs(temp_parts_dir, exist_ok=True)

    part1 = os.path.join(temp_parts_dir, "part1_intro.mp4")
    part2 = os.path.join(temp_parts_dir, "part2_walkthrough_p1.mp4")
    part3 = os.path.join(temp_parts_dir, "part3_hardware.mp4")
    part4 = os.path.join(temp_parts_dir, "part4_walkthrough_p2.mp4")
    part5 = os.path.join(temp_parts_dir, "part5_blender.mp4")
    part6 = os.path.join(temp_parts_dir, "part6_outro.mp4")

    print("Step 1: Generating Part 1 (Opening Card, 20.0s)...")
    cmd1 = [
        ffmpeg_exe, "-y",
        "-loop", "1", "-i", open_card,
        "-t", "20.0",
        "-vf", "scale=1920:1080,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an",
        part1
    ]
    subprocess.run(cmd1, check=True)

    print("Step 2: Extracting Part 2 (Walkthrough Part 1, 70.0s)...")
    cmd2 = [
        ffmpeg_exe, "-y",
        "-ss", "0.0", "-to", "70.0",
        "-i", walkthrough_vid,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an",
        part2
    ]
    subprocess.run(cmd2, check=True)

    print("Step 3: Formatting Part 3 (Hardware Demonstration with Lower Third, 32.11s)...")
    # Draw lower-third overlay directly onto the hardware demo
    # Hardware video is vertical/pillarbox, pad to 1920x1080 with dark slate letterbox
    hw_filter = (
        "scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#080C15,"
        "drawbox=y=890:color=#0E1626@0.95:width=iw:height=140:t=fill,"
        "drawbox=y=890:color=#3DCD58:width=iw:height=4:t=fill,"
        "drawtext=text='PHYSICAL PROTOTYPE - Local Sensing + LoRa RF Telemetry':fontcolor=#3DCD58:fontsize=32:x=120:y=920,"
        "drawtext=text='RAKwireless WisBlock RAK4631 (nRF52840 + SX1262 LoRa 865 MHz) | Live Field Telemetry Acquisition':fontcolor=#F1F5F9:fontsize=22:x=120:y=970,"
        "fps=30,format=yuv420p"
    )
    cmd3 = [
        ffmpeg_exe, "-y",
        "-i", hardware_vid,
        "-vf", hw_filter,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an",
        part3
    ]
    subprocess.run(cmd3, check=True)

    print("Step 4: Extracting Part 4 (Walkthrough Part 2: Deficit to Economics, 142.0s)...")
    cmd4 = [
        ffmpeg_exe, "-y",
        "-ss", "70.0", "-to", "212.0",
        "-i", walkthrough_vid,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an",
        part4
    ]
    subprocess.run(cmd4, check=True)

    print("Step 5: Extracting Part 5 (Blender Extended Digital Twin, 30.0s)...")
    cmd5 = [
        ffmpeg_exe, "-y",
        "-t", "30.0",
        "-i", blender_vid,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an",
        part5
    ]
    subprocess.run(cmd5, check=True)

    print("Step 6: Generating Part 6 (Closing Card, 15.0s)...")
    cmd6 = [
        ffmpeg_exe, "-y",
        "-loop", "1", "-i", close_card,
        "-t", "15.0",
        "-vf", "scale=1920:1080,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an",
        part6
    ]
    subprocess.run(cmd6, check=True)

    print("Step 7: Concatenating all 6 segments into master final 5-minute video...")
    concat_list = os.path.join(temp_parts_dir, "concat_master.txt")
    with open(concat_list, "w") as f:
        for p in [part1, part2, part3, part4, part5, part6]:
            f.write(f"file '{p.replace(chr(92), '/')}'\n")

    cmd_concat = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-an",
        output_vid
    ]
    res = subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        print(f"SUCCESS: Assembled master 5-minute video at {output_vid}")
        return True
    else:
        print(f"Concatenation failed:\n{res.stderr}")
        return False

if __name__ == "__main__":
    assemble_master_video()
