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

# Default verified Pexels API Key
DEFAULT_PEXELS_KEY = "LgGZ2h14XBOQe9vuq4vgzmZpUT2WzvzbpltBDyDhEmcnDpHJ1xoMaaqQ"

def clean_voice_name(voice_input):
    """Extract standard voice ID if friendly name was selected"""
    if " " in voice_input:
        return voice_input.split(" ")[0].strip()
    return voice_input.strip()

def split_sentence_into_cues(start_s, end_s, text, max_words=3):
    """Splits a sentence into punchy 2-3 word subtitle cues with interpolated timings"""
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

def format_srt_time(sec):
    """Formats float seconds into SRT timestamp HH:MM:SS,mmm"""
    hrs = int(sec // 3600)
    mins = int((sec % 3600) // 60)
    secs = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms >= 1000:
        secs += 1
        ms = 0
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

async def generate_speech_and_subtitles(script_text, voice_id, audio_output_path, srt_output_path):
    """Uses edge_tts to generate realistic audio and precise word-chunk SRT subtitles"""
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
                
    with open(srt_output_path, "w", encoding="utf-8") as f:
        for i, (s, e, t) in enumerate(cues):
            f.write(f"{i+1}\n{format_srt_time(s)} --> {format_srt_time(e)}\n{t}\n\n")
            
    print(f"✅ Voiceover generated! ({len(cues)} punchy subtitle cues created)")
    return len(cues)

def get_audio_duration(audio_path):
    """Gets exact duration of the audio file via ffprobe"""
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

def fetch_pexels_video_clip(query, pexels_key, output_clip_path, duration):
    """Searches Pexels for a real moving HD video clip and trims it to duration"""
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
                # Find best video file
                best_link = None
                for v in videos:
                    for f in v.get("video_files", []):
                        # Prefer HD portrait (height >= 1080 and height > width)
                        if f.get("height", 0) > f.get("width", 0):
                            best_link = f["link"]
                            break
                    if best_link:
                        break
                
                # If no strict portrait file, take any high resolution video
                if not best_link:
                    for v in videos:
                        if v.get("video_files"):
                            best_link = v["video_files"][0]["link"]
                            break
                            
                if best_link:
                    raw_dl = "temp/raw_download.mp4"
                    print(f"📥 Downloading real moving footage from Pexels...")
                    res = requests.get(best_link, timeout=30)
                    with open(raw_dl, "wb") as f:
                        f.write(res.content)
                    
                    # Process and crop into 1080x1920 portrait with exact duration
                    cmd = [
                        "ffmpeg", "-y",
                        "-stream_loop", "-1",
                        "-i", raw_dl,
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                        "-t", str(duration),
                        "-c:v", "libx264",
                        "-preset", "veryfast",
                        "-pix_fmt", "yuv420p",
                        "-an",
                        output_clip_path
                    ]
                    subprocess.run(cmd, check=True)
                    print(f"✅ Real moving clip processed ({duration:.1f}s)!")
                    return True
    except Exception as e:
        print(f"Pexels fetch error for '{clean_q}': {e}")
    return False

def build_multi_scene_real_video(script_text, topic, total_duration, pexels_key, output_bg_path, output_thumb_path):
    """
    Builds a dynamic real-footage video by cutting multiple real moving video clips from Pexels every 3-5 seconds!
    """
    # Define smart sequential search queries based on the script and topic
    queries = []
    lower_script = script_text.lower()
    
    if "lion" in lower_script or "lion" in topic.lower():
        queries = ["lion walking in wild", "dense tropical jungle", "wild animals in savanna", "lion face close up"]
    elif "space" in lower_script or "black hole" in lower_script or "space" in topic.lower():
        queries = ["galaxy stars in space", "black hole cosmos", "earth from space orbit", "nebula universe"]
    elif "ocean" in lower_script or "sea" in lower_script:
        queries = ["deep ocean waves", "underwater marine life", "ocean aerial view", "coral reef"]
    elif "tech" in lower_script or "ai" in lower_script or "future" in lower_script:
        queries = ["cyberpunk futuristic city", "robot technology artificial intelligence", "digital cyber code network"]
    else:
        queries = [f"{topic}", f"{topic} cinematic", f"{topic} close up", f"{topic} landscape"]

    # Target 3-4 scenes
    num_scenes = min(max(3, int(total_duration / 4.5)), len(queries))
    scene_dur = total_duration / num_scenes
    selected_queries = queries[:num_scenes]
    
    print(f"🎬 Creating {num_scenes} REAL MOVING video scenes from Pexels (each ~{scene_dur:.1f}s)...")
    
    clip_files = []
    for i, q in enumerate(selected_queries):
        clip_path = f"temp/real_clip_{i}.mp4"
        success = fetch_pexels_video_clip(q, pexels_key, clip_path, scene_dur + 0.2)
        if success:
            clip_files.append(clip_path)
            # Capture first frame of first clip as thumbnail
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
        
    # Concatenate all real moving clips into one continuous video
    concat_list = "temp/real_concat.txt"
    with open(concat_list, "w") as f:
        for c in clip_files:
            f.write(f"file '{os.path.abspath(c)}'\n")
            
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        output_bg_path
    ]
    subprocess.run(cmd_concat, check=True)
    print("🎉 FULL REAL-FOOTAGE MULTI-SCENE BACKGROUND COMPLETE!")

def render_final_short(bg_path, audio_path, srt_path, duration, output_path, color_name="Yellow"):
    """
    Assembles real moving footage, voiceover, and burns high-visibility bold yellow/white subtitles.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"🎬 Burning bold subtitles and syncing audio onto REAL footage (Duration: {duration:.2f}s)...")
    
    color_map = {
        "Yellow": "&H0000FFFF",
        "White": "&H00FFFFFF",
        "Cyan": "&H00FFFF00",
        "Green": "&H0000FF00"
    }
    primary_color = color_map.get(color_name, "&H0000FFFF")
    
    escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")
    subtitle_style = f"Fontname=DejaVu Sans,Fontsize=22,PrimaryColour={primary_color},OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=2,Alignment=2,MarginV=160,Bold=1"
    
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", bg_path,
        "-i", audio_path,
        "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,subtitles={escaped_srt}:force_style='{subtitle_style}'",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "19",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(duration + 0.2),
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]
    
    subprocess.run(cmd, check=True)
    print(f"🎉 FINAL VIDEO READY! Saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="AI YouTube Shorts Real Video Generator")
    parser.add_argument("--script", type=str, required=True, help="Narration script text")
    parser.add_argument("--voice", type=str, default="en-US-ChristopherNeural", help="Edge TTS Voice name")
    parser.add_argument("--topic", type=str, default="nature", help="Background visual topic")
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
    srt_path = "temp/subtitles.srt"
    bg_video_path = "temp/background.mp4"

    # Step 1: Voice & punchy SRT Subtitles
    asyncio.run(generate_speech_and_subtitles(args.script, clean_voice, audio_path, srt_path))

    # Step 2: Audio Duration
    duration = get_audio_duration(audio_path)

    # Step 3: Multi-scene REAL MOVING VIDEO FOOTAGE from Pexels
    build_multi_scene_real_video(args.script, args.topic, duration, pexels_key, bg_video_path, args.thumb)

    # Step 4: Final Assembly & Burned Subtitles
    render_final_short(bg_video_path, audio_path, srt_path, duration, args.output, color_name=args.color)

if __name__ == "__main__":
    main()
