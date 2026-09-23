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

import base64

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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
    with open(audio_output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                start_s = chunk["offset"] / 10_000_000
                end_s = start_s + (chunk["duration"] / 10_000_000)
                sentence_cues = split_sentence_into_cues(start_s, end_s, chunk["text"], max_words=3)
                cues.extend(sentence_cues)
                
    generate_hormozi_ass_subtitles(cues, ass_output_path)
    return len(cues)

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
        return 20.0

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
# 1. ✍️ Screenplay Writer : Gemini 3.8 Flash (Deep viral storytelling - 1 call)
# 2. 🎬 Visual Director    : Gemini 3.5 Flash Lite (High-speed 4K clip curator - 500 RPD)
# =========================================================================

SCRIPT_MODELS = [
    "gemini-3.8-flash",       # Top priority: Google's newest flagship for mind-bending scripts
    "gemini-3.6-flash",       # High-tier backup
    "gemini-3.5-flash-lite"   # Rock-solid backup
]

DIRECTOR_MODELS = [
    "gemini-3.5-flash-lite",  # Top priority: 500 RPD for lightning-fast clip curation
    "gemini-3.1-flash-lite"   # 500 RPD backup
]

def call_gemini_json_api(gemini_key, prompt, model_list, timeout=20):
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

def generate_ai_director_plan(gemini_key, topic="deep space mystery"):
    """
    Uses Gemini 3.8 Flash (Screenplay Specialist) to write an unforgettable viral script
    """
    prompt = f"""You are a master viral YouTube Shorts creator and director specializing in cosmic anomalies, space mysteries, and mind-bending astronomy for an American audience.
Create an unforgettable, high-retention 40-second space mystery short script on the topic: '{topic}'.
Requirements:
1. Hook (0-3s): Punchy, shocking first sentence that stops scrolling immediately.
2. 4 to 5 sequential scenes that build suspense to a chilling climax.
3. Each scene must have:
   - scene_id: 1, 2, ...
   - voice_line: Narration line for this scene (12-18 words, authentic dramatic American documentary style)
   - visual_vibe: Detailed visual description of what should be seen
   - search_queries: List of 2 Pexels search terms (2-3 words each, e.g. ['deep space galaxy', 'spiral vortex cosmic'])
4. hook_banner: 3-5 word uppercase text for the top banner (e.g. 'SCIENTISTS CANNOT EXPLAIN THIS')
5. title: Catchy YouTube Shorts title with emoji and #shorts
6. full_script: Complete voiceover script combining all scenes smoothly.

Output valid, pure JSON without any markdown formatting or extra text."""

    print(f"✍️ Screenplay Master (Gemini 3.8 Flash) is composing a viral script for: '{topic}'...")
    data, used_model = call_gemini_json_api(gemini_key, prompt, SCRIPT_MODELS, timeout=25)
    if data:
        print(f"✨ Masterpiece Script written by: [{used_model}]")
        print(f"🎬 Title: {data.get('title')}")
        print(f"📌 Hook Banner: {data.get('hook_banner')}")
        print(f"📜 Generated {len(data.get('scenes', []))} sequential scenes.")
        return data

    print("⚠️ Falling back to curated high-retention space mystery plan.")
    return FALLBACK_PLANS[0]

def director_select_best_clip(gemini_key, scene, candidates):
    """
    Uses Gemini 3.5 Flash Lite (Visual Director - 500 RPD) to curate and approve footage
    """
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    candidate_summaries = []
    for idx, c in enumerate(candidates[:3]):
        candidate_summaries.append({
            "candidate_index": idx,
            "url": c.get("url"),
            "tags": c.get("tags", []),
            "duration": c.get("duration"),
            "author": c.get("user", {}).get("name")
        })

    prompt = f"""You are the Lead Visual Director for a cinematic space documentary Short.
Scene Narration: "{scene.get('voice_line', '')}"
Desired Visual Mood: "{scene.get('visual_vibe', '')}"

Candidate Clips from Pexels:
{json.dumps(candidate_summaries, indent=2)}

Select the best candidate clip index (0 to {len(candidate_summaries)-1}) that has the most cinematic, eerie, and accurate visual atmosphere.
Output JSON:
{{"selected_index": 0, "director_reason": "Brief reason for selection"}}"""

    decision, used_model = call_gemini_json_api(gemini_key, prompt, DIRECTOR_MODELS, timeout=12)
    if decision:
        sel_idx = decision.get("selected_index", 0)
        if 0 <= sel_idx < len(candidates):
            print(f"🎬 Visual Director [{used_model}] selected candidate #{sel_idx}: {decision.get('director_reason')}")
            return candidates[sel_idx]

    return candidates[0]

def fetch_pexels_candidates(queries, pexels_key):
    headers = {"Authorization": pexels_key.strip()}
    candidates = []
    seen_ids = set()

    for q in queries:
        clean_q = re.sub(r'[^a-zA-Z0-9\s]', '', q).strip()
        encoded = urllib.parse.quote(clean_q)
        url = f"https://api.pexels.com/videos/search?query={encoded}&orientation=portrait&per_page=4"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                videos = r.json().get("videos", [])
                for v in videos:
                    vid = v.get("id")
                    if vid and vid not in seen_ids:
                        seen_ids.add(vid)
                        candidates.append(v)
            if len(candidates) >= 4:
                break
        except Exception as e:
            print(f"Pexels search error for '{q}': {e}")

    return candidates

def download_and_standardize_clip(video_obj, output_path, duration):
    # Find best portrait video file
    best_link = None
    for f in video_obj.get("video_files", []):
        if f.get("height", 0) > f.get("width", 0):
            best_link = f["link"]
            break
    if not best_link and video_obj.get("video_files"):
        best_link = video_obj["video_files"][0]["link"]

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

def build_ai_directed_multi_scene_video(scenes, total_duration, pexels_key, gemini_key, output_bg_path, output_thumb_path):
    num_scenes = max(1, len(scenes))
    scene_dur = total_duration / num_scenes
    print(f"🎬 Assembling {num_scenes} AI-Directed moving scenes (cutting every ~{scene_dur:.1f}s)...")

    clip_files = []
    for i, scene in enumerate(scenes):
        print(f"\n--- Scene {i+1}/{num_scenes}: '{scene.get('voice_line', '')[:40]}...' ---")
        queries = scene.get("search_queries", ["space galaxy"])
        candidates = fetch_pexels_candidates(queries, pexels_key)

        chosen_clip = director_select_best_clip(gemini_key, scene, candidates)
        if not chosen_clip:
            print("⚠️ No candidate found, using fallback search 'space universe'")
            candidates = fetch_pexels_candidates(["space universe", "galaxy nebula"], pexels_key)
            chosen_clip = candidates[0] if candidates else None

        if chosen_clip:
            clip_path = f"temp/scene_clip_{i}.mp4"
            success = download_and_standardize_clip(chosen_clip, clip_path, scene_dur + 0.1)
            if success:
                clip_files.append(clip_path)
                if i == 0:
                    cmd_thumb = [
                        "ffmpeg", "-y",
                        "-ss", "00:00:01",
                        "-i", clip_path,
                        "-vframes", "1",
                        output_thumb_path
                    ]
                    subprocess.run(cmd_thumb, check=False)

    if not clip_files:
        raise Exception("Could not download any approved clips. Please check Pexels API key.")

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
    print("🎉 FULL STUTTER-FREE AI-DIRECTED MULTI-SCENE VIDEO COMPLETE!")

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
    parser = argparse.ArgumentParser(description="AI YouTube Shorts Generator with Gemini 3.6 Flash Director & Hormozi Subtitles")
    parser.add_argument("--script", type=str, default="", help="Narration script text (leave blank for Gemini AI auto-pilot)")
    parser.add_argument("--auto", action="store_true", help="Enable 100% automated script & visual direction via Gemini 3.6 Flash")
    parser.add_argument("--voice", type=str, default="en-US-ChristopherNeural", help="Edge TTS Voice name")
    parser.add_argument("--topic", type=str, default="deep space mystery", help="Topic for script and visuals")
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

    # Step 1: Script & Scene Generation via Gemini 3.6 Flash
    if not args.script or args.script.strip() == "" or args.auto or args.script.lower() == "auto":
        plan = generate_ai_director_plan(gemini_key, args.topic)
        script_text = plan.get("full_script") or " ".join([s.get("voice_line", "") for s in plan.get("scenes", [])])
        hook_title = plan.get("hook_banner", "DEEP SPACE MYSTERY")
        scenes = plan.get("scenes", [])
        
        # Save metadata for YouTube auto-uploader
        meta = {
            "title": plan.get("title", f"Mysteries of Deep Space 🌌 #shorts"),
            "description": f"{script_text}\n\n#shorts #space #mystery #cosmic #astronomy #science",
            "hook_banner": hook_title,
            "tags": ["shorts", "space", "astronomy", "mystery", "science", "nasa", "universe"]
        }
        with open("output/metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        print(f"💾 Saved video metadata to output/metadata.json")
    else:
        script_text = args.script
        hook_title = "DEEP SPACE MYSTERY"
        scenes = [
            {"scene_id": 1, "voice_line": script_text, "visual_vibe": args.topic, "search_queries": [args.topic, "space galaxy"]}
        ]

    # Step 2: Voice & Hormozi-style two-tone ASS Subtitles
    asyncio.run(generate_speech_and_subtitles(script_text, clean_voice, audio_path, ass_path))

    # Step 3: Audio Duration
    duration = get_audio_duration(audio_path)

    # Step 4: Fetch Cinematic Background Music
    fetch_bgm_track(args.topic, bgm_path)

    # Step 5: Multi-scene AI-DIRECTED REAL MOVING VIDEO FOOTAGE
    build_ai_directed_multi_scene_video(scenes, duration, pexels_key, gemini_key, bg_video_path, args.thumb)

    # Step 6: Render with Top Hook Banner & Audible BGM
    render_final_short_with_bgm(bg_video_path, audio_path, ass_path, bgm_path, duration, args.output, hook_title)

if __name__ == "__main__":
    main()
