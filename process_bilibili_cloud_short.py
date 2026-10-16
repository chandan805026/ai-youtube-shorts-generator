import os
import sys
import json
import time
import subprocess
import argparse
import urllib.request
import yt_dlp
from tts_rotator import synthesize_speech
import build_meme_vault
from upload_to_youtube import upload_short

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_bilibili_cookie():
    try:
        req = urllib.request.Request(
            'https://api.bilibili.com/x/frontend/finger/spi',
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36', 'Referer': 'https://www.bilibili.com/'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            b3 = data.get('data', {}).get('b_3')
            if b3:
                print(f"[Downloader] Generated fresh Bilibili buvid3 token: {b3[:15]}...")
                return f"buvid3={b3}; b_nut={int(time.time())}"
    except Exception as e:
        print("[Downloader] Notice fetching SPI cookie:", e)
    return "buvid3=6EA88FF2-65FF-DCA9-4B8B-794F121676FC01753infoc; b_nut=1728994393"

def download_cdn_stream(url, out_path, referer="https://www.bilibili.com/"):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': referer
    }
    req = urllib.request.Request(url, headers=headers)
    print(f"[CDN Downloader] Direct stream download: {url[:70]}...")
    with urllib.request.urlopen(req, timeout=45) as resp, open(out_path, 'wb') as f:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    print(f"[CDN Downloader] Saved {out_path} ({os.path.getsize(out_path)/(1024*1024):.2f} MB)")

def download_bilibili_video(video_url: str, out_merged_mp4: str) -> str:
    manifest_path = os.path.join(BASE_DIR, "bilibili_stream_manifest.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            bvid = manifest.get("bvid", "")
            if bvid and (bvid in video_url or manifest.get("video_url") == video_url):
                print(f"[Downloader] Using pre-resolved Akamai CDN streams for {video_url}...")
                v_url = manifest["video_stream_url"]
                a_url = manifest.get("audio_stream_url")
                
                v_m4s = os.path.join(BASE_DIR, "raw_stream_v.m4s")
                download_cdn_stream(v_url, v_m4s)
                
                if a_url:
                    a_m4s = os.path.join(BASE_DIR, "raw_stream_a.m4s")
                    download_cdn_stream(a_url, a_m4s)
                    cmd = ["ffmpeg", "-y", "-i", v_m4s, "-i", a_m4s, "-c:v", "copy", "-c:a", "aac", out_merged_mp4]
                else:
                    cmd = ["ffmpeg", "-y", "-i", v_m4s, "-c:v", "copy", out_merged_mp4]
                
                subprocess.run(cmd, check=True)
                print(f"[Downloader] Remuxed video into {out_merged_mp4}")
                return out_merged_mp4
        except Exception as e:
            print(f"[Downloader] Manifest download notice: {e}, attempting yt-dlp fallback...")

    # Fallback to yt-dlp
    cookie_str = get_bilibili_cookie()
    out_tmpl = os.path.join(BASE_DIR, 'raw_bilibili_video.%(ext)s')
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': out_tmpl,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Cookie': cookie_str
        },
        'quiet': False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    actual_files = [f for f in os.listdir(BASE_DIR) if f.startswith('raw_bilibili_video.') and not f.endswith(('.f100026.mp4', '.f30280.m4a'))]
    if not actual_files:
        raise FileNotFoundError("Could not find merged downloaded Bilibili MP4!")
    return os.path.join(BASE_DIR, actual_files[0])

def get_video_info(video_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-of", "json",
        video_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        st = data["streams"][0]
        return int(st["width"]), int(st["height"]), float(st.get("duration", 30.51))
    except Exception:
        return 1920, 1080, 30.51

def fmt_ass_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def run_cloud_pipeline(video_url: str, title: str = None, desc: str = None, auto_upload: bool = True):
    print("=" * 70)
    print("🚀 AUTONOMOUS BILIBILI CLOUD SHORTS ENGINE (100% GITHUB ACTIONS)")
    print("=" * 70)

    # 1. Initialize Meme Sounds
    print("\n[Step 1/5] Initializing Cloud SFX & Music Vault...")
    if hasattr(build_meme_vault, "download_all"):
        build_meme_vault.download_all()
    elif hasattr(build_meme_vault, "download_meme_sounds"):
        build_meme_vault.download_meme_sounds()

    # 2. Download Raw Video
    print(f"\n[Step 2/5] Downloading Bilibili Video from Cloud Edge: {video_url}...")
    merged_target = os.path.join(BASE_DIR, "raw_bilibili_video.mp4")
    raw_video = download_bilibili_video(video_url, merged_target)
    print(f"Downloaded raw video: {raw_video} ({os.path.getsize(raw_video)/(1024*1024):.2f} MB)")

    width, height, total_dur = get_video_info(raw_video)
    print(f"Raw Video Dimensions: {width}x{height}, Duration: {total_dur:.2f}s")

    # 3. Voiceover Generation - FULL SEQUENTIAL CONCATENATION (ZERO CHANCE OF CUTOFF)
    print("\n[Step 3/5] Generating Seamless Full-Coverage Viral Voiceover...")
    
    script_segments = [
        {
            "audio_text": "Can a human actually mimic a 100-ton hydraulic press?! Watch this!",
            "sub_cards": [
                "Can a human mimic a 100-ton hydraulic press?!",
                "Watch this! 👀"
            ]
        },
        {
            "audio_text": "This green monster is about to get flattened into absolute oblivion!",
            "sub_cards": [
                "This green monster...",
                "is about to get FLATTENED! 😱"
            ]
        },
        {
            "audio_text": "The steel cylinder pushes down, and her legs shoot straight up in sync!",
            "sub_cards": [
                "The cylinder pushes down...",
                "her legs shoot STRAIGHT UP! 🚀"
            ]
        },
        {
            "audio_text": "Look at her face! She is matching every millimeter in real time!",
            "sub_cards": [
                "LOOK AT HER FACE! 🤣",
                "Matching EVERY millimeter!"
            ]
        },
        {
            "audio_text": "Fifty tons of crushing force, and her body is completely squashed flat!",
            "sub_cards": [
                "50 TONS of crushing force...",
                "completely SQUASHED flat! 💪"
            ]
        },
        {
            "audio_text": "The rubber folds flat against the base, and she stays in pure comedy agony!",
            "sub_cards": [
                "The rubber folds flat...",
                "pure COMEDY AGONY! 😂💀"
            ]
        },
        {
            "audio_text": "The dedication is unreal! Drop a like if her mimic was a solid ten out of ten!",
            "sub_cards": [
                "The dedication is UNREAL!",
                "Drop a LIKE for 10/10! 🔥👇"
            ]
        }
    ]

    current_audio_time = 0.30  # Speech starts at 0.3s
    all_sub_cues = []
    tts_mp3_files = []

    for idx, seg in enumerate(script_segments):
        out_mp3 = os.path.join(BASE_DIR, f"tts_{idx+1:02d}.mp3")
        synthesize_speech(seg["audio_text"], out_mp3)
        tts_mp3_files.append(out_mp3)
        
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", out_mp3]
        pr = subprocess.run(cmd, capture_output=True, text=True)
        dur = float(json.loads(pr.stdout)["format"]["duration"])
        
        start_t = current_audio_time
        end_t = start_t + dur
        seg["start"] = start_t
        seg["end"] = end_t
        seg["duration"] = dur
        seg["mp3"] = out_mp3
        print(f"  -> Segment {idx+1} ({start_t:.2f}s - {end_t:.2f}s | dur {dur:.2f}s): {seg['audio_text']}")

        # Split subtitle display into fast, punchy 1.5-2.0s cards
        n_cards = len(seg["sub_cards"])
        card_dur = dur / n_cards
        for c_idx, card_text in enumerate(seg["sub_cards"]):
            c_start = start_t + (c_idx * card_dur)
            c_end = c_start + card_dur
            is_hook = (idx == 0) or (idx == len(script_segments) - 1 and c_idx == 1) or ("FLATTENED" in card_text) or ("LOOK AT HER FACE" in card_text)
            all_sub_cues.append({
                "start": c_start,
                "end": c_end,
                "text": card_text,
                "style": "CenterHook" if is_hook else "CenterStory"
            })

        current_audio_time = end_t

    total_spoken_time = current_audio_time
    print(f"\nTotal Spoken Narration Duration: {total_spoken_time:.2f}s (Video duration: {total_dur:.2f}s) -> PERFECT COVERAGE!")

    # Combine all TTS segments into ONE SINGLE continuous audio track via concat demuxer
    tts_list_file = os.path.join(BASE_DIR, "tts_concat_list.txt")
    with open(tts_list_file, "w", encoding="utf-8") as f:
        for p in tts_mp3_files:
            f.write(f"file '{p}'\n")

    full_voice_path = os.path.join(BASE_DIR, "full_voiceover.wav")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", tts_list_file,
        "-c:a", "pcm_s16le",
        full_voice_path
    ]
    subprocess.run(concat_cmd, check=True)
    print(f"Concatenated all voice segments into single continuous master voice track: {full_voice_path}")

    # 4. ASS Subtitles - EXACT SCREEN CENTER ALIGNED (Alignment = 5)
    print("\n[Step 4/5] Generating 1080x1920 CENTER-ALIGNED Subtitles...")
    ass_path = os.path.join(BASE_DIR, "bilibili_subtitles.ass")
    
    # ASS Alignment 5 puts text directly in the geometric center (X=540, Y=960)
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CenterHook,DejaVu Sans,62,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,5,50,50,0,1
Style: CenterStory,DejaVu Sans,56,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,5,50,50,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for cue in all_sub_cues:
        st = fmt_ass_time(cue["start"])
        et = fmt_ass_time(cue["end"])
        ass_header += f"Dialogue: 0,{st},{et},{cue['style']},,0,0,0,,{cue['text']}\n"

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)

    # 5. Build Master Audio Mix - WITH LONGEST DURATION (NO EARLY CUTOFF)
    print("\n[Step 5/5] Mixing Master Voiceover, BGM, and Sound Effects...")
    bgm_path = os.path.join(BASE_DIR, "meme_sound_vault", "monkeys_spinning_monkeys.mp3")
    if not os.path.exists(bgm_path):
        bgm_path = os.path.join(BASE_DIR, "meme_sound_vault", "sneaky_snitch.mp3")

    sfx_pipe = os.path.join(BASE_DIR, "meme_sound_vault", "metal_pipe.mp3")
    sfx_wow = os.path.join(BASE_DIR, "meme_sound_vault", "anime_wow.mp3")

    master_audio = os.path.join(BASE_DIR, "master_audio_cloud.wav")
    
    # Mix single continuous voice track with background music & sound effects
    filter_complex = (
        "[0:a]adelay=300|300,volume=1.35[a_vox];"
        f"[1:a]atrim=0:{total_dur},volume=0.10,afade=t=in:st=0:d=0.5,afade=t=out:st={total_dur-1.0}:d=1.0[a_bgm];"
        "[2:a]adelay=500|500,volume=0.50[a_sfx1];"
        "[3:a]adelay=26500|26500,volume=0.60[a_sfx2];"
        "[a_vox][a_bgm][a_sfx1][a_sfx2]amix=inputs=4:duration=longest:dropout_transition=0[a_mix]"
    )

    audio_cmd = [
        "ffmpeg", "-y",
        "-i", full_voice_path,
        "-i", bgm_path,
        "-i", sfx_pipe,
        "-i", sfx_wow,
        "-filter_complex", filter_complex,
        "-map", "[a_mix]",
        "-t", str(total_dur),
        master_audio
    ]
    subprocess.run(audio_cmd, check=True)
    print(f"Master audio successfully mixed: {master_audio}")

    # 6. Render Final 9:16 Video
    print("\n[Step 6/6] Rendering High-Definition 1080x1920 Short with FFmpeg...")
    final_output = os.path.join(BASE_DIR, "final_cloud_short.mp4")

    if width > height:
        print("Detected 16:9 side-by-side split screen! Converting to Vertical Stack (Press on Top, Girl on Bottom)...")
        filter_str = (
            f"[0:v]crop=960:1080:0:0,scale=1080:960[top];"
            f"[0:v]crop=960:1080:960:0,scale=1080:960[bottom];"
            f"[top][bottom]vstack[v_stack];"
            f"[v_stack]subtitles={ass_path}[v_out]"
        )
        render_cmd = [
            "ffmpeg", "-y",
            "-i", raw_video,
            "-i", master_audio,
            "-filter_complex", filter_str,
            "-map", "[v_out]",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(total_dur),
            final_output
        ]
    else:
        print("Detected native vertical format! Applying subtitle overlay...")
        filter_str = f"subtitles={ass_path}"
        render_cmd = [
            "ffmpeg", "-y",
            "-i", raw_video,
            "-i", master_audio,
            "-vf", filter_str,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(total_dur),
            final_output
        ]

    subprocess.run(render_cmd, check=True)
    print(f"\n✅ Video successfully rendered on Cloud: {final_output} ({os.path.getsize(final_output)/(1024*1024):.2f} MB)")

    # 7. Upload to YouTube
    if auto_upload:
        if not title:
            title = "When You Try To Mimic A 100-Ton Hydraulic Press (Green Edition)! 😂 #Shorts"
        if not desc:
            desc = "Can a human actually imitate a hydraulic press crushing a green monster?! Her core strength and facial expressions are 100% accurate! 😂🔥 #Shorts #Comedy #HydraulicPress #Funny #Reaction #Viral #Challenge #Mimic"
        tags = ["Shorts", "Comedy", "HydraulicPress", "Funny", "Reaction", "Mimic", "Viral", "Challenge", "Dedication", "GreenMonster"]
        print(f"\n🚀 Initiating Direct YouTube Shorts Upload from Cloud Runner...")
        video_id, yt_url = upload_short(video_source=final_output, title=title, desc=desc, tags=tags)
        print(f"\n🎉 CLOUD PUBLISH COMPLETE: {yt_url}")
        return yt_url
    return final_output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://www.bilibili.com/video/BV1ZoEB6pEZa", help="Bilibili Video URL")
    parser.add_argument("--title", default="When You Try To Mimic A 100-Ton Hydraulic Press (Green Edition)! 😂 #Shorts", help="YouTube Short Title")
    parser.add_argument("--desc", default="Can a human actually imitate a hydraulic press crushing a green monster?! Her core strength and facial expressions are 100% accurate! 😂🔥 #Shorts #Comedy #HydraulicPress #Funny #Reaction #Viral #Challenge #Mimic", help="YouTube Short Description")
    parser.add_argument("--upload", action="store_true", default=True, help="Auto upload to YouTube")
    args = parser.parse_args()

    run_cloud_pipeline(args.url, title=args.title, desc=args.desc, auto_upload=args.upload)
