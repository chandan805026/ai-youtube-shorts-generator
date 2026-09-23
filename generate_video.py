import asyncio
import os
import sys
import argparse
import subprocess
import requests
import json
import re

# Curated High-Definition Royalty-Free Public Direct Video URLs (Fallback if no Pexels key is provided)
CURATED_BACKGROUNDS = {
    "space": [
        "https://assets.mixkit.co/videos/preview/mixkit-stars-in-space-1610-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-galaxy-with-bright-stars-41618-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-flight-through-a-starfield-in-space-32988-large.mp4"
    ],
    "galaxy": [
        "https://assets.mixkit.co/videos/preview/mixkit-stars-in-space-1610-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-galaxy-with-bright-stars-41618-large.mp4"
    ],
    "dark mystery": [
        "https://assets.mixkit.co/videos/preview/mixkit-smoke-floating-in-the-dark-42468-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-waves-in-the-water-1164-large.mp4"
    ],
    "technology": [
        "https://assets.mixkit.co/videos/preview/mixkit-tunnel-of-futuristic-neon-lights-42527-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-digital-animation-of-screens-with-code-31911-large.mp4"
    ],
    "future city": [
        "https://assets.mixkit.co/videos/preview/mixkit-tunnel-of-futuristic-neon-lights-42527-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-traffic-at-night-in-the-city-4318-large.mp4"
    ],
    "nature": [
        "https://assets.mixkit.co/videos/preview/mixkit-aerial-view-of-waves-crashing-on-a-rocky-beach-41527-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-waterfall-in-forest-2213-large.mp4"
    ],
    "ocean": [
        "https://assets.mixkit.co/videos/preview/mixkit-aerial-view-of-waves-crashing-on-a-rocky-beach-41527-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-waves-in-the-water-1164-large.mp4"
    ],
    "finance": [
        "https://assets.mixkit.co/videos/preview/mixkit-traffic-at-night-in-the-city-4318-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-digital-animation-of-screens-with-code-31911-large.mp4"
    ]
}

def clean_voice_name(voice_input):
    """Extract standard voice ID if friendly name was selected"""
    if " " in voice_input:
        return voice_input.split(" ")[0].strip()
    return voice_input.strip()

async def generate_speech_and_words(script_text, voice_id, audio_output_path):
    """Uses edge_tts to generate natural human voice and word-level timestamps"""
    import edge_tts
    print(f"🎙️ Generating voiceover using voice: {voice_id}...")
    communicate = edge_tts.Communicate(script_text, voice_id)
    
    words = []
    with open(audio_output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "start": chunk["offset"] / 10_000_000,
                    "duration": chunk["duration"] / 10_000_000,
                    "text": chunk["text"]
                })
    print(f"✅ Voiceover generated! ({len(words)} words detected)")
    return words

def format_ass_time(seconds):
    """Formats float seconds into ASS subtitle time: H:MM:SS.CC"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis == 100:
        secs += 1
        centis = 0
    return f"{hrs:d}:{mins:02d}:{secs:02d}.{centis:02d}"

def create_ass_subtitles(words, ass_path, color_name="Yellow", max_words_per_chunk=3):
    """
    Creates eye-catching, modern, punchy centered subtitles (Hormozi / Shorts style).
    Groups words into punchy 2-4 word bursts with high-contrast outline.
    """
    color_map = {
        "Yellow": "&H0000FFFF",
        "White": "&H00FFFFFF",
        "Cyan": "&H00FFFF00",
        "Green": "&H0000FF00"
    }
    primary_color = color_map.get(color_name, "&H0000FFFF")

    # Group words into short chunks
    chunks = []
    curr_chunk = []
    
    for w in words:
        curr_chunk.append(w)
        # Split chunk if reaches word limit or sentence end punctuation
        if len(curr_chunk) >= max_words_per_chunk or any(curr_chunk[-1]["text"].endswith(p) for p in [".", "!", "?", ","]):
            chunks.append(curr_chunk)
            curr_chunk = []
    if curr_chunk:
        chunks.append(curr_chunk)

    # Build ASS content
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,62,{primary_color},&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,2,40,40,780,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for chunk in chunks:
        start_time = format_ass_time(chunk[0]["start"])
        end_time = format_ass_time(chunk[-1]["start"] + chunk[-1]["duration"] + 0.15)
        text = " ".join([w["text"].upper() for w in chunk])
        # Escape curly braces
        text = text.replace("{", "").replace("}", "")
        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
    print(f"✅ Styled ASS Subtitles created: {ass_path}")

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
        return 30.0

def fetch_background_video(topic, pexels_api_key, output_video_path):
    """
    Downloads high quality portrait background video.
    First tries Pexels if API key is given, else uses curated high quality CDN clips,
    and falls back to procedural FFmpeg generation if offline.
    """
    # 1. Try Pexels if API key exists
    if pexels_api_key and pexels_api_key.strip():
        print(f"🔍 Searching Pexels for topic '{topic}'...")
        headers = {"Authorization": pexels_api_key.strip()}
        url = f"https://api.pexels.com/videos/search?query={topic}&orientation=portrait&per_page=10"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                videos = data.get("videos", [])
                if videos:
                    # Pick a suitable HD video file
                    for v in videos:
                        for vf in v.get("video_files", []):
                            if vf.get("width") and vf.get("height") and vf["height"] > vf["width"]:
                                video_url = vf["link"]
                                print(f"📥 Downloading video from Pexels: {video_url[:60]}...")
                                vid_data = requests.get(video_url, timeout=30)
                                with open(output_video_path, "wb") as f:
                                    f.write(vid_data.content)
                                print("✅ Pexels background downloaded successfully!")
                                return True
        except Exception as e:
            print(f"Pexels fetch failed ({e}), falling back to curated library.")

    # 2. Try curated CDN loops
    topic_key = topic.lower().strip()
    urls = CURATED_BACKGROUNDS.get(topic_key) or CURATED_BACKGROUNDS.get("space")
    for u in urls:
        try:
            print(f"📥 Fetching background loop for '{topic_key}': {u}...")
            res = requests.get(u, timeout=20)
            if res.status_code == 200 and len(res.content) > 100000:
                with open(output_video_path, "wb") as f:
                    f.write(res.content)
                print("✅ Royalty-free background video downloaded!")
                return True
        except Exception as e:
            print(f"Failed to fetch {u}: {e}")

    # 3. Ultimate Fallback: Procedural Sci-Fi animated background via FFmpeg
    print("🎨 Generating procedural dynamic background with FFmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "gradients=s=1080x1920:c0=0x0d0d1a:c1=0x38124d:c2=0x0a1c3d:speed=0.01:r=30",
        "-t", "30",
        "-pix_fmt", "yuv420p",
        output_video_path
    ]
    subprocess.run(cmd, check=True)
    print("✅ Procedural background generated!")
    return True

def render_final_short(bg_path, audio_path, ass_path, duration, output_path):
    """
    Assembles background video, audio, and burned subtitles into a 1080x1920 9:16 vertical MP4.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"🎬 Rendering final 1080x1920 video (Duration: {duration:.2f}s)...")
    
    # FFmpeg command to loop background, crop to 1080x1920, burn ASS subtitles, and sync audio
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", bg_path,
        "-i", audio_path,
        "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,ass={ass_path}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(duration + 0.3),
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]
    
    subprocess.run(cmd, check=True)
    print(f"🎉 FINAL VIDEO READY! Saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="AI YouTube Shorts Video Generator")
    parser.add_argument("--script", type=str, required=True, help="Narration script text")
    parser.add_argument("--voice", type=str, default="en-US-ChristopherNeural", help="Edge TTS Voice name")
    parser.add_argument("--topic", type=str, default="space", help="Background visual topic/theme")
    parser.add_argument("--color", type=str, default="Yellow", help="Subtitle highlight color")
    parser.add_argument("--pexels_key", type=str, default="", help="Optional Pexels API key")
    parser.add_argument("--output", type=str, default="output/final_video.mp4", help="Output path")
    args = parser.parse_args()

    clean_voice = clean_voice_name(args.voice)
    os.makedirs("temp", exist_ok=True)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    audio_path = "temp/voice.mp3"
    ass_path = "temp/subtitles.ass"
    bg_video_path = "temp/background.mp4"

    # Step 1: Voice & word timings
    words = asyncio.run(generate_speech_and_words(args.script, clean_voice, audio_path))

    # Step 2: ASS Subtitles
    create_ass_subtitles(words, ass_path, color_name=args.color)

    # Step 3: Exact Audio Duration
    duration = get_audio_duration(audio_path)

    # Step 4: Background Video
    fetch_background_video(args.topic, args.pexels_key, bg_video_path)

    # Step 5: Render Final Video
    render_final_short(bg_video_path, audio_path, ass_path, duration, args.output)

if __name__ == "__main__":
    main()
