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
import asyncio
import shutil

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ==========================================
# 1. LIVE CHINESE DOUYIN INGESTION ENGINE
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
        print(f"🔍 [TikWM] Querying watermark-free API for: {video_url}")
        resp = requests.post("https://www.tikwm.com/api/", data={"url": video_url}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and "data" in data and "play" in data["data"]:
                play_url = data["data"]["play"]
                title = data["data"].get("title", "Viral Chinese Comedy")
                print("✅ [TikWM] Found direct video stream! Downloading...")
                if download_file_stream(play_url, dest_path):
                    return True, title
    except Exception as e:
        print(f"⚠️ [TikWM] Error: {e}")
    return False, ""

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

def extract_preview_frames(video_path, num_frames=4):
    """
    Extracts 4 story-arc JPEG keyframes (Hook, Setup, Rising Tension, Climax Punchline)
    giving Gemini Baba complete visual story context in milliseconds.
    """
    frames = []
    dur = get_media_duration(video_path)
    # Story-arc checkpoints: 8% (Hook), 35% (Setup), 65% (Tension), 90% (Punchline/Twist)
    checkpoints = [
        max(0.4, dur * 0.08),
        dur * 0.35,
        dur * 0.65,
        min(dur - 0.5, dur * 0.90)
    ]
    for idx, t in enumerate(checkpoints):
        out_f = f"{video_path}_frame_{idx+1}.jpg"
        cmd = [
            "ffmpeg", "-y", "-ss", f"{t:.2f}",
            "-i", video_path, "-vframes", "1",
            "-q:v", "4", out_f
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(out_f) and os.path.getsize(out_f) > 1000:
            with open(out_f, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
                frames.append(b64_data)
            try:
                os.remove(out_f)
            except Exception:
                pass
    return frames

def audition_candidates_with_gemini(candidates, gemini_key):
    """
    AI Executive Producer & Quality Judge:
    Auditions top viral candidates using Gemini Multimodal Vision to pick the single best winner based on:
    1. US, UK & Western viral appeal (funny pets, physical comedy, fails, instant karma).
    2. Zero or minimal burned-in Chinese dialogue subtitles / text watermarks.
    3. Immediate 2-second swipe-stopper visual hook.
    """
    os.makedirs("temp/audition", exist_ok=True)
    audition_data = []

    dl_headers = {"User-Agent": "okhttp/3.10.0.1"}
    for idx, c in enumerate(candidates):
        cand_path = os.path.join("temp", "audition", f"cand_{idx}.mp4")
        try:
            with requests.get(c["url"], headers=dl_headers, stream=True, timeout=20) as r:
                r.raise_for_status()
                with open(cand_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*256):
                        if chunk:
                            f.write(chunk)
            if os.path.exists(cand_path) and os.path.getsize(cand_path) > 30000:
                frames_b64 = extract_preview_frames(cand_path, num_frames=4)
                if frames_b64:
                    audition_data.append({
                        "index": idx + 1,
                        "candidate": c,
                        "video_path": cand_path,
                        "frames": frames_b64
                    })
        except Exception as e:
            print(f"⚠️ Audition candidate {idx+1} download notice: {e}")

    if not audition_data:
        return None

    content_parts = [{
        "text": (
            "You are the Executive Producer & Quality Judge for an international viral YouTube Shorts studio "
            "targeting audiences in the US, UK, and Western countries.\n\n"
            "Evaluate the candidate video clips below (each candidate has 4 chronological story-arc frames shown: Hook, Setup, Tension, Punchline):\n"
        )
    }]

    for item in audition_data:
        c = item["candidate"]
        content_parts.append({
            "text": f"\n--- CANDIDATE #{item['index']} ---\nCaption: {c['desc']}\nLikes: {c['likes']:,} | Shares: {c['shares']:,}\nVisual Frames:"
        })
        for f_b64 in item["frames"]:
            content_parts.append({
                "inlineData": {
                    "mimeType": "image/jpeg",
                    "data": f_b64
                }
            })

    content_parts.append({
        "text": (
            "\n=======================================================\n"
            "STRICT BRAND MANDATE (Crazy Vault Channel):\n"
            "We ONLY publish high-stakes PHYSICAL COMEDY, insane PRANKS, hilarious FAILS, or crazy ANIMAL CHAOS.\n"
            "ABSOLUTE DISQUALIFICATION (winner_index: 0 - ZERO TOLERANCE):\n"
            "- ANY video of people just sitting at a dinner table, eating food, drinking, or chatting.\n"
            "- ANY talking head, dialogue drama, skit with speaking, interview, or personal vlog.\n"
            "- ANY wedding, romance, couple drama, makeup, beauty, haircut, or crafts.\n"
            "- ANY video where NO physical action, fall, prank, or funny pet moment occurs!\n"
            "CRITICAL MANDATE: Crazy Vault is an ACTION & PHYSICAL COMEDY channel. We ONLY accept:\n"
            "1. Real physical fails, slipping, falling, getting startled, instant karma, or gym fails.\n"
            "2. Hilarious pet & animal chaos (cats, dogs, wildlife doing funny things).\n"
            "3. Insane human acrobatics, reflexes, or crazy visual stunts.\n\n"
            "If NO candidate meets this standard (e.g. if it's just people eating or chatting), YOU MUST RETURN winner_index: 0 so we swipe for better clips!\n\n"
            "PRIMARY TARGET AUDIENCE: 🇺🇸 UNITED STATES (USA - 50%+ Core Demographic)!\n"
            "SELECTION CRITERIA:\n"
            "1. 🇺🇸 USA VIRAL COMEDY & TWIST DNA (60%): Must have maximum appeal to American viewers (hilarious pet chaos, savage pranks, gym/sports fails, 'bro thought he was slick' fails, instant karma)!\n"
            "2. 🚫 ZERO CHINESE TEXT (30%): Clean visual footage with zero burned-in Chinese dialogue subtitles.\n"
            "3. 🧲 2-SECOND AMERICAN HOOK (10%): Opening visual that instantly stops a scrolling American teenager or young adult.\n\n"
            "Respond in valid JSON format:\n"
            "{\n"
            '  "winner_index": 1,\n'
            '  "winner_reason": "Candidate #X has zero Chinese text and features a universal funny dog moment that US/UK viewers will love.",\n'
            '  "cleanliness_score": 10,\n'
            '  "western_appeal_score": 9\n'
            "}\n"
        )
    })

    models_to_try = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-flash-latest", "gemini-flash-lite-latest"]
    for mod in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": content_parts}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048, "responseMimeType": "application/json"}
            }
            r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=25)
            if r.status_code == 200:
                data = r.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.I)
                cleaned = re.sub(r"\s*```$", "", cleaned)
                json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if json_match:
                    cleaned = json_match.group(0)
                parsed = json.loads(cleaned)
                w_idx = int(parsed.get("winner_index", 1))
                reason = parsed.get("winner_reason", "Selected by AI Producer")
                clean_sc = parsed.get("cleanliness_score", "N/A")
                west_sc = parsed.get("western_appeal_score", "N/A")

                if w_idx == 0:
                    print(f"🚫 [AI AUDITION PRODUCER] Entire audition batch DISQUALIFIED (winner_index: 0)!")
                    print(f"   💡 Reason: {reason}")
                    return None

                chosen = next((item for item in audition_data if item["index"] == w_idx), None)
                if not chosen:
                    print(f"⚠️ [AI AUDITION PRODUCER] Winner index {w_idx} not found. Disqualifying batch.")
                    return None

                print(f"🏆 [AI AUDITION PRODUCER] Winner Selected: Candidate #{chosen['index']}!")
                print(f"   🇬🇧/🇺🇸 Western Appeal: {west_sc}/10 | 🚫 Cleanliness: {clean_sc}/10")
                print(f"   💡 Reason: {reason}")

                chosen["candidate"]["pre_downloaded_path"] = chosen["video_path"]
                return chosen["candidate"]
        except Exception as e:
            print(f"⚠️ Gemini audition {mod} notice: {e}")

    return None

def ingest_live_chinese_video(video_url="", topic="auto", history_file="history.json"):
    """
    100% Dynamic Chinese Douyin Video Ingestion:
    - Multi-Swipe Aggregation: swipes high-yield ByteDance mobile endpoints.
    - Strict Virality Gatekeeper: Only accepts Mega-Viral clips (100K+ Likes Priority, 50K+ floor).
    - Bulletproof Anti-Duplicate memory matching raw ID and douyin_ prefixed ID.
    - Direct unwatermarked HD download from ByteDance China CDN.
    """
    os.makedirs("temp", exist_ok=True)
    raw_video_path = os.path.join("temp", "source_video.mp4")

    # 1. Custom URL given by user
    if video_url and video_url.strip():
        url = video_url.strip()
        print(f"\n🎯 Processing Custom Video URL: {url}")
        if url.endswith(".mp4") or url.endswith(".webm"):
            if download_file_stream(url, raw_video_path):
                return raw_video_path, "Viral Comedy Short #shorts", "Watch this hilarious moment unfold 💀", "custom_url", {"id": "custom_url"}
        if "youtube.com" in url or "youtu.be" in url:
            print(f"📥 Downloading YouTube Video via yt-dlp: {url}")
            try:
                import yt_dlp
                ydl_opts = {
                    'outtmpl': raw_video_path,
                    'format': 'mp4/bestvideo+bestaudio/best',
                    'overwrites': True,
                    'quiet': True
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    yt_title = info.get('title', 'Viral Comedy Short #shorts')
                    yt_desc = info.get('description', '')
                if os.path.exists(raw_video_path) and os.path.getsize(raw_video_path) > 10000:
                    print("✅ Successfully downloaded YouTube video!")
                    return raw_video_path, yt_title, yt_desc, "youtube_custom", {"id": "youtube_custom"}
            except Exception as e:
                print(f"⚠️ YouTube download error: {e}")

        if "douyin.com" in url or "tiktok.com" in url:
            ok, det_title = try_tikwm_download(url, raw_video_path)
            if ok:
                return raw_video_path, det_title or "Viral Asian Comedy #shorts", "Viral Douyin comedy clip", "custom_url", {"id": "custom_url"}

    # 2. Live Chinese Douyin ByteDance Feed API (Direct from China CDN)
    print(f"\n=======================================================")
    print(f"🚀 [CHINA LIVE STREAM] Scanning Live Douyin for 100K+ Likes Mega-Clips...")
    print(f"=======================================================")

    used_ids = set()
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    cid = str(item.get("clip_id", "")).strip()
                    if cid:
                        used_ids.add(cid)
                        clean_id = cid.replace("douyin_", "").replace("vault_", "").strip()
                        if clean_id:
                            used_ids.add(clean_id)
        except Exception:
            pass

    # Keyword mappings for Chinese Douyin topics
    topic_keywords = {
        "suspense": ["\u53cd\u8f6c", "\u60ca\u559c", "\u610f\u5916", "\u795e\u8f6c\u6298", "\u6ca1\u60f3\u5230", "\u7ed3\u5c40"],
        "prank": ["\u6574\u86ca", "\u6076\u641e", "\u6076\u4f5c\u5267", "\u6574\u4eba"],
        "pets": ["\u840c\u5ba0", "\u72d7\u72d7", "\u732b\u54aa", "\u5ba0\u7269", "\u6c6a\u661f\u4eba"],
        "comedy": ["\u6c99\u96d5", "\u641e\u7b11", "\u5e7d\u9ed8", "\u7b11\u6599"]
    }
    keywords = []
    if topic and topic.strip().lower() != "auto":
        keywords = topic_keywords.get(topic.strip().lower(), [topic.strip().lower()])

    endpoints = [
        "https://aweme.snssdk.com/aweme/v1/feed/?count=35&pull_type=2",
        "https://api.amemv.com/aweme/v1/feed/?count=35&pull_type=1",
        "https://aweme.snssdk.com/aweme/v1/feed/?count=35&type=0&max_cursor=0",
        "https://api3-normal-c-hl.amemv.com/aweme/v1/feed/?count=35&channel_id=0",
        "https://aweme.snssdk.com/aweme/v1/feed/?count=35&feed_style=0&filter_warn=0",
        "https://aweme.snssdk.com/aweme/v1/feed/?count=35&device_platform=android&version_code=250000"
    ]
    headers = {"User-Agent": "okhttp/3.10.0.1", "Accept": "application/json"}

        # BRAND PURITY BLACKLIST: Zero tolerance for ads, crafts, farming, cooking, makeup, vlogs, weddings
    brand_exclusion_blacklist = [
        # Commercial / Ads / E-Commerce
        "带货", "下单", "广告", "直播", "链接", "点击", "购买", "包邮", "领券", "优惠", "同款", "橱窗",
        # Art, Painting, Sculpture, Crafts (Zero corn art / drawing reveals!)
        "画画", "沙画", "微缩", "雕刻", "非遗", "手艺", "手工制作", "书法", "手绘", "刺绣", "木工", "国风",
        # Agriculture, Farming, Harvest
        "庄稼", "玉米地", "丰收", "种地", "麦子", "田地", "农活",
        # Food, Cooking, Mukbang, Dinner Tables, Eating, Drinking, Banquets
        "做饭", "美食制作", "烹饪", "吃播", "探店", "食谱", "教程", "厨房", "家常菜", 
        "吃饭", "聚餐", "饭局", "酒局", "请客", "餐桌", "餐厅", "火锅", "烤肉", "喝茶", "吃席", "下馆子", "大排档", "吃顿好的",
        # Dialogue Skits, Talking Heads, Interviews, Blind Dates, Daily Chat
        "相亲", "聊天", "对话", "段子剧", "情景剧", "短剧", "访谈", "采访", "连麦", "唠嗑", "说书", "讲故事", "小品", "相声", "谈心",
        # Vlogs, Daily Life, Talking Heads, Selfies, Cringe Diaries (Zero Vlogs Allowed!)
        "vlog", "Vlog", "VLOG", "生活记录", "记录生活", "记录美好生活", "碎碎念", "沉浸式化妆", "开箱", "好物分享", 
        "测评", "种草", "打卡", "自媒体", "独居生活", "一个人生活", "治愈系", "慢生活", "生活碎片",
        # Weddings, Romance, Brides, Grooms (Zero Wedding / Love Vlogs!)
        "婚礼", "结婚现场", "新娘", "新郎", "伴娘", "伴郎", "接亲", "敬酒", "婚纱", "婚宴", "领证", "求婚", "秀恩爱",
        # Beauty, Makeup, Transformations (Zero Beauty / Makeovers!)
        "化妆教程", "美妆博主", "变装秀", "换装秀", "改造前后", "变帅", "变美", "穿搭分享", "发型设计", "美甲", "护肤心得", "整容",
        # News, Speeches, Interviews
        "新闻联播", "正能量", "演讲", "采访", "街访", "文案语录"
    ]
    # STRICT GENRE WHITELIST: Hardcore Comedy Fails, Slapstick, Pranks, Animal Chaos & Viral Humor
    viral_tags = [
        # Explicit Physical Fails & Instant Karma
        "翻车", "翻车现场", "打脸", "大冤种", "社死", "作死", "滑倒", "摔倒", "失误", "尴尬", "名场面", "反转", "神操作", "神走位",
        # Pure Comedy, Humor & Meme
        "搞笑", "幽默", "沙雕", "整蛊", "恶搞", "笑死", "逗比", "逆天操作", "哈哈", "爆笑", "纯搞笑", "笑抽", "兄弟",
        # Pet & Animal Chaos
        "修狗", "猫咪", "萌宠", "宠物搞笑", "动物搞笑", "拆家", "狗子", "喵星人", "动物", "小狗", "小猫"
    ]

    # CUMULATIVE MULTI-ROUND MEMORY POOL: Collects viral clips across all 10 rounds without losing any
    all_accumulated_candidates = []
    seen_candidate_ids = set()

    for attempt in range(10):
        print(f"\n🔄 [MULTI-SWIPE INGESTION] Aggregating massive video pool (Round {attempt+1}/10)...")
        raw_items = []
        seen_batch_ids = set()

        for swipe_idx, ep_url in enumerate(endpoints):
            try:
                sep = "&" if "?" in ep_url else "?"
                url_with_ts = f"{ep_url}{sep}_rticket={int(time.time() * 1000)}&ts={int(time.time())}"
                resp = requests.get(url_with_ts, headers=headers, timeout=12)
                if resp.status_code == 200:
                    feed_list = resp.json().get("aweme_list", [])
                    new_count = 0
                    for it in feed_list:
                        aid = str(it.get("aweme_id", "")).strip()
                        if aid and aid not in seen_batch_ids:
                            seen_batch_ids.add(aid)
                            raw_items.append(it)
                            new_count += 1
                    print(f"   📲 Swipe {swipe_idx+1}: +{new_count} candidates (Running total: {len(raw_items)})")
            except Exception as e:
                print(f"   ⚠️ Swipe {swipe_idx+1} notice: {e}")
            time.sleep(0.2)

        print(f"📦 Total Unique Scanned Pool: {len(raw_items)} candidate clips in memory!")

        for item in raw_items:
            aweme_id = str(item.get("aweme_id", "")).strip()
            # Bulletproof duplicate check: check both pure ID and prefixed ID
            if not aweme_id or aweme_id in used_ids or f"douyin_{aweme_id}" in used_ids:
                continue

            # 1. Skip Commercial Ads and E-Commerce Shopping
            if item.get("is_ads") or item.get("commerce_info"):
                continue
            desc = item.get("desc", "")
            if any(w in desc for w in brand_exclusion_blacklist):
                continue

            # 2. SWEET SPOT 10.0s - 38.0s DURATION GATEKEEPER
            dur = item.get("duration", 0) / 1000.0
            if not (10.0 <= dur <= 38.0):
                continue

            # 3. Check direct playable stream URL
            play_urls = item.get("video", {}).get("play_addr", {}).get("url_list", [])
            if not play_urls:
                continue

            # 4. STRICT COMEDY, SUSPENSE & PLOT TWIST GATEKEEPER
            # Video MUST contain at least one approved genre keyword/tag
            is_genre_match = any(vt in desc for vt in viral_tags)
            if keywords:
                is_genre_match = is_genre_match or any(kw in desc for kw in keywords)
            if not is_genre_match:
                continue

            # 5. Extract Real Metrics (Likes, Shares, Comments)
            stats = item.get("statistics", {})
            likes = stats.get("digg_count", 0)
            shares = stats.get("share_count", 0)
            comments = stats.get("comment_count", 0)

            # 5. Virality Score calculation (Likes + 10x Shares + 5x Comments)
            virality_score = likes + (shares * 10) + (comments * 5)

            # Boost for comedy/twist tags
            for vt in viral_tags:
                if vt in desc:
                    virality_score += 50000

            # Boost for user topic keywords
            for kw in keywords:
                if kw in desc:
                    virality_score += 100000

            # Golden duration sweet spot bonus (18s to 35s)
            if 18.0 <= dur <= 35.0:
                virality_score += 50000

            is_100k_plus = (likes >= 100000)
            is_50k_plus = (likes >= 50000)

            if aweme_id not in seen_candidate_ids:
                seen_candidate_ids.add(aweme_id)
                all_accumulated_candidates.append({
                    "score": virality_score,
                    "likes": likes,
                    "shares": shares,
                    "comments": comments,
                    "is_100k_plus": is_100k_plus,
                    "is_50k_plus": is_50k_plus,
                    "dur": dur,
                    "id": aweme_id,
                    "desc": desc,
                    "url": play_urls[0]
                })

        # Strict Quality Gatekeeper: Evaluates cumulative pool from all rounds
        tier1 = [c for c in all_accumulated_candidates if c["is_100k_plus"]]
        tier2 = [c for c in all_accumulated_candidates if c["is_50k_plus"]]

        chosen_pool = None
        tier_badge = ""

        if tier1:
            chosen_pool = tier1
            tier_badge = f"🔥 TIER-1 (100K+ MEGA-VIRAL: {len(tier1)} candidates across {attempt+1} rounds)"
        elif tier2 and (attempt >= 2 or len(tier2) >= 2):
            chosen_pool = tier2
            tier_badge = f"⚡ TIER-2 (50K+ HIGH-VIRAL: {len(tier2)} candidates across {attempt+1} rounds)"
        elif attempt >= 2 and all_accumulated_candidates:
            # Pick highest scoring comedy clip once we have accumulated multiple rounds
            chosen_pool = all_accumulated_candidates
            tier_badge = f"✨ TIER-3 (TOP COMEDY ENGAGEMENT: {len(all_accumulated_candidates)} pool across {attempt+1} rounds)"

        if chosen_pool:
            chosen_pool.sort(key=lambda x: x["score"], reverse=True)
            gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()

            top_pick = chosen_pool[0]
            if chosen_pool and gemini_key:
                audition_pool = chosen_pool[:3]
                print(f"\n🎬 [AI AUDITION PRODUCER] Auditioning Top {len(audition_pool)} Finalists for Visual Slapstick Action...")
                winner = audition_candidates_with_gemini(audition_pool, gemini_key)
                if winner:
                    top_pick = winner
                elif attempt < 9:
                    print("🚫 [AI AUDITION PRODUCER] Candidates rejected (no physical action / boring talking head). Swiping fresh pool...")
                    time.sleep(1)
                    continue

            score = top_pick["score"]
            dur = top_pick["dur"]
            aweme_id = top_pick["id"]
            desc = top_pick["desc"]
            play_url = top_pick["url"]
            likes = top_pick["likes"]
            shares = top_pick["shares"]
            comments = top_pick["comments"]
            orig_web_url = f"https://www.douyin.com/video/{aweme_id}"

            print(f"\n🏆 [VIRAL QUALITY GATEKEEPER] Selected Rank #1 Clip! [{tier_badge}]")
            print(f"   🆔 Video ID: {aweme_id} ({dur:.1f}s)")
            print(f"   👍 Likes: {likes:,} | 🔄 Shares: {shares:,} | 💬 Comments: {comments:,}")
            print(f"   🚀 Virality Score: {score:,}")
            print(f"   🔗 Original Douyin Link: {orig_web_url}")
            print(f"   📝 Caption: {desc}")

            if top_pick.get("pre_downloaded_path") and os.path.exists(top_pick["pre_downloaded_path"]):
                print("⚡ Using pre-downloaded HD stream from AI Audition...")
                shutil.copyfile(top_pick["pre_downloaded_path"], raw_video_path)
            else:
                print(f"⬇️ Downloading direct unwatermarked HD stream from ByteDance China CDN...")
                dl_headers = {"User-Agent": "okhttp/3.10.0.1"}
                with requests.get(play_url, headers=dl_headers, stream=True, timeout=30) as dl_resp:
                    dl_resp.raise_for_status()
                    with open(raw_video_path, "wb") as f:
                        for chunk in dl_resp.iter_content(chunk_size=1024*512):
                            if chunk:
                                f.write(chunk)

            if os.path.exists(raw_video_path) and os.path.getsize(raw_video_path) > 50000:
                file_mb = os.path.getsize(raw_video_path) / (1024 * 1024)
                print(f"✅ Successfully downloaded brand new Chinese Douyin video ({file_mb:.2f} MB)!")
                meta = {
                    "id": f"douyin_{aweme_id}",
                    "aweme_id": aweme_id,
                    "douyin_url": orig_web_url,
                    "likes": likes,
                    "shares": shares,
                    "title": "Chinese TikTok Went Too Far 💀 #shorts",
                    "hook_banner": "WAIT FOR THE TWIST 💀" if "suspense" in (topic or "").lower() else "WAIT TILL THE END 💀",
                    "description": desc,
                    "fallback_script": "Wait for it, because bro really thought he had the master plan! Look at that unmatched confidence right before disaster strikes. The way he froze the second everything went completely wrong is pure comedy gold! You can literally see his whole soul leaving his body in 4K! What would you even do if this happened to you? Tell me in the comments right now! 💀"
                }
                return raw_video_path, meta["title"], desc, "douyin_live_china", meta
        else:
            print(f"⚠️ Round {attempt+1}: No 50K+/100K+ clip in this pool. Swiping again for mega-viral clip...")
            time.sleep(1)

    print("⚠️ Whitelist pool empty after 10 rounds. Running emergency wide comedy sweep...")
    for emergency_ep in [
        "https://aweme.snssdk.com/aweme/v1/feed/?count=50&pull_type=2",
        "https://api.amemv.com/aweme/v1/feed/?count=50&type=0"
    ]:
        try:
            r = requests.get(emergency_ep, headers=headers, timeout=10)
            if r.status_code == 200:
                for it in r.json().get("aweme_list", []):
                    aid = str(it.get("aweme_id", "")).strip()
                    if not aid or aid in used_ids or f"douyin_{aid}" in used_ids:
                        continue
                    dur = it.get("duration", 0) / 1000.0
                    if not (10.0 <= dur <= 38.0):
                        continue
                    desc = it.get("desc", "")
                    if any(w in desc for w in brand_exclusion_blacklist):
                        continue
                    purls = it.get("video", {}).get("play_addr", {}).get("url_list", [])
                    if not purls:
                        continue
                    st = it.get("statistics", {})
                    l = st.get("digg_count", 0)
                    all_accumulated_candidates.append({
                        "score": l + (st.get("share_count", 0) * 10),
                        "likes": l,
                        "shares": st.get("share_count", 0),
                        "comments": st.get("comment_count", 0),
                        "is_100k_plus": (l >= 100000),
                        "is_50k_plus": (l >= 50000),
                        "dur": dur,
                        "id": aid,
                        "desc": desc,
                        "url": purls[0]
                    })
        except Exception:
            pass
        if all_accumulated_candidates:
            break

    if all_accumulated_candidates:
        all_accumulated_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_pick = all_accumulated_candidates[0]
        score = top_pick["score"]
        dur = top_pick["dur"]
        aweme_id = top_pick["id"]
        desc = top_pick["desc"]
        play_url = top_pick["url"]
        likes = top_pick["likes"]
        shares = top_pick["shares"]
        comments = top_pick["comments"]
        orig_web_url = f"https://www.douyin.com/video/{aweme_id}"
        print(f"\n🏆 [EMERGENCY SWEEP] Selected Top Engaged Clip: {aweme_id} ({dur:.1f}s)")
        print(f"⬇️ Downloading direct unwatermarked HD stream from ByteDance China CDN...")
        dl_headers = {"User-Agent": "okhttp/3.10.0.1"}
        with requests.get(play_url, headers=dl_headers, stream=True, timeout=30) as dl_resp:
            dl_resp.raise_for_status()
            with open(raw_video_path, "wb") as f:
                for chunk in dl_resp.iter_content(chunk_size=1024*512):
                    if chunk:
                        f.write(chunk)
        if os.path.exists(raw_video_path) and os.path.getsize(raw_video_path) > 50000:
            meta = {
                "id": f"douyin_{aweme_id}",
                "aweme_id": aweme_id,
                "douyin_url": orig_web_url,
                "likes": likes,
                "shares": shares,
                "title": "Chinese TikTok Went Too Far 💀 #shorts",
                "hook_banner": "WAIT TILL THE END 💀",
                "description": desc,
                "fallback_script": "Wait for it, because bro really thought he had the master plan! Look at that unmatched confidence right before disaster strikes. The way he froze the second everything went completely wrong is pure comedy gold! You can literally see his whole soul leaving his body in 4K! What would you even do if this happened to you? Tell me in the comments right now! 💀"
            }
            return raw_video_path, meta["title"], desc, "douyin_live_china", meta

    raise RuntimeError("Critical: Could not acquire a fresh video from Douyin China API. Retrying...")

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

    # DYNAMIC TIMING & WORD LIMIT CALIBRATION (Tight speech-to-video lock)
    target_audio_dur = max(8.0, min(27.0, target_duration - 0.6))
    # Edge TTS GuyNeural at +16% speed delivers ~3.3 - 3.4 words per second
    word_target = int(target_audio_dur * 3.3)
    word_min = max(24, word_target - 3)
    word_max = min(92, word_target + 3)
    safe_audio_dur = target_audio_dur
    print(f"🎯 Calibrated Commentary Target: {target_audio_dur:.1f}s speech ({word_min}-{word_max} words) for {target_duration:.1f}s video")

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
            "You are the Head Comedy Director of an explosive viral animation & skit dubbing channel (Village Whispora style, but in fluent English for US/UK/Global audience)!\n"
            "CRITICAL FORMAT DIFFERENCE: Instead of an outside narrator talking about the video ('Bro really thought he was...'), THE CHARACTERS VISIBLE ON SCREEN TALK DIRECTLY TO EACH OTHER IN 1ST-PERSON LIVE COMEDY DIALOGUE!\n\n"
            "OUR RECURRING VIRAL COMEDY CAST:\n"
            "1. CHAD (Male Lead / Hero):\n"
            "   - Personality: Overconfident show-off, acts like a Hollywood action star or irresistible Casanova. Brags loudly about his skills, machine, or rizz, but panics instantly when things go wrong.\n"
            "   - Catchphrases: 'Watch this, baby!', 'Witness pure perfection!', 'Chloe, hop on!', 'Wait wait, NOT THE FACE!'\n"
            "2. CHLOE (Female Lead):\n"
            "   - Personality: Sassy, super smart, sarcastic girl who instantly calls out Chad's stupidity, roasts him, and laughs when he gets destroyed.\n"
            "   - Catchphrases: 'Chad, stop embarrassing yourself!', 'You are literally an idiot!', 'I don't know this man!', 'Hahaha, karma is beautiful!'\n"
            "3. KEVIN (Goofy Friend / Extra Guy):\n"
            "   - Personality: The totally clueless buddy or panicked bystander. Always does the wrong thing at the wrong time.\n"
            "   - Catchphrases: 'Wait, is that supposed to explode?!', 'Chad, did we break it?!', 'I didn't do it!'\n"
            "4. BUSTER (Dog / Pet / Animal):\n"
            "   - Personality: Savage, hungry, mischievous pet who treats humans like lunch or clowns them.\n"
            "   - Catchphrases: 'Target acquired!', 'Did someone order free lunch?!', 'Nom nom nom!'\n\n"
            "CASTING RULES FOR ON-SCREEN CHARACTERS:\n"
            "- If a guy is showing off / trying to do a stunt / acting cool -> Name him CHAD.\n"
            "- If a girl / woman is present -> Name her CHLOE.\n"
            "- If a second guy / friend / bystander is present -> Name him KEVIN.\n"
            "- If a dog / cat / pet / animal is interacting -> Name it BUSTER.\n\n"
            "CRITICAL RETENTION & PACING LAWS:\n"
            "1. 0s-3s HOOK: Chad or Chloe drops an immediate punchy line teasing the situation ('Chloe, feast your eyes on peak male performance!').\n"
            "2. MID-VIDEO BANTER: Rapid-fire back-and-forth dialogue matching on-screen physical actions and facial expressions.\n"
            "3. CLIMAX (Final 2-3s): The fail / twist lands! Chad screams or panics, Chloe roasts him or laughs!\n"
            "4. NO BORING EXPLANATIONS: Do NOT describe what happened like a documentary. Speak as the characters in real-time!\n"
            "5. WORD BUDGET: Total words across all dialogue lines combined MUST BE EXACTLY {word_min} to {word_max} words to fill {safe_audio_dur:.1f}s of video.\n"
            "Format your response as a valid raw JSON object with keys: title, hook_banner, characters_detected, dialogue, sfx_timeline, description, tags."
        )

        user_prompt = f"""
WATCH AND DIRECT THIS VIRAL VIDEO FOOTAGE AS A CHARACTER DUBBING SKIT (VILLAGE WHISPORA STYLE):
- Total Video Duration: {target_duration:.1f} seconds
- Channel Genre: Viral Slapstick Comedy & Dubbed Character Skits
- Recurring Cast: CHAD, CHLOE, KEVIN, BUSTER

DIRECTING RULES:
1. Examine the actors and actions on screen closely:
   - Who is acting cool or driving/running? Assign as CHAD.
   - Who is watching, reacting, or getting annoyed? Assign as CHLOE.
   - Any friend, assistant, or bystander? Assign as KEVIN.
   - Any dog, puppy, or animal? Assign as BUSTER.
2. Write rapid-fire comedic dialogue where the characters talk directly to each other!
3. The lines must chronologically match what is happening on screen:
   - Line 1 (0s-3s Hook): High-energy opener establishing Chad's boast or the conflict.
   - Lines 2-4 (Buildup): Hilarious argument / banter as the stunt progresses.
   - Final Lines (Climax): Disaster strikes! Chad panics, Chloe or Buster delivers the punchline!
4. Target word count across all dialogue lines combined: {word_min} to {word_max} words.

Provide JSON with:
- "title": High-curiosity American/Western viral meme title under 60 characters with funny emojis (💀, 😂, 😭) and #shorts featuring Chad, Chloe or the scene (e.g. "Chad Tried To Impress Chloe 💀 #shorts").
- "hook_banner": 3-5 words ALL CAPS punchy suspense hook banner matching the visual (e.g. "CHAD'S BIGGEST REGRET 💀").
- "characters_detected": ["CHAD", "CHLOE", "BUSTER"],
- "dialogue": [
    {{"speaker": "CHAD", "text": "Chloe, feast your eyes on peak male fitness! Hop on!"}},
    {{"speaker": "CHLOE", "text": "Chad, stop! You don't even have a driver's license!"}},
    {{"speaker": "BUSTER", "text": "Target locked! Time to chomp!"}},
    {{"speaker": "CHAD", "text": "Wait nice puppy, good puppy! AAAAAH CHLOE HELP!"}},
    {{"speaker": "CHLOE", "text": "Haha! Good boy Buster, bite him again!"}}
  ],
- "sfx_timeline": [
    {{"time": 0.4, "sound": "whoosh", "zoom": false}},
    {{"time": {min(safe_audio_dur, 12.0):.1f}, "sound": "vine_boom", "zoom": true}}
  ],
- "description": "Hilarious Chad and Chloe comedy dub! #shorts #viral #funny #comedy #crazyvault #plottwist",
- "tags": "shorts, funny, comedy, viral, meme, chad, chloe, kevin, hilarious"

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

        # Proven stable multimodal video models
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-flash-latest"
        ]
        print(f"🎯 Target Gemini models to try: {models_to_try}")
        for mod in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": content_parts}],
                    "systemInstruction": {"parts": [{"text": system_instruction}]},
                    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048, "responseMimeType": "application/json"}
                }
                r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=45)
                if r.status_code == 200:
                    data = r.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.I)
                    cleaned = re.sub(r"\s*```$", "", cleaned)
                    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                    if json_match:
                        cleaned = json_match.group(0)
                    parsed = json.loads(cleaned)
                    if ("dialogue" in parsed or "script" in parsed) and "title" in parsed:
                        if "dialogue" in parsed and isinstance(parsed["dialogue"], list) and "script" not in parsed:
                            parsed["script"] = " ".join(f"[{d.get('speaker','CHAD')}]: {d.get('text','')}" for d in parsed["dialogue"] if isinstance(d, dict))
                        print(f"🎉 Gemini Baba Village Whispora Director Success! Title: {parsed['title']}")
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
    print("💡 Using Curated Village Whispora Dub Script from Vault...")
    if fallback_meta and isinstance(fallback_meta, dict) and "title" in fallback_meta:
        return {
            "title": fallback_meta["title"],
            "hook_banner": fallback_meta.get("hook_banner", "CHAD'S BIGGEST REGRET 💀"),
            "characters_detected": ["CHAD", "CHLOE"],
            "dialogue": [
                {"speaker": "CHAD", "text": "Chloe, feast your eyes on peak male performance! Watch this move!"},
                {"speaker": "CHLOE", "text": "Chad, please stop before you embarrass both of us!"},
                {"speaker": "CHAD", "text": "Impossible! Nothing can stop the champion—WHOAAAA!"},
                {"speaker": "CHLOE", "text": "Hahaha! And down goes the champion in 4K!"}
            ],
            "script": fallback_meta.get("fallback_script", "Chad tried to show off and failed!"),
            "description": f"Hilarious Chad & Chloe dub! {fallback_meta['title']} #shorts #funny #viral #comedy",
            "tags": "shorts, funny, comedy, viral, meme, chad, chloe, kevin, hilarious"
        }

    return {
        "title": "Chad Tried To Impress Chloe 💀 #shorts",
        "hook_banner": "CHAD'S BIGGEST REGRET 💀",
        "characters_detected": ["CHAD", "CHLOE"],
        "dialogue": [
            {"speaker": "CHAD", "text": "Chloe, feast your eyes on peak male performance! Watch this move!"},
            {"speaker": "CHLOE", "text": "Chad, please stop before you embarrass both of us!"},
            {"speaker": "CHAD", "text": "Impossible! Nothing can stop the champion—WHOAAAA!"},
            {"speaker": "CHLOE", "text": "Hahaha! And down goes the champion in 4K!"}
        ],
        "script": "[CHAD]: Chloe, feast your eyes on peak male performance! Watch this move! [CHLOE]: Chad, please stop before you embarrass both of us! [CHAD]: Impossible! Nothing can stop the champion! [CHLOE]: Hahaha! And down goes the champion in 4K!",
        "description": "Hilarious Chad and Chloe comedy dub! #shorts #viral #funny #comedy #crazyvault",
        "tags": "shorts, funny, comedy, viral, meme, chad, chloe, kevin, hilarious"
    }

# ==========================================
# 4. MICROSOFT EDGE TTS & HORMOZI SUBTITLES
# ==========================================
def parse_vtt_timestamps(vtt_file):
    """Parses SRT/WebVTT subtitle cues generated by edge-tts into word/phrase segments."""
    cues = []
    if not os.path.exists(vtt_file):
        return cues
    try:
        with open(vtt_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        time_pat = re.compile(r"(\d{1,2}:?\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{1,2}:?\d{2}:\d{2}[.,]\d{3})")
        current_start = None
        current_end = None
        for line in lines:
            line = line.strip()
            m = time_pat.search(line)
            if m:
                current_start = m.group(1)
                current_end = m.group(2)
            elif current_start and current_end and line and not line.isdigit() and not line.startswith("WEBVTT"):
                clean_text = re.sub(r"<[^>]+>", "", line).strip()
                if clean_text:
                    cues.append((vtt_time_to_seconds(current_start), vtt_time_to_seconds(current_end), clean_text))
                current_start = None
                current_end = None
    except Exception as e:
        print(f"⚠️ Error parsing subtitles: {e}")
    return cues

def vtt_time_to_seconds(ts):
    ts = str(ts).strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        h = float(parts[0])
        m = float(parts[1])
        s = float(parts[2])
        return h * 3600 + m * 60 + s
    elif len(parts) == 2:
        m = float(parts[0])
        s = float(parts[1])
        return m * 60 + s
    return float(ts)

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

async def generate_edge_tts_with_word_boundaries_async(text, voice, output_audio, rate="+16%"):
    """Hooks directly into Microsoft Edge TTS websocket stream to extract exact millisecond word boundaries."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words_timing = []
    with open(output_audio, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start_sec = chunk["offset"] / 10_000_000.0
                dur_sec = chunk["duration"] / 10_000_000.0
                end_sec = start_sec + dur_sec
                word = chunk["text"].strip()
                if word:
                    words_timing.append((start_sec, end_sec, word))
    return words_timing

CHARACTER_CAST = {
    "CHAD": {
        "voice": "en-US-GuyNeural",
        "rate": "+15%",
        "label_color": "&H0000FFFF&",       # Bold Yellow in ASS BGR (&H00BBGGRR&)
        "word_active_color": "&H0000FFFF&",
        "text_color": "&H00FFFFFF&"
    },
    "CHLOE": {
        "voice": "en-US-JennyNeural",
        "rate": "+13%",
        "label_color": "&H00FF55FF&",       # Bold Pink/Magenta
        "word_active_color": "&H00FF55FF&",
        "text_color": "&H00FFFFFF&"
    },
    "KEVIN": {
        "voice": "en-US-ChristopherNeural",
        "rate": "+14%",
        "label_color": "&H0000FF00&",       # Bright Lime Green
        "word_active_color": "&H0000FF00&",
        "text_color": "&H00FFFFFF&"
    },
    "BUSTER": {
        "voice": "en-US-EricNeural",
        "rate": "+15%",
        "label_color": "&H0000A5FF&",       # Comic Orange
        "word_active_color": "&H0000A5FF&",
        "text_color": "&H00FFFFFF&"
    }
}

# 🎙️ ElevenLabs Studio Voice Mapping (Hyper-Realistic Character Acting)
ELEVENLABS_VOICE_MAP = {
    "CHAD": "pNInz6obpgDQGcFmaJgB",   # Adam (Dominant, firm hero voice)
    "CHLOE": "cgSgspJ2msm6clMCkdW9",  # Jessica (Playful, bright, warm sassy girl)
    "KEVIN": "TX3LPaxmHKxFdv7VOQHJ",  # Liam (Energetic social creator / goofy friend)
    "BUSTER": "N2lVS1w4EtoT3dr4eOWO"  # Callum (Husky trickster / hilarious dog voice)
}

def alignment_to_word_timings(alignment):
    chars = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends = alignment.get("character_end_times_seconds", [])
    words_timing = []
    current_word = []
    w_start = None
    w_end = None
    for i, c in enumerate(chars):
        if c.isspace():
            if current_word:
                words_timing.append((w_start, w_end, "".join(current_word)))
                current_word = []
                w_start = None
                w_end = None
        else:
            if w_start is None:
                w_start = starts[i]
            w_end = ends[i]
            current_word.append(c)
    if current_word:
        words_timing.append((w_start, w_end, "".join(current_word)))
    return words_timing

def try_elevenlabs_tts(text, speaker, output_mp3, api_keys_list):
    """
    Attempts to generate high-emotion character audio via ElevenLabs API with Word-Lock timestamps.
    Automatically rotates keys on quota exhaustion (401/429/credit limit).
    """
    if not api_keys_list:
        return False, []
    
    voice_id = ELEVENLABS_VOICE_MAP.get(speaker, ELEVENLABS_VOICE_MAP["CHAD"])
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.85
        }
    }
    
    for k_idx, key in enumerate(api_keys_list):
        headers = {
            "xi-api-key": key.strip(),
            "Content-Type": "application/json"
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=25)
            if r.status_code == 200:
                res = r.json()
                audio_b64 = res.get("audio_base64", "")
                if audio_b64:
                    with open(output_mp3, "wb") as f:
                        f.write(base64.b64decode(audio_b64))
                    alignment = res.get("alignment", {})
                    words_timing = alignment_to_word_timings(alignment)
                    print(f"   ⚡ [ELEVENLABS SUCCESS] Line [{speaker}] voiced by ElevenLabs (Voice ID: {voice_id})!")
                    return True, words_timing
            else:
                print(f"   ⚠️ ElevenLabs key #{k_idx+1} notice (HTTP {r.status_code}): {r.text[:120]}")
        except Exception as e:
            print(f"   ⚠️ ElevenLabs API request notice: {e}")
            
    return False, []

def resolve_character_speaker(raw_spk):
    spk = str(raw_spk or "").strip().upper()
    if spk in CHARACTER_CAST:
        return spk
    if any(k in spk for k in ["DOG", "PUPPY", "PET", "CAT", "ANIMAL", "BUSTER"]):
        return "BUSTER"
    if any(k in spk for k in ["CHLOE", "GIRL", "WOMAN", "LADY", "FEMALE", "SISTER", "MOM"]):
        return "CHLOE"
    if any(k in spk for k in ["KEVIN", "FRIEND", "BRO", "BOY2", "EXTRA", "BYSTANDER"]):
        return "KEVIN"
    return "CHAD"

def generate_multivoice_dialogue_and_ass(dialogue_list, output_audio, output_ass, hook_banner=""):
    """
    Village Whispora Multi-Character Dubbing Engine:
    - Prioritizes ElevenLabs Hyper-Realistic Studio Voices (Adam, Jessica, Liam, Callum).
    - Auto-rotates multiple ElevenLabs API keys on quota exhaustion.
    - Seamlessly falls back to Microsoft Edge-TTS if ElevenLabs quota is exhausted.
    - Captures word boundaries for 1:1 millisecond lock.
    - Formats character-tagged Hormozi ASS subtitles with distinct color badges.
    - Seamlessly joins dialogue audio clips into a unified master audio track.
    """
    os.makedirs(os.path.dirname(output_audio) or ".", exist_ok=True)
    parts_dir = "temp/dialogue_parts"
    os.makedirs(parts_dir, exist_ok=True)

    if isinstance(dialogue_list, str):
        dialogue_list = [{"speaker": "CHAD", "text": dialogue_list}]
    elif not isinstance(dialogue_list, list) or len(dialogue_list) == 0:
        dialogue_list = [{"speaker": "CHAD", "text": "Wait for it! This is crazy!"}]

    # Load ElevenLabs API keys (supports comma-separated rotation pool)
    raw_el_keys = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    el_keys = [k.strip() for k in raw_el_keys.split(",") if k.strip()]
    if el_keys:
        print(f"🎙️ ElevenLabs Engine Activated! ({len(el_keys)} API keys in rotation pool)")
    else:
        print("🎙️ ElevenLabs API key not set, using Microsoft Edge-TTS Studio voices.")

    # Create 0.18s silence WAV for natural conversational rhythm
    silence_wav = os.path.join(parts_dir, "pause_silence.wav")
    sample_rate = 44100
    n_pause_samples = int(0.18 * sample_rate)
    with wave.open(silence_wav, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b'\x00\x00\x00\x00' * n_pause_samples)

    wav_parts = []
    ass_cards = []
    current_time_sec = 0.0

    print(f"🎙️ Generating Multi-Character Skit Dubbing ({len(dialogue_list)} dialogue lines)...")

    for idx, d in enumerate(dialogue_list):
        if not isinstance(d, dict):
            continue
        speaker = resolve_character_speaker(d.get("speaker", "CHAD"))
        char_info = CHARACTER_CAST[speaker]
        raw_text = d.get("text", "")
        clean_text = strip_emojis(raw_text).strip()
        if not clean_text:
            continue

        print(f"   ▶ Line {idx+1} [{speaker}]: \"{clean_text}\"")

        part_mp3 = os.path.join(parts_dir, f"part_{idx}.mp3")
        part_wav = os.path.join(parts_dir, f"part_{idx}.wav")
        part_srt = os.path.join(parts_dir, f"part_{idx}.srt")

        words_timing = []
        el_success = False

        # 1. Try ElevenLabs Studio Voice
        if el_keys:
            el_success, words_timing = try_elevenlabs_tts(clean_text, speaker, part_mp3, el_keys)

        # 2. Fallback to Edge-TTS if ElevenLabs not available or quota reached
        if not el_success:
            print(f"   🔄 Voicing [{speaker}] via Edge-TTS ({char_info['voice']})...")
            try:
                words_timing = asyncio.run(
                    generate_edge_tts_with_word_boundaries_async(
                        clean_text, char_info["voice"], part_mp3, rate=char_info["rate"]
                    )
                )
            except Exception as e:
                print(f"   ⚠️ Async Edge TTS notice for line {idx+1}: {e}")

            if not words_timing or not os.path.exists(part_mp3) or os.path.getsize(part_mp3) < 500:
                cmd = [
                    sys.executable, "-m", "edge_tts",
                    "--voice", char_info["voice"],
                    "--rate", char_info["rate"],
                    "--text", clean_text,
                    "--write-media", part_mp3,
                    "--write-subtitles", part_srt
                ]
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as e:
                    print(f"   ⚠️ Edge TTS CLI fallback error: {e}")

        # Convert line MP3 to standard 44.1kHz stereo 16-bit WAV
        cmd_wav = [
            "ffmpeg", "-y", "-i", part_mp3,
            "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le",
            part_wav
        ]
        subprocess.run(cmd_wav, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not os.path.exists(part_wav) or os.path.getsize(part_wav) < 500:
            continue

        line_dur = get_media_duration(part_wav)

        # Parse timing for subtitle cards (2-3 words per card)
        chunk_size = 3
        if words_timing:
            for i in range(0, len(words_timing), chunk_size):
                chunk = words_timing[i:i + chunk_size]
                s_rel = chunk[0][0]
                e_rel = max(chunk[-1][1], s_rel + 0.25)
                c_words = [w[2] for w in chunk]
                start_s = current_time_sec + s_rel
                end_s = current_time_sec + e_rel
                ass_cards.append((speaker, start_s, end_s, c_words))
        else:
            # Fallback uniform timing if word boundaries missing
            words = clean_text.split()
            w_dur = line_dur / max(len(words), 1)
            for i in range(0, len(words), chunk_size):
                chunk = words[i:i + chunk_size]
                s_rel = i * w_dur
                e_rel = min(line_dur, (i + len(chunk)) * w_dur)
                start_s = current_time_sec + s_rel
                end_s = current_time_sec + e_rel
                ass_cards.append((speaker, start_s, end_s, chunk))

        wav_parts.append(part_wav)
        # Add pause after line unless it is the very last line
        if idx < len(dialogue_list) - 1:
            wav_parts.append(silence_wav)
            current_time_sec += line_dur + 0.18
        else:
            current_time_sec += line_dur

    if not wav_parts:
        raise RuntimeError("No dialogue audio clips could be generated!")

    # Concatenate all WAV parts into master WAV
    master_wav = "temp/dialogue_master.wav"
    with wave.open(master_wav, "wb") as outfile:
        for p_idx, f_wav in enumerate(wav_parts):
            with wave.open(f_wav, "rb") as infile:
                if p_idx == 0:
                    outfile.setparams(infile.getparams())
                outfile.writeframes(infile.readframes(infile.getnframes()))

    # Encode master WAV to output_audio (e.g. MP3)
    cmd_enc = [
        "ffmpeg", "-y", "-i", master_wav,
        "-c:a", "libmp3lame", "-b:a", "192k",
        output_audio
    ]
    subprocess.run(cmd_enc, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    total_audio_dur = get_media_duration(output_audio)
    print(f"✅ Master Multi-Voice Dialogue Audio Assembled: {output_audio} ({total_audio_dur:.2f}s)")

    # Write ASS File with character-colored badges & Hormozi typography
    with open(output_ass, "w", encoding="utf-8") as f:
        f.write("[Script Info]\n")
        f.write("ScriptType: v4.00+\n")
        f.write("PlayResX: 1080\n")
        f.write("PlayResY: 1920\n")
        f.write("ScaledBorderAndShadow: yes\n\n")
        
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        # Premium Hormozi Floating Subtitles: Bold yellow & white, thick black outline (5px) + 3D drop shadow (3px), Golden Center / Eye-Level Zone (MarginV 680)
        f.write("Style: Hormozi,DejaVu Sans,58,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,5,3,2,50,50,680,1\n")
        # Top Hook Banner: High-contrast yellow & white text on dark pill box, eye-level top safe zone (MarginV 200, Alignment 8)
        f.write("Style: TopHook,DejaVu Sans,50,&H0000FFFF,&H00FFFFFF,&H00000000,&HA0000000,-1,0,0,0,100,100,2,0,3,10,0,8,40,40,200,1\n\n")
        
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        
        if hook_banner and hook_banner.strip():
            clean_hook = re.sub(r'[^\w\s\?!.,\x27-]', '', hook_banner).strip().replace("\r", "").replace("\n", " ").upper()
            total_end = seconds_to_ass_time(ass_cards[-1][2] if ass_cards else total_audio_dur)
            f.write(f"Dialogue: 0,0:00:00.00,{total_end},TopHook,,0,0,0,,{clean_hook}\n")

        for speaker, start_s, end_s, words in ass_cards:
            start_ts = seconds_to_ass_time(start_s)
            end_ts = seconds_to_ass_time(end_s)
            char_cfg = CHARACTER_CAST.get(speaker, CHARACTER_CAST["CHAD"])
            badge_color = char_cfg["label_color"]
            word_color = char_cfg["word_active_color"]
            
            badge = f"{{\\c{badge_color}&}}[{speaker}]"
            if len(words) == 1:
                content = f"{{\\c{word_color}&}}{words[0].upper()}"
            elif len(words) >= 2:
                w1 = f"{{\\c{word_color}&}}{words[0].upper()}"
                w_rest = f"{{\\c&H00FFFFFF&}}{' '.join(words[1:]).upper()}"
                content = f"{w1} {w_rest}"
            else:
                content = ""
            styled_text = f"{badge} {content}"
            f.write(f"Dialogue: 0,{start_ts},{end_ts},Hormozi,,0,0,0,,{styled_text}\n")

    print(f"✅ Generated {len(ass_cards)} Multi-Character ASS Subtitle Cards (1:1 Word Sync): {output_ass}")
    return total_audio_dur

def generate_voiceover_and_ass(script_text, voice, output_audio, output_ass, hook_banner=""):
    """Backward compatibility wrapper."""
    dialogue_list = [{"speaker": "CHAD", "text": script_text}]
    return generate_multivoice_dialogue_and_ass(dialogue_list, output_audio, output_ass, hook_banner=hook_banner)

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

def synthesize_sfx_pack(temp_dir):
    """
    Synthesizes crisp, punchy, copyright-free sound effects (7-Piece Soundboard):
    1. whoosh.wav (universal hook intro sound)
    2. bonk.wav (slapstick cartoon fail sound)
    3. vine_boom.wav (sub-bass meme shock sound)
    4. record_scratch.wav (sudden freeze / pause / WTF moment)
    5. buzzer.wav (wrong move / caught buzzer)
    6. pop.wav (playful cute bubble sound)
    7. ding.wav (smart trick / victory bell chime)
    """
    sample_rate = 44100
    os.makedirs(temp_dir, exist_ok=True)
    paths = {
        "whoosh": os.path.join(temp_dir, "sfx_whoosh.wav"),
        "bonk": os.path.join(temp_dir, "sfx_bonk.wav"),
        "vine_boom": os.path.join(temp_dir, "sfx_vine_boom.wav"),
        "record_scratch": os.path.join(temp_dir, "sfx_record_scratch.wav"),
        "buzzer": os.path.join(temp_dir, "sfx_buzzer.wav"),
        "pop": os.path.join(temp_dir, "sfx_pop.wav"),
        "ding": os.path.join(temp_dir, "sfx_ding.wav")
    }

    # 1. Whoosh SFX (0.35s sweep)
    if not os.path.exists(paths["whoosh"]):
        with wave.open(paths["whoosh"], "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
            dur = 0.35; n = int(sample_rate * dur); frames = bytearray()
            for i in range(n):
                t = i / sample_rate
                env = math.sin(math.pi * (t / dur)) ** 1.8
                freq = 200 + 1400 * (t / dur) ** 2
                val = int(32767 * 0.45 * env * math.sin(2 * math.pi * freq * t))
                frames.extend(struct.pack('<h', max(-32768, min(32767, val))))
            wf.writeframes(frames)

    # 2. Bonk SFX (0.35s cartoon slapstick pitch drop)
    if not os.path.exists(paths["bonk"]):
        with wave.open(paths["bonk"], "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
            dur = 0.35; n = int(sample_rate * dur); frames = bytearray()
            for i in range(n):
                t = i / sample_rate
                env = math.exp(-t * 12.0)
                freq = 420.0 * math.exp(-t * 8.0) + 120.0
                val = int(32767 * 0.65 * env * (0.7 * math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(4 * math.pi * freq * t)))
                frames.extend(struct.pack('<h', max(-32768, min(32767, val))))
            wf.writeframes(frames)

    # 3. Vine Boom / Shock Bass Drop (0.75s)
    if not os.path.exists(paths["vine_boom"]):
        with wave.open(paths["vine_boom"], "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
            dur = 0.75; n = int(sample_rate * dur); frames = bytearray()
            for i in range(n):
                t = i / sample_rate
                env = math.exp(-t * 4.5)
                freq = 75.0 * math.exp(-t * 2.2) + 28.0
                val = int(32767 * 0.75 * env * (math.sin(2 * math.pi * freq * t) + 0.4 * math.sin(4 * math.pi * freq * t)))
                frames.extend(struct.pack('<h', max(-32768, min(32767, val))))
            wf.writeframes(frames)

    # 4. Record Scratch (0.45s vinyl pause)
    if not os.path.exists(paths["record_scratch"]):
        with wave.open(paths["record_scratch"], "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
            dur = 0.45; n = int(sample_rate * dur); frames = bytearray()
            for i in range(n):
                t = i / sample_rate
                env = math.sin(math.pi * (t / dur)) ** 1.2
                freq = 1800.0 * (1.0 - (t / dur) ** 0.8) + 150.0
                noise = ((i * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff - 0.5
                val = int(32767 * 0.50 * env * (0.6 * math.sin(2 * math.pi * freq * t) + 0.4 * noise))
                frames.extend(struct.pack('<h', max(-32768, min(32767, val))))
            wf.writeframes(frames)

    # 5. Buzzer (0.35s harsh buzz)
    if not os.path.exists(paths["buzzer"]):
        with wave.open(paths["buzzer"], "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
            dur = 0.35; n = int(sample_rate * dur); frames = bytearray()
            for i in range(n):
                t = i / sample_rate
                env = 1.0 if t < 0.3 else math.exp(-(t - 0.3) * 30.0)
                phase = (t * 140.0) % 1.0
                wave_val = 1.0 if phase < 0.5 else -1.0
                val = int(32767 * 0.45 * env * wave_val)
                frames.extend(struct.pack('<h', max(-32768, min(32767, val))))
            wf.writeframes(frames)

    # 6. Pop SFX (0.15s bubble pop)
    if not os.path.exists(paths["pop"]):
        with wave.open(paths["pop"], "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
            dur = 0.15; n = int(sample_rate * dur); frames = bytearray()
            for i in range(n):
                t = i / sample_rate
                env = math.exp(-t * 28.0)
                freq = 600.0 + 900.0 * (1.0 - t / dur)
                val = int(32767 * 0.55 * env * math.sin(2 * math.pi * freq * t))
                frames.extend(struct.pack('<h', max(-32768, min(32767, val))))
            wf.writeframes(frames)

    # 7. Ding (0.45s clean chime bell)
    if not os.path.exists(paths["ding"]):
        with wave.open(paths["ding"], "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
            dur = 0.45; n = int(sample_rate * dur); frames = bytearray()
            for i in range(n):
                t = i / sample_rate
                env = math.exp(-t * 8.0)
                freq = 1318.51
                val = int(32767 * 0.50 * env * (0.8 * math.sin(2 * math.pi * freq * t) + 0.2 * math.sin(4 * math.pi * freq * t)))
                frames.extend(struct.pack('<h', max(-32768, min(32767, val))))
            wf.writeframes(frames)

    print("🔊 Synthesized 7-Piece Soundboard Pack (Whoosh, Bonk, Vine Boom, Record Scratch, Buzzer, Pop, Ding)")
    return paths

# ==========================================
# 6. FFMPEG TRANSFORMATIVE VIDEO STUDIO
# ==========================================
def render_transformative_short(input_video, narration_audio, ass_subtitles, hook_banner, output_video, output_thumb, sfx_timeline=None):
    """
    Renders 100% Monetizable YouTube Short with Adaptive Framing & Dynamic AI Soundboard:
    - Smart Aspect Ratio Detection:
      * Landscape (16:9): Ambient Blurred Studio Frame (100% full action visible, zero cropping/zooming)
      * Vertical (9:16): Native 9:16 vertical framing with dynamic punch-in zoom on climax moments
    - Horizontal Flip (hflip) & dynamic speed match (setpts)
    - Full AI Soundboard Mixing:
      * 7 Universal effects: Whoosh, Bonk, Vine Boom, Record Scratch, Buzzer, Pop, Ding
      * AI Director selects 1 to 3 cues with exact millisecond timestamps
    - Dynamic Punch-in Zoom (1.12x centered during climax)
    - Top Hook Banner Pill Box (ALL CAPS)
    - Burned Hormozi Yellow/White Subtitles
    - Multi-Track Audio Mixing (Voiceover 1.0 + BGM 0.12 + Soundboard Tracks)
    """
    os.makedirs(os.path.dirname(output_video) or ".", exist_ok=True)
    os.makedirs("temp", exist_ok=True)

    src_dur = get_media_duration(input_video)
    narration_dur = get_media_duration(narration_audio)
    # 1:1 Video-Audio Perfect Sync: Video cuts precisely when narration completes (+ 0.35s punchline breath)
    # Zero dead air: never keep playing after the narration stops!
    target_dur = narration_dur + 0.35
    # Keep final short within optimal bounds (never exceed 28.5s, minimum 8.0s)
    target_dur = min(28.5, max(8.0, target_dur))
    v_w, v_h = get_video_dimensions(input_video)
    is_landscape = (v_w > v_h) or (v_w / max(v_h, 1) >= 0.85)

    print(f"🎬 Video Sync: Source={src_dur:.2f}s | Narration={narration_dur:.2f}s | Target Short={target_dur:.2f}s")
    print(f"📐 Video Dimensions: {v_w}x{v_h} | Layout: {'Studio Ambient Blur Frame (Full Action, Zero Zoom)' if is_landscape else 'Native 9:16 Vertical'}")

    # Pure Natural 1.0x Real-Life Speed (Zero fast-forwarding, full authentic motion)
    speed_filter = "setpts=PTS"
    print(f"⚡ Natural Video Speed: 1.0x Real Speed (setpts=PTS, full {target_dur:.2f}s duration)")

    # 1. Synthesize background music & 7-effect SFX pack
    bgm_path = "temp/comedy_bgm.wav"
    synthesize_comedy_bgm(bgm_path, target_dur + 2.0)
    sfx_pack = synthesize_sfx_pack("temp")

    # 2. Resolve AI Soundboard Timeline
    active_cues = []
    zoom_time = None

    if isinstance(sfx_timeline, list):
        for item in sfx_timeline:
            if not isinstance(item, dict):
                continue
            snd = str(item.get("sound") or item.get("sfx") or "").lower()
            try:
                t = float(item.get("time") or item.get("timestamp") or 0.0)
            except Exception:
                continue
            zm = bool(item.get("zoom", False))
            if snd in sfx_pack and 0.2 <= t <= (target_dur - 0.7):
                active_cues.append({
                    "sound": snd,
                    "file": sfx_pack[snd],
                    "time": t,
                    "zoom": zm
                })
                if zm and zoom_time is None:
                    zoom_time = t

    # Ensure intro hook whoosh at 0.10s for instantaneous ear grab (Zero dead silence at 0.0s)
    if not any(c["sound"] == "whoosh" for c in active_cues):
        active_cues.insert(0, {
            "sound": "whoosh",
            "file": sfx_pack["whoosh"],
            "time": 0.10,
            "zoom": False
        })
    else:
        for c in active_cues:
            if c["sound"] == "whoosh" and c["time"] > 0.2:
                c["time"] = 0.10

    active_cues.sort(key=lambda x: x["time"])
    active_cues = active_cues[:4]

    print(f"🎛️ AI Audio Director: {len(active_cues)} Soundboard Cues Activated:")
    for c in active_cues:
        print(f"   ▶ {c['time']:.2f}s: [{c['sound'].upper()}] {'(Camera Zoom 1.12x)' if c['zoom'] else ''}")

    # 3. Build FFmpeg Filtergraph
    clean_hook = re.sub(r'[^\w\s\?!.,\x27-]', '', hook_banner).replace("'", "").replace(":", "").strip().upper()
    ass_escaped = ass_subtitles.replace("\\", "/").replace(":", "\\:")

    # Build dynamic FFmpeg audio inputs & filter
    cmd_inputs = [
        "-stream_loop", "-1", "-i", input_video,      # [0:v]
        "-i", narration_audio,                        # [1:a]
        "-i", bgm_path                                # [2:a]
    ]

    audio_filter_parts = [
        "[1:a]volume=1.0[voice];",
        "[2:a]volume=0.12[bgm];"
    ]
    amix_labels = ["[voice]", "[bgm]"]

    for idx, c in enumerate(active_cues):
        in_idx = 3 + idx
        cmd_inputs.extend(["-i", c["file"]])
        delay_ms = int(c["time"] * 1000)
        vol = 0.40 if c["sound"] == "whoosh" else 0.60
        label = f"[sfx_{idx}]"
        audio_filter_parts.append(f"[{in_idx}:a]adelay={delay_ms}|{delay_ms},volume={vol:.2f}{label};")
        amix_labels.append(label)

    audio_filter_parts.append(
        f"{''.join(amix_labels)}amix=inputs={len(amix_labels)}:duration=longest:dropout_transition=2[outa]"
    )
    audio_mix_filter = "".join(audio_filter_parts)

    do_zoom = zoom_time is not None

    if is_landscape:
        zoom_filter = ""
        if do_zoom:
            t_s = max(0.5, zoom_time - 0.2)
            t_e = min(target_dur - 0.5, zoom_time + 1.1)
            zoom_filter = f",crop=w='if(between(t,{t_s:.2f},{t_e:.2f}),in_w*0.88,in_w)':h='if(between(t,{t_s:.2f},{t_e:.2f}),in_h*0.88,in_h)':x=(in_w-out_w)/2:y=(in_h-out_h)/2,scale=1080:-2:flags=lanczos"

        filter_complex = (
            f"[0:v]hflip,{speed_filter},split=2[v_bg][v_fg];"
            f"[v_bg]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
            f"boxblur=25:8,eq=brightness=-0.15[bg_blur];"
            f"[v_fg]scale=1080:-2:flags=lanczos{zoom_filter}[fg_crisp];"
            f"[bg_blur][fg_crisp]overlay=0:(H-h)/2[base_comp];"
            f"[base_comp]subtitles='{ass_escaped}'[outv];"
            f"{audio_mix_filter}"
        )
        simpler_filter = (
            f"[0:v]hflip,{speed_filter},split=2[v_bg][v_fg];"
            f"[v_bg]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
            f"boxblur=25:8,eq=brightness=-0.15[bg_blur];"
            f"[v_fg]scale=1080:-2:flags=lanczos[fg_crisp];"
            f"[bg_blur][fg_crisp]overlay=0:(H-h)/2[base_comp];"
            f"[base_comp]subtitles='{ass_escaped}'[outv];"
            f"{audio_mix_filter}"
        )
    else:
        # Native Vertical 9:16 Video (Clean Ultra-Premium Fullscreen, Zero Black Bars)
        if do_zoom:
            t_s = max(0.5, zoom_time - 0.2)
            t_e = min(target_dur - 0.5, zoom_time + 1.1)
            crop_logic = f"crop=w='if(between(t,{t_s:.2f},{t_e:.2f}),1080*0.88,1080)':h='if(between(t,{t_s:.2f},{t_e:.2f}),1920*0.88,1920)':x=(in_w-out_w)/2:y=(in_h-out_h)/2,scale=1080:1920:flags=lanczos"
        else:
            crop_logic = "crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2"

        filter_complex = (
            f"[0:v]hflip,{speed_filter},"
            f"scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
            f"{crop_logic},"
            f"subtitles='{ass_escaped}'[outv];"
            f"{audio_mix_filter}"
        )
        simpler_filter = (
            f"[0:v]hflip,{speed_filter},"
            f"scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
            f"subtitles='{ass_escaped}'[outv];"
            f"{audio_mix_filter}"
        )

    cmd = [
        "ffmpeg", "-y",
        *cmd_inputs,
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

    # 1. Live Chinese Douyin Ingestion
    raw_video, raw_title, raw_desc, route_used, vault_meta = ingest_live_chinese_video(
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
    
    dialogue_list = director_output.get("dialogue")
    if not dialogue_list:
        raw_s = director_output.get("script", "")
        dialogue_list = [{"speaker": "CHAD", "text": raw_s}]

    print("\n🎭 --- DIRECTED MULTI-CHARACTER SKIT DETAILS ---")
    print(f"📌 Title: {director_output.get('title')}")
    print(f"🏷️ Top Hook: {director_output.get('hook_banner')}")
    print(f"👥 Characters: {director_output.get('characters_detected', ['CHAD', 'CHLOE'])}")
    print("🗣️ Village Whispora Skit Dialogue:")
    for d in dialogue_list:
        if isinstance(d, dict):
            print(f"   [{d.get('speaker', 'CHAD')}]: \"{d.get('text', '')}\"")
    print("------------------------------------------------\n")

    # 3. Microsoft Edge TTS Multi-Voice Synthesis & Character Subtitles
    os.makedirs("temp", exist_ok=True)
    audio_path = "temp/narration.mp3"
    ass_path = "temp/subtitles.ass"
    generate_multivoice_dialogue_and_ass(
        dialogue_list=dialogue_list,
        output_audio=audio_path,
        output_ass=ass_path,
        hook_banner=director_output.get("hook_banner", "WAIT FOR IT 😂")
    )

    # 4. Transformative FFmpeg Editing (Anti-Reused Content & Full Soundboard)
    render_transformative_short(
        input_video=raw_video,
        narration_audio=audio_path,
        ass_subtitles=ass_path,
        hook_banner=director_output.get("hook_banner", "WAIT FOR IT 😂"),
        output_video=args.output,
        output_thumb=args.thumb,
        sfx_timeline=director_output.get("sfx_timeline", [])
    )

    # 5. Save Video Metadata
    os.makedirs("output", exist_ok=True)
    metadata_path = "output/metadata.json"
    metadata = {
        "title": director_output.get("title", "Viral Comedy Short #shorts"),
        "description": director_output.get("description", "Hilarious viral comedy short! #shorts #viral #funny"),
        "tags": director_output.get("tags", "shorts, funny, comedy, viral, meme"),
        "hook_banner": director_output.get("hook_banner", "WAIT FOR IT 😂"),
        "dialogue": dialogue_list,
        "characters": director_output.get("characters_detected", ["CHAD", "CHLOE"]),
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

    # 7. Auto-Cleanup Temporary Files (Zero leftover video junk)
    try:
        import shutil
        if os.path.exists("temp"):
            shutil.rmtree("temp", ignore_errors=True)
            print("🧹 [CLEANUP] Successfully deleted all temporary raw video and audio files!")
    except Exception as e:
        print(f"⚠️ Cleanup notice: {e}")

    print("\n===================================================================")
    print("🎉 VIRAL COMEDY SHORT SUCCESSFULLY GENERATED!")
    print(f"🎬 Video: {args.output}")
    print(f"🖼️ Thumbnail: {args.thumb}")
    print("===================================================================\n")

if __name__ == "__main__":
    main()
