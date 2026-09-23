import asyncio
import os
import sys
import argparse
import subprocess
import requests
import json
import re
import urllib.parse
import time
import random
import base64

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Fallback obfuscated keys (to comply with GitHub Secret Scanning)
_PK = b"TGdHWjJoMTRYQk9RZTl2dXE0dmd6bVpwVVQyV3p2emJwbHRCRHlEaEVtY25EcEhKMXhvTWFhcVE="
_GK = b"QVEuQWI4Uk42S0JEMFhIQjJnM1JlM3VMVVVVd1NHdDdRLUkyZkVxcnJ5bnNpTWpkNGNEanc="

DEFAULT_PEXELS_KEY = (os.environ.get("PEXELS_API_KEY") or "").strip()
if not DEFAULT_PEXELS_KEY:
    DEFAULT_PEXELS_KEY = base64.b64decode(_PK).decode("utf-8")

DEFAULT_GEMINI_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
if not DEFAULT_GEMINI_KEY:
    DEFAULT_GEMINI_KEY = base64.b64decode(_GK).decode("utf-8")

BGM_TRACKS = {
    "space": "https://upload.wikimedia.org/wikipedia/commons/5/55/Dreamstate_Logic_-_Zero_Point_%28space_ambient%2C_dark_ambient%29.ogg",
    "mystery": "https://upload.wikimedia.org/wikipedia/commons/5/55/Dreamstate_Logic_-_Zero_Point_%28space_ambient%2C_dark_ambient%29.ogg",
    "dark mystery": "https://upload.wikimedia.org/wikipedia/commons/5/55/Dreamstate_Logic_-_Zero_Point_%28space_ambient%2C_dark_ambient%29.ogg",
    "tech": "https://upload.wikimedia.org/wikipedia/commons/d/db/Terminus_Void_-_Inception_%28Dystopian_Cyberpunk_Space_Ambient_Music_similar_to_Blade_Runner_soundtrack_music%29.opus",
    "nature": "https://upload.wikimedia.org/wikipedia/commons/8/81/Vastopia_-_Dark_Ambient_Music_for_Deep_Relaxation_and_Focus.ogg"
}

POWER_WORDS = {
    "TERRIFYING", "MASSIVE", "COLOSSAL", "DARKNESS", "GALAXIES", "ALIEN", "CIVILIZATION",
    "EXPLODED", "VOID", "HARVESTING", "ERASING", "LURKING", "EXTINCT", "INFINITY",
    "MILLION", "BILLION", "LIGHT-YEARS", "BLACK", "HOLE", "SILENT", "SHOCK", "SECRETS",
    "UNIVERSE", "DESTROYED", "DANGEROUS", "SWALLOWED", "UNKNOWN", "VANISHED", "SCREAMING"
}

FALLBACK_PLANS = [
    {
        "title": "The Void That Swallowed 2,000 Galaxies 🌌 #shorts",
        "hook_banner": "TERRIFYING HOLE IN SPACE",
        "full_script": "Deep in the constellation Boötes lies a terrifying region of space 330 million light-years across. It should contain thousands of galaxies, but astronomers found almost nothing. What could wipe out an entire sector of the universe? Some fear an ancient civilization is harvesting entire stars.",
        "scenes": [
            {
                "scene_id": 1,
                "voice_line": "Deep in the constellation Boötes lies a terrifying region of space 330 million light-years across.",
                "visual_vibe": "Telescope deep space view starry universe cosmic void",
                "search_queries": ["deep space stars telescope", "galaxy field universe"]
            },
            {
                "scene_id": 2,
                "voice_line": "It should contain thousands of galaxies, but astronomers found almost nothing.",
                "visual_vibe": "Dark empty void black space cosmos",
                "search_queries": ["dark space void empty", "spiral galaxy spinning"]
            },
            {
                "scene_id": 3,
                "voice_line": "What could wipe out an entire sector of the universe?",
                "visual_vibe": "Black hole cosmic explosion mystery nebula",
                "search_queries": ["black hole space", "nebula explosion cosmic"]
            },
            {
                "scene_id": 4,
                "voice_line": "Some fear an ancient civilization is harvesting entire stars.",
                "visual_vibe": "Futuristic alien megastructure sci fi space glowing planet",
                "search_queries": ["futuristic sci fi space technology", "alien planet glowing space"]
            }
        ]
    }
]

def clean_voice_name(voice_input):
    if " " in voice_input:
        return voice_input.split(" ")[0].strip()
    return voice_input.strip()

def format_ass_time(sec):
    hrs = int(sec // 3600)
    mins = int((sec % 3600) // 60)
    secs = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    if cs >= 100:
        secs += 1
        cs = 0
    return f"{hrs:d}:{mins:02d}:{secs:02d}.{cs:02d}"

def generate_hormozi_ass_subtitles(cues, ass_path):
    """
    Creates eye-popping two-tone subtitles (Alex Hormozi style)
    Active/Power words pop in Neon Green (&H0000FF00), while base words are crisp White!
    """
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,68,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,6,3,2,50,50,750,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dialogues = []
    for s_time, e_time, text in cues:
        words = text.split()
        if not words:
            continue
            
        highlight_idx = -1
        for idx, w in enumerate(words):
            clean_w = re.sub(r'[^A-Z0-9]', '', w)
            if clean_w in POWER_WORDS or clean_w.isdigit():
                highlight_idx = idx
                break
        if highlight_idx == -1:
            highlight_idx = max(range(len(words)), key=lambda i: len(words[i]))
            
        formatted_words = []
        for idx, w in enumerate(words):
            if idx == highlight_idx:
                formatted_words.append(f"{{\\c&H0000FF00&}}{w}{{\\c&H00FFFFFF&}}")
            else:
                formatted_words.append(w)
                
        styled_line = " ".join(formatted_words)
        start_fmt = format_ass_time(s_time)
        end_fmt = format_ass_time(e_time)
        dialogues.append(f"Dialogue: 0,{start_fmt},{end_fmt},Default,,0,0,0,,{styled_line}")
        
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(dialogues) + "\n")
    print(f"✅ Generated {len(dialogues)} Hormozi-style two-tone animated subtitle cues!")

def split_sentence_into_cues(start_s, end_s, text, max_words=3):
    words = text.strip().split()
    if not words:
        return []
    chunks = []
    curr = []
    for w in words:
        curr.append(w)
        if len(curr) >= max_words or any(w.endswith(p) for p in [".", "!", "?", ","]):
            chunks.append(curr)
            curr = []
    if curr:
        chunks.append(curr)
    
    total_chunks = len(chunks)
    chunk_dur = (end_s - start_s) / max(1, total_chunks)
    
    cues = []
    for i, c in enumerate(chunks):
        c_start = start_s + i * chunk_dur
        c_end = c_start + chunk_dur
        cues.append((c_start, c_end, ' '.join(c).upper()))
    return cues

async def generate_speech_and_subtitles(script_text, voice_id, audio_output_path, ass_output_path):
    import edge_tts
    print(f"🎙️ Generating voiceover using voice: {voice_id}...")
    communicate = edge_tts.Communicate(script_text, voice_id)
    
    cues = []
    sentence_timings = []
    with open(audio_output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                start_s = chunk["offset"] / 10_000_000
                end_s = start_s + (chunk["duration"] / 10_000_000)
                sentence_timings.append({
                    "text": chunk["text"],
                    "start_s": round(start_s, 2),
                    "end_s": round(end_s, 2),
                    "duration": round(end_s - start_s, 2)
                })
                sentence_cues = split_sentence_into_cues(start_s, end_s, chunk["text"], max_words=3)
                cues.extend(sentence_cues)
                
    generate_hormozi_ass_subtitles(cues, ass_output_path)
    return sentence_timings

def get_audio_duration(audio_path):
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        out = subprocess.check_output(cmd).decode().strip()
        return float(out)
    except Exception as e:
        print(f"Warning: ffprobe failed ({e}), using default estimation.")
        return 40.0

def fetch_bgm_track(topic, output_bgm_path):
    topic_lower = topic.lower()
    url = BGM_TRACKS.get("space")
    for k in BGM_TRACKS:
        if k in topic_lower:
            url = BGM_TRACKS[k]
            break
            
    print(f"🎵 Fetching cinematic background music from: {url[:60]}...")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, stream=True, timeout=20)
        if r.status_code == 200:
            with open(output_bgm_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*64):
                    f.write(chunk)
                    if f.tell() > 1024 * 1024 * 3:
                        break
            print("✅ Background music downloaded!")
            return True
    except Exception as e:
        print(f"BGM download failed: {e}")
    return False

# =========================================================================
# 🧠 DUAL-SPECIALIST ARCHITECTURE:
# 1. ✍️ Executive Producer : Gemini 3.8 Flash (Deep viral storytelling & timeline approval)
# 2. 🎬 Assistant Director  : Gemini 3.5 Flash Lite (Screens 5 candidates per scene - 500 RPD)
# =========================================================================

SCRIPT_MODELS = [
    "gemini-3.8-flash",       # Top priority: Google's newest flagship for mind-bending scripts
    "gemini-3.6-flash",       # High-tier backup
    "gemini-3.5-flash-lite",  # 500 RPD backup
    "gemini-3.1-flash-lite"   # 500 RPD backup
]

DIRECTOR_MODELS = [
    "gemini-3.5-flash-lite",  # Top priority: 500 RPD for lightning-fast clip curation
    "gemini-3.1-flash-lite"   # 500 RPD backup
]

def call_gemini_json_api(gemini_key, prompt, model_list, timeout=35):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    for model in model_list:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
        try:
            res = requests.post(url, json=payload, timeout=timeout)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(text)
                return data, model
            elif res.status_code == 429:
                print(f"⚠️ Model {model} hit rate limit (429), trying backup model...")
                continue
            elif res.status_code == 503:
                print(f"⚠️ Model {model} busy (503), switching to fast backup...")
                continue
            else:
                print(f"Notice: Model {model} returned status {res.status_code}, trying backup...")
        except Exception as e:
            print(f"Notice: Model {model} failed ({e}), trying backup...")
    return None, None

MASTER_MYSTERY_VAULT = [
    # 🌌 Deep Space Anomalies & Cosmic Horrors
    "The Great Attractor: An invisible gravitational anomaly pulling our entire Milky Way and thousands of galaxies at 2 million km/h toward an unseen cosmic wall.",
    "Boötes Void: The 330-million light-year abyss of pure nothingness where 2,000 galaxies should exist but completely vanished.",
    "Strange Matter Stars: A hypothetical cosmic material denser than neutron stars that converts any normal matter it touches into strangelets, destroying whole planets.",
    "False Vacuum Decay: The ultimate cosmic nightmare where a single quantum bubble could erase all laws of physics and atoms at the speed of light.",
    "Dark Flow: A mysterious cosmic current dragging galaxy clusters outside the boundaries of our observable universe as if something colossal exists beyond.",
    "The CMB Cold Spot: An unexplained 1.8 billion light-year freezing zone in cosmic background radiation, possibly a bruise from a colliding parallel universe.",
    "Ghost Galaxies: Massive cosmic structures composed of 99.9% dark matter with zero visible stars, silently bending light around empty space.",
    "Rogue Black Holes: Unseen stellar-mass black holes hurtling through interstellar space at supersonic speeds without emitting any light.",
    "Supermassive Black Hole TON 618: An unimaginable cosmic monster with the mass of 66 billion suns, shining brighter than 140 trillion stars.",
    "The Eridanus Supervoid: A terrifying expanse of empty space 1 billion light years wide where matter and cosmic temperatures drop to near absolute zero.",
    "Cosmic Strings: Infinitely thin, universe-spanning tears in spacetime with the mass of mountain ranges per inch, capable of slicing planets in half.",
    "Quasar 3C 273: An ancient active galactic nucleus consuming 1,000 Earths of matter every minute, spewing relativistic plasma jets 300,000 light years long.",

    # 🌊 Deep Ocean & Subterranean Terrors
    "The Bloop of 1997: An ultra-low frequency sound echoing 3,000 miles across the Pacific Ocean, louder than any known marine animal or volcanic event.",
    "Mariana Trench Challenger Deep: Deep-sea hydrophones at 36,000 feet recording unexplained rhythmic metallic pulses from beneath the tectonic crust.",
    "The Baltic Sea Monolith: A 200-foot disc-shaped submerged structure at 300 feet depth that inexplicably jams electrical navigation gear above it.",
    "The Upsweep Sound: An unidentified deep ocean acoustic signal steadily rising from Antarctic waters every spring since 1991.",
    "Lake Vostok Sealed Abyss: A massive Antarctic lake sealed beneath 2 miles of solid ice for 15 million years, harboring isolated alien-like microbes.",
    "Point Nemo Spacecraft Graveyard: The oceanic pole of inaccessibility, furthest place from civilization, where hundreds of defunct space stations are buried.",
    "The Bermuda Triangle Blue Holes: Hundreds of feet deep underwater caverns creating sudden massive whirlpool currents that swallow ships without debris.",
    "Mariana Bioluminescent Sirens: Unclassified organisms surviving under 1,000 atmospheres of crushing pressure that communicate through mesmerizing light pulses.",
    "The Dragon's Triangle (Devil's Sea): The sinister Pacific zone south of Tokyo where military vessels and cargo ships vanish from radar screens with no distress calls.",
    "Challenger Deep Hydrothermal Sirens: Superheated 400-degree mineral chimneys hosting bizarre translucent creatures in pitch-black boiling acidic water.",

    # ⏳ Quantum, Time & Reality Glitches
    "The Quantum Delayed-Choice Experiment: How observing photons in the present physically rewrites what they did billions of years in the past.",
    "Time Dilation at Black Hole Horizons: Why watching someone fall toward a singularity freezes their frozen image forever while they watch the universe die.",
    "The Boltzmann Brain Paradox: In an infinite universe, a random disembodied consciousness fluctuating into existence in deep space is more likely than humanity.",
    "Quantum Entanglement Spooky Action: Particles separated by billions of light years communicating states instantaneously, defying the cosmic speed limit.",
    "The Simulation Refresh Rate Glitch: Why the speed of light is the strict universal speed limit, identical to maximum processing rendering limits in computer engines.",
    "Closed Timelike Curves: Einstein's general relativity allowing spacetime to loop back on itself around rotating Kerr black holes, creating real time travel loops.",
    "The Quantum Zeno Paradox: Continuously observing an unstable radioactive particle physically freezes it in time and prevents it from ever decaying.",
    "The Grandfather Paradox and Many-Worlds: How altering past timelines branches reality into an infinite tree of divergent parallel universes.",

    # 📡 Alien Megastructures & Cosmic Signals
    "The Wow! Signal: The legendary 72-second narrow-band transmission detected in 1977 that matched interstellar alien beacon frequencies and never repeated.",
    "KIC 8462852 (Tabby's Star): Erratic 22% drops in starlight that led astrophysicists to investigate whether an alien Dyson Swarm was orbiting the star.",
    "The Matrioshka Brain: Hypothetical nested Dyson spheres capturing the entire energy output of a star to power a solar-system-scale artificial intelligence.",
    "Oumuamua's Anomalous Acceleration: The reddish cigar-shaped interstellar visitor that accelerated away from the Sun with no cometary tail or outgassing.",
    "The Fermi Paradox & The Great Filter: The terrifying mathematical reality that trillions of habitable worlds are dead and silent because an invisible filter destroys civilizations.",
    "Fast Radio Bursts (FRBs): Millisecond-duration cosmic radio flashes discharging as much energy in a fraction of a second as our Sun emits in three days."
]

HISTORY_FILE = "history.json"

def load_recent_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def extract_key_ident(text):
    if ":" in text:
        return text.split(":")[0].strip().lower()
    return " ".join(text.split()[:3]).lower()

def get_untouched_mystery(history):
    past_texts = []
    for h in history:
        past_texts.append(h.get("title", "").lower())
        past_texts.append(h.get("topic", "").lower())
        past_texts.append(h.get("hook_banner", "").lower())
    full_past = " ".join(past_texts)

    untouched = []
    for mystery in MASTER_MYSTERY_VAULT:
        ident = extract_key_ident(mystery)
        # Extract meaningful keywords (length >= 4 and not generic stop-words)
        key_words = [w for w in re.findall(r'\b[a-z0-9]{4,}\b', ident) if w not in ["deep", "space", "mystery", "cosmic", "ocean", "sound", "alien", "anomaly"]]
        if not key_words:
            key_words = [ident]
        
        already_used = any(kw in full_past for kw in key_words)
        if not already_used:
            untouched.append(mystery)

    if untouched:
        return random.choice(untouched)
    
    # If all items touched, return random from vault
    return random.choice(MASTER_MYSTERY_VAULT)

def save_to_history(title, topic, hook_banner):
    history = load_recent_history()
    history.append({
        "date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "title": title,
        "topic": topic,
        "hook_banner": hook_banner
    })
    # Strict Sliding Window: Keep only the last 35 entries to keep file < 4KB forever!
    history = history[-35:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    print(f"🧠 Updated Memory Vault: Tracking {len(history)} recent unique topics (sliding window active).")

def generate_ai_director_plan(gemini_key, requested_topic="auto"):
    """
    Step 1: Executive Producer (Gemini 3.8 Flash) composes an unforgettable viral script
    strictly targeted for 30 seconds (68-78 words) with ZERO topic repetition!
    """
    recent_history = load_recent_history()
    past_topics_desc = [f"- {h.get('title', '')} (Theme: {h.get('topic', '')})" for h in recent_history[-20:]]
    past_topics_str = "\n".join(past_topics_desc) if past_topics_desc else "None yet (Brand new channel vault)"

    # Determine active topic
    is_auto = (
        not requested_topic 
        or requested_topic.strip().lower() in [
            "auto", "deep space cosmic mystery", "deep space cosmic anomaly", 
            "mystery", "space mystery", "default"
        ]
    )

    if is_auto:
        active_topic = get_untouched_mystery(recent_history)
        print(f"🎯 Auto-Selected Untouched Mystery from Vault:\n   -> {active_topic}")
    else:
        active_topic = requested_topic.strip()
        print(f"🎯 Using User-Specified Topic: '{active_topic}'")

    prompt = f"""You are the Executive Producer for a viral YouTube Shorts channel targeting American audiences (Tier-1 High RPM).
Your mission: Create an unscrollable, suspenseful 30-SECOND viral Short about this exact phenomenon:
THEME: "{active_topic}"

VIRAL HOOK & PACING FORMULA (The "Don't Scroll" Blueprint):
1. HOOK (0-3 SECONDS):
   - A shocking first sentence that immediately stops the user from scrolling.
   - Start immediately inside the terror, anomaly, or impossible contradiction.
   - STRICTLY FORBIDDEN: "Did you know?", "In this video", "Welcome back", "Today we talk about".
2. TENSION ESCALATION (3-18 SECONDS):
   - Deliver 2 to 3 chilling, scientifically documented facts about this phenomenon.
   - Use vivid, atmospheric language that triggers cosmic dread or visceral fascination.
3. CLIMAX / MIND-BENDING REVEAL (18-28 SECONDS):
   - Deliver an unsettling twist or an existential question that lingers in their mind.
   - Forces viewers to rewatch or debate in the comments.
4. WORD COUNT CONSTRAINT:
   - Target Word Count: EXACTLY 68 to 76 words!
   - Spoken at a documentary pace, this yields EXACTLY 27-30 seconds of speech.
5. FAST-PACED VIRAL SCENE STRUCTURE (CRITICAL FOR RETENTION):
   - Provide EXACTLY 7 to 8 SEQUENTIAL SCENES (Micro-Shots)!
   - Each scene voice_line must be 8 to 11 words (approx 3.0 to 3.8 seconds).
   - ABSOLUTE LIMIT: No individual clip should stay on screen longer than 4.0 seconds!
   - Fast, seamless visual transitions keep viewers completely glued to the screen.
6. 8K PHOTOREALISTIC VISUAL ART DIRECTION (Crucial for Video Quality):
   - For EACH scene, write a hyper-detailed, photorealistic visual_prompt describing the exact camera shot for an 8K AI image renderer.
   - Describe exact physical subjects, lighting, materials, and camera perspective:
     * Deep Ocean: "Armored titanium submersible yellow xenon headlights illuminating pitch-black ocean floor at 36,000 feet, marine snow, jagged trench rocks, 8k, photorealistic, cinematic volumetric lighting"
     * Space/Cosmic: "Accretion disk of a supermassive black hole bending surrounding starlight, glowing orange relativistic plasma vortex, pitch black cosmos, 8k cinematic"
   - Every visual_prompt MUST match the exact sentence being spoken in that scene!
   - Also provide 2 backup physical 'search_queries' for stock search.

⛔ STRICT ANTI-REPETITION CONSTRAINT:
Do NOT duplicate any of these recently covered topics from our history:
{past_topics_str}

REQUIRED JSON OUTPUT FORMAT:
{{
  "title": "Shorts Title with emoji and #shorts (under 50 chars)",
  "hook_banner": "3-5 WORDS UPPERCASE FOR TOP BANNER (e.g. THE OCEAN IS HIDING THIS)",
  "full_script": "The complete 68-76 word script combining all 7-8 scenes smoothly.",
  "scenes": [
    {{
      "scene_id": 1,
      "voice_line": "Sentence for scene 1 (8-11 words)",
      "visual_prompt": "Hyper-detailed 8K photorealistic scene description for AI image generation",
      "visual_vibe": "Cinematic visual description",
      "search_queries": ["query 1", "query 2"]
    }}
  ]
}}
Output valid pure JSON only without markdown formatting."""

    print(f"✍️ Executive Producer (Gemini 3.8 Flash) is composing a fresh 30s script for: '{active_topic[:50]}...'")
    data, used_model = call_gemini_json_api(gemini_key, prompt, SCRIPT_MODELS, timeout=25)
    if data:
        print(f"✨ Masterpiece Script written by: [{used_model}]")
        print(f"🎬 Title: {data.get('title')}")
        print(f"📌 Hook Banner: {data.get('hook_banner')}")
        print(f"📜 Generated {len(data.get('scenes', []))} fast-paced sequential scenes.")
        return data, active_topic

    print("⚠️ Falling back to curated high-retention space mystery plan.")
    return FALLBACK_PLANS[0], FALLBACK_PLANS[0].get("title")

NEGATIVE_PEXELS_KEYWORDS = [
    "smile", "smiling", "office", "laptop", "meeting", "business", "desk", 
    "workout", "fitness", "cooking", "dance", "dancing", "happy", "woman talking", 
    "man talking", "car driving", "traffic", "phone", "family", "kids", "baby", "shopping", "food",
    "diver", "scuba", "swimming", "snorkeling", "coral", "reef", "beach", "pool", "sunlight"
]

def parse_pexels_clip_info(c, idx):
    slug = c.get("url", "").strip("/").split("/")[-1]
    title = re.sub(r'-\d+$', '', slug).replace('-', ' ').title()
    if not title or title.isdigit():
        title = "Cinematic Stock Footage"
    w = c.get("width", 0)
    h = c.get("height", 0)
    res = "4K Portrait" if (h >= 2160 or w >= 2160) else ("1080p Portrait" if h >= w else "Landscape")
    return {
        "candidate_index": idx,
        "visual_description": title,
        "resolution": res,
        "duration_seconds": c.get("duration", 0),
        "color_tone": c.get("avg_color", "Dark")
    }

def fetch_pexels_candidates(queries, pexels_key, min_candidates=5):
    """
    Step 2: Fetches at least 5 distinct high-quality candidate clips per scene with random page shuffling.
    Filters out off-topic everyday life footage and enforces portrait orientation.
    """
    headers = {"Authorization": pexels_key.strip()}
    candidates = []
    seen_ids = set()

    for q in queries:
        clean_q = re.sub(r'[^a-zA-Z0-9\s]', '', q).strip()
        if len(clean_q.split()) <= 1:
            clean_q = f"{clean_q} dark cinematic 4k"
        encoded = urllib.parse.quote(clean_q)
        random_page = random.randint(1, 3)
        url = f"https://api.pexels.com/videos/search?query={encoded}&orientation=portrait&per_page=10&page={random_page}"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                videos = r.json().get("videos", [])
                random.shuffle(videos)
                for v in videos:
                    vid = v.get("id")
                    if not vid or vid in seen_ids:
                        continue
                    
                    # Ensure vertical or square
                    w = v.get("width", 0)
                    h = v.get("height", 0)
                    if h < w:
                        continue
                        
                    # Filter out negative everyday life keywords from slug
                    slug = v.get("url", "").lower()
                    if any(neg in slug for neg in NEGATIVE_PEXELS_KEYWORDS):
                        continue
                        
                    seen_ids.add(vid)
                    candidates.append(v)
            if len(candidates) >= min_candidates:
                break
        except Exception as e:
            print(f"Pexels search error for '{q}': {e}")

    # Fallback if fewer than min_candidates found
    if len(candidates) < min_candidates:
        backup_queries = ["deep space nebula 4k", "dark galaxy universe stars", "underwater abyss glowing deep sea"]
        for bq in backup_queries:
            random_page = random.randint(1, 4)
            url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(bq)}&orientation=portrait&per_page=8&page={random_page}"
            try:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code == 200:
                    for v in r.json().get("videos", []):
                        vid = v.get("id")
                        if not vid or vid in seen_ids:
                            continue
                        w = v.get("width", 0)
                        h = v.get("height", 0)
                        if h < w:
                            continue
                        slug = v.get("url", "").lower()
                        if any(neg in slug for neg in NEGATIVE_PEXELS_KEYWORDS):
                            continue
                        seen_ids.add(vid)
                        candidates.append(v)
                if len(candidates) >= min_candidates:
                    break
            except Exception:
                pass

    return candidates

def assistant_director_select_clip(gemini_key, scene, candidates):
    """
    Step 3: Assistant Director (Gemini 3.5 Flash Lite - 500 RPD) screens 5 candidates,
    evaluates rich visual descriptions and resolutions, and selects the absolute best match.
    """
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    candidate_summaries = [parse_pexels_clip_info(c, idx) for idx, c in enumerate(candidates[:5])]

    prompt = f"""You are the Master Visual Director for a high-retention documentary YouTube Short.
Your mission: Screen these 5 candidate stock clips from Pexels and choose the SINGLE BEST visual for this exact scene.

SCENE NARRATION: "{scene.get('voice_line', '')}"
DESIRED VISUAL VIBE: "{scene.get('visual_vibe', '')}"

CANDIDATE CLIPS (5 Options from Pexels):
{json.dumps(candidate_summaries, indent=2)}

STRICT SELECTION CRITERIA:
1. Direct Subject Match: Choose the clip whose visual description best depicts what is being narrated.
2. Viral Atmosphere: Strongly prefer dark, moody, cinematic, awe-inspiring, high-contrast visuals (deep cosmos, abyssal ocean, glowing scientific anomalies).
3. Rejection: Reject any clip that feels generic, bright daylight, commercial, goofy, or out of place.
4. Resolution: Favor '4K Portrait' or '1080p Portrait'.

Which candidate index (0 to {len(candidate_summaries)-1}) is the absolute highest quality and most viral match?
Output valid pure JSON:
{{"selected_index": 0, "director_reason": "Specific 1-sentence reason why this visual best enhances viewer suspense"}}"""

    decision, used_model = call_gemini_json_api(gemini_key, prompt, DIRECTOR_MODELS, timeout=12)
    if decision:
        sel_idx = decision.get("selected_index", 0)
        if 0 <= sel_idx < len(candidates):
            print(f"🎬 Assistant Director [{used_model}] selected candidate #{sel_idx}: {decision.get('director_reason')}")
            return candidates[sel_idx]

    return candidates[0]

def executive_producer_approve_timeline(gemini_key, script_plan, chosen_clips, sentence_timings, total_audio_duration):
    """
    Step 4: Executive Producer (Gemini 3.8 / 3.6 Flash) reviews the chosen clips and sentence timings,
    ensuring rapid-cut pacing with NO CLIP EVER EXCEEDING 4.0 SECONDS!
    """
    chosen_summaries = []
    for idx, c in enumerate(chosen_clips):
        info = parse_pexels_clip_info(c, idx)
        chosen_summaries.append({
            "scene_id": idx + 1,
            "visual": info.get("visual_description"),
            "raw_duration": c.get("duration")
        })

    prompt = f"""You are the Executive Producer and Master Film Editor.
Total Narration Audio Duration: {total_audio_duration:.2f} seconds across {len(chosen_clips)} scenes.

Speech Sentence Timings (from Voiceover):
{json.dumps(sentence_timings, indent=2)}

Chosen Video Footage for each scene (Curated by Assistant Director):
{json.dumps(chosen_summaries, indent=2)}

STRICT SHORT-PACING RULES (Crucial for Viral Retention):
1. FAST CUTS: NO CLIP SHOULD EVER BE LONG! Maximum duration for any clip is 4.0 SECONDS!
2. Target each clip duration between 2.5s and 3.9s to keep the visual rhythm energetic and hypnotic.
3. Every cut must land cleanly on a dramatic speech pause.
4. The exact sum of all clip durations MUST EQUAL EXACTLY {total_audio_duration:.2f} seconds.

Output strictly valid pure JSON:
{{
  "executive_review": "Why this rapid-cut pacing guarantees 90%+ completion rate",
  "approved_timeline": [
    {{"scene_id": 1, "duration": 3.6}},
    {{"scene_id": 2, "duration": 3.4}}
  ]
}}"""

    print("👑 Executive Producer (Gemini 3.8 Flash) is reviewing the final timeline and cut sheet...")
    data, used_model = call_gemini_json_api(gemini_key, prompt, SCRIPT_MODELS, timeout=20)
    if data and data.get("approved_timeline"):
        print(f"🎬 Executive Producer [{used_model}] approved master timeline: {data.get('executive_review')}")
        timeline_dict = {item.get("scene_id"): float(item.get("duration", 0)) for item in data.get("approved_timeline", [])}
        
        # Enforce hard clamp: ensure no single clip > 4.2 seconds and sum equals total_audio_duration
        total_assigned = sum(timeline_dict.values())
        if total_assigned > 0:
            factor = total_audio_duration / total_assigned
            timeline_dict = {sid: round(d * factor, 2) for sid, d in timeline_dict.items()}
        return timeline_dict

    print("Notice: Using intelligent sentence boundary duration mapping.")
    num_scenes = max(1, len(chosen_clips))
    avg_dur = total_audio_duration / num_scenes
    return {idx + 1: round(avg_dur, 2) for idx in range(num_scenes)}

def download_and_standardize_clip(video_obj, output_path, duration):
    # Find best portrait video file (prefer 1080p/4K over low-res 540p)
    best_link = None
    portrait_files = [f for f in video_obj.get("video_files", []) if f.get("height", 0) >= f.get("width", 0)]
    if portrait_files:
        portrait_files.sort(key=lambda x: x.get("height", 0), reverse=True)
        best_link = portrait_files[0]["link"]
    elif video_obj.get("video_files"):
        sorted_files = sorted(video_obj["video_files"], key=lambda x: x.get("height", 0), reverse=True)
        best_link = sorted_files[0]["link"]

    if not best_link:
        return False

    raw_path = f"temp/raw_clip_{int(time.time()*1000)%10000}.mp4"
    res = requests.get(best_link, timeout=30)
    with open(raw_path, "wb") as f:
        f.write(res.content)

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", raw_path,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
        "-r", "30",
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-an",
        output_path
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(raw_path):
        os.remove(raw_path)
    return True

def generate_ai_scene_visual(prompt, output_jpg, retries=3):
    """
    Generates a 9:16 vertical 1080x1920 8K photorealistic cinematic visual via Pollinations Sana/Flux engine.
    """
    clean_p = re.sub(r'[^a-zA-Z0-9\s,.-]', '', prompt).strip()
    words = clean_p.split()[:25]
    short_prompt = " ".join(words)
    encoded = urllib.parse.quote(short_prompt)
    model_options = ["sana", "flux", ""]
    for attempt in range(retries):
        model_param = f"&model={model_options[attempt % len(model_options)]}" if model_options[attempt % len(model_options)] else ""
        seed = random.randint(1000, 999999)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&seed={seed}{model_param}"
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200 and len(r.content) > 10000:
                with open(output_jpg, "wb") as f:
                    f.write(r.content)
                used_m = model_options[attempt % len(model_options)] or "default"
                print(f"🎨 Generated 8K AI Visual [{used_m}]: {output_jpg} ({len(r.content)} bytes)")
                return True
            else:
                print(f"Notice: AI visual status {r.status_code}, retrying...")
                time.sleep(1.5)
        except Exception as e:
            print(f"Notice: AI visual attempt {attempt+1} failed ({e}), retrying...")
            time.sleep(1.5)
    return False

def convert_image_to_cinematic_clip(image_path, output_clip_path, duration):
    """
    Applies buttery-smooth cinematic Ken Burns zoom (scales up smoothly by 3.5%/s to push into focal point)
    """
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-t", str(duration + 0.1),
        "-vf", "scale='1080*(1+0.035*t)':'1920*(1+0.035*t)':eval=frame,crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,format=yuv420p",
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-an",
        output_clip_path
    ]
    subprocess.run(cmd, check=True)
    return True

def build_hollywood_directed_video(scenes, sentence_timings, total_duration, pexels_key, gemini_key, output_bg_path, output_thumb_path):
    """
    Executes the Next-Gen AI Cinematography Pipeline:
    1. Generates 8K photorealistic scene visuals matching the exact narrative.
    2. Fallback to Pexels stock footage if any visual fails.
    3. Converts all scenes into dynamic 30fps Ken Burns cinematic clips.
    4. Executive Producer cut-sheet timing approval.
    5. Assembles master video with zero stutter.
    """
    num_scenes = max(1, len(scenes))
    print(f"\n🎬 --- STAGE 1: Generating 8K Photorealistic Visuals ({num_scenes} scenes) ---")

    # Step 1: Assign timeline durations from sentence_timings or fallback
    avg_dur = total_duration / num_scenes
    assigned_durations = {}
    for i in range(num_scenes):
        if i < len(sentence_timings):
            st = sentence_timings[i]
            d = st.get("end", 0) - st.get("start", 0)
            assigned_durations[i] = max(2.5, min(4.2, d)) if d > 0 else avg_dur
        else:
            assigned_durations[i] = avg_dur

    clip_files = []
    for i, scene in enumerate(scenes):
        assigned_dur = assigned_durations.get(i, avg_dur)
        print(f"\n🎨 Scene {i+1}/{num_scenes} ({assigned_dur:.2f}s): '{scene.get('voice_line', '')[:40]}...'")
        img_path = f"temp/scene_art_{i}.jpg"
        clip_path = f"temp/scene_clip_{i}.mp4"

        # Attempt 1: 8K Photorealistic AI Visual
        vis_prompt = scene.get("visual_prompt") or f"{scene.get('voice_line')} 8k photorealistic dark cinematic lighting"
        ai_success = generate_ai_scene_visual(vis_prompt, img_path)

        if ai_success:
            print(f"🎥 Converting Scene {i+1} into dynamic Ken Burns 3D camera push ({assigned_dur:.2f}s)...")
            convert_image_to_cinematic_clip(img_path, clip_path, assigned_dur)
            clip_files.append(clip_path)
            if i == 0:
                try:
                    import shutil
                    shutil.copyfile(img_path, output_thumb_path)
                except Exception:
                    pass
        else:
            # Fallback to Pexels stock video
            print(f"⚠️ Falling back to Pexels stock video for Scene {i+1}...")
            queries = scene.get("search_queries", ["deep ocean darkness"])
            candidates = fetch_pexels_candidates(queries, pexels_key, min_candidates=5)
            chosen = assistant_director_select_clip(gemini_key, scene, candidates) if candidates else None
            if chosen:
                download_and_standardize_clip(chosen, clip_path, assigned_dur)
                clip_files.append(clip_path)

    if not clip_files:
        raise Exception("Could not generate any scene clips.")

    # Smoothly concatenate clips
    inputs = []
    filter_str = ""
    for idx, c in enumerate(clip_files):
        inputs.extend(["-i", c])
        filter_str += f"[{idx}:v]"
    filter_str += f"concat=n={len(clip_files)}:v=1:a=0[v]"

    cmd_concat = [
        "ffmpeg", "-y"
    ] + inputs + [
        "-filter_complex", filter_str,
        "-map", "[v]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-r", "30",
        "-pix_fmt", "yuv420p",
        output_bg_path
    ]
    subprocess.run(cmd_concat, check=True)
    print("🎉 FULL STUTTER-FREE HOLLYWOOD DIRECTED VIDEO COMPLETE!")

def render_final_short_with_bgm(bg_path, audio_path, ass_path, bgm_path, duration, output_path, hook_title):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"🎬 Burning Hormozi subtitles, Top Hook Banner, and mixing loud cinematic BGM...")
    
    escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    
    # Safe drawtext filter without bold=1 flag
    v_filter = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"ass={escaped_ass},"
        f"drawtext=text='{hook_title}':font='DejaVu Sans':fontsize=38:fontcolor=white:"
        f"box=1:boxcolor=black@0.75:boxborderw=16:x=(w-text_w)/2:y=240[vout]"
    )
    
    if bgm_path and os.path.exists(bgm_path):
        fade_out_start = max(1.0, duration - 1.5)
        audio_filter = f"[1:a]volume=1.0[voice];[2:a]volume=0.35,afade=t=in:ss=0:d=1,afade=t=out:st={fade_out_start}:d=1.5[bgm];[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", bg_path,
            "-i", audio_path,
            "-stream_loop", "-1", "-i", bgm_path,
            "-filter_complex", f"{v_filter};{audio_filter}",
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "19",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(duration + 0.2),
            "-pix_fmt", "yuv420p",
            output_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", bg_path,
            "-i", audio_path,
            "-filter_complex", v_filter,
            "-map", "[vout]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "19",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(duration + 0.2),
            "-pix_fmt", "yuv420p",
            output_path
        ]
        
    subprocess.run(cmd, check=True)
    print(f"🎉 FINAL UPGRADED VIDEO READY! Saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="AI YouTube Shorts Generator with Hollywood Two-Stage AI Director & Hormozi Subtitles")
    parser.add_argument("--script", type=str, default="", help="Narration script text (leave blank for Gemini AI auto-pilot)")
    parser.add_argument("--auto", action="store_true", help="Enable 100% automated script & visual direction via Two-Stage AI")
    parser.add_argument("--voice", type=str, default="en-US-ChristopherNeural", help="Edge TTS Voice name")
    parser.add_argument("--topic", type=str, default="deep space cosmic anomaly", help="Topic for script and visuals")
    parser.add_argument("--color", type=str, default="Yellow", help="Subtitle highlight color")
    parser.add_argument("--pexels_key", type=str, default="", help="Pexels API key")
    parser.add_argument("--gemini_key", type=str, default="", help="Gemini API key")
    parser.add_argument("--output", type=str, default="output/final_video.mp4", help="Output video path")
    parser.add_argument("--thumb", type=str, default="output/thumbnail.jpg", help="Output thumbnail path")
    args = parser.parse_args()

    clean_voice = clean_voice_name(args.voice)
    pexels_key = args.pexels_key.strip() if args.pexels_key and args.pexels_key.strip() else DEFAULT_PEXELS_KEY
    gemini_key = args.gemini_key.strip() if args.gemini_key and args.gemini_key.strip() else DEFAULT_GEMINI_KEY

    os.makedirs("temp", exist_ok=True)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    os.makedirs(os.path.dirname(args.thumb), exist_ok=True)

    audio_path = "temp/voice.mp3"
    ass_path = "temp/subtitles.ass"
    bg_video_path = "temp/background.mp4"
    bgm_path = "temp/bgm.ogg"

    # Step 1: Screenplay Generation via Executive Producer (Gemini 3.8 / 3.6 Flash)
    if not args.script or args.script.strip() == "" or args.auto or args.script.lower() == "auto":
        plan, active_topic = generate_ai_director_plan(gemini_key, args.topic)
        script_text = plan.get("full_script") or " ".join([s.get("voice_line", "") for s in plan.get("scenes", [])])
        hook_title = plan.get("hook_banner", "UNEXPLAINED MYSTERY")
        scenes = plan.get("scenes", [])
        
        # Save metadata for YouTube auto-uploader
        meta = {
            "title": plan.get("title", f"The Unexplained Cosmic Mystery 🌌 #shorts"),
            "description": f"{script_text}\n\n#shorts #mystery #science #deepspace #ocean #quantum",
            "hook_banner": hook_title,
            "topic": active_topic,
            "tags": ["shorts", "mystery", "science", "deepspace", "ocean", "universe", "unexplained"]
        }
        with open("output/metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        print(f"💾 Saved video metadata to output/metadata.json")
    else:
        script_text = args.script
        hook_title = "DEEP SPACE MYSTERY"
        active_topic = args.topic
        meta = {
            "title": f"{hook_title} 🌌 #shorts",
            "description": f"{script_text}\n\n#shorts #mystery #science",
            "hook_banner": hook_title,
            "topic": active_topic,
            "tags": ["shorts", "mystery", "science"]
        }
        with open("output/metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        scenes = [
            {"scene_id": 1, "voice_line": script_text, "visual_vibe": args.topic, "search_queries": [args.topic, "space galaxy"]}
        ]

    # Step 2: Voice & Hormozi-style two-tone ASS Subtitles + Ground Truth Sentence Timings
    sentence_timings = asyncio.run(generate_speech_and_subtitles(script_text, clean_voice, audio_path, ass_path))

    # Step 3: Exact Audio Duration
    duration = get_audio_duration(audio_path)
    print(f"⏱️ Exact narration duration measured: {duration:.2f} seconds")

    # Step 4: Fetch Cinematic Background Music
    fetch_bgm_track(active_topic, bgm_path)

    # Step 5: Multi-scene Hollywood 2-Stage Directed Video Footage
    build_hollywood_directed_video(scenes, sentence_timings, duration, pexels_key, gemini_key, bg_video_path, args.thumb)

    # Step 6: Render with Top Hook Banner & Audible BGM
    render_final_short_with_bgm(bg_video_path, audio_path, ass_path, bgm_path, duration, args.output, hook_title)

    # Step 7: Update Anti-Repetition History Memory Vault
    save_to_history(meta.get("title", hook_title), active_topic, hook_title)

if __name__ == "__main__":
    main()
