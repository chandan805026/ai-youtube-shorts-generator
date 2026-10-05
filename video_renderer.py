import os
import sys
import subprocess
import re

def render_short(video_path, audio_path, ass_path, output_path="final_short.mp4", banner_text="CHINA KA KHATARNAK GADGET"):
    ffmpeg_bin = "ffmpeg"
    print("Rendering Short using FFmpeg...")

    p = subprocess.run([ffmpeg_bin, "-i", audio_path], stderr=subprocess.PIPE, text=True, errors="ignore")
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    audio_dur = 15.0
    if m:
        audio_dur = float(m.group(1))*3600 + float(m.group(2))*60 + float(m.group(3))
    print(f"Voiceover length: {audio_dur:.2f}s")

    clean_ass = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")

    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
        f"subtitles='{clean_ass}'[v];"
        f"[0:a]volume=0.25[a_bg];"
        f"[1:a]volume=1.0[a_voice];"
        f"[a_voice][a_bg]amix=inputs=2:duration=first:dropout_transition=2[a]"
    )

    cmd = [
        ffmpeg_bin, "-y",
        "-t", str(audio_dur + 0.5),
        "-i", video_path,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path
    ]

    print("Running FFmpeg encoding pipeline...")
    res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
    if res.returncode != 0:
        print("Complex filter notice, trying safe fallback...")
        safe_filter = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
            f"subtitles='{clean_ass}'[v];"
            f"[0:a]volume=0.2[a_bg];[1:a]volume=1.0[a_voice];[a_voice][a_bg]amix=inputs=2:duration=first[a]"
        )
        cmd_safe = [
            ffmpeg_bin, "-y",
            "-t", str(audio_dur + 0.5),
            "-i", video_path,
            "-i", audio_path,
            "-filter_complex", safe_filter,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        res_safe = subprocess.run(cmd_safe, capture_output=True, text=True, errors="ignore")
        if res_safe.returncode != 0:
            print(f"Render error: {res_safe.stderr[:300]}")
            return None

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Final Short rendered: {size_mb:.2f} MB -> {output_path}")
    return output_path
