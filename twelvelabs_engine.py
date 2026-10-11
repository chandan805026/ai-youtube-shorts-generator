import os
import sys
import json
import time
import subprocess
import re
import shutil
from twelvelabs import TwelveLabs

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_BIN = r"C:\Users\ladu\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = "ffmpeg"


def get_twelvelabs_client():
    api_key = os.environ.get("TWELVELABS_API_KEY") or os.environ.get("TL_API_KEY")
    if not api_key:
        api_key = "tlk_31ZGGWG3PE2HKP20QA7H81VYKYZF"
    return TwelveLabs(api_key=api_key)


def get_video_duration(video_path: str) -> float:
    cmd = [FFMPEG_BIN, "-i", video_path]
    p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
    for line in p.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 120.0


def make_lightweight_upload_copy(src_path: str) -> str:
    """Compresses video for fast TwelveLabs upload & indexing while keeping 100% frame/time accuracy."""
    dst_path = os.path.join(SCRATCH_DIR, f"tl_upload_{os.path.basename(src_path)}")
    if os.path.exists(dst_path) and os.path.getsize(dst_path) > 1000:
        return dst_path

    size_mb = os.path.getsize(src_path) / (1024 * 1024)
    print(f"[TwelveLabs] Creating fast-upload copy from {size_mb:.1f} MB source...")
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", src_path,
        "-vf", "scale=640:-2",
        "-c:v", "libx264",
        "-crf", "28",
        "-preset", "veryfast",
        "-c:a", "aac",
        "-b:a", "64k",
        dst_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[TwelveLabs] Upload copy ready: {os.path.getsize(dst_path) / (1024 * 1024):.1f} MB")
    return dst_path


def snap_timestamp_to_camera_cut(video_path: str, target_t: float, total_dur: float, is_start: bool = True) -> float:
    """
    Uses FFmpeg scdet around target_t (±1.2s) to snap cut points to exact millisecond
    camera angle changes so no stray frame from an adjacent shot ever flashes.
    """
    if target_t <= 1.0:
        return 0.0
    if target_t >= total_dur - 1.5:
        return round(total_dur, 2)

    win_start = max(0.0, target_t - 1.2)
    win_dur = 2.4
    cmd = [
        FFMPEG_BIN, "-ss", f"{win_start:.2f}", "-t", f"{win_dur:.2f}",
        "-i", video_path,
        "-vf", "scdet=threshold=12",
        "-an", "-f", "null", "-"
    ]
    p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
    cuts = []
    for line in p.stderr.splitlines():
        if "lavfi.scd.time:" in line:
            m = re.search(r"lavfi\.scd\.time:\s*([0-9\.]+)", line)
            if m:
                rel_t = float(m.group(1))
                abs_t = win_start + rel_t
                cuts.append(abs_t)

    if cuts:
        best_cut = min(cuts, key=lambda c: abs(c - target_t))
        adjusted = best_cut + (0.04 if is_start else -0.04)
        print(f"[SceneLock] Snapped {'START' if is_start else 'END'} {target_t:.2f}s -> exact camera cut {adjusted:.2f}s")
        return round(max(0.0, min(total_dur, adjusted)), 2)

    return round(target_t, 2)


def condense_video_with_twelvelabs(raw_video_path: str, output_path: str = None) -> str:
    """
    Sends the raw video to TwelveLabs Pegasus with the EXACT SAME Master Film & Comedy Video Editor prompt,
    then cuts and joins the returned chapters purely with FFmpeg (no Gemini, no ElevenLabs).
    """
    total_dur = get_video_duration(raw_video_path)
    print(f"\n[TwelveLabs Editor] Video is {total_dur:.1f}s. Uploading to TwelveLabs Pegasus with exact Master Editor prompt...")

    client = get_twelvelabs_client()
    upload_file = make_lightweight_upload_copy(raw_video_path)

    with open(upload_file, "rb") as f:
        asset = client.assets.create(method="direct", file=f)
    print(f"[TwelveLabs] Asset created with ID: {asset.id}. Waiting for indexing...")

    for attempt in range(60):
        cur_asset = client.assets.retrieve(asset.id)
        if cur_asset.status == "ready":
            print(f"[TwelveLabs] Asset {asset.id} is READY! (attempt {attempt + 1})")
            break
        elif cur_asset.status == "failed":
            raise RuntimeError(f"TwelveLabs processing failed for asset {asset.id}")
        time.sleep(5)

    # EXACT SAME PROMPT AS GEMINI PASS 1 (ZERO CHANGES)
    editor_prompt = f"""You are a Master Film & Comedy Video Editor.
First, watch this entire video carefully from start to finish ({total_dur:.1f} seconds). Deeply understand the complete story, characters, setups, pranks, and final climax.

TASK:
This video is {total_dur:.1f} seconds long, which is too long for a 60-second YouTube Short.
Your job is to select 2 or 3 LONG, CONTINUOUS, CONNECTED STORY CHAPTERS that tell the COMPLETE funny story from beginning to climax in a combined duration of 56 to 65 seconds (so at 1.15x playback it will be 49 to 56 seconds, strictly under 1 minute).

STRICT CONTINUITY & EDITING RULES (DO NOT VIOLATE):
1. NO TINY FRAGMENTS: Never cut small 3-to-8 second pieces! Every chapter you select MUST be between 15.0 and 26.0 seconds long so the viewer watches a smooth, uninterrupted scene without sudden jumps.
2. ONLY 2 OR 3 CONNECTED CHAPTERS IN CHRONOLOGICAL ORDER:
   - Chapter 1 (Opening Setup & Problem): 15 to 20 seconds showing how the story/problem begins.
   - Chapter 2 (The Main Funny Plan / Trap / Action): 18 to 24 seconds showing the main comedic action or prank.
   - Chapter 3 (The Final Climax & Payoff): 18 to 24 seconds showing the hilarious ending payoff.
3. ZERO ABRUPT JUMPS ("Achanak koi alag hissa na aaye"):
   - Start and end each chapter ONLY at a clean camera angle change or completed action.
   - Never cut in the middle of someone walking, speaking, or swinging!
   - Only remove slow, repetitive walking/waiting filler between the 3 main chapters.
4. TOTAL COMBINED DURATION of all chapters MUST be between 56.0 and 65.0 seconds.

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown backticks, no extra text):
{{
  "story_summary": "Brief summary of the full story",
  "chapters": [
    {{"start": 0.0, "end": 18.0, "description": "Opening setup"}},
    {{"start": 40.0, "end": 62.0, "description": "Main funny trap"}},
    {{"start": 96.0, "end": 118.0, "description": "Final climax"}}
  ]
}}"""

    print("[TwelveLabs] Sending exact Master Editor prompt to Pegasus 1.5...")
    res = client.analyze(
        model_name="pegasus1.5",
        video={"type": "asset_id", "asset_id": asset.id},
        prompt=editor_prompt
    )

    raw_text = res.data if hasattr(res, "data") else str(res)
    print(f"\n[TwelveLabs Raw Output]:\n{raw_text}\n")

    clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip()).strip()
    parsed = None
    try:
        parsed = json.loads(clean_json)
    except Exception:
        m = re.search(r"\{.*\}", clean_json, re.DOTALL)
        if m:
            parsed = json.loads(m.group(0))

    if not parsed or not parsed.get("chapters"):
        raise RuntimeError(f"TwelveLabs did not return valid chapters JSON: {raw_text}")

    print(f"[TwelveLabs Story Summary]: {parsed.get('story_summary', '')}")
    selected_chapters = parsed.get("chapters", [])

    valid_ranges = []
    prev_end = 0.0
    for ch in selected_chapters:
        s = max(prev_end, float(ch.get("start", 0.0)))
        e = min(total_dur, float(ch.get("end", s + 18.0)))
        if e > s + 2.0:
            valid_ranges.append((s, e, ch.get("description", "Story chapter")))
            prev_end = e

    part_files = []
    for idx, (s_raw, e_raw, desc) in enumerate(valid_ranges):
        s_snap = snap_timestamp_to_camera_cut(raw_video_path, s_raw, total_dur, is_start=True)
        e_snap = snap_timestamp_to_camera_cut(raw_video_path, e_raw, total_dur, is_start=False)
        if e_snap - s_snap < 5.0:
            s_snap, e_snap = s_raw, e_raw

        part_path = os.path.join(SCRATCH_DIR, f"tl_chap_{idx:02d}_{os.path.basename(raw_video_path)}")
        print(f"[TwelveLabs FFmpeg Cut] Chapter {idx+1}: {s_snap:.2f}s -> {e_snap:.2f}s ({e_snap - s_snap:.1f}s) [{desc}] (Raw TL: {s_raw:.2f}s->{e_raw:.2f}s)")
        dur_c = e_snap - s_snap
        vf_fade = f"fade=t=in:st=0:d=0.15,fade=t=out:st={max(0.1, dur_c - 0.15):.2f}:d=0.15"
        cmd_part = [
            FFMPEG_BIN, "-y",
            "-ss", f"{s_snap:.2f}",
            "-to", f"{e_snap:.2f}",
            "-i", raw_video_path,
            "-vf", vf_fade,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            part_path
        ]
        subprocess.run(cmd_part, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        part_files.append(part_path)

    concat_list_path = os.path.join(SCRATCH_DIR, "tl_chapters_concat.txt")
    with open(concat_list_path, "w", encoding="utf-8") as cf:
        for pf in part_files:
            safe_p = pf.replace("\\", "/")
            cf.write(f"file '{safe_p}'\n")

    if not output_path:
        output_path = os.path.join(SCRATCH_DIR, f"condensed_tl_{os.path.basename(raw_video_path)}")

    cmd_concat = [
        FFMPEG_BIN, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]
    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    new_dur = get_video_duration(output_path)
    print(f"[TwelveLabs FFmpeg Cut] Final cut video ready: {output_path} ({new_dur:.1f}s from {total_dur:.1f}s raw)")
    return output_path
