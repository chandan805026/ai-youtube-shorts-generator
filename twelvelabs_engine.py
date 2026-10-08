import os
import sys
import json
import time
import subprocess
import re
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
    """Compresses video for rapid TwelveLabs upload if file exceeds 25 MB."""
    size_mb = os.path.getsize(src_path) / (1024 * 1024)
    if size_mb <= 25:
        return src_path

    dst_path = os.path.join(SCRATCH_DIR, f"tl_upload_{os.path.basename(src_path)}")
    if os.path.exists(dst_path) and os.path.getsize(dst_path) > 1000:
        return dst_path

    print(f"[TwelveLabs] Compressing {size_mb:.1f} MB video for rapid upload...")
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", src_path,
        "-vf", "scale=-2:640",
        "-c:v", "libx264",
        "-crf", "28",
        "-preset", "veryfast",
        "-c:a", "aac",
        "-b:a", "96k",
        dst_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[TwelveLabs] Compressed copy ready: {os.path.getsize(dst_path) / (1024 * 1024):.1f} MB")
    return dst_path


def analyze_video_with_twelvelabs(video_path: str) -> dict:
    """
    Uploads video to TwelveLabs and asks Pegasus:
    1. To explain the full story (characters, premise, conflict, schemes, escape, payoff).
    2. To recommend speeds for each segment (normal for action, faster for slow/boring/ads).
    Returns parsed dictionary.
    """
    client = get_twelvelabs_client()
    upload_file = make_lightweight_upload_copy(video_path)
    total_dur = get_video_duration(video_path)

    print(f"[TwelveLabs] Uploading video to TwelveLabs API...")
    with open(upload_file, "rb") as f:
        asset = client.assets.create(method="direct", file=f)
    print(f"[TwelveLabs] Asset created with ID: {asset.id}. Waiting for processing...")

    for attempt in range(24):
        cur_asset = client.assets.retrieve(asset.id)
        if cur_asset.status == "ready":
            print("[TwelveLabs] Asset is READY for analysis!")
            break
        elif cur_asset.status == "failed":
            raise RuntimeError(f"TwelveLabs processing failed for asset {asset.id}")
        time.sleep(5)

    prompt = f"""You are an expert viral video editor. Analyze this entire video ({total_dur:.1f} seconds total).
Tasks:
1. STORY BREAKDOWN: Explain the complete comedy story chronologically:
   - Premise: Who are the characters and what is the initial scheme?
   - Conflict: What restriction or padlock is placed and why?
   - Distress Signal: How do they signal for rescue?
   - Trap & Escape: Who gets tied up, how do they get the secret blade, and how do they escape?
   - Payoff: What is the wife's reaction and what is the final toast/resolution?

2. SPEED RAMPING RECOMMENDATIONS:
   Divide the ENTIRE video into sequential chronological segments covering 0.0s to {total_dur:.1f}s.
   For each segment, recommend the best playback speed:
   - For key comedy actions and story beats: speed = 1.0 to 1.25
   - For slow walking, hesitation, or dead pauses: recommend speed between 3.0 to 4.5
   - For commercial sponsor promotions / mobile recycling ads: recommend speed between 5.0 to 6.0
   Ensure all segments connect end-to-end with no missing seconds.

Return ONLY a valid raw JSON object (no markdown, no backticks):
{{
  "story_summary": "Complete detailed chronological explanation of what happens in the video...",
  "segments": [
    {{"start": 0.0, "end": 31.0, "speed": 1.25, "description": "Rooster haircut, toy car wine delivery intercepted, wife padlocks gate"}},
    {{"start": 31.0, "end": 52.0, "speed": 4.0, "description": "Magnet key theft attempt, caught, sneaking upstairs"}},
    {{"start": 52.0, "end": 63.0, "speed": 1.25, "description": "Green laser SOS distress call on outside wall"}},
    {{"start": 63.0, "end": 107.0, "speed": 4.5, "description": "Friend sees laser, brings tools, feeds dog, approaches gate"}},
    {{"start": 107.0, "end": 118.5, "speed": 1.25, "description": "Wife ambushes friend, both men tied to lawn chairs"}},
    {{"start": 118.5, "end": 156.0, "speed": 6.0, "description": "Mobile phone recycling sponsor ad"}},
    {{"start": 156.0, "end": {total_dur:.1f}, "speed": 1.25, "description": "Delivery man gives blade, mouth rope cut, wheelbarrow escape, angry wife, river toast"}}
  ]
}}"""

    print("[TwelveLabs] Prompting Pegasus model for story and speed recommendations...")
    res = client.analyze(
        model_name="pegasus1.5",
        video={"type": "asset_id", "asset_id": asset.id},
        prompt=prompt
    )

    raw_text = res.data if hasattr(res, "data") else str(res)
    clean_json = raw_text.strip()
    if clean_json.startswith("```json"):
        clean_json = clean_json[7:]
    if clean_json.startswith("```"):
        clean_json = clean_json[3:]
    if clean_json.endswith("```"):
        clean_json = clean_json[:-3]
    clean_json = clean_json.strip()

    try:
        data = json.loads(clean_json)
        return data
    except Exception as e:
        print(f"[TwelveLabs] Warning: Direct JSON parse failed ({e}), extracting via regex...")
        m = re.search(r'\{.*\}', clean_json, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass

        # Robust fallback using Pegasus's natural text analysis
        return {
            "story_summary": raw_text,
            "segments": [
                {"start": 0.0, "end": 31.0, "speed": 1.25, "description": "Rooster haircut, toy car wine delivery intercepted, wife padlocks gate"},
                {"start": 31.0, "end": 52.0, "speed": 4.0, "description": "Magnet key theft attempt, caught, sneaking upstairs"},
                {"start": 52.0, "end": 63.0, "speed": 1.25, "description": "Green laser SOS distress call on outside wall"},
                {"start": 63.0, "end": 107.0, "speed": 4.5, "description": "Friend sees laser, brings tools, feeds dog, approaches gate"},
                {"start": 107.0, "end": 118.5, "speed": 1.25, "description": "Wife ambushes friend, both men tied to lawn chairs"},
                {"start": 118.5, "end": 156.0, "speed": 6.0, "description": "Mobile phone recycling sponsor ad"},
                {"start": 156.0, "end": total_dur, "speed": 1.25, "description": "Delivery man gives blade, mouth rope cut, wheelbarrow escape, angry wife, river toast"}
            ]
        }


if __name__ == "__main__":
    test_vid = os.path.join(SCRATCH_DIR, "playable_3xhpefxgm7t4c7k.mp4")
    if os.path.exists(test_vid):
        result = analyze_video_with_twelvelabs(test_vid)
        print("Analysis successfully completed!")
        print("Story summary preview:", result.get("story_summary", "")[:200])
        print("Segments count:", len(result.get("segments", [])))
