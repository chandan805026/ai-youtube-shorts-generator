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

GEMINI_MODELS = [
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite"
]


def normalize_script_data(data: dict, total_duration: float) -> dict:
    """
    Normalizes script data for 3-Act Inverted Story Architecture:
    - Guarantees valid chronological segments within [0, total_duration].
    - ALWAYS anchors the last segment to the exact end of the raw video (total_duration)
      so the punchline / fiery reaction is NEVER cut!
    - Enforces 50 to 58s target duration by trimming middle fluff, NEVER the ending.
    - Synchronizes Liam's speech cues, SFX, and subtitles across the resulting timeline.
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

            # Discard hallucinated timestamps beyond video duration
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

    # If no segments, construct a safe 3-act split anchored to end
    if not norm_segs:
        if total_duration > 60.0:
            act1_len = 18.0
            act2_start = max(25.0, total_duration * 0.35)
            act2_len = 16.0
            act3_start = max(act2_start + act2_len + 5.0, total_duration - 22.0)
            norm_segs = [
                (0.0, act1_len),
                (act2_start, act2_start + act2_len),
                (act3_start, total_duration)
            ]
        else:
            norm_segs = [(0.0, total_duration)]

    # Sort chronologically
    norm_segs.sort(key=lambda x: x[0])

    # RULE 2 SACRED ENDING ANCHOR: The final segment MUST extend to the exact end of the video
    if total_duration > 60.0 and len(norm_segs) > 0:
        last_st, last_et = norm_segs[-1]
        # Make sure the last segment covers the final 18-24 seconds right up to total_duration
        if last_et < total_duration - 1.0:
            norm_segs[-1] = (last_st, total_duration)

    # If total duration > 60s, trim earlier segments if sum exceeds 58.0s (NEVER trim the ending!)
    target_max = 58.0
    current_dur = sum(et - st for st, et in norm_segs)

    if total_duration > 60.0 and current_dur > target_max:
        excess = current_dur - target_max
        # Trim excess from earlier segments first to protect the climax in the final segment
        for i in range(len(norm_segs) - 1):
            st, et = norm_segs[i]
            dur = et - st
            if dur > 12.0:
                can_trim = min(excess, dur - 10.0)
                norm_segs[i] = (st, et - can_trim)
                excess -= can_trim
                if excess <= 0:
                    break

    # If segments add up to less than 50s, expand earlier segments
    current_dur = sum(et - st for st, et in norm_segs)
    if total_duration > 60.0 and current_dur < 50.0 and len(norm_segs) > 1:
        needed = 54.0 - current_dur
        expand_per_seg = needed / (len(norm_segs) - 1)
        for i in range(len(norm_segs) - 1):
            st, et = norm_segs[i]
            norm_segs[i] = (st, et + expand_per_seg)

    edited_duration = sum([max(0.0, et - st) for st, et in norm_segs])
    data["edit_segments"] = [(round(s, 2), round(e, 2)) for s, e in norm_segs]
    data["edited_duration"] = round(edited_duration, 2)
    data["total_edited_duration"] = round(edited_duration, 2)

    # Re-scale / distribute speech, subtitles, and SFX if they ended too early
    speech = data.get("speech", [])
    if speech and len(speech) > 1 and edited_duration > 40.0:
        last_speech_time = float(speech[-1][1])
        if last_speech_time < (edited_duration * 0.70):
            scale_factor = (edited_duration - 5.5) / max(1.0, last_speech_time)
            new_speech = []
            for item in speech:
                code = item[0]
                t = float(item[1])
                txt = item[2]
                new_speech.append([code, round(t * scale_factor, 1), txt])
            data["speech"] = new_speech

            subtitles = data.get("subtitles", [])
            new_subs = []
            for sub in subtitles:
                s_st = round(float(sub.get("start", 0.0)) * scale_factor, 1)
                s_et = round(float(sub.get("end", 0.0)) * scale_factor, 1)
                new_subs.append({
                    "start": s_st,
                    "end": min(edited_duration, max(s_st + 1.2, s_et)),
                    "style": sub.get("style", "CenterPunch"),
                    "text": sub.get("text", "")
                })
            data["subtitles"] = new_subs

            sfx = data.get("sfx", [])
            new_sfx = []
            for sf in sfx:
                if len(sf) >= 3:
                    new_sfx.append([sf[0], round(float(sf[1]) * scale_factor, 1), sf[2]])
                elif len(sf) == 2:
                    new_sfx.append([sf[0], round(float(sf[1]) * scale_factor, 1), 0.9])
            data["sfx"] = new_sfx

    return data


def generate_comedy_script_with_gemini(video_path: str, caption: str, author: str, total_duration: float) -> dict:
    """
    Analyzes the comedy video with Gemini Vision to produce:
    1. Inverted Editing: Cuts ONLY the junk blocks (sponsor ads & dead pauses).
    2. Sacred Ending Anchor: Climax & ending reaction 100% preserved.
    3. Liam Bridge Narration: Glues scene transitions seamlessly.
    4. 50-58s YouTube Shorts sweet spot.
    """
    print(f"\n[AI Script] Analyzing video ({total_duration:.1f}s) for '{author}' with Master Inverted Story Engine...")

    # 1. PRIMARY: Gemini Vision via official google-genai SDK
    if GEMINI_API_KEY and video_path and os.path.exists(video_path):
        try:
            from google import genai
            print(f"[AI Script] Initializing Google GenAI Client (Safe 500 RPD Tier)...")
            client = genai.Client(api_key=GEMINI_API_KEY)

            print(f"[AI Script] Uploading video to Gemini Vision API: {os.path.basename(video_path)} ({os.path.getsize(video_path)/(1024*1024):.2f} MB)...")
            vf = client.files.upload(file=video_path)

            retries = 0
            while vf.state.name == "PROCESSING" and retries < 30:
                time.sleep(2)
                vf = client.files.get(name=vf.name)
                retries += 1

            if vf.state.name != "ACTIVE":
                print(f"[AI Script] Video state is {vf.state.name}, proceeding with caution...")

            print(f"[AI Script] Video active on Gemini cloud ({vf.name}). Prompting Gemini Vision...")

            climax_target_start = max(0.0, total_duration - 22.0)

            vision_prompt = f"""You are a master viral YouTube Shorts storyteller and British comedy narrator (in the deadpan, sarcastic style of Liam).
You have full multimodal video and audio understanding.

CRITICAL OBJECTIVE: 
Turn this Chinese comedy video (Total Duration: {total_duration:.1f}s) into a crystal-clear, hilarious, fast-paced story for global audiences 
WITHOUT confusing jump cuts, WITHOUT unexplained sudden scenes, and WITHOUT cutting the climax ending!

TARGET DURATION & 3-ACT MATH:
- The total duration of all combined 'edit_segments' must be between 50 to 58 seconds (strict YouTube Shorts limit).
- To preserve the climax without exceeding 58s, divide your cuts smartly:
  * Segment 1 (The Setup & Conflict): 0.0s to ~20.0s (around 18-22s duration)
  * Segment 2 (The Secret Trick / Escalation): Middle action (around 12-16s duration)
  * Segment 3 (The Escape, Climax & Punchline): Start right where the rescue/escape begins and go ALL THE WAY to the exact last second of the video: [{climax_target_start:.1f}, {total_duration:.1f}] (around 18-22s duration).

RULE 1: INVERTED EDITING (CUT ONLY THE JUNK, KEEP CONTINUITY)
- Do NOT chop the video into tiny 3-5 second pieces.
- Identify and remove ONLY the BORING FLUFF & SPONSOR AD BLOCKS:
  * In-video commercial promotions (e.g. phone recycling apps, brand sponsorships, shop visits).
  * Long awkward dead walking or repetitive silence.
- Keep the remaining story as 2 to 3 smooth, continuous scenes.

RULE 2: THE SACRED ENDING ANCHOR (NEVER CUT THE PUNCHLINE)
- The final edit segment MUST extend all the way to the very last second of the video ({total_duration:.1f}s).
- The big climax payoff, furious reactions (e.g. wife screaming with flames), and the lads' final victory/toast must 100% be preserved!

RULE 3: LIAM'S "BRIDGE NARRATION" & MOTIVATION
- Liam's sarcastic BBC-documentary narration glues the cuts together.
- If cutting over an ad/dead scene, Liam MUST use a snappy bridge line (e.g., "Skipping past the domestic interrogation, tactical reinforcements have arrived...").
- Clarify motives simply: Explain WHY the husband was trapped/locked, WHAT the distress tool was, and HOW the lads pulled off the escape.
- Assign witty British nicknames to the characters (e.g., Gary, Big Dave, Brenda).

RULE 4: AUDIO TIMELINE & PACING (CRITICAL)
- IMPORTANT: All timestamps in "speech", "sfx", and "subtitles" MUST BE ON THE FINAL EDITED TIMELINE (starting at 0.0s of the concatenated output video, NOT the source video).
- Provide 7 to 9 punchy speech lines for Liam evenly distributed across the 50-58s timeline (10 to 16 words max per line).
- Leave 1.0 - 1.5s silent windows between lines for meme SFX (vine_boom, bruh, ding_idea, wheeze_laugh).
- The final meme sound effect (wheeze_laugh or vine_boom) MUST land directly on the final punchline reaction!

OUTPUT FORMAT:
Return ONLY valid, raw JSON (no markdown formatting, no ```json backticks):
{{
  "ad_or_junk_range": [70.0, 125.0],
  "edit_segments": [
    [0.0, 20.0],
    [45.0, 60.0],
    [{climax_target_start:.1f}, {total_duration:.1f}]
  ],
  "edited_duration": 56.5,
  "title": "Witty British Title",
  "speech": [
    ["01", 0.5, "Line 1 introducing Gary and the absurd setup..."],
    ["02", 7.0, "Line 2 Brenda locking the gate..."],
    ["03", 14.0, "Line 3 Deploying the secret distress signal..."],
    ["04", 21.0, "Line 4 The plan gets compromised..."],
    ["05", 28.5, "Line 5 [Bridge] Skipping the hostage drama, backup arrives..."],
    ["06", 36.0, "Line 6 Baozi brings the secret tools..."],
    ["07", 43.5, "Line 7 Hoisted over the wall into freedom..."],
    ["08", 51.0, "Line 8 Brenda screams in pure fiery rage while the lads celebrate!"]
  ],
  "sfx": [
    ["vine_boom.mp3", 6.5, 0.9],
    ["bruh.mp3", 13.5, 0.85],
    ["ding_idea.mp3", 20.5, 0.85],
    ["vine_boom.mp3", 35.5, 0.9],
    ["oh_no_wheeze_laugh.mp3", 50.5, 0.95]
  ],
  "subtitles": [
    {{"start": 0.5, "end": 6.5, "style": "CenterHook", "text": "Gary's peaceful poultry grooming 🐔"}},
    {{"start": 7.0, "end": 13.5, "style": "CenterPunch", "text": "Brenda locks the perimeter gate! 🔒"}},
    {{"start": 14.0, "end": 20.5, "style": "CenterPunch", "text": "Deploying the tactical laser SOS 🔦"}},
    {{"start": 21.0, "end": 28.0, "style": "CenterPunch", "text": "Hostage situation on the patio ⛓️"}},
    {{"start": 28.5, "end": 35.5, "style": "CenterPunch", "text": "Emergency backup mobilizes! 🚨"}},
    {{"start": 36.0, "end": 43.0, "style": "CenterPunch", "text": "Delivery disguise with angle grinder 🛠️"}},
    {{"start": 43.5, "end": 50.5, "style": "CenterPunch", "text": "Wheelbarrow extraction into freedom 🚜"}},
    {{"start": 51.0, "end": 57.0, "style": "CenterPunch", "text": "Brenda screaming with literal flames! 🔥"}}
  ]
}}
"""

            response = None
            for vision_model in GEMINI_MODELS:
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
                print(f"[AI Script] Master Story script ready: {len(script_data.get('speech', []))} lines, {len(script_data.get('edit_segments', []))} segments, {script_data.get('edited_duration', 0):.1f}s duration (Ending 100% Anchored)!")
                return script_data

        except Exception as e:
            print(f"[AI Script] Gemini Vision processing error: {e}")

    # 2. SECONDARY: Fallback to text prompt
    print("[AI Script] Using high-retention default master comedy template.")
    return normalize_script_data(get_fallback_template(total_duration), total_duration)


def generate_comedy_script_with_ai(title: str, author: str, duration: float) -> dict:
    return generate_comedy_script_with_gemini("", title, author, duration)


def get_fallback_template(duration: float) -> dict:
    """High-retention 3-Act template adapted to duration with zero audio clashing."""
    cut_len = min(duration, 56.0)
    climax_start = max(0.0, duration - 20.0)
    return {
        "edit_segments": [(0.0, 18.0), (30.0, 48.0), (climax_start, duration)],
        "edited_duration": cut_len,
        "title": "The Great Padlock Escape",
        "speech": [
            ("01", 0.5, "Gary thought he had a quiet afternoon grooming poultry, until Brenda brought out the industrial padlock."),
            ("02", 7.0, "Locked inside his own compound, our lad knows standard diplomatic channels have officially failed."),
            ("03", 14.0, "Desperate times call for covert tactical tech. Gary deploys the high-powered green laser distress beacon."),
            ("04", 21.0, "Down at the local pub, the signal is received loud and clear on the brickwork."),
            ("05", 28.5, "Skipping past the domestic interrogation, tactical backup has officially arrived on scene."),
            ("06", 36.0, "Disguised as a courier, Baozi slips Gary the secret angle grinder right under Brenda's nose."),
            ("07", 43.5, "Hoisted onto the heavy-duty rescue wheelbarrow, the lads make a break for the perimeter."),
            ("08", 51.0, "Brenda returns only to find empty chairs, screaming with literal flames while the boys toast to freedom!")
        ],
        "sfx": [
            ("vine_boom.mp3", 6.5, 0.9),
            ("ding_idea.mp3", 13.5, 0.85),
            ("bruh.mp3", 20.5, 0.9),
            ("vine_boom.mp3", 35.5, 0.9),
            ("oh_no_wheeze_laugh.mp3", 50.5, 0.95)
        ],
        "subtitles": [
            {"start": 0.5, "end": 6.5, "style": "CenterHook", "text": "Gary's peaceful poultry grooming 🐔"},
            {"start": 7.0, "end": 13.5, "style": "CenterPunch", "text": "Brenda locks the perimeter gate! 🔒"},
            {"start": 14.0, "end": 20.5, "style": "CenterPunch", "text": "Deploying the tactical laser SOS 🔦"},
            {"start": 21.0, "end": 28.0, "style": "CenterPunch", "text": "Signal received at the local pub! 🚨"},
            {"start": 28.5, "end": 35.5, "style": "CenterPunch", "text": "Emergency backup mobilizes! 🚜"},
            {"start": 36.0, "end": 43.0, "style": "CenterPunch", "text": "Delivery disguise with angle grinder 🛠️"},
            {"start": 43.5, "end": 50.5, "style": "CenterPunch", "text": "Wheelbarrow extraction into freedom 💨"},
            {"start": 51.0, "end": 56.5, "style": "CenterPunch", "text": "Brenda screaming with literal flames! 🔥"}
        ]
    }
