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


def generate_foreign_comedy_script(story_summary: str, total_duration: float, segments: list) -> dict:
    """
    Takes TwelveLabs story summary and timeline segments, then uses Gemini
    to adapt the story for foreign/UK audiences in the deadpan, witty style of Liam.
    """
    print(f"\n[Gemini Script] Writing foreign comedy script for {total_duration:.1f}s timeline...")

    num_lines = max(6, min(10, int(total_duration / 8.5)))
    
    prompt = f"""You are a master viral YouTube Shorts storyteller and British comedy narrator (in the deadpan, sarcastic style of Liam).

CONTEXT FROM VIDEO ANALYSIS:
Here is the exact real story and event sequence identified from the video:
\"\"\"{story_summary}\"\"\"

TARGET DURATION:
The final edited video timeline runs for exactly {total_duration:.1f} seconds.

CRITICAL RULES FOR NARRATION:
1. GROUNDED & RELATABLE: Do NOT use over-the-top, screaming, or cringe Internet clichés (STRICTLY FORBIDDEN: 'BRO THOUGHT', 'WAIT FOR IT', 'ABSOLUTE CINEMA', 'LEGENDARY DIFFICULTY').
2. BRITISH DEADPAN WIT: Narrate with dry, calm, sarcastic UK humor (like a BBC documentary host who has completely lost faith in humanity).
3. NATURAL STORY CONTINUITY: Explain WHY things happen logically:
   - Gary's absurd opening scheme (e.g. stylish rooster haircut or secret contraband).
   - Brenda's fierce reaction (locking the gate with the padlock).
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
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            raw_text = resp.text.strip()
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
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
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
        "title": "Tactical Barnyard Rescue Gone Wrong",
        "speech": [
            ["01", 0.5, "Gary has decided his prize rooster is overdue for a stylish haircut. Brenda considers this treason."],
            ["02", 8.5, "To smuggle out some celebratory wine, the lads launch a tactical toy car. Stopped by Brendas flip-flop."],
            ["03", 18.0, "Gate padlocked. Gary attempts a stealth magnetic key theft, and gets caught red-handed."],
            ["04", 27.5, "Plan B: Gary deploys an emergency laser distress signal onto the neighborhood wall."],
            ["05", 37.0, "Fast-forwarding past Terrys dog-bribing techniques, backup has arrived at the perimeter."],
            ["06", 47.0, "Catastrophic failure. Brenda ambushes the rescue, and both blokes are swiftly tied to lawn chairs."],
            ["07", 56.5, "Skipping the hostage negotiations, a friendly delivery driver slips a covert blade through the bars."],
            ["08", 64.0, "Gary gnaws through the ropes, initiating a high-speed wheelbarrow escape into freedom."],
            ["09", 71.5, "Brenda erupts into pure fiery rage, while the lads toast by the river. Brilliant."]
        ],
        "sfx": [
            ["vine_boom.mp3", 15.5, 0.85],
            ["windows_error.mp3", 24.0, 0.80],
            ["ding_idea.mp3", 28.0, 0.80],
            ["bruh.mp3", 53.0, 0.90],
            ["oh_no_wheeze_laugh.mp3", max(0.0, total_duration - 3.0), 0.80]
        ],
        "subtitles": [
            {"start": 0.5, "end": 6.8, "style": "CenterHook", "text": "ROOSTER GETS A FRESH FADE 💀"},
            {"start": 8.5, "end": 15.0, "style": "CenterPunch", "text": "TACTICAL WINE SHUTTLE 🍷"},
            {"start": 17.5, "end": 23.5, "style": "CenterPunch", "text": "STEALTH MAGNETIC KEY THEFT 🧲"},
            {"start": 26.5, "end": 32.0, "style": "CenterPunch", "text": "EMERGENCY LASER SOS SIGNAL 🚨"},
            {"start": 36.0, "end": 42.0, "style": "CenterPunch", "text": "FAST-FORWARD: DOG BRIBERY 🐕"},
            {"start": 46.5, "end": 53.0, "style": "CenterPunch", "text": "BOTH BLOKES BOUND TO CHAIRS 💀"},
            {"start": 56.0, "end": 61.5, "style": "CenterPunch", "text": "COVERT BLADE SPECIAL DELIVERY 📦"},
            {"start": 63.5, "end": 69.0, "style": "CenterPunch", "text": "HIGH-SPEED WHEELBARROW ESCAPE 🛞"},
            {"start": 70.5, "end": 76.0, "style": "CenterPunch", "text": "PURE FIERY RAGE VS FREEDOM 🍻"}
        ]
    }
