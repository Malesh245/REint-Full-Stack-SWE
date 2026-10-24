import os
import subprocess

# Timing breakdown in seconds matching the voiceover_full.mp3
# Total audio duration = 562.63 seconds (9 minutes 22 seconds)
TIMINGS = [
    # Part 1: Client Pitch
    ("video_frames/slide_01_part1_intro.png", 35.0),
    ("video_frames/slide_02_dashboard_kpis.png", 40.0),
    ("video_frames/slide_03_dashboard_curves.png", 40.0),
    ("video_frames/slide_04_accuracy_top.png", 45.0),
    ("video_frames/slide_05_accuracy_histogram.png", 40.0),
    ("video_frames/slide_06_accuracy_diurnal.png", 40.0),
    ("video_frames/slide_07_forecast_explorer.png", 35.0),
    ("video_frames/slide_08_part1_summary.png", 19.71),
    
    # Part 2: Technical Lead Review
    ("video_frames/slide_09_part2_intro.png", 40.29),
    ("video_frames/slide_10_resampling.png", 45.0),
    ("video_frames/slide_11_gate_closure.png", 50.0),
    ("video_frames/slide_12_analytics_math.png", 50.0),
    ("video_frames/slide_13_devops_caching.png", 45.0),
    ("video_frames/slide_14_conclusion.png", 37.63),
]

def render_video():
    print("Generating ffmpeg input file list...")
    input_list = "video_slides_input.txt"
    with open(input_list, "w", encoding="utf-8") as f:
        for img_path, duration in TIMINGS:
            abs_path = os.path.abspath(img_path).replace("\\", "/")
            f.write(f"file '{abs_path}'\n")
            f.write(f"duration {duration}\n")
        # ffmpeg concat demuxer requires repeating the last file
        last_img = os.path.abspath(TIMINGS[-1][0]).replace("\\", "/")
        f.write(f"file '{last_img}'\n")

    output_video = "WindSight_Demo_Walkthrough.mp4"
    audio_path = os.path.abspath("voiceover_full.mp3").replace("\\", "/")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", input_list,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_video
    ]
    
    print("Rendering final 1080p MP4 video with FFmpeg...")
    print("Command:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    
    if os.path.exists(output_video):
        size_mb = os.path.getsize(output_video) / (1024 * 1024)
        print(f"\n=======================================================")
        print(f"SUCCESS: Video rendered: {output_video}")
        print(f"Resolution: 1920x1080 (Full HD)")
        print(f"File Size: {size_mb:.2f} MB")
        print(f"Duration: 9 minutes 22 seconds")
        print(f"=======================================================\n")
    else:
        print("Error: output video file not created.")

if __name__ == "__main__":
    render_video()
