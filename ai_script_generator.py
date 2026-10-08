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
    Normalizes script data for 3-Act Story Architecture:
    - Guarantees valid chronological segments within [0, total_duration].
    - For long raw videos (>60s), enforces a strict ~50-60s Short duration (never 20-30s!).
    - Expands or adjusts segments if AI under-cuts the narrative.
    - Synchronizes Liam's speech cues, SFX, and subtitles across the full resulting timeline.
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

    # If no segments, construct a safe 3-act split for long videos
    if not norm_segs:
        if total_duration > 60.0:
            act1_len = min(18.0, total_duration * 0.15)
            act2_start = max(act1_len + 5.0, total_duration * 0.35)
            act2_len = 20.0
            act3_start = max(act2_start + act2_len + 5.0, total_duration - 18.0)
            norm_segs = [
                (0.0, act1_len),
                (act2_start, min(total_duration, act2_start + act2_len)),
                (act3_start, total_duration)
            ]
        else:
            norm_segs = [(0.0, total_duration)]

    # Sort chronologically
    norm_segs.sort(key=lambda x: x[0])

    # If raw video is long (>60s) but segments add up to less than 50s, expand them to preserve the story!
    if total_duration > 60.0:
        current_dur = sum(et - st for st, et in norm_segs)
        if current_dur < 50.0 and len(norm_segs) > 0:
            needed = 54.0 - current_dur
            expand_per_seg = needed / len(norm_segs)
            expanded = []
            for i, (st, et) in enumerate(norm_segs):
                prev_bound = expanded[i - 1][1] + 0.5 if i > 0 else 0.0
                next_bound = norm_segs[i + 1][0] - 0.5 if i + 1 < len(norm_segs) else total_duration
                
                # Check backwards room
                back_room = max(0.0, st - prev_bound)
                back_expand = min(back_room, expand_per_seg * 0.35)
                # Remainder goes forwards
                fwd_expand = expand_per_seg - back_expand
                
                new_st = max(prev_bound, st - back_expand)
                new_et = min(next_bound, et + fwd_expand)
                if new_et > new_st + 0.5:
                    expanded.append((new_st, new_et))
                else:
                    expanded.append((st, et))
            norm_segs = expanded

    # Strictly cap total edited duration to maximum 60.0s for YouTube Shorts compliance
    accumulated = 0.0
    capped_segs = []
    for st, et in norm_segs:
        dur = et - st
        if dur <= 0.5:
            continue
        if accumulated + dur > 60.0:
            allowed = max(2.0, 60.0 - accumulated)
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
    data["edit_segments"] = [(round(s, 2), round(e, 2)) for s, e in capped_segs]
    data["edited_duration"] = round(edited_duration, 2)

    # Re-scale / distribute speech, subtitles, and SFX if they ended too early
    speech = data.get("speech", [])
    if speech and len(speech) > 1 and edited_duration > 40.0:
        last_speech_time = float(speech[-1][1])
        if last_speech_time < (edited_duration * 0.65):
            scale_factor = (edited_duration - 6.0) / max(1.0, last_speech_time)
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
    1. 3-Act Narrative Arc (Setup -> Scheme/Conflict -> Climax/Escape).
    2. Strict 50 to 60-second edited duration without story loss.
    3. Complete removal of awkward dead space and in-video sponsor advertisements.
    4. Liam storyteller voiceover explaining the hilarious plot to Western viewers.
    5. Meme sound effect cue points and Center Safe-Zone subtitles.
    """
    print(f"\n[AI Script] Analyzing video ({total_duration:.1f}s) for '{author}' with 3-Act Story Engine...")

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

            is_long = (total_duration > 60.0)
            if is_long:
                editing_instructions = f"""STEP 3: 3-ACT NARRATIVE STORY EDITING (~50-60 SECONDS TOTAL)
This raw comedy skit is {total_duration:.1f} seconds long. For maximum viral retention and complete story comprehension, you must edit this video into a coherent 50 to 60-second mini-movie (TARGET: 52 to 58 seconds total).

CRITICAL STORYTELLING RULES:
1. PRESERVE THE COMPLETE 3-ACT NARRATIVE ARC:
   A successful comedy skit must have beginning, middle, and end. Do NOT skip any act:
   - ACT 1: THE SETUP & CONFLICT (14 to 18 seconds, starts at 0.0s):
     Introduce who the characters are, what crazy/absurd thing is happening, and what restriction/conflict is imposed (e.g. wife locking the gate with a huge padlock).
   - ACT 2: THE SCHEME / ESCALATION (18 to 22 seconds, from the middle):
     Show the sneaky trick or distress signal used to solve the problem (e.g. secret green laser SOS beacon, toy cart trick, distress call, or getting tied to chairs).
   - ACT 3: THE RESCUE / CLIMAX & PUNCHLINE (14 to 18 seconds, towards the ending):
     Show how backup arrives (e.g. with a wheelbarrow/tools), the successful escape, and the opponent/wife's stunned, bewildered reaction!

2. WHAT TO REMOVE (BORING FLUFF & ADS):
   - Cut out slow walking, long silent pauses, repetitive dialogue before actions.
   - CRITICAL: STRICTLY REMOVE ANY IN-VIDEO COMMERCIAL SPONSOR ADS / PRODUCT PROMOTIONS (e.g. phone recycling, apps, brand plugs) that disrupt the comedy story!

3. STRICT DURATION CONSTRAINT:
   - Provide "edit_segments": [[start1, end1], [start2, end2], [start3, end3]]
   - The SUM of all segment durations MUST BE BETWEEN 50.0 AND 60.0 SECONDS! (e.g. 52s - 58s).
   - NEVER make the total duration shorter than 50 seconds (do NOT make 20-30s clips).
   - Segments must appear in strictly ascending chronological order.

4. LIAM STORYTELLER NARRATION & SFX:
   - Provide 8 to 10 punchy voiceover lines for ElevenLabs Liam ("speech").
   - Liam MUST ACT AS THE STORYTELLER / NARRATOR: Explain what is happening step-by-step so a viewer who does not speak Chinese understands the hilarious plot completely!
   - Space lines with 1.0 - 1.5s silence pockets between them for meme SFX.
   - Include 4 to 6 meme SFX ('vine_boom.mp3', 'bruh.mp3', 'ding_idea.mp3', 'oh_no_wheeze_laugh.mp3') timed right after key revelations/punchlines.
   - Include dynamic Center Eye-Level Safe Zone subtitles with emojis.
"""
            else:
                editing_instructions = f"""STEP 3: COMEDY SCRIPT SYNCHRONIZATION (~{total_duration:.1f}s)
This video is already within the ideal short duration ({total_duration:.1f}s).
Keep the whole clip: "edit_segments": [[0.0, {total_duration:.1f}]]
Write 5 to 7 punchy voiceover lines for Liam, spaced with 1.0 - 1.5s silence pockets for meme sound effects.
Include 3-4 meme SFX from ('vine_boom.mp3', 'bruh.mp3', 'ding_idea.mp3', 'oh_no_wheeze_laugh.mp3') timed right after key revelations.
Add center eye-level safe zone subtitles with emojis.
"""

            vision_prompt = f"""You are a master viral YouTube Shorts comedy writer and British deadpan narrator (BBC Wildlife Documentary meets sarcastic UK comedian like Liam).

You have full multimodal vision and audio capabilities.
CRITICAL MISSION: Watch the visual action and listen to the Chinese dialogue in this video. Your goal is to turn this Chinese comedy skit into a crystal-clear, hilarious 50-60 second Short for global/Western audiences who do not speak Chinese!

STEP 1: UNDERSTAND THE REAL COMEDY STORYLINE
- What is the premise? (e.g. who are the main characters, what funny hobby/activity is happening, what restriction or conflict is placed on them?)
- What is the rising tension? (e.g. how do they try to overcome the obstacle, what secret distress signals or absurd tools do they use?)
- What is the final twist or payoff? (e.g. how do the friends/rescuers break in, how do they escape, what is the wife's stunned reaction?)
- Ignore and completely cut any in-video commercial sponsor advertisements (e.g. app plugs, phone recycling, product placements).

STEP 2: UK / WESTERN ROAST STORYTELLING (FOR ELEVENLABS LIAM)
- Deliver deadpan, witty British narration that tells the STORY chronologically from start to finish.
- Give characters British comedy nicknames (e.g. Gary the Barber, Brenda, Terry, Dave).
- Never leave the viewer confused: explain WHY someone is trapped, WHAT their ridiculous plan is, and HOW they get away with it!
- STRICTLY FORBIDDEN: NEVER use generic cliches ('Bro thought', 'Wait for it', 'Absolute cinema', 'Legendary difficulty'). Use vivid, descriptive British humor.

{editing_instructions}

Return ONLY valid JSON with this exact schema:
{{
  "edit_segments": [
    [0.0, 18.0],
    [45.0, 66.0],
    [135.0, 154.0]
  ],
  "edited_duration": 58.0,
  "title": "Short punchy title",
  "speech": [
    ["01", 0.5, "Line 1 introducing the setup..."],
    ["02", 6.5, "Line 2..."],
    ["03", 12.5, "Line 3..."],
    ["04", 19.0, "Line 4 introducing the plan..."],
    ["05", 25.5, "Line 5..."],
    ["06", 32.0, "Line 6..."],
    ["07", 38.5, "Line 7 introducing the rescue..."],
    ["08", 45.0, "Line 8..."],
    ["09", 51.5, "Line 9 delivering punchline..."]
  ],
  "sfx": [
    ["vine_boom.mp3", 6.0, 0.9],
    ["ding_idea.mp3", 18.5, 0.85],
    ["bruh.mp3", 31.5, 0.9],
    ["vine_boom.mp3", 38.0, 0.9],
    ["oh_no_wheeze_laugh.mp3", 51.0, 0.95]
  ],
  "subtitles": [
    {{"start": 0.5, "end": 6.0, "style": "CenterHook", "text": "SUBTITLE LINE 💀"}},
    {{"start": 6.5, "end": 12.0, "style": "CenterPunch", "text": "SUBTITLE LINE 🚨"}},
    {{"start": 12.5, "end": 18.5, "style": "CenterPunch", "text": "SUBTITLE LINE 🔒"}},
    {{"start": 19.0, "end": 25.0, "style": "CenterPunch", "text": "SUBTITLE LINE 💡"}},
    {{"start": 25.5, "end": 31.5, "style": "CenterPunch", "text": "SUBTITLE LINE 🔦"}},
    {{"start": 32.0, "end": 38.0, "style": "CenterPunch", "text": "SUBTITLE LINE ⛓️"}},
    {{"start": 38.5, "end": 44.5, "style": "CenterPunch", "text": "SUBTITLE LINE 🚜"}},
    {{"start": 45.0, "end": 51.0, "style": "CenterPunch", "text": "SUBTITLE LINE 💨"}},
    {{"start": 51.5, "end": 56.5, "style": "CenterPunch", "text": "SUBTITLE LINE 👑"}}
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
                print(f"[AI Script] Gemini Vision 3-Act script ready: {len(script_data.get('speech', []))} lines, {len(script_data.get('edit_segments', []))} segments, {script_data.get('edited_duration', 0):.1f}s total duration!")
                return script_data

        except Exception as e:
            print(f"[AI Script] Gemini Vision processing error: {e}")

    # 2. SECONDARY: Fallback to text prompt if video upload wasn't possible
    print("[AI Script] Fallback: using text-based prompt...")
    text_prompt = f"""You are a master viral YouTube Shorts comedy writer and British deadpan narrator.
A Chinese slapstick comedy creator named "{author}" published a video with caption: "{caption}".
Video duration: {total_duration:.1f} seconds.

Turn this into a viral 52-58 second UK meme Short with Liam voiceover.
Tone: Deadpan British documentary sarcasm.
Return ONLY valid JSON matching:
{{
  "edit_segments": [[0.0, 18.0], [30.0, 50.0], [{max(51.0, total_duration - 18.0):.1f}, {total_duration:.1f}]],
  "edited_duration": 56.0,
  "title": "Slapstick Escape",
  "speech": [
    ["01", 0.5, "Text..."],
    ["02", 7.0, "Text..."],
    ["03", 14.0, "Text..."],
    ["04", 21.0, "Text..."],
    ["05", 28.0, "Text..."],
    ["06", 35.0, "Text..."],
    ["07", 42.0, "Text..."],
    ["08", 49.0, "Text..."]
  ],
  "sfx": [
    ["vine_boom.mp3", 6.5, 0.9],
    ["ding_idea.mp3", 20.5, 0.85],
    ["bruh.mp3", 34.5, 0.9],
    ["oh_no_wheeze_laugh.mp3", 48.5, 0.95]
  ],
  "subtitles": [
    {{"start": 0.5, "end": 6.5, "style": "CenterHook", "text": "Text 💀"}},
    {{"start": 7.0, "end": 13.5, "style": "CenterPunch", "text": "Text 🚨"}}
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

    print("[AI Script] Using high-retention default 3-act comedy template.")
    return normalize_script_data(get_fallback_template(total_duration), total_duration)


def generate_comedy_script_with_ai(title: str, author: str, duration: float) -> dict:
    return generate_comedy_script_with_gemini("", title, author, duration)


def get_fallback_template(duration: float) -> dict:
    """High-retention 3-Act template adapted to duration with zero audio clashing."""
    cut_len = min(duration, 55.0)
    return {
        "edit_segments": [(0.0, 18.0), (25.0, 45.0), (max(46.0, duration - 15.0), duration)],
        "edited_duration": cut_len,
        "title": "The Great Padlock Escape",
        "speech": [
            ("01", 0.5, "Gary thought he had a quiet afternoon grooming poultry, until Brenda brought out the industrial padlock."),
            ("02", 7.0, "Locked inside his own compound, our lad knows standard diplomatic channels have officially failed."),
            ("03", 14.0, "Desperate times call for covert tactical tech. Gary deploys the high-powered green laser distress beacon."),
            ("04", 21.0, "Down at the local pub, the signal is received loud and clear on the brickwork."),
            ("05", 28.5, "Brenda discovers the secret transmissions and ties the boys to chairs in pure retaliation."),
            ("06", 35.5, "Under the radar, the extraction squad mobilizes with the heavy-duty rescue wheelbarrow."),
            ("07", 42.5, "Before Brenda can blink, the boys are hoisted over the perimeter into sweet, glorious freedom."),
            ("08", 49.5, "Leaving Brenda standing at the open gate, utterly flabbergasted by the great escape.")
        ],
        "sfx": [
            ("vine_boom.mp3", 6.5, 0.9),
            ("ding_idea.mp3", 13.5, 0.85),
            ("bruh.mp3", 20.5, 0.9),
            ("vine_boom.mp3", 28.0, 0.9),
            ("oh_no_wheeze_laugh.mp3", 49.0, 0.95)
        ],
        "subtitles": [
            {"start": 0.5, "end": 6.5, "style": "CenterHook", "text": "Brenda brings out the industrial padlock 🔒"},
            {"start": 7.0, "end": 13.5, "style": "CenterPunch", "text": "Locked inside his own compound! 💀"},
            {"start": 14.0, "end": 20.5, "style": "CenterPunch", "text": "Gary deploys the tactical laser beacon 🔦"},
            {"start": 21.0, "end": 28.0, "style": "CenterPunch", "text": "Signal received at the local pub! 🚨"},
            {"start": 28.5, "end": 35.0, "style": "CenterPunch", "text": "Brenda ties the lads to the chairs ⛓️"},
            {"start": 35.5, "end": 42.0, "style": "CenterPunch", "text": "Rescue squad arrives with the wheelbarrow! 🚜"},
            {"start": 42.5, "end": 49.0, "style": "CenterPunch", "text": "Hoisted over the perimeter into freedom 💨"},
            {"start": 49.5, "end": 55.0, "style": "CenterPunch", "text": "Brenda utterly flabbergasted by the escape! 👑"}
        ]
    }
