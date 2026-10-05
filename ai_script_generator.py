import os
import sys
import json
import urllib.request
import urllib.error

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


def generate_comedy_script_with_gemini(title: str, author: str, duration: float) -> dict:
    """
    Calls Gemini API to generate:
    1. Continuous natural scene cut (35 to 45 seconds, no choppy jumps)
    2. Adam voiceover lines with SILENCE POCKETS for meme sounds
    3. Meme sound effect cue points (Vine boom, Bruh, Inception, Wheeze laugh, etc.)
    4. Center-Screen Eye-Level Safe Zone Subtitles (MarginV: 420)
    """
    if not GEMINI_API_KEY:
        print("[AI Script] No GEMINI_API_KEY found, using high-retention default comedy template.")
        return get_fallback_template(duration)

    prompt = f"""You are a master viral YouTube Shorts / TikTok meme creator and comedy writer.
A Chinese slapstick comedy creator named "{author}" published a video with title/caption: "{title}".
Video duration: {duration:.1f} seconds.

Your task is to turn this into a viral 35-42 second Western meme Short with Adam voiceover.

CRITICAL RULES:
1. CONTINUOUS STORY FLOW: If duration > 60s, select ONE continuous 35-42 second segment where the main comedy action happens (e.g. from 0 to 40, or from 45 to 85). DO NOT do choppy micro-cuts.
2. VOCAL PAUSES / MEME POCKETS: Leave 1.0 to 1.5 seconds of silence between spoken lines whenever a meme sound effect plays, so the voiceover and meme sound NEVER overlap or clash!
3. VOICE TONE: Deadpan, sarcastic, Gen-Z / YouTuber reaction style ("When your wife...", "Bro really thought...", "Absolute legend", "Massive W").
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
    {{"start": start_sec, "end": end_sec, "style": "CenterHook", "text": "Hook text\\NSecond line 💀"}},
    {{"start": start_sec, "end": end_sec, "style": "CenterPunch", "text": "PUNCHLINE! 🚨"}}
  ]
}}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
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
            script_data = json.loads(text)
            print(f"[AI Script] Gemini generated custom viral script ({len(script_data.get('speech', []))} lines)!")
            return script_data
    except Exception as e:
        print(f"[AI Script] Gemini API error: {e}. Using fallback template.")
        return get_fallback_template(duration)


def get_fallback_template(duration: float) -> dict:
    """High-retention template with continuous scene cut and zero audio clashing."""
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
