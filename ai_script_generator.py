import os
import sys
import json
import urllib.request
import urllib.error
import re
import time

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()


def generate_foreign_comedy_script(story_summary: str, total_duration: float, segments: list, character_emotions: str = "") -> dict:
    """
    Takes TwelveLabs story summary, character facial emotions, and timeline segments, then uses Gemini
    to adapt the story for foreign/UK audiences in the deadpan, witty style of Liam matching facial emotions.
    """
    print(f"\n[Gemini Script] Writing foreign comedy script for {total_duration:.1f}s timeline (Face Matched)...")

    num_lines = max(7, min(10, int(total_duration / 10.0)))
    
    prompt = f"""You are a master viral YouTube Shorts comedy narrator (in the deadpan, sarcastic style of Liam).

CONTEXT FROM VIDEO ANALYSIS:
Story:
\"\"\"{story_summary}\"\"\"

Character Facial Emotions & Expressions:
\"\"\"{character_emotions}\"\"\"

TARGET DURATION:
The final edited video timeline runs for exactly {total_duration:.1f} seconds.

CRITICAL RULES FOR NARRATION:
1. MATCH FACIAL EXPRESSIONS: Connect the commentary to what the characters' faces show (e.g. Brenda's angry glare/scowl, Gary's nervous guilt when caught stealing the keys, both blokes looking stunned and defeated on lawn chairs, and Brenda's screaming rage at the end).
2. GROUNDED BRITISH DEADPAN WIT: Narrate with dry, calm, sarcastic UK humor (like a BBC mockumentary host roasting the absurd schemes). Strictly NO cringe over-screaming or clichés ('BRO THOUGHT', 'WAIT FOR IT', 'ABSOLUTE CINEMA').
3. NATURAL STORY CONTINUITY: Explain WHY things happen logically:
   - Gary's absurd opening scheme (stylish rooster haircut & toy car wine delivery).
   - Brenda's fierce padlock reaction.
   - The distress signal (laser on the wall) and how the friend arrives.
   - The ambush (both tied to lawn chairs).
   - The secret blade escape and the final victory toast by the river.

4. PACING & GAPS:
   - Provide {num_lines} concise speech lines (10 to 14 words per line) evenly spaced across the 0.0s to {total_duration:.1f}s timeline.
   - Leave 1.5 to 2.5 seconds of silence between speech lines for meme sound effects.
5. MEME SFX PLACEMENT:
   - Place meme sound effects during the silent gaps:
     * 'vine_boom.mp3' on unexpected surprises / Brenda's catches.
     * 'windows_error.mp3' on silly fails / caught stealing keys.
     * 'ding_idea.mp3' on the laser or secret plan.
     * 'bruh.mp3' on both men tied to lawn chairs.
     * 'oh_no_wheeze_laugh.mp3' on Brenda's fiery scream reaction at the end.

OUTPUT FORMAT:
Return ONLY a valid raw JSON object (no markdown, no ```json backticks):
{{
  "title": "Short witty British title",
  "speech": [
    ["01", 0.5, "Line 1 introducing Gary and the scheme..."],
    ["02", 9.0, "Line 2 Brenda intercepts and padlocks the gate..."],
    ["03", 18.0, "Line 3 ..."]
  ],
  "sfx": [
    ["vine_boom.mp3", 15.5, 0.85],
    ["windows_error.mp3", 24.0, 0.80],
    ["ding_idea.mp3", 28.0, 0.80],
    ["bruh.mp3", 52.0, 0.90],
    ["oh_no_wheeze_laugh.mp3", {total_duration - 3.0:.1f}, 0.80]
  ],
  "subtitles": [
    {{"start": 0.5, "end": 7.0, "style": "CenterHook", "text": "ROOSTER GETS A FRESH FADE 💀"}},
    {{"start": 9.0, "end": 16.0, "style": "CenterPunch", "text": "TACTICAL WINE SHUTTLE 🍷"}}
  ]
}}"""

    # Try Google GenAI SDK first
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            print("[Gemini Script] Calling Gemini via official google-genai SDK...")
            raw_text = None
            for m_name in ["gemini-2.0-flash", "gemini-1.5-flash"]:
                try:
                    resp = client.models.generate_content(model=m_name, contents=prompt)
                    raw_text = resp.text.strip()
                    if raw_text:
                        break
                except Exception as ex_m:
                    print(f"[Gemini Script] Model {m_name} failed: {ex_m}")

            if raw_text:
                clean_json = raw_text
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.startswith("```"):
                    clean_json = clean_json[3:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                clean_json = clean_json.strip()

                data = json.loads(clean_json)
                print(f"[Gemini Script] Successfully received {len(data.get('speech', []))} speech lines!")
                return data
        except Exception as e:
            print(f"[Gemini Script] SDK call warning: {e}, trying direct REST fallback...")

    # Fallback to direct REST API
    api_key = GEMINI_API_KEY or os.environ.get("GEMINI_KEY", "")
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                clean_json = text
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.startswith("```"):
                    clean_json = clean_json[3:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                clean_json = clean_json.strip()
                return json.loads(clean_json)
        except Exception as e:
            print(f"[Gemini Script] REST API error: {e}")

    # Robust local British script fallback
    print("[Gemini Script] Using grounded default British script...")
    return {
        "title": "Tactical Barnyard Rescue: High Speed",
        "speech": [
            ["01", 0.5, "Gary decides his prize rooster needs an emergency haircut. Brenda is thoroughly unimpressed."],
            ["02", 7.5, "Smuggling wine via toy car fails miserably, so Brenda padlocks the front gate."],
            ["03", 15.0, "Gary attempts a stealth magnetic key theft and gets caught instantly."],
            ["04", 22.0, "Plan B: Gary blasts a green laser distress signal across the neighborhood wall."],
            ["05", 29.5, "Fast-forward past Terrys dog-bribing techniques, backup has arrived."],
            ["06", 37.0, "Catastrophic ambush: both blokes end up tightly bound to lawn chairs."],
            ["07", 43.5, "A friendly delivery driver slips a secret blade right through the gate."],
            ["08", 49.5, "Ropes cut, wheelbarrow sprint, and the lads toast to sweet freedom. Brilliant."]
        ],
        "sfx": [
            ["vine_boom.mp3", 7.0, 0.85],
            ["windows_error.mp3", 14.5, 0.80],
            ["ding_idea.mp3", 21.5, 0.80],
            ["bruh.mp3", 36.5, 0.90],
            ["oh_no_wheeze_laugh.mp3", max(0.0, total_duration - 3.5), 0.80]
        ],
        "subtitles": [
            {"start": 0.5, "end": 6.8, "style": "CenterHook", "text": "ROOSTER FRESH FADE 💀"},
            {"start": 7.5, "end": 14.0, "style": "CenterPunch", "text": "TACTICAL WINE SHUTTLE 🍷"},
            {"start": 14.8, "end": 21.0, "style": "CenterPunch", "text": "STEALTH MAGNETIC KEY THEFT 🧲"},
            {"start": 21.8, "end": 28.5, "style": "CenterPunch", "text": "EMERGENCY LASER SOS 🚨"},
            {"start": 29.5, "end": 36.0, "style": "CenterPunch", "text": "FAST-FORWARD: DOG BRIBERY 🐕"},
            {"start": 36.8, "end": 42.5, "style": "CenterPunch", "text": "BOUND TO LAWN CHAIRS 💀"},
            {"start": 43.2, "end": 48.8, "style": "CenterPunch", "text": "COVERT BLADE DELIVERY 📦"},
            {"start": 49.5, "end": 55.5, "style": "CenterPunch", "text": "WHEELBARROW ESCAPE & TOAST 🍻"}
        ]
    }

