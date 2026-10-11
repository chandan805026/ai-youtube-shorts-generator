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
    PASS 1 (Master Story Editor):
    If the raw video is longer than 68s, Gemini carefully watches the full video,
    understands the complete story, and selects 2 or 3 LONG, CONNECTED STORY CHAPTERS
    (each 15s-26s long, totaling ~58-65s raw -> ~50-56s after 1.15x speed) with
    exact camera-cut snapping so there are ZERO sudden or confusing jumps!
    """
    global LAST_CONDENSED_CHAPTERS
    LAST_CONDENSED_CHAPTERS = []

    total_dur = get_video_duration(raw_video_path)
    if total_dur <= 68.0:
        print(f"[Editor Pass 1] Video is {total_dur:.1f}s (<=68s), already under 1 min at 1.15x! Keeping 100% uncut.")
        LAST_CONDENSED_CHAPTERS = [{"chap": 1, "start": 0.0, "end": round(total_dur, 2), "description": "Full continuous comedy video"}]
        return raw_video_path

    print(f"\n[Editor Pass 1] Video is {total_dur:.1f}s. Asking Gemini Master Editor to select connected story chapters (<60s target)...")
    candidate_keys = get_candidate_gemini_keys()
    lowres_full = make_lowres_copy_for_gemini(raw_video_path, prefix="pass1_full", burn_timecode=True)

    editor_prompt = f"""You are a Master Film & Comedy Video Editor.
First, watch this entire video carefully from start to finish ({total_dur:.1f} seconds). Notice the yellow 'TIME: X.Xs' digital clock in the top-left corner showing the exact second of every frame. Deeply understand the complete story, characters, setups, pranks, and final climax.

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

    selected_chapters = None
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
                    res = requests.post(gen_url, json=payload, timeout=50)
                    if res.status_code == 200:
                        raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text).strip()
                        parsed = json.loads(clean_json)
                        chaps = parsed.get("chapters", [])
                        if 2 <= len(chaps) <= 4:
                            print(f"[Editor Pass 1] Gemini ({model}) Story Summary: {parsed.get('story_summary', '')}")
                            selected_chapters = chaps
                            break
                except Exception as ex:
                    print(f"[Editor Pass 1] Model {model} notice: {ex}")
            if selected_chapters:
                break
        except Exception as e:
            print(f"[Editor Pass 1] Key error: {e}")

    # Validate & sanitize chapters (if Gemini didn't return valid chapters, use 3-part story arc: Setup + Middle + Climax)
    valid_ranges = []
    if selected_chapters:
        prev_end = 0.0
        for ch in selected_chapters:
            s = max(prev_end, float(ch.get("start", 0.0)))
            e = min(total_dur, float(ch.get("end", s + 18.0)))
            if e - s >= 10.0:
                valid_ranges.append((s, e, ch.get("description", "Story chapter")))
                prev_end = e + 0.5

    total_selected = sum(e - s for s, e, _ in valid_ranges)
    if not valid_ranges or total_selected < 42.0 or total_selected > 72.0:
        print("[Editor Pass 1] Applying balanced 3-Chapter Story Arc (Setup 18s + Main Action 22s + Climax 22s = 62s)...")
        mid_start = round(total_dur * 0.38, 1)
        valid_ranges = [
            (0.0, 18.0, "Opening Setup"),
            (mid_start, mid_start + 22.0, "Main Comedy Action"),
            (max(mid_start + 23.0, total_dur - 22.0), total_dur, "Final Climax")
        ]

    # Snap every cut to exact millisecond camera shot boundaries and extract chapters
    part_files = []
    running_t = 0.0
    for idx, (s_raw, e_raw, desc) in enumerate(valid_ranges):
        s_snap = snap_timestamp_to_camera_cut(raw_video_path, s_raw, total_dur, is_start=True)
        e_snap = snap_timestamp_to_camera_cut(raw_video_path, e_raw, total_dur, is_start=False)
        if e_snap - s_snap < 8.0:
            s_snap, e_snap = s_raw, e_raw

        part_path = os.path.join(SCRATCH_DIR, f"chap_{idx:02d}_{os.path.basename(raw_video_path)}")
        dur_c = e_snap - s_snap
        print(f"[Editor Pass 1] Extracting Chapter {idx+1}: {s_snap:.2f}s -> {e_snap:.2f}s ({dur_c:.1f}s) | Condensed Window: [{running_t:.2f}s -> {running_t + dur_c:.2f}s] [{desc}]")
        LAST_CONDENSED_CHAPTERS.append({
            "chap": idx + 1,
            "start": round(running_t, 2),
            "end": round(running_t + dur_c, 2),
            "description": desc
        })
        running_t += dur_c

        # Smooth 0.15s fade-in/out on chapter boundaries so transitions feel like a movie edit
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

    concat_list_path = os.path.join(SCRATCH_DIR, "chapters_concat.txt")
    with open(concat_list_path, "w", encoding="utf-8") as cf:
        for pf in part_files:
            safe_p = pf.replace("\\", "/")
            cf.write(f"file '{safe_p}'\n")

    condensed_path = os.path.join(SCRATCH_DIR, f"condensed_{os.path.basename(raw_video_path)}")
    cmd_concat = [
        FFMPEG_BIN, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        condensed_path
    ]
    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    new_dur = get_video_duration(condensed_path)
    print(f"[Editor Pass 1] Condensed story video ready: {condensed_path} ({new_dur:.1f}s raw -> {new_dur/1.15:.1f}s at 1.15x!)")
    return condensed_path


def normalize_script_timeline(data: dict, total_dur: float) -> dict:
    if "speech" not in data or not data["speech"]:
        return data

    speech = data["speech"]
    max_allowed = max(3.0, total_dur - 2.2)

    # Identify exact chapter boundary cut points (e.g. 21.01s, 40.10s)
    cut_boundaries = [ch["start"] for ch in LAST_CONDENSED_CHAPTERS if ch["start"] > 1.0]

    for idx, row in enumerate(speech):
        raw_t = float(row[1])
        # Visual-First Reaction Lock:
        # 1. If a line was placed in the last 2.2s right BEFORE a chapter transition,
        #    it almost certainly belongs to the incoming chapter — snap it to cut_t + 0.5s
        #    so the audio NEVER speaks before the new chapter appears on screen!
        snapped_to_cut = False
        for cut_t in cut_boundaries:
            if (cut_t - 2.2) <= raw_t < (cut_t + 0.4):
                new_t = round(cut_t + 0.5, 1)
                print(f"[VisualSync] Snapped early pre-cut line '{row[2][:32]}...' from {raw_t:.1f}s -> {new_t:.1f}s (after chapter cut {cut_t:.2f}s)")
                raw_t = new_t
                snapped_to_cut = True
                break

        # 2. For all lines after the opening hook (idx > 0) that weren't just snapped,
        #    add a +0.5s Visual-First Reaction Delay so the viewer's eyes see the visual
        #    action FIRST and hear the voiceover right as it happens (never audio-first!).
        if idx > 0 and not snapped_to_cut:
            raw_t = round(raw_t + 0.5, 1)

        row[1] = round(min(max_allowed, max(0.3, raw_t)), 1)

    speech.sort(key=lambda x: float(x[1]))

    # Ensure minimum 3.4s spacing so lines never crowd or push each other out of sync
    for i in range(1, len(speech)):
        if speech[i][1] < speech[i - 1][1] + 3.4:
            speech[i][1] = round(min(max_allowed, speech[i - 1][1] + 3.4), 1)

    data["speech"] = speech

    for row in data.get("sfx", []):
        row[1] = round(min(max_allowed, max(0.4, float(row[1]) + 0.4)), 1)

    print(f"[Gemini Pass 2] Locked {len(speech)} visual-first timestamps across {total_dur:.1f}s edited video.")
    return data


def generate_comedy_script_with_gemini(edited_video_path: str) -> dict:
    """
    PASS 2 (1:1 Storyteller on the Condensed Video):
    Gemini watches the ALREADY-CONDENSED ~60s video (with burned-in yellow 'TIME: X.Xs' clock)
    and writes a comedy narrative strictly locked inside each chapter's exact time window!
    """
    total_dur = get_video_duration(edited_video_path)
    candidate_keys = get_candidate_gemini_keys()
    lowres_vid = make_lowres_copy_for_gemini(edited_video_path, prefix="pass2_edited", burn_timecode=True)

    chapter_guide_lines = []
    if LAST_CONDENSED_CHAPTERS:
        for ch in LAST_CONDENSED_CHAPTERS:
            c_idx = ch["chap"]
            c_s = ch["start"]
            c_e = ch["end"]
            c_desc = ch["description"]
            safe_s = round(c_s + 0.5, 1)
            safe_e = round(max(safe_s + 2.0, c_e - 2.5), 1)
            chapter_guide_lines.append(
                f"   - CHAPTER {c_idx} ({c_s:.1f}s to {c_e:.1f}s): \"{c_desc}\"\n"
                f"     -> Place Chapter {c_idx} speech lines ONLY between {safe_s:.1f}s and {safe_e:.1f}s! NEVER mention Chapter {c_idx} events before {safe_s:.1f}s!"
            )
    chapter_guide_text = "\n".join(chapter_guide_lines) if chapter_guide_lines else f"   - Full Video (0.5s to {total_dur - 2.5:.1f}s)"

    prompt = f"""You are an observant comedy storyteller (witty British/Global meme narrator style, like Liam).
First, watch this entire {total_dur:.1f}-second video from start to finish.
Look at the yellow 'TIME: X.Xs' digital clock in the top-left corner of every frame! That clock shows the EXACT timestamp in seconds.

EXACT CHAPTER MAP OF THIS {total_dur:.1f}-SECOND VIDEO:
{chapter_guide_text}

STRICT VISUAL-FIRST AUDIO SYNC RULES (CRITICAL — DO NOT VIOLATE):
1. NEVER SPEAK BEFORE THE VISUAL ACTION APPEARS ("Audio pahle mat bolo, video dikhne ke baad bolo"):
   - Read the yellow 'TIME: X.Xs' clock on the frame when an action, object, or person ACTUALLY APPEARS on screen.
   - Set the speech line's timestamp to the exact second (or +0.4s AFTER) that visual appears on screen—NEVER 1 to 3 seconds before it appears!
   - Strictly obey the CHAPTER MAP above: NEVER mention an action from Chapter 2 while the video is still in Chapter 1, and NEVER mention an action from Chapter 3 while the video is still in Chapter 2!
2. PUNCHY & CONCISE LINES (10 to 12 lines total):
   - Write 3 to 4 lines per chapter, spaced at least 4.5 to 5.5 seconds apart.
   - Keep each line short and punchy (5 to 8 words maximum) so it finishes cleanly within 2.5 seconds while that exact shot is still on screen.
3. UNIVERSAL VIRAL MEME TITLE:
   - Write a broad, mass-appeal viral title (e.g., "Bro Really Thought His 200 IQ Plan Would Work 💀" or "Instant Karma Hit Him at 100 MPH 😂").
4. PERFECT SFX TIMING:
   - Place meme sounds at the exact second on the yellow clock where shock, fail, or laughter happens:
     'vine_boom.mp3', 'wait_a_minute.mp3', 'metal_pipe.mp3', 'windows_error.mp3', 'bruh.mp3', 'no_god_please_no.mp3', 'sad_violin.mp3', 'oh_no_wheeze_laugh.mp3', 'anime_wow.mp3', 'fbi_open_up.mp3', 'ding_idea.mp3', 'yeet.mp3'
5. NEVER MENTION SOUND NAMES IN SPEECH:
   - The "speech" list is 100% pure spoken comedy storytelling. Never write '.mp3' or sound names in speech.

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown backticks, no extra text):
{{
  "title": "Bro Really Thought His 200 IQ Plan Would Work 💀 #Shorts",
  "speech": [
    ["01", 0.5, "Opening hook matching the first scene."],
    ["02", 5.5, "Next witty line right after the action appears."]
  ],
  "sfx": [
    ["vine_boom.mp3", 5.5, 0.85],
    ["oh_no_wheeze_laugh.mp3", 25.0, 0.85]
  ]
}}"""

    for api_key in candidate_keys:
        try:
            file_uri = upload_video_to_gemini_files(lowres_vid, api_key)
            if not file_uri:
                continue

            print(f"[Gemini Pass 2] Prompting Gemini for Visual-First + Chapter-Locked script on {total_dur:.1f}s video...")
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
                    res = requests.post(gen_url, json=payload, timeout=50)
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

                        if len(data["speech"]) >= 5:
                            print(f"[Gemini Pass 2] Received {len(data['speech'])} scene-locked lines from {model}!")
                            return normalize_script_timeline(data, total_dur)
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
        "Right, watch what this absolute genius is trying to pull off.",
        "Look at the sheer confidence right before chaos begins.",
        "So he immediately comes up with a two hundred IQ backup plan.",
        "Wait for it... this is where the whole mission goes sideways.",
        "Bro really thought nobody would notice what just happened.",
        "And that instant karma at the end is pure comedy gold."
    ]:
        if t < total_dur - 2.5:
            generic_beats.append([f"line_{idx:02d}", round(t, 1), line])
            t += step_interval
            idx += 1
    return {
        "title": "Bro Really Thought His 200 IQ Plan Would Work 💀 #Shorts",
        "speech": generic_beats,
        "sfx": [
            ["vine_boom.mp3", 1.0, 0.85],
            ["windows_error.mp3", min(round(total_dur * 0.5, 1), total_dur - 4.0), 0.85],
            ["oh_no_wheeze_laugh.mp3", max(0.5, round(total_dur - 2.5, 1)), 0.85]
        ]
    }
