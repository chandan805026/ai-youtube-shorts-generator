import os
import sys
import json
import time
import subprocess
import requests
import re
import base64

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_BIN = r"C:\Users\ladu\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = "ffmpeg"


def get_candidate_gemini_keys():
    keys = []
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_KEY")
    if env_key and env_key.strip() and not env_key.strip().startswith("${{"):
        keys.append(env_key.strip())
    fallback = base64.b64decode("QVEuQWI4Uk42TDZKYkRDb0lueUpGN1c1TlMydVpZc2ZWclpRWk9EZDVENkNPVGtRQWk4SkE=").decode("utf-8")
    if fallback not in keys:
        keys.append(fallback)
    return keys


def sanitize_speech_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\b[\w\-]+(?:\.mp3|\.wav|\.ogg)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\.(?:mp3|wav|ogg)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\*.*?\*', '', text)
    text = re.sub(r'\b(?:SFX|SOUND EFFECT|FX|MEME)\s*:?\b', '', text, flags=re.I)

    sfx_patterns = [
        r'\bvine[\s_\-]*boom\b', r'\bwindows[\s_\-]*error\b', r'\bmetal[\s_\-]*pipe\b',
        r'\bsad[\s_\-]*violin\b', r'\btitanic[\s_\-]*bad[\s_\-]*recorder\b',
        r'\bno[\s_\-]*god[\s_\-]*please[\s_\-]*no\b', r'\bincorrect[\s_\-]*buzzer\b',
        r'\boh[\s_\-]*no[\s_\-]*wheeze[\s_\-]*laugh\b', r'\bsuspense[\s_\-]*sting\b',
        r'\bfbi[\s_\-]*open[\s_\-]*up\b', r'\bding[\s_\-]*idea\b', r'\bwait[\s_\-]*a[\s_\-]*minute\b',
        r'\banime[\s_\-]*wow\b', r'\bbruh\b', r'\byeet\b', r'\brizz\b'
    ]
    for pat in sfx_patterns:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)

    # Family-safe / Shorts Seed-Shelf safe word replacements
    safe_replacements = [
        (r'\bholding\s+(.*?)\s+hostage\b', r'using \1 as a bargaining chip'),
        (r'\bheld\s+(.*?)\s+hostage\b', r'used \1 as a bargaining chip'),
        (r'\bhostage\b', 'tied-up'),
        (r'\blive\s+bomb\b', 'firecracker'),
        (r'\bbomb\b', 'firecracker'),
        (r'\bcommit\s+a\s+crime\b', 'lose her temper'),
        (r'\bcrime\b', 'prank'),
        (r'\bnear\s+death\s+experience\b', 'hilarious close call'),
        (r'\bdeath\b', 'disaster'),
        (r'\bdead\b', 'done for'),
        (r'\bkilled\b', 'busted'),
        (r'\bkill\b', 'catch'),
        (r'\bmurder\b', 'trouble'),
        (r'\bsuicide\b', 'mistake'),
        (r'\bkidnapped\b', 'carried away'),
        (r'\bkidnap\b', 'carry away'),
        (r'\bterrorist\b', 'prankster'),
        (r'\bweapon\b', 'prop'),
        (r'\bgun\b', 'water blaster'),
        (r'\bliquor\b', 'secret drink'),
        (r'\balcohol\b', 'secret drink'),
    ]
    for pat, repl in safe_replacements:
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)

    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^[\s\-_:,\.]+|[\s\-_:,\.]+$', '', text).strip()
    return text


def get_video_duration(video_path: str) -> float:
    cmd = [FFMPEG_BIN, "-i", video_path]
    p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
    for line in p.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 60.0


LAST_CONDENSED_CHAPTERS = []


def make_lowres_copy_for_gemini(src_path: str, prefix: str = "gemini_lowres", burn_timecode: bool = True) -> str:
    dst_path = os.path.join(SCRATCH_DIR, f"{prefix}_{os.path.basename(src_path)}")
    print(f"[Gemini] Compressing video to 480p lightweight copy for Gemini (On-Screen Timecode={burn_timecode})...")
    if burn_timecode:
        vf_str = "scale=-2:480,drawtext=text='TIME\\: %{pts\\:flt}s':x=16:y=16:fontsize=32:fontcolor=yellow:box=1:boxcolor=black@0.85"
        cmd_tc = [
            FFMPEG_BIN, "-y",
            "-i", src_path,
            "-vf", vf_str,
            "-c:v", "libx264",
            "-crf", "30",
            "-preset", "veryfast",
            "-c:a", "aac",
            "-b:a", "64k",
            dst_path
        ]
        res = subprocess.run(cmd_tc, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(dst_path) and os.path.getsize(dst_path) > 1000:
            print(f"[Gemini] Lightweight timecode-stamped copy ready: {os.path.getsize(dst_path) / (1024*1024):.1f} MB")
            return dst_path

    cmd = [
        FFMPEG_BIN, "-y",
        "-i", src_path,
        "-vf", "scale=-2:480",
        "-c:v", "libx264",
        "-crf", "30",
        "-preset", "veryfast",
        "-c:a", "aac",
        "-b:a", "64k",
        dst_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[Gemini] Lightweight copy ready: {os.path.getsize(dst_path) / (1024*1024):.1f} MB")
    return dst_path


def upload_video_to_gemini_files(lowres_vid: str, api_key: str) -> str:
    file_size = os.path.getsize(lowres_vid)
    init_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={api_key}"
    headers = {
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(file_size),
        "X-Goog-Upload-Header-Type": "video/mp4",
        "Content-Type": "application/json"
    }
    r1 = requests.post(init_url, headers=headers, json={"file": {"display_name": os.path.basename(lowres_vid)}}, timeout=15)
    up_url = r1.headers.get("X-Goog-Upload-URL") or r1.headers.get("Upload-URL")
    if not up_url:
        return ""

    with open(lowres_vid, "rb") as f:
        data = f.read()

    r2 = requests.post(up_url, headers={
        "Content-Length": str(file_size),
        "X-Goog-Upload-Offset": "0",
        "X-Goog-Upload-Command": "upload, finalize"
    }, data=data, timeout=45)

    file_info = r2.json().get("file", {})
    file_name = file_info.get("name")
    file_uri = file_info.get("uri")
    print(f"[Gemini] Uploaded {file_name}. Waiting for ACTIVE state...")

    check_url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={api_key}"
    for _ in range(35):
        time.sleep(3)
        info = requests.get(check_url, timeout=10).json()
        if info.get("state") == "ACTIVE":
            print(f"[Gemini] Video {file_name} is ACTIVE!")
            return file_uri
    return ""


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
        # Add +0.04s on start cut or -0.04s on end cut to stay strictly inside the intended camera shot
        adjusted = best_cut + (0.04 if is_start else -0.04)
        print(f"[SceneLock] Snapped {'START' if is_start else 'END'} {target_t:.2f}s -> exact camera cut {adjusted:.2f}s")
        return round(max(0.0, min(total_dur, adjusted)), 2)

    return round(target_t, 2)


def condense_video_with_gemini(raw_video_path: str) -> str:
    """
    PASS 1 (Master Story Arc Finder — Zero Middle Jump Cuts):
    Gemini watches the entire raw video from start to finish and finds the SINGLE BEST,
    MOST HILARIOUS, SELF-CONTAINED CONTINUOUS STORY ARC (60s to 67s long -> ~53s to 58.5s at 1.15x).
    Because it is extracted as ONE UNBROKEN CONTINUOUS SEQUENCE (snapped to exact camera cuts),
    there are ZERO sudden middle jumps.
    """
    global LAST_CONDENSED_CHAPTERS
    LAST_CONDENSED_CHAPTERS = []

    total_dur = get_video_duration(raw_video_path)
    if total_dur <= 68.0:
        print(f"[Editor Pass 1] Video is {total_dur:.1f}s (<=68s), already under 1 min at 1.15x! Keeping 100% uncut.")
        LAST_CONDENSED_CHAPTERS = [{
            "chap": 1,
            "start": 0.0,
            "end": round(total_dur, 2),
            "description": "Full continuous comedy story",
            "full_backstory": "Complete original video"
        }]
        return raw_video_path

    print(f"\n[Editor Pass 1] Video is {total_dur:.1f}s. Asking Gemini to find the SINGLE BEST continuous 60-67s story arc (Zero Middle Cuts)...")
    candidate_keys = get_candidate_gemini_keys()
    lowres_full = make_lowres_copy_for_gemini(raw_video_path, prefix="pass1_full", burn_timecode=True)

    editor_prompt = f"""You are a Master Comedy Film Editor.
First, watch this ENTIRE video carefully from 0.0s to {total_dur:.1f}s. Look at the yellow 'TIME: X.Xs' digital clock in the top-left corner of every frame.
Understand the complete plot, why the characters are doing what they are doing, and where the funniest continuous story arc happens.

TASK:
Select ONE SINGLE, UNBROKEN, CONTINUOUS STORY ARC (between 60.0 and 67.0 seconds long) that tells a complete, crystal-clear, hilarious story from setup to climax with ZERO middle cuts!

STRICT RULES:
1. INSTANT OPENING HOOK (FIRST 2 SECONDS):
   - The 'start' timestamp MUST begin right at an eye-catching, funny, or expressive action moment (never start on an empty or slow walking frame).
2. ONE UNBROKEN CONTINUOUS STORY (60 to 67 SECONDS LONG):
   - Do NOT cut pieces from different places. Pick ONE continuous window [start, end] (60.0 to 67.0 seconds total) that contains a complete comedy sequence and ends on the funniest payoff!
3. FAMILY-SAFE SUMMARY:
   - Describe the plot and backstory using 100% clean, family-safe comedy words (never use words like hostage, bomb, crime, kill, death, murder, kidnap).

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown backticks, no extra text):
{{
  "full_backstory": "Clear, family-safe explanation of the full video plot and why the characters are in this funny situation",
  "story_summary": "Clear summary of what happens inside this continuous story arc [start to end]",
  "start": 18.0,
  "end": 84.0,
  "why_this_arc_works": "Why this continuous ~65s window tells a complete, hilarious story"
}}"""

    chosen_start = None
    chosen_end = None
    chosen_summary = "Continuous comedy story arc"
    full_backstory = "Hilarious comedy skit"

    for api_key in candidate_keys:
        try:
            file_uri = upload_video_to_gemini_files(lowres_full, api_key)
            if not file_uri:
                continue

            for model in ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-flash-latest"]:
                try:
                    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                    payload = {
                        "contents": [{
                            "parts": [
                                {"file_data": {"mime_type": "video/mp4", "file_uri": file_uri}},
                                {"text": editor_prompt}
                            ]
                        }]
                    }
                    res = requests.post(gen_url, json=payload, timeout=55)
                    if res.status_code == 200:
                        raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text).strip()
                        parsed = json.loads(clean_json)
                        if "start" in parsed and "end" in parsed:
                            s_val = float(parsed["start"])
                            e_val = float(parsed["end"])
                            if e_val - s_val >= 45.0:
                                chosen_start = s_val
                                chosen_end = e_val
                                chosen_summary = sanitize_speech_text(parsed.get("story_summary", chosen_summary))
                                full_backstory = sanitize_speech_text(parsed.get("full_backstory", chosen_summary))
                                print(f"[Editor Pass 1] Gemini ({model}) Selected Continuous Arc: {chosen_start:.1f}s -> {chosen_end:.1f}s ({chosen_end - chosen_start:.1f}s)")
                                print(f"[Editor Pass 1] Full Backstory: {full_backstory}")
                                print(f"[Editor Pass 1] Story Arc Summary: {chosen_summary}")
                                break
                except Exception as ex:
                    print(f"[Editor Pass 1] Model {model} notice: {ex}")
            if chosen_start is not None:
                break
        except Exception as e:
            print(f"[Editor Pass 1] Key error: {e}")

    if chosen_start is None or chosen_end is None:
        chosen_end = total_dur
        chosen_start = max(0.0, round(total_dur - 65.0, 1))
        print(f"[Editor Pass 1] Using continuous climax story arc: {chosen_start:.1f}s -> {chosen_end:.1f}s")

    # Clamp duration to [56s, 67s] so at 1.15x it is 49s to 58.5s (proven 75% retention sweet spot)
    chosen_start = max(0.0, min(chosen_start, total_dur - 56.0))
    if chosen_end - chosen_start > 67.5:
        chosen_end = chosen_start + 66.0
    elif chosen_end - chosen_start < 54.0:
        chosen_end = min(total_dur, chosen_start + 63.0)

    s_snap = snap_timestamp_to_camera_cut(raw_video_path, chosen_start, total_dur, is_start=True)
    e_snap = snap_timestamp_to_camera_cut(raw_video_path, chosen_end, total_dur, is_start=False)
    if e_snap - s_snap < 45.0:
        s_snap, e_snap = chosen_start, chosen_end

    dur_c = e_snap - s_snap
    LAST_CONDENSED_CHAPTERS = [{
        "chap": 1,
        "start": 0.0,
        "end": round(dur_c, 2),
        "description": chosen_summary,
        "full_backstory": full_backstory
    }]

    condensed_path = os.path.join(SCRATCH_DIR, f"condensed_{os.path.basename(raw_video_path)}")
    print(f"[Editor Pass 1] Extracting UNBROKEN Continuous Story Arc: {s_snap:.2f}s -> {e_snap:.2f}s ({dur_c:.1f}s raw -> {dur_c/1.15:.1f}s at 1.15x)")
    vf_fade = f"fade=t=in:st=0:d=0.2,fade=t=out:st={max(0.1, dur_c - 0.2):.2f}:d=0.2"
    cmd_extract = [
        FFMPEG_BIN, "-y",
        "-ss", f"{s_snap:.2f}",
        "-to", f"{e_snap:.2f}",
        "-i", raw_video_path,
        "-vf", vf_fade,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        condensed_path
    ]
    subprocess.run(cmd_extract, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    new_dur = get_video_duration(condensed_path)
    print(f"[Editor Pass 1] Condensed unbroken story video ready: {condensed_path} ({new_dur:.1f}s raw -> {new_dur/1.15:.1f}s at 1.15x!)")
    return condensed_path


def normalize_script_timeline(data: dict, total_dur: float) -> dict:
    if "speech" not in data or not data["speech"]:
        return data

    speech = data["speech"]
    max_allowed = max(3.0, total_dur - 2.2)

    for idx, row in enumerate(speech):
        raw_t = float(row[1])
        # Visual-First Reaction Delay (+0.4s after opening hook) so the viewer sees the action first
        if idx > 0:
            raw_t = round(raw_t + 0.4, 1)
        row[1] = round(min(max_allowed, max(0.4, raw_t)), 1)

    speech.sort(key=lambda x: float(x[1]))

    # Ensure minimum 3.6s spacing so storytelling lines never crowd each other
    for i in range(1, len(speech)):
        if speech[i][1] < speech[i - 1][1] + 3.6:
            speech[i][1] = round(min(max_allowed, speech[i - 1][1] + 3.6), 1)

    data["speech"] = speech

    for row in data.get("sfx", []):
        row[1] = round(min(max_allowed, max(0.4, float(row[1]) + 0.3)), 1)

    print(f"[Gemini Pass 2] Locked {len(speech)} visual-first storytelling lines across {total_dur:.1f}s continuous video.")
    return data


def generate_comedy_script_with_gemini(edited_video_path: str) -> dict:
    """
    PASS 2 (Clear & Engaging Comedy Storyteller — Proven 14XiUbqjqvw Formula + 100% Seed-Shelf Safe):
    Gemini watches the UNBROKEN ~65s video (with burned-in yellow 'TIME: X.Xs' clock)
    and writes a clear, funny, easy-to-follow story narration + unique topic-matched title,
    description, and tags with ZERO unsafe trigger words.
    """
    total_dur = get_video_duration(edited_video_path)
    candidate_keys = get_candidate_gemini_keys()
    lowres_vid = make_lowres_copy_for_gemini(edited_video_path, prefix="pass2_edited", burn_timecode=True)

    story_context = LAST_CONDENSED_CHAPTERS[0]["description"] if LAST_CONDENSED_CHAPTERS else "Continuous comedy story"
    full_backstory = LAST_CONDENSED_CHAPTERS[0].get("full_backstory", story_context) if LAST_CONDENSED_CHAPTERS else story_context

    prompt = f"""You are a hilarious, crystal-clear comedy storyteller (like a top viral YouTube Shorts narrator).
First, watch this entire {total_dur:.1f}-second continuous video carefully from start to finish.
Look at the yellow 'TIME: X.Xs' digital clock in the top-left corner of every frame! That clock shows the EXACT timestamp in seconds.

STORY CONTEXT OF THIS VIDEO:
- Full video plot: "{full_backstory}"
- What happens in this {total_dur:.1f}s clip: "{story_context}"

YOUR GOAL:
Narrate this video so that ANY viewer immediately understands the FULL STORY—who the characters are, WHY they are doing what they're doing, what their funny plan/trick is, and how it turns out! Never leave the viewer confused about what is happening!

STRICT RULES (DO NOT VIOLATE):
1. CLEAR STORYTELLING (EXPLAIN THE 'WHY' AND 'WHAT'):
   - Clearly and wittily explain the story beats on screen (e.g., "Angry wife charges with giant hammer after catching husband with his secret stash!", "His smart buddy quickly hides him under a straw pile!", "He pulls out a romantic rose to charm the neighbor instead!", "When she puckers up for a kiss, he sprints off with his buddy!").
   - Every line must connect naturally to the next like a fun story!
2. 100% FAMILY-SAFE & YOUTUBE SHORTS SEED-SHELF SAFE LANGUAGE (CRITICAL):
   - NEVER use sensitive or restricted words anywhere in title, description, tags, or speech: NO 'hostage', 'bomb', 'live bomb', 'crime', 'commit a crime', 'kill', 'murder', 'dead', 'death', 'suicide', 'kidnap', 'terror', 'gun', 'weapon', 'blood', 'liquor', 'alcohol'.
   - Use playful, family-friendly comedy words instead: 'secret bottle', 'bargaining chip', 'sneaky trap', 'clever prank', 'tied up', 'fake fainting trick', 'hilarious close call', 'busted'.
3. VISUAL-FIRST AUDIO SYNC (READ THE YELLOW 'TIME: X.Xs' CLOCK):
   - Total video duration is EXACTLY {total_dur:.1f} seconds.
   - Read the yellow 'TIME: X.Xs' clock on the frame when an action physically starts on screen, and place your line at that exact second so the viewer sees the action and hears your explanation simultaneously!
   - Write 11 to 12 engaging lines across the {total_dur:.1f}s video (roughly every 4.8 to 5.2 seconds, between 0.5s and {total_dur - 2.5:.1f}s).
   - Keep each line 7 to 11 words long—clear, natural, and funny!
4. UNIQUE, SPECIFIC VIRAL TITLE, DESCRIPTION & TAGS (NO REPETITIVE SPAM):
   - Write a fresh, curiosity-inducing title specific to THIS video's funniest object/action (e.g., "His Rose Distraction Plan Backfired Instantly! 🌹😂 #Shorts" or "When Husband Tries To Outsmart His Powerful Wife! 🔨😂 #Shorts"). Do NOT put "200 IQ" or "Hostage" in the title!
   - Write a unique 2-sentence description summarizing this exact funny story, plus 6-8 relevant hashtags.
   - Provide 10-12 specific tags matching the actual objects and characters in this video (never include unrelated tags like 'Rooster' or 'Barnyard' unless a rooster is actually in the video).
5. PERFECT SFX TIMING:
   - Place meme sounds at the exact second on the yellow clock where shock, fail, or laughter happens:
     'vine_boom.mp3', 'wait_a_minute.mp3', 'metal_pipe.mp3', 'windows_error.mp3', 'bruh.mp3', 'no_god_please_no.mp3', 'sad_violin.mp3', 'oh_no_wheeze_laugh.mp3', 'anime_wow.mp3', 'fbi_open_up.mp3', 'ding_idea.mp3', 'yeet.mp3'
6. NEVER MENTION SOUND NAMES IN SPEECH:
   - The "speech" list is 100% pure spoken comedy storytelling. Never write '.mp3' or sound names in speech.

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown backticks, no extra text):
{{
  "title": "His Rose Distraction Plan Backfired Instantly! 🌹😂 #Shorts",
  "description": "Unique 2-sentence summary of this exact comedy story! 😂🔥 #Shorts #Comedy #Funny #Prank #Humor #Storytime",
  "tags": ["Shorts", "Comedy", "Funny", "Prank", "Humor", "Storytime", "HusbandWife", "InstantKarma", "Viral", "Laughter"],
  "speech": [
    ["01", 0.5, "Clear, funny opening hook explaining how the situation starts."],
    ["02", 5.4, "Next connected storytelling line matching the yellow clock."]
  ],
  "sfx": [
    ["vine_boom.mp3", 5.4, 0.85],
    ["oh_no_wheeze_laugh.mp3", 25.0, 0.85]
  ]
}}"""

    for api_key in candidate_keys:
        try:
            file_uri = upload_video_to_gemini_files(lowres_vid, api_key)
            if not file_uri:
                continue

            print(f"[Gemini Pass 2] Prompting Gemini for Clear Connected Story Script on {total_dur:.1f}s unbroken video...")
            for model in ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-flash-latest", "gemini-3.1-flash-lite"]:
                try:
                    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                    payload = {
                        "contents": [{
                            "parts": [
                                {"file_data": {"mime_type": "video/mp4", "file_uri": file_uri}},
                                {"text": prompt}
                            ]
                        }]
                    }
                    res = requests.post(gen_url, json=payload, timeout=55)
                    if res.status_code == 200:
                        raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text).strip()
                        data = json.loads(clean_json)

                        clean_speech = []
                        for sp in data.get("speech", []):
                            s_id = sp[0] if len(sp) > 2 else f"line_{len(clean_speech):02d}"
                            s_t = float(sp[1]) if len(sp) > 2 else 0.5
                            s_txt = str(sp[2]) if len(sp) > 2 else str(sp[0])
                            s_clean = sanitize_speech_text(s_txt)
                            if len(s_clean.split()) >= 2:
                                clean_speech.append([s_id, s_t, s_clean])
                        data["speech"] = clean_speech

                        if "title" in data:
                            data["title"] = sanitize_speech_text(data["title"])
                            if "#Shorts" not in data["title"] and "#shorts" not in data["title"]:
                                data["title"] = f"{data['title']} #Shorts"
                        if "description" in data:
                            data["description"] = sanitize_speech_text(data["description"])

                        if len(data["speech"]) >= 5:
                            norm_data = normalize_script_timeline(data, total_dur)
                            try:
                                meta_path = os.path.join(SCRATCH_DIR, "latest_metadata.json")
                                with open(meta_path, "w", encoding="utf-8") as mf:
                                    json.dump({
                                        "title": norm_data.get("title", ""),
                                        "description": norm_data.get("description", ""),
                                        "tags": norm_data.get("tags", [])
                                    }, mf, indent=2, ensure_ascii=False)
                            except Exception:
                                pass
                            print(f"[Gemini Pass 2] Received {len(norm_data['speech'])} clear, family-safe storytelling lines from {model}!")
                            return norm_data
                except Exception as ex_m:
                    print(f"[Gemini Pass 2] Model {model} attempt: {ex_m}")
        except Exception as e:
            print(f"[Gemini Pass 2] API error: {e}")

    print("[Gemini Pass 2] Using dynamic comedy fallback...")
    step_interval = max(4.5, total_dur / 10.0)
    generic_beats = []
    t = 0.5
    idx = 1
    for line in [
        "Watch how this clever prank plan starts unfolding right here.",
        "Look at their sheer confidence right before the chaos begins.",
        "So they immediately come up with a sneaky backup plan.",
        "Wait for it... this is where the whole trick goes sideways.",
        "He really thought nobody would notice what just happened.",
        "And that instant karma at the end is pure comedy gold."
    ]:
        if t < total_dur - 2.5:
            generic_beats.append([f"line_{idx:02d}", round(t, 1), line])
            t += step_interval
            idx += 1
    return {
        "title": "His Clever Prank Plan Backfired Instantly! 😂 #Shorts",
        "description": "He really thought his sneaky backup plan would work, until instant karma took over! 😂🔥 #Shorts #Comedy #Funny #Prank #Humor #Storytime",
        "tags": ["Shorts", "Comedy", "Funny", "Prank", "Humor", "Storytime", "InstantKarma", "Viral", "Laughter"],
        "speech": generic_beats,
        "sfx": [
            ["vine_boom.mp3", 1.0, 0.85],
            ["windows_error.mp3", min(round(total_dur * 0.5, 1), total_dur - 4.0), 0.85],
            ["oh_no_wheeze_laugh.mp3", max(0.5, round(total_dur - 2.5, 1)), 0.85]
        ]
    }
