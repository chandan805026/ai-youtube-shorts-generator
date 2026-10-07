import os
import sys
import json
import re
import time
import subprocess
from google import genai

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LINKS_FILE = os.path.join(BASE_DIR, "links.txt")
STATE_FILE = os.path.join(BASE_DIR, "queue_state.json")
SCENES_DIR = os.path.join(BASE_DIR, "raw_scenes")
os.makedirs(SCENES_DIR, exist_ok=True)

from kuaishou_downloader import fetch_kuaishou_video_info, download_and_transcode
from pipeline import get_video_duration, extract_continuous_segment

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"current_link": "", "current_photo_id": "", "raw_scenes": [], "completed_links_count": 0}


def save_state(state: dict):
    state["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_next_link() -> str:
    """Reads the first active link from links.txt."""
    if not os.path.exists(LINKS_FILE):
        return ""
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                return line
    return ""


def remove_current_link(target_url: str):
    """Removes a finished URL from links.txt."""
    if not os.path.exists(LINKS_FILE):
        return
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    removed = False
    for line in lines:
        cleaned = line.strip()
        if cleaned == target_url.strip() and not removed:
            removed = True
            continue
        new_lines.append(line)

    with open(LINKS_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"[Harvester] Removed completed URL from links.txt: {target_url}")


def detect_top_scenes_with_gemini(video_path: str, total_duration: float, client) -> list:
    """
    Uses Gemini 3.5 Flash Lite Vision to find 1 to 3 best standalone comedy scenes.
    """
    if total_duration <= 45.0:
        print(f"[Harvester] Short video ({total_duration:.1f}s) -> 1 complete scene.")
        return [{"start": 0.0, "end": total_duration, "title": "Full Skit"}]

    print(f"[Harvester] Long compilation ({total_duration:.1f}s) -> Uploading to Gemini to extract Top 2-3 funniest skits...")
    vf = client.files.upload(file=video_path)
    retries = 0
    while vf.state.name == "PROCESSING" and retries < 30:
        time.sleep(2)
        vf = client.files.get(name=vf.name)
        retries += 1

    prompt = f"""You are an expert viral video editor and comedy scout.
You just watched this entire comedy compilation video (Total duration: {total_duration:.1f} seconds).

Your task is to identify the Top 1 to 3 BEST, funniest, and most viral standalone comedy skits in this video.

CRITICAL RULES:
1. Each scene must be a complete self-contained story or prank from start to punchline.
2. Duration of each scene must be between 28 and 38 seconds (never exceed 40 seconds).
3. Do NOT overlap scenes. Leave boundaries clean.
4. Rank the funniest scenes first. Max 3 scenes.

Return ONLY valid JSON with this exact structure:
{{
  "scenes": [
    {{"start": 12.0, "end": 46.5, "title": "Wig Disguise Skit"}},
    {{"start": 95.0, "end": 130.0, "title": "Food Stall Prank"}}
  ]
}}
"""

    response = client.models.generate_content(
        model='gemini-3.5-flash-lite',
        contents=[client.files.get(name=vf.name), prompt],
        config={'response_mime_type': 'application/json', 'temperature': 0.3}
    )

    try:
        client.files.delete(name=vf.name)
    except Exception:
        pass

    try:
        raw_text = response.text
        m = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            scenes = data.get("scenes", [])
            if scenes:
                print(f"[Harvester] Gemini successfully identified {len(scenes)} top comedy scenes!")
                return scenes[:3]
    except Exception as e:
        print(f"[Harvester] Error parsing Gemini scene detection: {e}")

    # Fallback if parsing failed: pick first 35 seconds
    return [{"start": 0.0, "end": min(total_duration, 35.0), "title": "Scene 1"}]


def harvest_next() -> bool:
    """
    Main Engine 1 entrypoint:
    Checks if raw_scenes/ needs stocking. If yes, fetches next link, slices scenes, and stores.
    """
    state = load_state()

    # 1. Check if raw_scenes/ already has un-processed clips
    existing_clips = [f for f in os.listdir(SCENES_DIR) if f.endswith(".mp4")]
    if existing_clips:
        print(f"[Harvester] Shelf already stocked with {len(existing_clips)} scenes: {existing_clips}")
        return True

    # 2. Get next link from links.txt
    url = get_next_link()
    if not url:
        print("[Harvester] links.txt is empty! Please add new Kuaishou/Douyin URLs.")
        return False

    print("=" * 60)
    print(f"🌾 ENGINE 1: HARVESTING SCENES FROM: {url}")
    print("=" * 60)

    # 3. Download master video
    info = fetch_kuaishou_video_info(url)
    photo_id = info["photo_id"]
    master_video = download_and_transcode(info, BASE_DIR)
    total_duration = get_video_duration(master_video)
    print(f"-> Master Video Duration: {total_duration:.1f}s")

    # 4. Initialize Gemini
    client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
    if not client:
        raise ValueError("GEMINI_API_KEY environment variable is missing!")

    # 5. Detect top 1 to 3 scenes
    detected_scenes = detect_top_scenes_with_gemini(master_video, total_duration, client)

    # 6. Slice each scene into raw_scenes/
    stocked_scenes = []
    for idx, sc in enumerate(detected_scenes):
        st = max(0.0, float(sc.get("start", 0.0)))
        et = min(total_duration, float(sc.get("end", st + 35.0)))
        dur = max(10.0, min(et - st, 38.0))

        scene_filename = f"clip_{photo_id}_part{idx+1}.mp4"
        scene_filepath = os.path.join(SCENES_DIR, scene_filename)

        extract_continuous_segment(master_video, st, dur, scene_filepath)
        stocked_scenes.append({
            "id": f"part{idx+1}",
            "filename": scene_filename,
            "filepath": scene_filepath,
            "start": st,
            "duration": dur,
            "title": sc.get("title", f"Part {idx+1}")
        })
        print(f"-> Saved Scene {idx+1}: {scene_filename} ({dur:.1f}s, start={st:.1f}s)")

    # 7. Cleanup heavy master files to keep disk usage near zero
    for temp_f in [master_video, master_video.replace("playable_", "raw_")]:
        if os.path.exists(temp_f):
            try:
                os.remove(temp_f)
            except Exception:
                pass

    # 8. Update state
    state["current_link"] = url
    state["current_photo_id"] = photo_id
    state["raw_scenes"] = stocked_scenes
    save_state(state)

    print(f"\n🎉 [Harvester] Stocked {len(stocked_scenes)} clean scenes into {SCENES_DIR}!")
    return True


if __name__ == "__main__":
    harvest_next()
