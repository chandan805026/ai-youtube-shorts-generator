"""
Playwright Stealth Douyin Channel & Couple Comedy Scraper
Runs natively on GitHub Actions runner with Chromium.
Intercepts ByteDance web search & creator API to extract direct unwatermarked MP4 streams.
"""

import os
import sys
import time
import json
import random
import requests

def scrape_douyin_couple_video(dest_path="temp/source_video.mp4", keyword="夫妻搞笑"):
    """
    Launches headless Chromium using Playwright with stealth settings,
    navigates to Douyin search or creator page, intercepts ByteDance's internal API
    response, and downloads the unwatermarked HD video stream.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("⚠️ Playwright not installed, skipping browser scrape...")
        return None

    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    captured_videos = []

    print(f"\n=======================================================")
    print(f"🕵️ [PLAYWRIGHT STEALTH] Launching Invisible Chrome for: '{keyword}'")
    print(f"=======================================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--window-size=1920,1080"
            ]
        )

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ]
        chosen_ua = random.choice(user_agents)

        context = browser.new_context(
            user_agent=chosen_ua,
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai"
        )

        # Stealth JS injections to defeat bot detection
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
        """)

        page = context.new_page()

        # Listen to all network responses
        def on_response(response):
            try:
                url = response.url
                if any(x in url for x in ["/search/item/", "/general/search/", "/aweme/post/", "/web/search/"]):
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        data = response.json()
                        raw_list = data.get("data", []) or data.get("aweme_list", [])
                        for item in raw_list:
                            aweme = item.get("aweme_info", item)
                            if not aweme or not isinstance(aweme, dict):
                                continue
                            
                            aweme_id = aweme.get("aweme_id")
                            desc = aweme.get("desc", "")
                            stats = aweme.get("statistics", {})
                            likes = stats.get("digg_count", 0)
                            
                            video_obj = aweme.get("video", {})
                            play_urls = video_obj.get("play_addr", {}).get("url_list", [])
                            dur = video_obj.get("duration", 0) / 1000.0

                            # Filter for sweet spot short videos (12s to 45s)
                            if play_urls and (10.0 <= dur <= 50.0):
                                captured_videos.append({
                                    "id": str(aweme_id),
                                    "desc": desc,
                                    "likes": likes,
                                    "duration": dur,
                                    "play_url": play_urls[0],
                                    "author": aweme.get("author", {}).get("nickname", "Douyin Creator")
                                })
            except Exception:
                pass

        page.on("response", on_response)

        # Search URLs to try
        search_encoded = requests.utils.quote(keyword)
        target_url = f"https://www.douyin.com/search/{search_encoded}?type=video"

        print(f"🌐 Navigating to Douyin: {target_url}")
        try:
            page.goto(target_url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"⚠️ Page navigation notice: {e}, waiting for responses...")

        # Small scroll to trigger lazy loading of API requests
        try:
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(4000)
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(3000)
        except Exception:
            pass

        browser.close()

    print(f"📦 Playwright Intercepted {len(captured_videos)} Couple Comedy Candidates!")

    if not captured_videos:
        print("⚠️ No videos intercepted via Playwright network listener.")
        return None

    # Sort by Likes (Highest engagement first)
    captured_videos.sort(key=lambda x: x["likes"], reverse=True)
    winner = captured_videos[0]

    print(f"\n🏆 [PLAYWRIGHT WINNER] Selected Top Couple Comedy Clip:")
    print(f"   🆔 Video ID: {winner['id']} ({winner['duration']:.1f}s)")
    print(f"   👤 Creator: {winner['author']}")
    print(f"   👍 Likes: {winner['likes']:,}")
    print(f"   📝 Caption: {winner['desc']}")
    print(f"   🔗 Play Stream URL: {winner['play_url'][:60]}...")

    # Download direct unwatermarked MP4
    print(f"⬇️ Downloading direct stream from ByteDance CDN...")
    headers = {"User-Agent": "okhttp/3.10.0.1"}
    try:
        with requests.get(winner["play_url"], headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*512):
                    if chunk:
                        f.write(chunk)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 50000:
            file_mb = os.path.getsize(dest_path) / (1024*1024)
            print(f"✅ [PLAYWRIGHT SUCCESS] Downloaded Couple Short ({file_mb:.2f} MB)!")
            return {
                "path": dest_path,
                "title": f"When Husband Tries To Prank His Wife 💀 #shorts",
                "desc": winner["desc"],
                "id": f"douyin_{winner['id']}",
                "likes": winner["likes"],
                "author": winner["author"]
            }
    except Exception as e:
        print(f"⚠️ Error downloading Playwright video: {e}")

    return None

if __name__ == "__main__":
    res = scrape_douyin_couple_video()
    print("Result:", res)
