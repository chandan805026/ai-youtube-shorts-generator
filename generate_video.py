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

DEFAULT_PEXELS_KEY = "LgGZ2h14XBOQe9vuq4vgzmZpUT2WzvzbpltBDyDhEmcnDpHJ1xoMaaqQ"

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
    "MILLION", "BILLION", "LIGHT-YEARS", "BLACK", "HOLE", "SILENT", "SHOCK", "SECRETS"
}

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
    Active/Power words pop in Neon Green or Yellow, while base words are crisp White!
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
            
        # Find which word to highlight in Neon Green
        # Priority: power words, digits, or the longest word
        highlight_idx = -1
        for idx, w in enumerate(words):
            clean_w = re.sub(r'[^A-Z0-9]', '', w)
            if clean_w in POWER_WORDS or clean_w.isdigit():
                highlight_idx = idx
                break
        if highlight_idx == -1:
            # Highlight the longest word
            highlight_idx = max(range(len(words)), key=lambda i: len(words[i]))
            
        formatted_words = []
        for idx, w in enumerate(words):
            if idx == highlight_idx:
                # Neon Green: &H0000FF00
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

def fetch_pexels_video_clip(query, pexels_key, output_clip_path, duration):
    headers = {"Authorization": pexels_key.strip()}
    clean_q = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()
    encoded = urllib.parse.quote(clean_q)
    url = f"https://api.pexels.com/videos/search?query={encoded}&orientation=portrait&per_page=6"
    
    print(f"🔍 Searching Pexels for REAL video: '{clean_q}'...")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            videos = r.json().get("videos", [])
            if videos:
                best_link = None
                for v in videos:
                    for f in v.get("video_files", []):
                        if f.get("height", 0) > f.get("width", 0):
                            best_link = f["link"]
                            break
                    if best_link:
                        break
                
                if not best_link:
                    for v in videos:
                        if v.get("video_files"):
                            best_link = v["video_files"][0]["link"]
                            break
                            
                if best_link:
                    raw_dl = f"temp/raw_{clean_q[:8].replace(' ', '_')}.mp4"
                    print(f"📥 Downloading real moving footage from Pexels for '{clean_q}'...")
                    res = requests.get(best_link, timeout=30)
                    with open(raw_dl, "wb") as f:
                        f.write(res.content)
                    
                    cmd = [
                        "ffmpeg", "-y",
                        "-stream_loop", "-1",
                        "-i", raw_dl,
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
                        "-r", "30",
                        "-t", str(duration),
                        "-c:v", "libx264",
                        "-preset", "veryfast",
                        "-pix_fmt", "yuv420p",
                        "-an",
                        output_clip_path
                    ]
                    subprocess.run(cmd, check=True)
                    print(f"✅ Real moving clip processed ({duration:.1f}s at 30fps)!")
                    return True
    except Exception as e:
        print(f"Pexels fetch error for '{clean_q}': {e}")
    return False

def build_multi_scene_real_video(script_text, topic, total_duration, pexels_key, output_bg_path, output_thumb_path):
    lower_script = script_text.lower()
    
    if "void" in lower_script or "bootes" in lower_script or "mystery" in lower_script or "dark mystery" in topic.lower():
        queries = [
            "telescope night sky stars",
            "dark space galaxy void",
            "spiral galaxy spinning space",
            "futuristic sci fi technology",
            "black hole space mystery"
        ]
    elif "space" in lower_script or "universe" in lower_script or "black hole" in lower_script or "space" in topic.lower():
        queries = [
            "galaxy stars space",
            "earth from space orbit",
            "supernova nebula cosmos",
            "astronaut floating space",
            "black hole universe"
        ]
    elif "lion" in lower_script or "lion" in topic.lower():
        queries = ["lion walking in wild", "dense tropical jungle", "wild animals in savanna", "lion face close up"]
    elif "ocean" in lower_script or "sea" in lower_script:
        queries = ["deep ocean waves", "underwater marine life", "ocean aerial view", "coral reef"]
    elif "tech" in lower_script or "ai" in lower_script or "future" in lower_script:
        queries = ["cyberpunk futuristic city", "robot technology artificial intelligence", "digital cyber code network", "futuristic technology"]
    else:
        queries = [f"{topic}", f"{topic} cinematic", f"{topic} close up", f"{topic} landscape", f"{topic} 4k"]

    num_scenes = min(max(4, int(total_duration / 3.8)), len(queries))
    scene_dur = total_duration / num_scenes
    selected_queries = queries[:num_scenes]
    
    print(f"🎬 Creating {num_scenes} REAL MOVING video scenes (cutting every ~{scene_dur:.1f}s)...")
    
    clip_files = []
    for i, q in enumerate(selected_queries):
        clip_path = f"temp/smooth_clip_{i}.mp4"
        success = fetch_pexels_video_clip(q, pexels_key, clip_path, scene_dur + 0.1)
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
        raise Exception("Could not download clips from Pexels. Please check API key.")
        
    inputs = []
    filter_str = ""
    for i, c in enumerate(clip_files):
        inputs.extend(["-i", c])
        filter_str += f"[{i}:v]"
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
    print("🎉 FULL STUTTER-FREE MULTI-SCENE REAL MOVING FOOTAGE COMPLETE!")

def get_hook_title(script_text, topic):
    """Generates an engaging, clickable top banner title"""
    lower = script_text.lower()
    if "void" in lower or "bootes" in lower:
        return "⚠️  THE BOOTES VOID MYSTERY  ⚠️"
    elif "space" in lower or "black hole" in lower:
        return "🌌  DEEP SPACE SECRETS  🌌"
    elif "lion" in lower:
        return "🦁  WILD JUNGLE STORIES  🦁"
    elif "tech" in lower or "ai" in lower:
        return "🤖  FUTURE TECH 2050  🤖"
    return f"⚡  {topic.upper()}  ⚡"

def render_final_short_with_bgm(bg_path, audio_path, ass_path, bgm_path, duration, output_path, hook_title):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"🎬 Burning Hormozi subtitles, Top Hook Banner, and mixing loud cinematic BGM...")
    
    escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    
    # Visual filter: Scale/crop 1080x1920 -> Burn two-tone ASS subtitles -> Add top header badge
    v_filter = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"ass={escaped_ass},"
        f"drawtext=text='{hook_title}':font='DejaVu Sans':fontsize=36:fontcolor=white:bold=1:"
        f"box=1:boxcolor=black@0.75:boxborderw=14:x=(w-text_w)/2:y=240[vout]"
    )
    
    if bgm_path and os.path.exists(bgm_path):
        fade_out_start = max(1.0, duration - 1.5)
        # BGM volume boosted to 0.32 so it is clearly audible on mobile/laptop speakers!
        audio_filter = f"[1:a]volume=1.0[voice];[2:a]volume=0.32,afade=t=in:ss=0:d=1,afade=t=out:st={fade_out_start}:d=1.5[bgm];[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        
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
    parser = argparse.ArgumentParser(description="AI YouTube Shorts Real Video Generator with BGM & Hormozi Subtitles")
    parser.add_argument("--script", type=str, required=True, help="Narration script text")
    parser.add_argument("--voice", type=str, default="en-US-ChristopherNeural", help="Edge TTS Voice name")
    parser.add_argument("--topic", type=str, default="space", help="Background visual topic")
    parser.add_argument("--color", type=str, default="Yellow", help="Subtitle highlight color")
    parser.add_argument("--pexels_key", type=str, default="", help="Pexels API key")
    parser.add_argument("--output", type=str, default="output/final_video.mp4", help="Output video path")
    parser.add_argument("--thumb", type=str, default="output/thumbnail.jpg", help="Output thumbnail path")
    args = parser.parse_args()

    clean_voice = clean_voice_name(args.voice)
    pexels_key = args.pexels_key.strip() if args.pexels_key and args.pexels_key.strip() else DEFAULT_PEXELS_KEY

    os.makedirs("temp", exist_ok=True)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    os.makedirs(os.path.dirname(args.thumb), exist_ok=True)

    audio_path = "temp/voice.mp3"
    ass_path = "temp/subtitles.ass"
    bg_video_path = "temp/background.mp4"
    bgm_path = "temp/bgm.ogg"

    # Step 1: Voice & Hormozi-style two-tone ASS Subtitles
    asyncio.run(generate_speech_and_subtitles(args.script, clean_voice, audio_path, ass_path))

    # Step 2: Audio Duration
    duration = get_audio_duration(audio_path)

    # Step 3: Fetch Cinematic Background Music
    fetch_bgm_track(args.topic, bgm_path)

    # Step 4: Multi-scene REAL MOVING VIDEO FOOTAGE
    build_multi_scene_real_video(args.script, args.topic, duration, pexels_key, bg_video_path, args.thumb)

    # Step 5: Render with Top Hook Banner & Audible BGM
    hook_title = get_hook_title(args.script, args.topic)
    render_final_short_with_bgm(bg_video_path, audio_path, ass_path, bgm_path, duration, args.output, hook_title)

if __name__ == "__main__":
    main()
