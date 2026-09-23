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

def clean_voice_name(voice_input):
    """Extract standard voice ID if friendly name was selected"""
    if " " in voice_input:
        return voice_input.split(" ")[0].strip()
    return voice_input.strip()

def split_sentence_into_cues(start_s, end_s, text, max_words=3):
    """Splits a long sentence into punchy 2-3 word subtitle cues with interpolated timings"""
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
                
    # Write SRT file
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

def fetch_ai_image(prompt_text, output_img_path):
    """Fetches high quality 9:16 vertical AI image from Pollinations with retry"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', prompt_text).strip()
    enhanced_prompt = f"cinematic 4k photorealistic vertical {clean[:80]} epic lighting highly detailed masterpiece 9:16"
    encoded = urllib.parse.quote(enhanced_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&nologo=true"
    
    print(f"🎨 Generating AI Image: {enhanced_prompt[:65]}...")
    for attempt in range(2):
        try:
            r = requests.get(url, headers=headers, timeout=25)
            if r.status_code == 200 and len(r.content) > 10000:
                with open(output_img_path, "wb") as f:
                    f.write(r.content)
                print("✅ AI Image generated successfully!")
                return True
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}. Retrying...")
            time.sleep(2)
    return False

def create_animated_scene_clip(image_path, duration, output_clip_path, zoom_in=True):
    """
    Turns a still AI image into a smooth cinematic Ken-Burns camera motion video clip.
    Crucial: d parameter must equal total frame count so zoom runs across the whole clip!
    """
    total_frames = max(30, int(duration * 30) + 15)
    
    if zoom_in:
        # Smooth slow zoom in from 1.0 to 1.25
        zoom_expr = "min(zoom+0.0012,1.25)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    else:
        # Smooth slow pan & zoom
        zoom_expr = "min(1.05+0.0010*on,1.25)"
        x_expr = "iw/2-(iw/zoom/2)+sin(on/25)*30"
        y_expr = "ih/2-(ih/zoom/2)"
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", f"scale=1920:3413,zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s=1080x1920:fps=30",
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        output_clip_path
    ]
    subprocess.run(cmd, check=True)

def generate_multi_scene_background(script_text, topic, total_duration, output_bg_path, output_thumb_path):
    """
    Creates dynamic animated background video with 1-2 photorealistic AI scenes.
    """
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', script_text) if len(s.strip()) > 5]
    if not sentences:
        sentences = [script_text]
        
    num_scenes = 2 if total_duration > 7.0 and len(sentences) > 1 else 1
    scene_dur = total_duration / num_scenes
    
    clip_files = []
    
    # Scene 1: Main Subject / Hero Scene
    hero_prompt = f"{sentences[0]} {topic}"
    hero_img = "temp/scene_0.jpg"
    success = fetch_ai_image(hero_prompt, hero_img)
    if not success:
        # Fallback prompt
        fetch_ai_image(f"cinematic {topic} landscape dramatic lighting", hero_img)
    
    # Save hero image as thumbnail for the web player
    if os.path.exists(hero_img):
        import shutil
        shutil.copyfile(hero_img, output_thumb_path)
        
    clip_0 = "temp/scene_0.mp4"
    create_animated_scene_clip(hero_img, scene_dur + 0.3, clip_0, zoom_in=True)
    clip_files.append(clip_0)
    
    # Scene 2 (if video is longer)
    if num_scenes > 1:
        scene_1_prompt = f"{sentences[-1]} {topic}"
        scene_1_img = "temp/scene_1.jpg"
        success2 = fetch_ai_image(scene_1_prompt, scene_1_img)
        if not success2:
            scene_1_img = hero_img # reuse hero image with different motion
            
        clip_1 = "temp/scene_1.mp4"
        create_animated_scene_clip(scene_1_img, scene_dur + 0.3, clip_1, zoom_in=False)
        clip_files.append(clip_1)

    if len(clip_files) == 1:
        import shutil
        shutil.copyfile(clip_files[0], output_bg_path)
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
    print("✅ Multi-scene animated background generated!")

def render_final_short(bg_path, audio_path, srt_path, duration, output_path, color_name="Yellow"):
    """
    Assembles background video, voice, and burns high-visibility bold yellow/white subtitles.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"🎬 Rendering final 1080x1920 video with burned subtitles (Duration: {duration:.2f}s)...")
    
    color_map = {
        "Yellow": "&H0000FFFF",
        "White": "&H00FFFFFF",
        "Cyan": "&H00FFFF00",
        "Green": "&H0000FF00"
    }
    primary_color = color_map.get(color_name, "&H0000FFFF")
    
    # Escape path for ffmpeg filter
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
        "-crf", "20",
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
    parser = argparse.ArgumentParser(description="AI YouTube Shorts Video Generator")
    parser.add_argument("--script", type=str, required=True, help="Narration script text")
    parser.add_argument("--voice", type=str, default="en-US-ChristopherNeural", help="Edge TTS Voice name")
    parser.add_argument("--topic", type=str, default="nature", help="Background visual topic")
    parser.add_argument("--color", type=str, default="Yellow", help="Subtitle highlight color")
    parser.add_argument("--pexels_key", type=str, default="", help="Optional Pexels API key")
    parser.add_argument("--output", type=str, default="output/final_video.mp4", help="Output video path")
    parser.add_argument("--thumb", type=str, default="output/thumbnail.jpg", help="Output thumbnail path")
    args = parser.parse_args()

    clean_voice = clean_voice_name(args.voice)
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

    # Step 3: Multi-scene Cinematic AI Background + Thumbnail
    generate_multi_scene_background(args.script, args.topic, duration, bg_video_path, args.thumb)

    # Step 4: Final Assembly & Burned Subtitles
    render_final_short(bg_video_path, audio_path, srt_path, duration, args.output, color_name=args.color)

if __name__ == "__main__":
    main()
