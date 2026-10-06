import os
import sys
import json
import urllib.request
import urllib.error
import re
import time

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Prioritized list of high-quota (500 RPD) models to prevent suspension
GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest"
]


def generate_comedy_script_with_gemini(title: str, author: str, duration: float) -> dict:
    """
    Calls Google Gemini (primary: gemini-3.5-flash-lite with 500 RPD safe quota) to generate:
    1. Continuous natural scene cut matching video duration
    2. Adam voiceover lines with SILENCE POCKETS for meme sounds
    3. Meme sound effect cue points (vine_boom, bruh, wheeze laugh, etc.)
    4. Center-Screen Eye-Level Safe Zone Subtitles (MarginV: 420)
    """
    is_short = duration <= 16.0

    if is_short:
        prompt = f"""You are a master viral YouTube Shorts comedy writer.
A Chinese comedy video by '{author}' is titled: '{title}'.
Video duration: {duration:.1f} seconds.

CRITICAL INSTRUCTIONS FOR SHORT VIDEO:
Since the video is only {duration:.1f} seconds long:
1. cut_start must be 0.0 and cut_end must be {duration:.1f}. duration must be {duration:.1f}.
2. Provide 1 to 2 very short, punchy, hilarious meme roast voiceover lines that fit completely before {max(1.0, duration - 1.0):.1f} seconds.
3. Add 1 or 2 meme sound effects (e.g., 'vine_boom.mp3', 'bruh.mp3', 'oh_no_wheeze_laugh.mp3') timed with the action.
4. Add safe zone center subtitles.

Return ONLY valid JSON with this exact schema:
{{
  "cut_start": 0.0,
  "cut_end": {duration:.1f},
  "duration": {duration:.1f},
  "speech": [
    ["01", 0.5, "Short hook line..."],
    ["02", 3.5, "Punchline reaction..."]
  ],
  "sfx": [
    ["vine_boom.mp3", 3.0, 0.9]
  ],
  "subtitles": [
    {{"start": 0.5, "end": 3.0, "style": "CenterHook", "text": "HOOK TEXT 💀"}},
    {{"start": 3.5, "end": {duration:.1f}, "style": "CenterPunch", "text": "PUNCHLINE! 😭"}}
  ]
}}
"""
    else:
        prompt = f"""You are a master viral YouTube Shorts / TikTok meme creator and comedy writer.
A Chinese slapstick comedy creator named "{author}" published a video with title/caption: "{title}".
Video duration: {duration:.1f} seconds.

Your task is to turn this into a viral 30-40 second Western meme Short with Adam voiceover.

CRITICAL RULES:
1. CONTINUOUS STORY FLOW & TIMESTAMPS: If duration > 50s, select ONE continuous 30-40 second segment where the main comedy action happens. All timestamps in speech, sfx, and subtitles MUST start at 0.0 (relative to the cut, e.g. 0.5, 4.0, 12.0) and must NEVER exceed duration!
2. VOCAL PAUSES / MEME POCKETS: Leave 1.0 to 1.5 seconds of silence between spoken lines whenever a meme sound effect plays, so the voiceover and meme sound NEVER overlap!
3. VOICE TONE: Deadpan, sarcastic, Gen-Z / British & American meme reaction style ("Bro really thought...", "Absolute legend", "When you realize...", "Wait for it 💀").
4. MEME SFX: Choose from available vault sounds:
   - 'vine_boom.mp3' (shock / impact)
   - 'bruh.mp3' (disbelief / freeze)
   - 'ding_idea.mp3' (smart / stupid idea)
   - 'fbi_open_up.mp3' (action squad entry)
   - 'wait_a_minute.mp3' (prank / realization)
   - 'oh_no_wheeze_laugh.mp3' (hilarious failure)
   - 'Metal Boom.mp3' (dramatic climax)
   - 'WOW.mp3' (victory celebration)

Return ONLY valid JSON with this exact structure:
{{
  "cut_start": float,
  "cut_end": float,
  "duration": float,
  "speech": [
    ["01", start_sec, "text..."],
    ["02", start_sec, "text..."]
  ],
  "sfx": [
    ["vine_boom.mp3", start_sec, gain_float],
    ["bruh.mp3", start_sec, gain_float]
  ],
  "subtitles": [
    {{"start": start_sec, "end": end_sec, "style": "CenterHook", "text": "Hook text 💀"}},
    {{"start": start_sec, "end": end_sec, "style": "CenterPunch", "text": "PUNCHLINE! 🚨"}}
  ]
}}
"""

    # 1. PRIMARY: Official Google Gemini with high-quota Flash Lite models
    if GEMINI_API_KEY:
        for model_name in GEMINI_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.7
                }
            }
            try:
                print(f"[AI Script] Calling Google Gemini model '{model_name}' (Safe 500 RPD Tier)...")
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    # Sanitize any invalid escape sequences before json.loads
                    text = re.sub(r'\\N', ' ', text)
                    text = re.sub(r'\\(?![/"\\bfnrtu])', r'\\\\', text)
                    m = re.search(r'\{.*\}', text, re.DOTALL)
                    if m:
                        script_data = json.loads(m.group(0))
                        print(f"[AI Script] Google Gemini ({model_name}) generated custom viral script ({len(script_data.get('speech', []))} lines)!")
                        return script_data
            except urllib.error.HTTPError as e:
                print(f"[AI Script] Google Gemini '{model_name}' HTTP {e.code}: {e.reason}")
                if e.code == 429:
                    print("[AI Script] Rate limit hit. Backing off 5s before fallback model...")
                    time.sleep(5)
            except Exception as e:
                print(f"[AI Script] Google Gemini error: {e}")

    # 2. SECONDARY: OpenRouter Fallback (if Gemini is unavailable)
    if OPENROUTER_API_KEY:
        try:
            print("[AI Script] Attempting OpenRouter backup...")
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps({
                    "model": "openrouter/free",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/chandan805026/ai-youtube-shorts-generator",
                    "X-Title": "Shorts Generator"
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                raw = res["choices"][0]["message"]["content"]
                m = re.search(r'\{.*\}', raw, re.DOTALL)
                if m:
                    script_data = json.loads(m.group(0))
                    print(f"[AI Script] Backup OpenRouter generated script ({len(script_data.get('speech', []))} lines)!")
                    return script_data
        except Exception as e:
            print(f"[AI Script] Backup OpenRouter error: {e}")

    print("[AI Script] Using high-retention default comedy template.")
    return get_fallback_template(duration)


def generate_comedy_script_with_ai(title: str, author: str, duration: float) -> dict:
    return generate_comedy_script_with_gemini(title, author, duration)


def get_fallback_template(duration: float) -> dict:
    """High-retention template adapted to duration with zero audio clashing."""
    if duration <= 16.0:
        return {
            "cut_start": 0.0,
            "cut_end": duration,
            "duration": duration,
            "speech": [
                ("01", 0.5, "Wait for it... Bro really thought nobody was watching."),
                ("02", max(2.5, duration - 4.0), "Absolute chaos! You cannot make this up.")
            ],
            "sfx": [
                ("vine_boom.mp3", max(2.0, duration - 4.5), 0.95),
                ("oh_no_wheeze_laugh.mp3", max(4.0, duration - 2.5), 1.0)
            ],
            "subtitles": [
                {"start": 0.5, "end": max(2.5, duration - 4.0), "style": "CenterHook", "text": "WAIT FOR IT... 💀"},
                {"start": max(2.5, duration - 4.0), "end": duration, "style": "CenterPunch", "text": "ABSOLUTE CHAOS! 😭🚨"}
            ]
        }

    cut_len = min(duration, 38.0)
    return {
        "cut_start": 0.0,
        "cut_end": cut_len,
        "duration": cut_len,
        "speech": [
            ("01", 0.5, "When your wife catches you going out with the boys and literally builds Alcatraz in the living room..."),
            ("02", 5.0, "Maximum security lockdown! Bro is in the dog house."),
            ("03", 8.0, "So he deploys an origami mechanical butterfly to summon the boys..."),
            ("04", 12.0, "Code Red! The distress signal has been received."),
            ("05", 15.5, "The squad mobilized in ten seconds! One pulled up in a three-piece suit in the cabbage patch."),
            ("06", 21.0, "Their master weapon? A mop with a wig to convince her the house is haunted!"),
            ("07", 26.0, "Bro literally tunneled under the cage like The Shawshank Redemption!"),
            ("08", 30.5, "Ten minutes later, back at the local pub for another cold round."),
            ("09", 34.5, "Bros before rules. Absolute legends. Massive W!")
        ],
        "sfx": [
            ("metal_clang", 2.2, 0.9),
            ("vine_boom.mp3", 4.4, 0.95),
            ("bruh.mp3", 7.2, 0.85),
            ("ding_idea.mp3", 11.2, 0.8),
            ("fbi_open_up.mp3", 14.5, 0.85),
            ("wait_a_minute.mp3", 19.8, 0.9),
            ("oh_no_wheeze_laugh.mp3", 23.5, 0.95),
            ("Metal Boom.mp3", 29.5, 0.85),
            ("WOW.mp3", 33.5, 0.85)
        ],
        "subtitles": [
            {"start": 0.5, "end": 4.5, "style": "CenterHook", "text": "Wife caught him going to the pub...\\Nand built ALCATRAZ in the house! 🔒💀"},
            {"start": 5.0, "end": 7.5, "style": "CenterPunch", "text": "MAXIMUM SECURITY LOCKDOWN! ⛓️"},
            {"start": 8.0, "end": 11.5, "style": "CenterHook", "text": "So he deployed a mechanical butterfly\\Nto summon the boys! 🦋"},
            {"start": 12.0, "end": 14.5, "style": "CenterPunch", "text": "CODE RED! DISTRESS SIGNAL! 🚨"},
            {"start": 15.5, "end": 20.0, "style": "CenterHook", "text": "The squad mobilized!\\nThree-piece suit in the cabbage patch! 🕶️"},
            {"start": 21.0, "end": 25.0, "style": "CenterPunch", "text": "Master weapon?\\nA mop wig ghost prank! 👻😭"},
            {"start": 26.0, "end": 29.5, "style": "CenterPunch", "text": "Bro tunneled under the cage\\nlike SHAWSHANK REDEMPTION! ⛏️"},
            {"start": 30.5, "end": 34.0, "style": "CenterHook", "text": "10 minutes later...\\nBack at the pub with the boys! 🍺"},
            {"start": 34.5, "end": 37.5, "style": "CenterPunch", "text": "BROS BEFORE RULES.\\nABSOLUTE LEGENDS! 👑"}
        ]
    }
