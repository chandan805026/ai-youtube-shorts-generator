import asyncio
import os
import sys
import argparse
import subprocess
import requests
import json
import re
import urllib.parse

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

    chunks = []
    curr_chunk = []
    
    for w in words:
        curr_chunk.append(w)
        if len(curr_chunk) >= max_words_per_chunk or any(curr_chunk[-1]["text"].endswith(p) for p in [".", "!", "?", ","]):
            chunks.append(curr_chunk)
            curr_chunk = []
    if curr_chunk:
        chunks.append(curr_chunk)

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
        return 20.0

def fetch_ai_image(prompt_text, output_img_path):
    """Fetches high quality 9:16 vertical AI image from Pollinations (100% Free, No Key)"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    # Enhance prompt for high quality photorealistic cinematic 9:16 visual
    clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', prompt_text).strip()
    enhanced_prompt = f"cinematic 4k photorealistic vertical {clean[:75]} masterpiece dramatic lighting 9:16"
    encoded = urllib.parse.quote(enhanced_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&nologo=true"
    
    print(f"🎨 Generating AI Visual: {enhanced_prompt[:60]}...")
    try:
        r = requests.get(url, headers=headers, timeout=25)
        if r.status_code == 200 and len(r.content) > 10000:
            with open(output_img_path, "wb") as f:
                f.write(r.content)
            print("✅ AI Image generated successfully!")
            return True
    except Exception as e:
        print(f"Pollinations fetch failed: {e}")
    return False

def create_animated_scene_clip(image_path, duration, output_clip_path, zoom_in=True):
    """
    Turns a still AI image into a smooth cinematic Ken-Burns camera motion video clip (1080x1920 30fps)
    """
    total_frames = int(duration * 30) + 10
    zoom_expr = "min(zoom+0.0012,1.25)" if zoom_in else "max(1.25-0.0012*on,1.0)"
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", f"scale=1920:3413,zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30",
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        output_clip_path
    ]
    subprocess.run(cmd, check=True)

def generate_multi_scene_background(script_text, topic, total_duration, output_bg_path):
    """
    Analyzes script, breaks into 2-3 visual scenes, creates AI images with cinematic motion,
    and concatenates into full vertical background video.
    """
    # Split script into sentences
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', script_text) if len(s.strip()) > 5]
    
    # Target 2 to 3 scenes (each 5-7 seconds)
    if not sentences:
        sentences = [script_text]
        
    num_scenes = min(max(2, int(total_duration / 6)), 3)
    if len(sentences) < num_scenes:
        # duplicate or supplement with topic
        sentences.append(f"{topic} cinematic view")
    
    selected_scenes = sentences[:num_scenes]
    scene_duration = total_duration / len(selected_scenes)
    
    print(f"🎬 Creating {len(selected_scenes)} cinematic AI scenes (each ~{scene_duration:.1f}s)...")
    
    clip_files = []
    last_valid_img = None
    
    for i, scene in enumerate(selected_scenes):
        img_path = f"temp/scene_{i}.jpg"
        clip_path = f"temp/scene_{i}.mp4"
        
        success = fetch_ai_image(f"{scene} {topic}", img_path)
        if not success:
            if last_valid_img and os.path.exists(last_valid_img):
                img_path = last_valid_img
            else:
                # Fallback to topic search
                fetch_ai_image(f"cinematic {topic} landscape", img_path)
        
        last_valid_img = img_path
        zoom_direction = (i % 2 == 0) # Alternate zoom in and zoom out
        create_animated_scene_clip(img_path, scene_duration + 0.2, clip_path, zoom_in=zoom_direction)
        clip_files.append(clip_path)

    # Concat clips
    if len(clip_files) == 1:
        os.replace(clip_files[0], output_bg_path)
    else:
        concat_list = "temp/concat_list.txt"
        with open(concat_list, "w") as f:
            for c in clip_files:
                f.write(f"file '{os.path.abspath(c)}'\n")
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            output_bg_path
        ]
        subprocess.run(cmd, check=True)
    print("✅ Full multi-scene cinematic background ready!")

def render_final_short(bg_path, audio_path, ass_path, duration, output_path):
    """
    Assembles background video, audio, and burned subtitles into a 1080x1920 9:16 vertical MP4.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"🎬 Rendering final 1080x1920 video with burned subtitles (Duration: {duration:.2f}s)...")
    
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

    # Step 4: Multi-scene Cinematic AI Background
    generate_multi_scene_background(args.script, args.topic, duration, bg_video_path)

    # Step 5: Render Final Video
    render_final_short(bg_video_path, audio_path, ass_path, duration, args.output)

if __name__ == "__main__":
    main()
