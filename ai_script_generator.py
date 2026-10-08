import os
import sys
import json
import urllib.request
import urllib.error
import re
import time

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()

# Prioritized list of high-quota (500 RPD) models
GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest"
]


def normalize_script_data(data: dict, total_duration: float) -> dict:
    """
    Ensures edit_segments is a clean list of (start, end) tuples and
    calculates the exact resulting edited duration, strictly capped at ~50-65s for YouTube Shorts.
    Guarantees every segment has start < end, start < total_duration, and positive duration.
    """
    raw_segs = data.get("edit_segments") or data.get("segments")
    norm_segs = []
    if raw_segs and isinstance(raw_segs, list):
        for item in raw_segs:
            raw_st = 0.0
            raw_et = 0.0
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                raw_st = float(item[0])
                raw_et = float(item[1])
            elif isinstance(item, dict) and "start" in item and "end" in item:
                raw_st = float(item["start"])
                raw_et = float(item["end"])

            # Discard hallucinated segments that start beyond total duration
            if raw_st >= total_duration - 1.0:
                continue

            clean_st = max(0.0, min(total_duration - 1.0, raw_st))
            clean_et = max(clean_st + 1.0, min(total_duration, raw_et))
            if clean_et > clean_st + 0.5:
                norm_segs.append((clean_st, clean_et))

    if not norm_segs and "cut_start" in data and "cut_end" in data:
        raw_st = float(data["cut_start"])
        raw_et = float(data["cut_end"])
        if raw_st < total_duration - 1.0:
            clean_st = max(0.0, raw_st)
            clean_et = max(clean_st + 1.0, min(total_duration, raw_et))
            norm_segs = [(clean_st, clean_et)]

    if not norm_segs:
        if total_duration > 65.0:
            norm_segs = [(0.0, min(total_duration, 60.0))]
        else:
            norm_segs = [(0.0, total_duration)]

    # Sort chronologically
    norm_segs.sort(key=lambda x: x[0])

    # Cap total edited duration to maximum 65.0s for Shorts
    accumulated = 0.0
    capped_segs = []
    for st, et in norm_segs:
        dur = et - st
        if dur <= 0.5:
            continue
        if accumulated + dur > 65.0:
            allowed = max(2.0, 65.0 - accumulated)
            if allowed >= 1.0:
                capped_segs.append((st, st + allowed))
                accumulated += allowed
            break
        else:
            capped_segs.append((st, et))
            accumulated += dur

    if not capped_segs:
        capped_segs = [(0.0, min(total_duration, 55.0))]

    edited_duration = sum([max(0.0, et - st) for st, et in capped_segs])
    data["edit_segments"] = capped_segs
    data["edited_duration"] = edited_duration
    return data


def generate_comedy_script_with_gemini(video_path: str, caption: str, author: str, total_duration: float) -> dict:
    """
    Analyzes the actual video with Gemini 3.5 Flash Lite Vision to produce:
    1. Exact narrative roast script matching visual events on screen.
    2. Continuous scene cut timestamps (cut_start, cut_end, duration).
    3. Adam voiceover lines with SILENCE POCKETS for meme sounds.
    4. Meme sound effect cue points (vine_boom, bruh, etc.).
    5. Center-Screen Eye-Level Safe Zone Subtitles (MarginV: 420).
    """
    print(f"\n[AI Script] Analyzing video ({total_duration:.1f}s) for '{author}'...")

    # 1. PRIMARY: Gemini Vision via official google-genai SDK
    if GEMINI_API_KEY and video_path and os.path.exists(video_path):
        try:
            from google import genai
            print(f"[AI Script] Initializing Google GenAI Client (Safe 500 RPD Tier)...")
            client = genai.Client(api_key=GEMINI_API_KEY)

            print(f"[AI Script] Uploading video to Gemini Vision API: {os.path.basename(video_path)} ({os.path.getsize(video_path)/(1024*1024):.2f} MB)...")
            vf = client.files.upload(file=video_path)
            
            # Wait for video processing
            retries = 0
            while vf.state.name == "PROCESSING" and retries < 30:
                time.sleep(2)
                vf = client.files.get(name=vf.name)
                retries += 1

            if vf.state.name != "ACTIVE":
                print(f"[AI Script] Video state is {vf.state.name}, proceeding with caution...")

            print(f"[AI Script] Video active on Gemini cloud ({vf.name}). Prompting Gemini 3.5 Flash Lite...")

            is_long = (total_duration > 65.0)
            if is_long:
                editing_instructions = f"""STEP 3: SMART 1-MINUTE EDITING & TIMELINE COMPRESSION
This raw comedy skit is {total_duration:.1f} seconds long. For viral YouTube Shorts retention, edit this skit down to around 1 minute (Target: 50 to 65 seconds total; slight overage like 60-68s is completely fine).

SMART EDITING RULES:
1. REMOVE BORING DEAD AREAS:
   - Identify and cut out long awkward silences, slow walking, slow setups, repetitive filler reactions, or dead transition time.
2. PRESERVE CRITICAL CONTEXT (SETUP):
   - Do NOT cut out the essential story setup! Viewers must clearly understand what the secret game/prank is, who is snitching, and why everyone is panicking.
3. PRESERVE COMEDIC CLIMAX & PUNCHLINES:
   - Keep the hilarious disguise moment (twisting clothes, slapping on a wig), the approaching danger, and the climax reactions.
4. SPECIFY EDIT SEGMENTS:
   - Provide "edit_segments": [[start1, end1], [start2, end2], ...]
   - The total sum of segment durations must be approximately 50 to 65 seconds (if 1 continuous segment captures the full comedy, you can provide [[start, end]]).
5. TIMELINE SYNCHRONIZATION:
   - Liam's speech lines ("speech"), meme sounds ("sfx"), and subtitles MUST be timed relative to the RESULTING STITCHED VIDEO TIMELINE (starting at 0.0 up to total edited duration)!
   - Provide 5 to 7 punchy voiceover lines for Liam, spaced with 1.0 - 1.5s silence pockets for meme sound effects.
   - Include 4-5 meme SFX from ('vine_boom.mp3', 'bruh.mp3', 'ding_idea.mp3', 'oh_no_wheeze_laugh.mp3') timed right after key revelations.
   - Add center eye-level safe zone subtitles with emojis.
"""
            else:
                editing_instructions = f"""STEP 3: COMEDY SCRIPT SYNCHRONIZATION (~{total_duration:.1f}s)
This video is already within the ideal short duration ({total_duration:.1f}s).
Keep the whole clip: "edit_segments": [[0.0, {total_duration:.1f}]]
Write 4 to 6 punchy voiceover lines for Liam, spaced with 1.0 - 1.5s silence pockets for meme sound effects.
Include 3-4 meme SFX from ('vine_boom.mp3', 'bruh.mp3', 'ding_idea.mp3', 'oh_no_wheeze_laugh.mp3') timed right after key revelations.
Add center eye-level safe zone subtitles with emojis.
"""

            vision_prompt = f"""You are a master viral YouTube Shorts comedy writer and British deadpan narrator (BBC Wildlife Documentary meets sarcastic UK comedian like Adam / Liam).

You have full multimodal vision and audio capabilities.
CRITICAL MISSION: Listen to the spoken Chinese dialogue in this video AND watch the video action carefully. Your goal is to explain and roast this situation for UK and Western audiences who don't speak Chinese!

STEP 1: MULTIMODAL AUDIO & DIALOGUE COMPREHENSION
- Listen to what the characters are saying/shouting in Chinese:
  - Who spots the secret game and what do they shout?
  - What does the snitch report to the wife (e.g. eating her meal)?
  - What warning is shouted when the wife approaches?
  - What panic ensues, what disguise is constructed (twisting clothes, slapping on a wig)?
  - What do the approaching people say when they arrive and look around confused?
- Match the spoken Chinese words with their exact physical slapstick actions.

STEP 2: UK / WESTERN ROAST ADAPTATION (FOR ELEVENLABS LIAM - VIRAL COMEDY CREATOR)
- Explain the hilarious situation to Western viewers who don't speak Chinese with vibrant comic energy, BBC documentary mock seriousness, and sharp wit.
- Give characters witty British names (e.g. Darren, Brenda, Susan).
- Highlight the contrast between what was said, the snitch's drama, and the absurd disguise (e.g. turning a string vest into an evening halterneck top and slapping on a wig found in a hedge).
- STRICTLY FORBIDDEN: NEVER use cheap generic AI clichés ('Bro thought', 'Wait for it', 'Absolute cinema', 'Heist', 'Legendary difficulty').

{editing_instructions}

Return ONLY valid JSON with this exact schema:
{{
  "edit_segments": [
    [0.0, 22.0],
    [45.0, 85.0]
  ],
  "edited_duration": 62.0,
  "title": "Short punchy title",
  "speech": [
    ["01", 0.5, "Line 1..."],
    ["02", 9.0, "Line 2..."],
    ["03", 18.5, "Line 3..."],
    ["04", 28.0, "Line 4..."],
    ["05", 38.0, "Line 5..."],
    ["06", 48.0, "Line 6..."]
  ],
  "sfx": [
    ["vine_boom.mp3", 8.0, 0.9],
    ["ding_idea.mp3", 17.5, 0.85],
    ["bruh.mp3", 27.0, 0.9],
    ["oh_no_wheeze_laugh.mp3", 37.0, 0.95]
  ],
  "subtitles": [
    {{"start": 0.5, "end": 8.0, "style": "CenterHook", "text": "SUBTITLE LINE 💀"}},
    {{"start": 9.0, "end": 17.5, "style": "CenterPunch", "text": "SUBTITLE LINE 🚨"}},
    {{"start": 18.5, "end": 27.0, "style": "CenterPunch", "text": "SUBTITLE LINE 🍚"}},
    {{"start": 28.0, "end": 37.0, "style": "CenterPunch", "text": "SUBTITLE LINE 💇"}},
    {{"start": 38.0, "end": 47.0, "style": "CenterPunch", "text": "SUBTITLE LINE 👗"}},
    {{"start": 48.0, "end": 56.0, "style": "CenterPunch", "text": "SUBTITLE LINE 👑"}}
  ]
}}
"""

            response = None
            for vision_model in ["gemini-flash-latest", "gemini-3.8-flash", "gemini-3.5-flash-lite"]:
                try:
                    print(f"[AI Script] Querying Gemini model: {vision_model}...")
                    response = client.models.generate_content(
                        model=vision_model,
                        contents=[
                            client.files.get(name=vf.name),
                            vision_prompt
                        ],
                        config={
                            'response_mime_type': 'application/json',
                            'temperature': 0.7
                        }
                    )
                    if response and response.text:
                        break
                except Exception as model_err:
                    print(f"[AI Script] Model {vision_model} error: {model_err}, trying next model...")
                    time.sleep(2)

            # Cleanup uploaded file immediately
            try:
                client.files.delete(name=vf.name)
                print(f"[AI Script] Cleaned up temporary video from Gemini cloud.")
            except Exception:
                pass

            raw_json = response.text
            m = re.search(r'\{.*\}', raw_json, re.DOTALL)
            if m:
                script_data = json.loads(m.group(0))
                script_data = normalize_script_data(script_data, total_duration)
                print(f"[AI Script] Gemini Vision successfully crafted script ({len(script_data.get('speech', []))} lines, {len(script_data.get('edit_segments', []))} edit segments, {script_data.get('edited_duration', 0):.1f}s) based on REAL video events!")
                return script_data

        except Exception as e:
            print(f"[AI Script] Gemini Vision processing error: {e}")

    # 2. SECONDARY: Fallback to text prompt if video upload wasn't possible
    print("[AI Script] Fallback: using text-based prompt...")
    text_prompt = f"""You are a master viral YouTube Shorts comedy writer and British deadpan narrator.
A Chinese slapstick comedy creator named "{author}" published a video with caption: "{caption}".
Video duration: {total_duration:.1f} seconds.

Turn this into a viral 30-38 second UK meme Short with Adam voiceover.
Tone: Deadpan British documentary sarcasm.
Return ONLY valid JSON matching:
{{
  "cut_start": 0.0,
  "cut_end": {min(total_duration, 38.0):.1f},
  "duration": {min(total_duration, 38.0):.1f},
  "title": "Slapstick Escape",
  "speech": [
    ["01", 0.5, "Text..."]
  ],
  "sfx": [
    ["vine_boom.mp3", 3.0, 0.9]
  ],
  "subtitles": [
    {{"start": 0.5, "end": 3.0, "style": "CenterHook", "text": "Text 💀"}}
  ]
}}
"""

    if GEMINI_API_KEY:
        for model_name in GEMINI_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": text_prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.7
                }
            }
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    m = re.search(r'\{.*\}', text, re.DOTALL)
                    if m:
                        return normalize_script_data(json.loads(m.group(0)), total_duration)
            except Exception as e:
                print(f"[AI Script] Gemini text fallback error ({model_name}): {e}")

    if OPENROUTER_API_KEY:
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps({
                    "model": "openrouter/free",
                    "messages": [{"role": "user", "content": text_prompt}],
                    "temperature": 0.7
                }).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                raw = res["choices"][0]["message"]["content"]
                m = re.search(r'\{.*\}', raw, re.DOTALL)
                if m:
                    return normalize_script_data(json.loads(m.group(0)), total_duration)
        except Exception as e:
            print(f"[AI Script] Backup OpenRouter error: {e}")

    print("[AI Script] Using high-retention default comedy template.")
    return normalize_script_data(get_fallback_template(total_duration), total_duration)


def generate_comedy_script_with_ai(title: str, author: str, duration: float) -> dict:
    return generate_comedy_script_with_gemini("", title, author, duration)


def get_fallback_template(duration: float) -> dict:
    """High-retention template adapted to duration with zero audio clashing."""
    cut_len = min(duration, 35.0)
    return {
        "edit_segments": [(0.0, cut_len)],
        "edited_duration": cut_len,
        "cut_start": 0.0,
        "cut_end": cut_len,
        "duration": cut_len,
        "title": "Master of Disguise",
        "speech": [
            ("01", 0.5, "Observe Darren sneaking off to play mahjong with the local lasses, blissfully unaware of impending doom."),
            ("02", 7.0, "Brenda discovers the betrayal mid-bite, her bowl of rice trembling with pure unbridled fury."),
            ("03", 14.5, "A tactical alert goes off as Brenda storms the courtyard looking for blood."),
            ("04", 22.0, "Panicked, Darren converts his singlet into a halterneck top and slaps on a wig at lightning speed."),
            ("05", 29.5, "The absolute masterclass in camouflage succeeds, leaving Brenda thoroughly baffled by the new lady at the table.")
        ],
        "sfx": [
            ("vine_boom.mp3", 6.5, 0.9),
            ("ding_idea.mp3", 14.0, 0.85),
            ("bruh.mp3", 21.5, 0.9),
            ("oh_no_wheeze_laugh.mp3", 29.0, 0.95)
        ],
        "subtitles": [
            {"start": 0.5, "end": 6.5, "style": "CenterHook", "text": "Observe Darren sneaking off to play mahjong 🏃"},
            {"start": 7.0, "end": 14.0, "style": "CenterPunch", "text": "Brenda discovers the betrayal mid-bite 🍚"},
            {"start": 14.5, "end": 21.5, "style": "CenterPunch", "text": "A tactical alert goes off as Brenda storms in 🚨"},
            {"start": 22.0, "end": 28.5, "style": "CenterPunch", "text": "Darren converts his singlet into a halterneck 💇"},
            {"start": 29.5, "end": 34.5, "style": "CenterPunch", "text": "The camouflage masterclass succeeds! 👑"}
        ]
    }
