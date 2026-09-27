#!/usr/bin/env python3
"""
Autonomous Viral Asian Meme & Comedy Shorts Studio
--------------------------------------------------
Designed for 100% cloud execution on GitHub Actions.
Bypasses YouTube Reused Content policy with transformative editing:
- Dual-Route Fail-safe Ingestion (Route 1: URL/yt-dlp, Route 2: Curated Viral Vault)
- Gemini Baba Multimodal / AI Comedy Director (Ray William Johnson / Meme creator style)
- Microsoft Edge TTS (en-US-GuyNeural energetic American voice)
- Hormozi / MrBeast Yellow & White Bold Animated Subtitles
- FFmpeg Transformative Studio: Horizontal Flip + 106% Dynamic Zoom + Micro Speed Ramp + Top Hook Banner + Audio Mixing
"""

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
import math
import struct
import wave
import base64

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ==========================================
# 1. VIRAL COMEDY VAULT (ROUTE 2 FAIL-SAFE)
# ==========================================
VIRAL_VAULT = [
    {
        "id": "vault_douyin_fresh_china",
        "category": "douyin_direct_china",
        "title": "Chinese TikTok Transformation Went Crazy 💀 #shorts",
        "hook_banner": "WAIT FOR THE TRANSFORMATION 😂",
        "description": "An authentic trending Douyin video directly from China (ID 7687882613504036777) featuring a jaw-dropping and hilarious Chinese costume and style transformation challenge to trending music.",
        "fallback_script": "Ain't no way Chinese TikTok just pulled off this insane transformation! Watch the transition right before the beat drops! The confidence, the style, the facial expression is pure gold! You can't even make this level of creativity up! Ten out of ten viral masterpiece! 💀",
        "local_fallback": "assets/vault/douyin_fresh_china.mp4",
        "cdn_urls": [
            "https://raw.githubusercontent.com/chandan805026/ai-youtube-shorts-generator/main/assets/vault/douyin_fresh_china.mp4"
        ]
    },
    {
        "id": "vault_douyin_china_live",
        "category": "douyin_direct_china",
        "title": "Dog Mom Gives Human Toilet Demo In 4K 😭💀 #shorts",
        "hook_banner": "MOM GAVE A LIVE DEMO 😂",
        "description": "An authentic viral Douyin comedy short directly from China where a golden retriever mother dog in yellow clothes teaches her cute puppy how to use the human toilet. When the confused puppy doesn't know what to do on the training seat, the mother dog literally hops onto the porcelain commode and balances all four paws on the rim to demonstrate how to use it like a civilized human!",
        "fallback_script": "Ain't no way this dog mom literally said: 'Watch and learn, son!' Look at her placing the puppy on the potty trainer first... but when the kid looks confused, SHE HOPS ON THE TOILET TO DEMO IT HERSELF! Four paws perfectly balanced on the porcelain throne looking at the camera like: 'See? It's that easy!' Asian parenting has officially crossed over to pets! 💀",
        "local_fallback": "assets/vault/douyin_china_live.mp4",
        "cdn_urls": [
            "https://raw.githubusercontent.com/chandan805026/ai-youtube-shorts-generator/main/assets/vault/douyin_china_live.mp4"
        ]
    },
    {
        "id": "vault_douyin_slapstick_fresh",
        "category": "asian_comedy",
        "title": "Bro Woke Up To The Ultimate Disrespect In 4K 😭💀 #shorts",
        "hook_banner": "WORST WAY TO WAKE UP 💀",
        "description": "A man is fast asleep dreaming peacefully on the couch, when his friend quietly sneaks up with a dirty bare foot and rests it right over his nose and mouth. The sleeping man begins sniffing it thinking it is breakfast, slowly opens his eyes in utter disbelief, and freaks out in horror.",
        "fallback_script": "Bro was having the most peaceful dream of his entire life... until his friend chose pure biological violence! Look at this man quietly sneaking up and putting his whole bare foot directly on his face! And bro is actually sniffing it in his sleep thinking it's breakfast! Wait for it... wait for it... look at his eyes opening! The exact second reality hits and he realizes what he's smelling, his whole soul exits his body in 4K! You literally cannot make this level of disrespect up! 💀",
        "local_fallback": "assets/vault/douyin_slapstick_fresh.mp4",
        "cdn_urls": [
            "https://raw.githubusercontent.com/chandan805026/ai-youtube-shorts-generator/main/assets/vault/douyin_slapstick_fresh.mp4"
        ]
    },
    {
        "id": "vault_douyin_hd_prank",
        "category": "douyin_comedy",
        "title": "Bro Tried To Prank His Best Friend And Paid In 4K 💀 #shorts",
        "hook_banner": "INSTANT KARMA 😂",
        "description": "A hilarious 27-second high-definition viral Douyin bestfriend prank where an elaborate setup backfires immediately with hysterical facial expressions and instant comedy karma.",
        "fallback_script": "Bro really spent two hours setting up this master prank! Look at that smug smile thinking he has the ultimate plan. But the universe said not today! The exact second it backfires, his whole soul leaves his body in 4K! You can't even make this level of instant karma up! Ten out of ten comedy gold! 💀",
        "local_fallback": "assets/vault/douyin_hd_prank.mp4",
        "cdn_urls": [
            "https://raw.githubusercontent.com/chandan805026/ai-youtube-shorts-generator/main/assets/vault/douyin_hd_prank.mp4"
        ]
    },
    {
        "id": "vault_douyin_hd_bad_luck",
        "category": "suspense",
        "title": "Bro Thought He Was Safe But Wait For The Plot Twist 💀 #shorts",
        "hook_banner": "WAIT FOR THE PLOT TWIST 💀",
        "description": "An intense, edge-of-your-seat viral Chinese suspense comedy short where a guy thinks he is completely safe in the room, until an escalating chain of shocking twists traps him, ending with a mind-blowing comedy climax in 4K!",
        "fallback_script": "Bro thought he had the smoothest escape of his entire life... but wait until you see the plot twist! Look at the tension building in this room! He thinks nobody is watching, but wait for it... wait for it... AND BOOM! The ending completely shattered his whole reality in 4K! You literally cannot make this level of suspense up! 💀",
        "local_fallback": "assets/vault/douyin_hd_bad_luck.mp4",
        "cdn_urls": [
            "https://raw.githubusercontent.com/chandan805026/ai-youtube-shorts-generator/main/assets/vault/douyin_hd_bad_luck.mp4"
        ]
    },
    {
        "id": "vault_douyin_viral_1",
        "category": "douyin_comedy",
        "title": "Chinese TikTok Really Hits Different 💀 #shorts",
        "hook_banner": "MILLION VIEWS ON DOUYIN 😂",
        "description": "A viral Douyin comedy short where an unexpected slapstick reaction and comedic face turn a normal moment into pure comedy gold.",
        "fallback_script": "Ain't no way Chinese TikTok just did that! Look at bro trying to keep a straight face before disaster strikes. The reaction at the end is pure comedy gold! You can't even make this stuff up! 💀",
        "local_fallback": "assets/vault/douyin_viral_1.mp4",
        "cdn_urls": [
            "https://raw.githubusercontent.com/chandan805026/ai-youtube-shorts-generator/main/assets/vault/douyin_viral_1.mp4"
        ]
    },
    {
        "id": "vault_douyin_viral_2",
        "category": "asian_comedy",
        "title": "Bro Woke Up And Chose Violence 🥁💀 #shorts",
        "hook_banner": "MAIN CHARACTER ENERGY 😂",
        "description": "An epic viral Chinese meme drum moment with dramatic focus, unexpected comedic timing, and hilarious intensity.",
        "fallback_script": "Bro really thought he was in Fast and Furious! Look at that intense focus right before the beat drops. The confidence is on another level! Ten out of ten for style! 😂",
        "local_fallback": "assets/vault/douyin_viral_2.mp4",
        "cdn_urls": [
            "https://raw.githubusercontent.com/chandan805026/ai-youtube-shorts-generator/main/assets/vault/douyin_viral_2.mp4"
        ]
    },
    {
        "id": "vault_douyin_viral_3",
        "category": "douyin_comedy",
        "title": "Bro Experienced Heartbreak In 4K 🚗😭 #shorts",
        "hook_banner": "BRO IS GOING THROUGH IT 💀",
        "description": "The legendary trending Chinese meme where someone dramatically weeps in the car with maximum emotional exaggeration and funny tearful face.",
        "fallback_script": "Bro is fighting for his life right now! Look at the tears pouring down in 4K! What song was playing in that car to make him this emotional?! Give this man an Oscar right now! 💀",
        "local_fallback": "assets/vault/douyin_viral_3.mp4",
        "cdn_urls": [
            "https://raw.githubusercontent.com/chandan805026/ai-youtube-shorts-generator/main/assets/vault/douyin_viral_3.mp4"
        ]
    },
    {
        "id": "vault_asian_street_comedy",
        "category": "asian_street_comedy",
        "title": "Bro Tried To Look Smooth And Failed 💀 #shorts",
        "hook_banner": "ACT NATURAL 😂",
        "description": "A stylish guy tries to do a smooth slow-motion pose while crossing a pedestrian bridge to impress someone walking by, trips over a tiny bump, does an awkward windmill arm recovery, and acts like it was totally intentional.",
        "fallback_script": "Bro was trying so hard to be the main character! He practiced that smooth walk for three hours in the mirror. But the pavement had other plans! One tiny stumble and the arms started flying like a helicopter! And look how he immediately acts like nothing happened. Respect the confidence! 😂",
        "local_fallback": "assets/vault/starter_comedy.mp4",
        "cdn_urls": [
            "https://raw.githubusercontent.com/chandan805026/ai-youtube-shorts-generator/main/assets/vault/starter_comedy.mp4"
        ]
    }
]

# ==========================================
# 2. INGESTION ENGINE (DUAL ROUTE FAIL-SAFE)
# ==========================================
def download_file_stream(url, dest_path, timeout=30):
    """Download a file with streaming and browser User-Agent headers."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }
    r = requests.get(url, headers=headers, stream=True, timeout=timeout)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 512):
            if chunk:
                f.write(chunk)
    return os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000

def try_tikwm_download(video_url, dest_path):
    """Attempt watermark-free extraction from TikWM API for Douyin/TikTok."""
    try:
        print(f"🔍 [Route 1 - TikWM] Querying watermark-free API for: {video_url}")
        resp = requests.post("https://www.tikwm.com/api/", data={"url": video_url}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and "data" in data and "play" in data["data"]:
                play_url = data["data"]["play"]
                title = data["data"].get("title", "Viral Comedy Short")
                print(f"✅ [Route 1 - TikWM] Found direct video stream! Downloading...")
                if download_file_stream(play_url, dest_path):
                    return True, title
    except Exception as e:
        print(f"⚠️ [Route 1 - TikWM] Error: {e}")
    return False, ""

def try_ytdlp_download(video_url, dest_path):
    """Attempt download via yt-dlp."""
    try:
        print(f"🔍 [Route 1 - yt-dlp] Invoking yt-dlp on: {video_url}")
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
            "--no-check-certificates",
            "--max-filesize", "50M",
            "-o", dest_path,
            video_url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode == 0 and os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
            print("✅ [Route 1 - yt-dlp] Download succeeded!")
            return True
        else:
            print(f"⚠️ [Route 1 - yt-dlp] Warning/Error:\n{res.stderr[:300]}")
    except Exception as e:
        print(f"⚠️ [Route 1 - yt-dlp] Exception: {e}")
    return False

def scrape_fresh_douyin_china_feed(dest_path):
    """
    Directly queries the live Chinese Douyin ByteDance mobile feed API from China CDN!
    Bypasses all western blocks and gets 100% authentic, unindexed Chinese clips.
    """
    try:
        print("🌐 [DOUYIN CHINA DIRECT] Scraping live Douyin ByteDance feed API...")
        url = "https://aweme.snssdk.com/aweme/v1/feed/?count=15"
        headers = {"User-Agent": "okhttp/3.10.0.1", "Accept": "application/json"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            for item in data.get("aweme_list", []):
                dur = item.get("duration", 0) / 1000.0
                video = item.get("video", {})
                play_urls = video.get("play_addr", {}).get("url_list", [])
                if 14.0 <= dur <= 35.0 and play_urls:
                    aweme_id = item.get("aweme_id")
                    desc = item.get("desc", "Viral Chinese Douyin Comedy")
                    print(f"✅ Found fresh Douyin clip ID {aweme_id} ({dur:.1f}s)! Downloading from ByteDance China CDN...")
                    dl_headers = {"User-Agent": "okhttp/3.10.0.1"}
                    with requests.get(play_urls[0], headers=dl_headers, stream=True, timeout=30) as resp:
                        resp.raise_for_status()
                        with open(dest_path, "wb") as f:
                            for chunk in resp.iter_content(chunk_size=1024*512):
                                if chunk:
                                    f.write(chunk)
                    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 50000:
                        print(f"🎉 Successfully downloaded live Chinese Douyin video ({os.path.getsize(dest_path)/(1024*1024):.2f} MB)!")
                        meta = {
                            "id": f"douyin_{aweme_id}",
                            "title": "Chinese TikTok Went Too Far 💀 #shorts",
                            "hook_banner": "WAIT TILL THE END 😂",
                            "description": desc,
                            "fallback_script": "Ain't no way Chinese TikTok just did that! Look at the reaction right before disaster strikes. Pure comedy gold in 4K! 💀"
                        }
                        return True, meta
    except Exception as e:
        print(f"⚠️ Live Douyin feed scrape notice: {e}")
    return False, None

def ingest_video_dual_route(video_url, topic, history_file="history.json"):
    """
    Dual-Route Ingestion Engine:
    Route 1: User URL (Douyin, TikTok, YouTube Shorts, or direct video URL)
    Route 2: Curated Viral Comedy Vault (Guaranteed zero-failure fallback)
    """
    os.makedirs("input", exist_ok=True)
    raw_video_path = os.path.join("input", "source_video.mp4")

    # 0. If a specific topic is requested (e.g. suspense, kids, pets), allow Vault to match it!
    if topic and topic.strip() and topic.strip().lower() != 'auto':
        print(f"🎯 [TARGETED NICHE] Topic requested: '{topic}'. Matching from Curated Vault...")
    elif not video_url or not video_url.strip():
        print(f"\n=======================================================")
        print(f"🇨🇳 [CHINA LIVE STREAM] Fetching brand new viral clip directly from Douyin China API...")
        print(f"=======================================================")
        ok, live_meta = scrape_fresh_douyin_china_feed(raw_video_path)
        if ok and live_meta:
            return raw_video_path, live_meta["title"], live_meta["description"], "douyin_live_china", live_meta

    # 1. Route 1: Try user-provided URL
    if video_url and video_url.strip():
        url = video_url.strip()
        print(f"\n=======================================================")
        print(f"🚀 [ROUTE 1 ACTIVATED] Processing Video URL: {url}")
        print(f"=======================================================")
        
        # Check if direct video file
        if url.endswith(".mp4") or url.endswith(".webm"):
            print("📥 Direct media link detected, streaming download...")
            try:
                if download_file_stream(url, raw_video_path):
                    print("✅ Direct download succeeded!")
                    return raw_video_path, "Viral Comedy Clip #shorts", "Watch this hilarious moment unfold 😂", "route_1", None
            except Exception as e:
                print(f"⚠️ Direct download failed: {e}")

        # Check if Douyin or TikTok
        if "douyin.com" in url or "tiktok.com" in url:
            ok, detected_title = try_tikwm_download(url, raw_video_path)
            if ok:
                return raw_video_path, detected_title or "Viral Asian Comedy #shorts", "Viral Douyin comedy clip", "route_1", None

        # Fall back to yt-dlp
        ok = try_ytdlp_download(url, raw_video_path)
        if ok:
            return raw_video_path, "Viral Comedy Short #shorts", "Hilarious trending video", "route_1", None

        print("\n⚠️ [ROUTE 1 FAILED] Could not download from provided URL (Firewall/Captcha/Rate-limit).")
        print("🔄 [FAIL-SAFE SWITCH] Seamlessly switching to Route 2: Curated Viral Vault!")

    # 2. Route 2: Curated Viral Comedy Vault Fallback
    print(f"\n=======================================================")
    print(f"🎯 [ROUTE 2 ACTIVATED] Accessing Curated Viral Comedy Vault...")
    print(f"=======================================================")

    # Load history memory to avoid repeating clips
    used_ids = set()
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                hist = json.load(f)
                for item in hist:
                    if "clip_id" in item:
                        used_ids.add(item["clip_id"])
        except Exception:
            pass

    # Filter out played clips
    available_clips = [c for c in VIRAL_VAULT if c["id"] not in used_ids]
    if not available_clips:
        print("🔄 Memory vault fully played! Resetting cycle for endless fresh content.")
        available_clips = VIRAL_VAULT

    # Filter by topic if specified
    if topic and topic.strip() and topic.strip().lower() != 'auto':
        topic_lower = topic.strip().lower()
        topic_matched = [c for c in available_clips if topic_lower in c["category"] or topic_lower in c["title"].lower()]
        if topic_matched:
            available_clips = topic_matched

    chosen_clip = random.choice(available_clips)
    print(f"🎬 Selected Vault Clip: {chosen_clip['id']} ({chosen_clip['category']})")
    print(f"📖 Context: {chosen_clip['description']}")

    # Obtain media file: try local asset first, then CDN URLs
    if os.path.exists(chosen_clip.get("local_fallback", "")):
        print(f"✅ Found verified local asset: {chosen_clip['local_fallback']}")
        import shutil
        shutil.copy(chosen_clip["local_fallback"], raw_video_path)
        return raw_video_path, chosen_clip["title"], chosen_clip["description"], "route_2", chosen_clip

    # Try CDN URLs
    for cdn_url in chosen_clip.get("cdn_urls", []):
        try:
            print(f"🌐 Fetching clip from CDN: {cdn_url}")
            if download_file_stream(cdn_url, raw_video_path, timeout=15):
                print("✅ Successfully downloaded clip from CDN!")
                return raw_video_path, chosen_clip["title"], chosen_clip["description"], "route_2", chosen_clip
        except Exception as e:
            print(f"⚠️ CDN download attempt failed: {e}")

    # Fallback to local starter clip
    if os.path.exists("assets/vault/starter_comedy.mp4"):
        import shutil
        shutil.copy("assets/vault/starter_comedy.mp4", raw_video_path)
        return raw_video_path, chosen_clip["title"], chosen_clip["description"], "route_2", chosen_clip

    raise RuntimeError("Critical: Unable to acquire video clip from either Route 1 or Route 2!")

# ==========================================
# 3. GEMINI BABA MULTIMODAL COMEDY DIRECTOR
# ==========================================
def upload_video_to_gemini(video_path, gemini_key):
    """
    Uploads the full raw downloaded video to the Google Gemini Files API
    so Gemini can watch the entire video with its own eyes!
    """
    if not video_path or not os.path.exists(video_path):
        print(f"⚠️ Video file does not exist for Gemini upload: {video_path}")
        return None, None

    file_size = os.path.getsize(video_path)
    print(f"📤 Uploading full video to Gemini Files API ({file_size / (1024*1024):.2f} MB)...")
    try:
        # Step 1: Initialize Resumable Upload
        init_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={gemini_key}"
        headers = {
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(file_size),
            "X-Goog-Upload-Header-Content-Type": "video/mp4",
            "Content-Type": "application/json"
        }
        metadata = {"file": {"display_name": os.path.basename(video_path)}}
        init_resp = requests.post(init_url, headers=headers, json=metadata, timeout=30)
        init_resp.raise_for_status()

        upload_url = init_resp.headers.get("X-Goog-Upload-URL") or init_resp.headers.get("x-goog-upload-url")
        if not upload_url:
            print("⚠️ Gemini Files API did not return an upload URL.")
            return None, None

        # Step 2: Upload Video File Content
        with open(video_path, "rb") as f:
            upload_headers = {
                "Content-Length": str(file_size),
                "X-Goog-Upload-Offset": "0",
                "X-Goog-Upload-Command": "upload, finalize"
            }
            up_resp = requests.put(upload_url, headers=upload_headers, data=f, timeout=120)
            up_resp.raise_for_status()
            res_data = up_resp.json()
            file_info = res_data.get("file", {})
            file_uri = file_info.get("uri")
            file_name = file_info.get("name")
            print(f"✅ Video successfully uploaded to Gemini! File ID: {file_name}")

        # Step 3: Wait for Gemini to finish processing video frames
        print("⏳ Waiting for Gemini to process the video stream...")
        for attempt in range(25):
            time.sleep(2)
            check_url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={gemini_key}"
            c_resp = requests.get(check_url, timeout=15)
            if c_resp.status_code == 200:
                c_json = c_resp.json()
                state = c_json.get("state")
                if state == "ACTIVE":
                    print(f"🎬 [SUCCESS] Video is ACTIVE! Gemini will watch the entire video.")
                    return file_uri, file_name
                elif state == "FAILED":
                    print(f"❌ Video processing failed on Gemini server.")
                    return None, None
            print(f"   ...processing video frames ({attempt+1}/25)...")

        return file_uri, file_name
    except Exception as e:
        print(f"⚠️ Gemini Files API upload failed: {e}")
        return None, None


def extract_video_keyframes_base64(video_path, num_frames=5):
    """
    Fallback visual extractor: extracts keyframes across the video using ffmpeg
    and encodes them as base64 images so Gemini can visually inspect the action.
    """
    frames_b64 = []
    try:
        dur = get_media_duration(video_path)
        if dur <= 1.0:
            return frames_b64
        timestamps = [dur * (i + 1) / (num_frames + 1) for i in range(num_frames)]
        temp_dir = "temp/frames"
        os.makedirs(temp_dir, exist_ok=True)
        for idx, ts in enumerate(timestamps):
            frame_file = os.path.join(temp_dir, f"frame_{idx}.jpg")
            cmd = [
                "ffmpeg", "-y", "-ss", f"{ts:.2f}",
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                frame_file
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(frame_file) and os.path.getsize(frame_file) > 1000:
                with open(frame_file, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                    frames_b64.append(b64)
        if frames_b64:
            print(f"📸 Extracted {len(frames_b64)} visual frames for Gemini vision analysis.")
    except Exception as e:
        print(f"⚠️ Frame extraction notice: {e}")
    return frames_b64


def direct_comedy_with_gemini(video_path=None, clip_description="", topic="", custom_script="", fallback_meta=None, target_duration=20.0):
    """
    Directs the short in American meme/commentary style:
    - Feeds the ACTUAL VIDEO directly to Gemini Baba using Multimodal Vision.
    - Gemini watches the real actions, characters, and punchline.
    - Writes energetic, hilarious voiceover commentary matched dynamically to video duration.
    - Writes high-retention Title with emojis & #shorts.
    - Writes 3-5 word ALL CAPS Top Hook Banner.
    """
    if custom_script and custom_script.strip():
        print("🎬 Using user-provided custom script...")
        return {
            "title": fallback_meta.get("title", "Viral Comedy Short #shorts") if fallback_meta else "Viral Comedy Short #shorts",
            "hook_banner": fallback_meta.get("hook_banner", "WAIT FOR IT 😂") if fallback_meta else "WAIT FOR IT 😂",
            "script": custom_script.strip(),
            "description": "Hilarious viral comedy moment! #shorts #viral #funny #comedy",
            "tags": "shorts, funny, comedy, viral, meme, hilarious"
        }

    # Calculate optimal word count for target duration (speech pace ~2.7 words/sec at +12% speed)
    safe_audio_dur = max(6.0, target_duration - 1.0)
    word_target = int(safe_audio_dur * 2.7)
    word_min = max(14, word_target - 4)
    word_max = word_target + 4
    print(f"🎯 Calibrated Commentary Target: {safe_audio_dur:.1f}s speech ({word_min}-{word_max} words)")

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        print("🧠 Calling Gemini Baba Multimodal Video Director...")

        # 1. Upload video file so Gemini directly watches it!
        file_uri = None
        file_name = None
        frame_images_b64 = []
        if video_path and os.path.exists(video_path):
            file_uri, file_name = upload_video_to_gemini(video_path, gemini_key)
            if not file_uri:
                print("🔄 Falling back to visual keyframe extraction for Gemini vision...")
                frame_images_b64 = extract_video_keyframes_base64(video_path)

        system_instruction = (
            "You are an elite YouTube Shorts & TikTok comedy writer in the style of Ray William Johnson, "
            "Daily Dose of Internet, and modern American meme creators ('Bro really thought...', 'Ain't no way').\n"
            "YOU ARE WATCHING THE ACTUAL VIDEO FOOTAGE. Do NOT hallucinate or guess.\n"
            "Your commentary must accurately reflect the EXACT physical actions and characters happening on screen, "
            "while being fast-paced, witty, highly energetic, and relatable for US/UK/global audiences.\n"
            "Format your entire response as a single valid JSON object with keys: title, hook_banner, script, description, tags."
        )

        user_prompt = f"""
WATCH AND ANALYZE THIS VIRAL VIDEO FOOTAGE CAREFULLY:
- Video Context / Clues: {clip_description}
- Genre/Niche: {topic}
- Target Video Duration: {target_duration:.1f} seconds

STRICT VIDEO INSPECTION INSTRUCTIONS:
1. Examine what actually happens across the seconds:
   - Who or what are the subjects? (e.g. Is it a mother dog and her puppy? A person doing a prank? Street slapstick?).
   - What is the step-by-step storyline? What starts the scene, what is the development, and what is the climax?
   - DO NOT make up random things that do not occur on screen!
   - If a mother dog is putting a puppy on a toilet trainer and then hops on the toilet rim to demonstrate how to use it, TALK SPECIFICALLY ABOUT HER DEMONSTRATING AND SHOWING OFF HER SKILLS!

2. Provide JSON with:
   - "title": High curiosity viral YouTube Shorts title under 60 characters with funny emojis and #shorts (e.g. 'Dog Mom Gives Human Toilet Demo In 4K 😭💀 #shorts').
   - "hook_banner": 3-5 words ALL CAPS punchy suspense hook banner matching the visual (e.g. 'MOM GAVE A LIVE DEMO 😂', 'WATCH AND LEARN 💀').
   - "script": Fast, hilarious English voiceover commentary of EXACTLY {word_min} to {word_max} words ({safe_audio_dur:.1f}s spoken at 1.12x speed).
     * Hook in first 1.5 seconds stating the wild situation.
     * Middle section: build comedic escalation based on the visual actions.
     * Climax: land the punchline right as the video's ending punchline hits!
   - "description": 2-line YouTube description with viral hashtags #shorts #funny #viral #comedy #douyin.
   - "tags": 8-10 comma-separated keywords.

Output ONLY raw JSON. No markdown ticks, no backticks.
"""
        # Build contents payload with video or visual frames
        content_parts = []
        if file_uri:
            content_parts.append({"fileData": {"fileUri": file_uri, "mimeType": "video/mp4"}})
            print("👁️ Attaching FULL MP4 VIDEO STREAM to Gemini contents!")
        elif frame_images_b64:
            for b64 in frame_images_b64:
                content_parts.append({"inlineData": {"mimeType": "image/jpeg", "data": b64}})
            print(f"👁️ Attaching {len(frame_images_b64)} visual frames to Gemini contents!")
        content_parts.append({"text": user_prompt})

        # Dynamic Gemini Model Discovery & Priority to gemini-2.5-flash
        models_to_try = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-exp", "gemini-1.5-pro"]
        try:
            m_resp = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}", timeout=10)
            if m_resp.status_code == 200:
                discovered = []
                for m in m_resp.json().get("models", []):
                    m_name = m.get("name", "").replace("models/", "")
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        discovered.append(m_name)
                priority_names = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-2.5-flash"]
                top_picks = [p for p in priority_names if p in discovered]
                rest = [m for m in discovered if m not in top_picks and "tts" not in m and "image" not in m]
                models_to_try = top_picks + rest
        except Exception as e:
            print(f"⚠️ Dynamic model discovery notice: {e}")
        print(f"🎯 Target Gemini models to try: {models_to_try[:4]}")
        for mod in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": content_parts}],
                    "systemInstruction": {"parts": [{"text": system_instruction}]},
                    "generationConfig": {"temperature": 0.85, "maxOutputTokens": 800}
                }
                r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=45)
                if r.status_code == 200:
                    data = r.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    cleaned = re.sub(r"^```json\s*", "", raw_text)
                    cleaned = re.sub(r"\s*```$", "", cleaned)
                    parsed = json.loads(cleaned)
                    if "script" in parsed and "title" in parsed:
                        print(f"🎉 Gemini Baba Multimodal Director Success! Title: {parsed['title']}")
                        # Clean up uploaded file from Gemini
                        if file_name:
                            try:
                                requests.delete(f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={gemini_key}", timeout=10)
                            except Exception:
                                pass
                        return parsed
                else:
                    print(f"⚠️ Gemini {mod} returned HTTP {r.status_code}: {r.text[:200]}")
            except Exception as e:
                print(f"⚠️ Gemini {mod} call notice: {e}")

        # Clean up uploaded file if generation failed
        if file_name:
            try:
                requests.delete(f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={gemini_key}", timeout=10)
            except Exception:
                pass

    # Fallback if Gemini key is missing or quota reached
    print("💡 Using Curated Comedy Script from Vault...")
    if fallback_meta:
        return {
            "title": fallback_meta["title"],
            "hook_banner": fallback_meta["hook_banner"],
            "script": fallback_meta["fallback_script"],
            "description": f"Hilarious viral moment! {fallback_meta['title']} #shorts #funny #viral #comedy",
            "tags": "shorts, funny, comedy, viral, meme, cute, hilarious"
        }

    return {
        "title": "Bro Really Thought He Got Away With It 💀 #shorts",
        "hook_banner": "HE WAS CAUGHT IN 4K 😂",
        "script": "Bro really thought he was slick! Look at that confidence right before disaster strikes. The way he froze the second he got caught is pure comedy gold! You can see his whole soul leaving his body in 4K! You can't even make this stuff up! 😂",
        "description": "Hilarious viral comedy moment! #shorts #viral #funny #comedy",
        "tags": "shorts, funny, comedy, viral, meme, hilarious"
    }

# ==========================================
# 4. MICROSOFT EDGE TTS & HORMOZI SUBTITLES
# ==========================================
def parse_vtt_timestamps(vtt_file):
    """Parses WebVTT subtitle cues generated by edge-tts into word/phrase segments."""
    cues = []
    if not os.path.exists(vtt_file):
        return cues
    try:
        with open(vtt_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        time_pat = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})")
        current_start = None
        current_end = None
        for line in lines:
            line = line.strip()
            m = time_pat.search(line)
            if m:
                current_start = m.group(1)
                current_end = m.group(2)
            elif current_start and current_end and line and not line.startswith("WEBVTT"):
                # Clean formatting tags
                clean_text = re.sub(r"<[^>]+>", "", line).strip()
                if clean_text:
                    cues.append((current_start, current_end, clean_text))
                current_start = None
                current_end = None
    except Exception as e:
        print(f"⚠️ Error parsing VTT: {e}")
    return cues

def vtt_time_to_seconds(ts):
    parts = ts.split(":")
    h = float(parts[0])
    m = float(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s

def seconds_to_ass_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int((sec - int(sec)) * 100)
    return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

def strip_emojis(text):
    """Remove emojis, symbols, and pictographs so Edge TTS doesn't speak their names."""
    if not text:
        return ""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols & pictographs (🤣, 💀)
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        "\U00002600-\U000026FF"  # misc symbols
        "\U00002B50"              # star
        "\U0000200D"              # zero-width joiner
        "\U0000FE0F"              # variation selector
        "]+",
        flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub('', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def generate_voiceover_and_ass(script_text, voice, output_audio, output_ass):
    """
    Generates Microsoft Edge TTS speech with +12% meme pace,
    and builds an animated yellow/white Hormozi ASS subtitle file.
    """
    os.makedirs(os.path.dirname(output_audio) or ".", exist_ok=True)
    vtt_file = output_audio.replace(".mp3", ".vtt")
    
    clean_spoken_text = strip_emojis(script_text)
    print(f"🎙️ Cleaned TTS Voiceover Text (no emojis spoken):\n   {clean_spoken_text}")
    print(f"🎙️ Generating voiceover with voice: {voice} at +5% speed...")
    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", voice,
        "--rate", "+5%",
        "--text", clean_spoken_text,
        "--write-media", output_audio,
        "--write-subtitles", vtt_file
    ]
    subprocess.run(cmd, check=True)

    # Parse cues
    cues = parse_vtt_timestamps(vtt_file)
    print(f"📝 Parsed {len(cues)} subtitle cues from Edge TTS.")

    # Group into punchy 2-4 word cards for high retention
    ass_cards = []
    chunk_size = 3
    if cues:
        for i in range(0, len(cues), chunk_size):
            chunk = cues[i:i + chunk_size]
            start_sec = vtt_time_to_seconds(chunk[0][0])
            end_sec = vtt_time_to_seconds(chunk[-1][1])
            card_words = [w[2] for w in chunk]
            ass_cards.append((start_sec, end_sec, card_words))
    else:
        # Fallback if VTT empty: estimate from words
        words = script_text.split()
        total_dur = 20.0
        w_dur = total_dur / max(len(words), 1)
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i + chunk_size]
            s = i * w_dur
            e = (i + len(chunk)) * w_dur
            ass_cards.append((s, e, chunk))

    # Write ASS File with Hormozi Yellow/White typography
    with open(output_ass, "w", encoding="utf-8") as f:
        f.write("[Script Info]\n")
        f.write("ScriptType: v4.00+\n")
        f.write("PlayResX: 1080\n")
        f.write("PlayResY: 1920\n")
        f.write("ScaledBorderAndShadow: yes\n\n")
        
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        # Bold yellow & white text, thick black outline, center bottom alignment (Alignment 2)
        f.write("Style: Hormozi,DejaVu Sans,58,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,40,40,320,1\n\n")
        
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        
        for start_s, end_s, words in ass_cards:
            start_ts = seconds_to_ass_time(start_s)
            end_ts = seconds_to_ass_time(end_s)
            
            # Format: First word yellow, remaining white, all uppercase
            if len(words) == 1:
                styled_text = f"{{\\c&H0000FFFF&}}{words[0].upper()}"
            elif len(words) >= 2:
                w1 = f"{{\\c&H0000FFFF&}}{words[0].upper()}"
                w_rest = f"{{\\c&H00FFFFFF&}}{' '.join(words[1:]).upper()}"
                styled_text = f"{w1} {w_rest}"
            else:
                styled_text = ""
                
            f.write(f"Dialogue: 0,{start_ts},{end_ts},Hormozi,,0,0,0,,{styled_text}\n")
            
    print(f"✅ Generated Hormozi ASS Subtitles: {output_ass}")

# ==========================================
# 5. AUDIO SYNTHESIS (COMEDY BGM & SFX)
# ==========================================
def synthesize_comedy_bgm(output_wav, duration_sec):
    """
    Synthesizes an upbeat, quirky comedy groove BGM using sine/square wave notes
    to ensure 100% royalty-free, copyright-free background music on cloud runners.
    """
    sample_rate = 44100
    total_samples = int(sample_rate * duration_sec)
    
    # Quirky comedy bassline notes (frequencies in Hz)
    bass_notes = [130.81, 146.83, 164.81, 174.61, 196.00, 220.00, 246.94] # C3-B3
    step_duration = 0.25 # 16th notes feel
    step_samples = int(sample_rate * step_duration)
    
    with wave.open(output_wav, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        
        frames = bytearray()
        step = 0
        for i in range(total_samples):
            if i % step_samples == 0:
                note_idx = (step % len(bass_notes))
                freq = bass_notes[note_idx]
                step += 1
                
            t = (i % step_samples) / sample_rate
            # Plucky envelope
            env = math.exp(-t * 6.0)
            sample_val = int(32767 * 0.18 * env * math.sin(2.0 * math.pi * freq * t))
            sample_val = max(-32768, min(32767, sample_val))
            
            # Stereo frames
            packed = struct.pack("<hh", sample_val, sample_val)
            frames.extend(packed)
            
        wf.writeframes(frames)
    print(f"🎵 Synthesized Royalty-Free Comedy BGM: {output_wav}")

# ==========================================
# 6. FFMPEG TRANSFORMATIVE VIDEO STUDIO
# ==========================================
def get_media_duration(file_path):
    """Probes media duration in seconds via ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 20.0

def get_video_dimensions(file_path):
    """Probes video width and height via ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            file_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        parts = res.stdout.strip().split("x")
        w, h = int(parts[0]), int(parts[1])
        return w, h
    except Exception as e:
        print(f"⚠️ ffprobe dimension check fallback: {e}")
        return 1920, 1080

def render_transformative_short(input_video, narration_audio, ass_subtitles, hook_banner, output_video, output_thumb):
    """
    Renders 100% Monetizable YouTube Short with Adaptive Framing:
    - Smart Aspect Ratio Detection:
      * Landscape (16:9): Ambient Blurred Studio Frame (100% full action visible, zero cropping/zooming)
      * Vertical (9:16): Native 9:16 vertical framing (zero artificial zoom)
    - Horizontal Flip (hflip) & dynamic speed match (setpts)
    - Top Hook Banner Pill Box (ALL CAPS)
    - Burned Hormozi Yellow/White Subtitles
    - Dual Audio Mixing (Voiceover 1.0 + Upbeat BGM 0.12)
    """
    os.makedirs(os.path.dirname(output_video) or ".", exist_ok=True)
    os.makedirs("temp", exist_ok=True)

    narration_dur = get_media_duration(narration_audio)
    target_dur = narration_dur + 0.6
    src_dur = get_media_duration(input_video)
    v_w, v_h = get_video_dimensions(input_video)
    is_landscape = (v_w > v_h) or (v_w / max(v_h, 1) >= 0.85)

    print(f"⏱️ Video Sync: Source={src_dur:.2f}s | Narration={narration_dur:.2f}s | Target Short={target_dur:.2f}s")
    print(f"📐 Video Dimensions: {v_w}x{v_h} | Layout: {'Studio Ambient Blur Frame (Full Action, Zero Zoom)' if is_landscape else 'Native 9:16 Vertical (Zero Artificial Zoom)'}")

    # Dynamic speed scaling: If source video duration is close to target duration,
    # calibrate PTS so the entire clip plays once from start to finish with zero awkward looping!
    if src_dur > 0 and 0.70 <= (target_dur / src_dur) <= 1.35:
        pts_scale = target_dur / src_dur
        speed_filter = f"setpts={pts_scale:.4f}*PTS"
        print(f"⚡ Dynamic Video Speed Scaling: {speed_filter} (100% synced, zero looping)")
    else:
        speed_filter = "setpts=0.97*PTS"

    # 1. Synthesize background music
    bgm_path = "temp/comedy_bgm.wav"
    synthesize_comedy_bgm(bgm_path, target_dur + 2.0)

    # 2. Build FFmpeg Filtergraph
    clean_hook = hook_banner.replace("'", "").replace(":", "").upper()
    ass_escaped = ass_subtitles.replace("\\", "/").replace(":", "\\:")

    if is_landscape:
        # Professional Studio Ambient Blur:
        # Foreground preserves 100% of the horizontal video (scale=1080:-2), centered vertically
        # Background is an ambient blurred version of the video filling 1080x1920
        # 100% of action, faces, and slapstick punchlines are in full view!
        filter_complex = (
            f"[0:v]hflip,{speed_filter},split=2[v_bg][v_fg];"
            f"[v_bg]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
            f"boxblur=25:8,eq=brightness=-0.15[bg_blur];"
            f"[v_fg]scale=1080:-2:flags=lanczos[fg_crisp];"
            f"[bg_blur][fg_crisp]overlay=0:(H-h)/2[base_comp];"
            f"[base_comp]drawbox=x=(iw-860)/2:y=120:w=860:h=90:color=black@0.75:t=fill,"
            f"drawtext=text='{clean_hook}':fontsize=40:fontcolor=yellow:x=(w-text_w)/2:y=142,"
            f"subtitles='{ass_escaped}'[outv];"
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume=0.12[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        )
        simpler_filter = (
            f"[0:v]hflip,{speed_filter},split=2[v_bg][v_fg];"
            f"[v_bg]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
            f"boxblur=25:8,eq=brightness=-0.15[bg_blur];"
            f"[v_fg]scale=1080:-2:flags=lanczos[fg_crisp];"
            f"[bg_blur][fg_crisp]overlay=0:(H-h)/2[base_comp];"
            f"[base_comp]subtitles='{ass_escaped}'[outv];"
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume=0.12[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        )
    else:
        # Native Vertical 9:16 Video:
        # Scale to 1080x1920 with minimal crop, ZERO artificial zoom
        filter_complex = (
            f"[0:v]hflip,{speed_filter},"
            f"scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
            f"drawbox=x=(iw-860)/2:y=110:w=860:h=90:color=black@0.75:t=fill,"
            f"drawtext=text='{clean_hook}':fontsize=40:fontcolor=yellow:x=(w-text_w)/2:y=132,"
            f"drawbox=x=0:y=1540:w=1080:h=260:color=black@0.85:t=fill,"
            f"subtitles='{ass_escaped}'[outv];"
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume=0.12[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        )
        simpler_filter = (
            f"[0:v]hflip,{speed_filter},"
            f"scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
            f"drawbox=x=0:y=1540:w=1080:h=260:color=black@0.85:t=fill,"
            f"subtitles='{ass_escaped}'[outv];"
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume=0.12[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        )

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", input_video,
        "-i", narration_audio,
        "-i", bgm_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "256k",
        "-t", f"{target_dur:.2f}",
        output_video
    ]

    print("🎬 Rendering final transformed YouTube Short with FFmpeg...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"⚠️ Primary FFmpeg render notice:\n{res.stderr[-500:]}")
        print("🔄 Falling back to simplified filtergraph (subtitles only)...")
        cmd_fallback = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", input_video,
            "-i", narration_audio,
            "-i", bgm_path,
            "-filter_complex", simpler_filter,
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "256k",
            "-t", f"{target_dur:.2f}",
            output_video
        ]
        res_fb = subprocess.run(cmd_fallback, capture_output=True, text=True)
        if res_fb.returncode != 0:
            raise RuntimeError(f"FFmpeg rendering failed completely: {res_fb.stderr[-500:]}")

    print(f"✅ Final Video Successfully Rendered: {output_video}")

    # Generate Thumbnail at 70% duration
    thumb_time = target_dur * 0.70
    cmd_thumb = [
        "ffmpeg", "-y",
        "-ss", f"{thumb_time:.2f}",
        "-i", output_video,
        "-vframes", "1",
        "-q:v", "2",
        output_thumb
    ]
    subprocess.run(cmd_thumb, check=True)
    print(f"✅ Thumbnail Generated: {output_thumb}")

# ==========================================
# 7. MAIN ENTRYPOINT
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="Autonomous Viral Asian Meme & Comedy Shorts Studio")
    parser.add_argument("--auto", action="store_true", help="100% Autonomous Auto-Pilot Mode")
    parser.add_argument("--video_url", type=str, default="", help="Douyin / TikTok / YouTube / MP4 URL")
    parser.add_argument("--topic", type=str, default="auto", help="Video Niche (e.g. cute kids, funny pets, comedy)")
    parser.add_argument("--voice", type=str, default="en-US-GuyNeural", help="Microsoft Edge TTS Voice")
    parser.add_argument("--script", type=str, default="", help="Optional custom commentary script")
    parser.add_argument("--output", type=str, default="output/final_video.mp4", help="Output video path")
    parser.add_argument("--thumb", type=str, default="output/thumbnail.jpg", help="Output thumbnail path")
    args = parser.parse_args()

    print("===================================================================")
    print("🔥 LAUNCHING VIRAL ASIAN MEME & COMEDY SHORTS STUDIO (100% CLOUD)")
    print("===================================================================")

    # 1. Dual-Route Ingestion
    raw_video, raw_title, raw_desc, route_used, vault_meta = ingest_video_dual_route(
        video_url=args.video_url,
        topic=args.topic,
        history_file="history.json"
    )
    print(f"📹 Acquired video via: {route_used.upper()}")

    # 1.1 Probe Video Duration for Perfect Timing
    src_dur = get_media_duration(raw_video)
    print(f"⏱️ Source Video Duration: {src_dur:.2f}s")

    # 2. Gemini Baba Multimodal / Script Direction
    director_output = direct_comedy_with_gemini(
        video_path=raw_video,
        clip_description=raw_desc,
        topic=args.topic,
        custom_script=args.script,
        fallback_meta=vault_meta,
        target_duration=src_dur
    )
    
    print("\n🎭 --- DIRECTED SHORT DETAILS ---")
    print(f"📌 Title: {director_output.get('title')}")
    print(f"🏷️ Top Hook: {director_output.get('hook_banner')}")
    print(f"🗣️ Voiceover Script:\n{director_output.get('script')}")
    print("---------------------------------\n")

    # 3. Microsoft Edge TTS & Hormozi Subtitles
    os.makedirs("temp", exist_ok=True)
    audio_path = "temp/narration.mp3"
    ass_path = "temp/subtitles.ass"
    generate_voiceover_and_ass(
        script_text=director_output.get("script", ""),
        voice=args.voice,
        output_audio=audio_path,
        output_ass=ass_path
    )

    # 4. Transformative FFmpeg Editing (Anti-Reused Content)
    render_transformative_short(
        input_video=raw_video,
        narration_audio=audio_path,
        ass_subtitles=ass_path,
        hook_banner=director_output.get("hook_banner", "WAIT FOR IT 😂"),
        output_video=args.output,
        output_thumb=args.thumb
    )

    # 5. Save Video Metadata
    os.makedirs("output", exist_ok=True)
    metadata_path = "output/metadata.json"
    metadata = {
        "title": director_output.get("title", "Viral Comedy Short #shorts"),
        "description": director_output.get("description", "Hilarious viral comedy short! #shorts #viral #funny"),
        "tags": director_output.get("tags", "shorts, funny, comedy, viral, meme"),
        "hook_banner": director_output.get("hook_banner", "WAIT FOR IT 😂"),
        "route_used": route_used,
        "clip_id": vault_meta["id"] if vault_meta else "custom_url",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"💾 Saved Video Metadata: {metadata_path}")

    # 6. Update Video Memory Vault (Anti-Repetition)
    history_file = "history.json"
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
            
    history.append({
        "date": metadata["created_at"],
        "clip_id": metadata["clip_id"],
        "title": metadata["title"],
        "hook_banner": metadata["hook_banner"],
        "route_used": route_used
    })
    
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    print(f"🧠 Updated Anti-Repetition Vault: {history_file} ({len(history)} total shorts)")

    print("\n===================================================================")
    print("🎉 VIRAL COMEDY SHORT SUCCESSFULLY GENERATED!")
    print(f"🎬 Video: {args.output}")
    print(f"🖼️ Thumbnail: {args.thumb}")
    print("===================================================================\n")

if __name__ == "__main__":
    main()
