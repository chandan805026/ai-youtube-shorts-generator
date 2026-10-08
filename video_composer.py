import os
import subprocess

FFMPEG_BIN = r"C:\Users\ladu\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = "ffmpeg"
SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))


def slice_and_concat(source_video: str, cut_ranges: list, out_video: str):
    """
    cut_ranges: list of tuples [(start_sec, end_sec), ...]
    Slices segments and concatenates them with uniform frame rate and resolution.
    """
    segment_files = []
    concat_list_file = os.path.join(SCRATCH_DIR, "concat_list.txt")

    valid_ranges = []
    for r in cut_ranges:
        st = max(0.0, float(r[0]))
        et = float(r[1])
        if et > st + 0.5:
            valid_ranges.append((st, et - st))

    if not valid_ranges:
        valid_ranges = [(0.0, 35.0)]

    for idx, (st, dur) in enumerate(valid_ranges):
        seg_path = os.path.join(SCRATCH_DIR, f"seg_{idx:02d}.mp4")
        cmd_cut = [
            FFMPEG_BIN, "-y",
            "-ss", f"{st:.2f}",
            "-i", source_video,
            "-t", f"{dur:.2f}",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-r", "60",
            "-an",
            seg_path
        ]
        subprocess.run(cmd_cut, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        segment_files.append(seg_path)

    with open(concat_list_file, "w", encoding="utf-8") as f:
        for p in segment_files:
            # Format: file 'C:\path\seg_00.mp4'
            f.write(f"file '{p}'\n")

    cmd_concat = [
        FFMPEG_BIN, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        out_video
    ]
    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Cleanup temp segments
    for p in segment_files:
        try:
            os.remove(p)
        except Exception:
            pass
    try:
        os.remove(concat_list_file)
    except Exception:
        pass

    print(f"[Composer] Sliced & stitched {len(cut_ranges)} clips into: {out_video}")


def extract_continuous_segment(source_video: str, start_sec: float, dur_sec: float, out_video: str):
    """
    Extracts a single continuous clip without re-encoding glitches.
    """
    cmd = [
        FFMPEG_BIN, "-y",
        "-ss", f"{start_sec:.2f}",
        "-i", source_video,
        "-t", f"{dur_sec:.2f}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-r", "60",
        "-an",
        out_video
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[Composer] Extracted continuous {dur_sec:.1f}s scene: {out_video}")


def render_final_short(video_path: str, audio_path: str, ass_path: str, final_output: str):
    """
    Burns subtitles, maps master audio, and encodes high-quality vertical Short.
    """
    ass_basename = os.path.basename(ass_path)
    ass_dir = os.path.dirname(ass_path)
    vf_str = f"subtitles={ass_basename}"

    cmd = [
        FFMPEG_BIN, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-vf", vf_str,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        final_output
    ]
    # Run in the directory of the ASS file so FFmpeg resolves relative subtitle path cleanly on Windows
    subprocess.run(cmd, cwd=ass_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print(f"[Composer] Final Viral Short Rendered: {final_output} ({os.path.getsize(final_output) / (1024*1024):.2f} MB)")
