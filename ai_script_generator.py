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

            target_scene_len = min(total_duration, 38.0)
            vision_prompt = f"""You are a master viral YouTube Shorts comedy writer and British deadpan narrator (BBC Wildlife Documentary meets sarcastic UK comedian like Adam/David Attenborough).
You just watched the provided video footage.

Write an authentic, hilarious English voiceover roast script that narrates the EXACT STORY happening on screen.

CRITICAL STORYTELLING RULES:
1. FACTUAL STORY NARRATION:
   - Identify the exact visual sequence:
     - Who is doing what at the start?
     - Who spots them / snitches on them?
     - Who is being informed (e.g. eating from a bowl, sitting at home)?
     - What is the panic, what clever or ridiculous disguise or trick is pulled (e.g. twisting clothes into a top, putting on a wig, hiding in plain sight)?
     - What happens when the confrontational person arrives (e.g. walking right past them, complete confusion, survival)?
   - Reference their EXACT clothing, items, expressions, and funny physical actions.
2. CHARACTERS & TONE:
   - Give them witty British nicknames (e.g., Darren, Brenda, Gary, Arthur, Susan).
   - Tone: Deadpan British documentary sarcasm, witty observation of disastrous life choices and genius survivals.
   - STRICTLY FORBIDDEN: NEVER use cheap generic AI filler phrases like 'Bro thought', 'Wait for it', 'Absolute cinema', 'Heist', 'Legendary difficulty', 'Bro really thought'.
3. SCENE SELECTION & TIMESTAMPS:
   - If the video is longer than 45 seconds, identify the single funniest continuous scene (cut_start and cut_end, lasting 30 to 40 seconds).
   - If video is <= 45 seconds, set cut_start: 0.0, cut_end: {total_duration:.1f}, duration: {total_duration:.1f}.
   - CRITICAL: All timestamps in 'speech', 'sfx', and 'subtitles' MUST be strictly 0-indexed relative to the start of the scene (from 0.0 to duration).
   - Space speech lines with 1.0 - 1.5 seconds gap so meme sound effects have dedicated silence pockets.
   - Each spoken line should be 1-2 punchy sentences.
4. MEME SFX & SILENCE POCKETS:
   - Choose 3-5 SFX from:
     'vine_boom.mp3', 'bruh.mp3', 'ding_idea.mp3', 'fbi_open_up.mp3', 'wait_a_minute.mp3', 'oh_no_wheeze_laugh.mp3', 'Metal Boom.mp3', 'WOW.mp3'.
   - Place SFX precisely at comedic beats (spotting, alarm, disguise reveal, near miss).
5. CENTER-SAFE SUBTITLES:
   - Create synchronized subtitle segments matching the spoken dialogue with emojis.

Return ONLY valid JSON matching this exact schema:
{{
  "cut_start": float,
  "cut_end": float,
  "duration": float,
  "title": "Short catchy title",
  "speech": [
    ["01", 0.5, "Line 1..."],
    ["02", 7.0, "Line 2..."],
    ["03", 14.5, "Line 3..."],
    ["04", 22.0, "Line 4..."],
    ["05", 29.5, "Line 5..."]
  ],
  "sfx": [
    ["vine_boom.mp3", 6.5, 0.9],
    ["ding_idea.mp3", 14.0, 0.85],
    ["bruh.mp3", 21.5, 0.9],
    ["oh_no_wheeze_laugh.mp3", 29.0, 0.95]
  ],
  "subtitles": [
    {{"start": 0.5, "end": 6.5, "style": "CenterHook", "text": "SUBTITLE LINE 💀"}},
    {{"start": 7.0, "end": 14.0, "style": "CenterPunch", "text": "SUBTITLE LINE 🚨"}},
    {{"start": 14.5, "end": 21.5, "style": "CenterPunch", "text": "SUBTITLE LINE 💇"}},
    {{"start": 22.0, "end": 28.5, "style": "CenterPunch", "text": "SUBTITLE LINE 🤫"}},
    {{"start": 29.5, "end": 34.5, "style": "CenterPunch", "text": "SUBTITLE LINE 👑"}}
  ]
}}
"""

            response = client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=[
                    client.files.get(name=vf.name),
                    vision_prompt
                ],
                config={
                    'response_mime_type': 'application/json',
                    'temperature': 0.7
                }
            )

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
                print(f"[AI Script] Gemini Vision successfully crafted script ({len(script_data.get('speech', []))} lines) based on REAL video events!")
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
                        return json.loads(m.group(0))
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
                    return json.loads(m.group(0))
        except Exception as e:
            print(f"[AI Script] Backup OpenRouter error: {e}")

    print("[AI Script] Using high-retention default comedy template.")
    return get_fallback_template(total_duration)


def generate_comedy_script_with_ai(title: str, author: str, duration: float) -> dict:
    return generate_comedy_script_with_gemini("", title, author, duration)


def get_fallback_template(duration: float) -> dict:
    """High-retention template adapted to duration with zero audio clashing."""
    cut_len = min(duration, 35.0)
    return {
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
