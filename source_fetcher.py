import os
import sys
import re
import json
import time
import requests

def get_next_video(vault_file="urls_vault.txt", history_file="history.json"):
    history_ids = set()
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                hdata = json.load(f)
                for item in hdata.get("processed_videos", []):
                    if isinstance(item, dict):
                        history_ids.add(str(item.get("video_id", "")))
                        history_ids.add(str(item.get("url", "")))
                    else:
                        history_ids.add(str(item))
        except Exception as e:
            print(f"Warning loading history: {e}")

    urls = []
    if os.path.exists(vault_file):
        with open(vault_file, "r", encoding="utf-8") as f:
            for line in f:
                l = line.strip()
                if l and not l.startswith("#"):
                    urls.append(l)

    selected_url = None
    for u in urls:
        m_id = extract_id(u)
        if u not in history_ids and (m_id is None or m_id not in history_ids):
            selected_url = u
            break

    if not selected_url:
        print("No new URLs in vault! Using top creator invention fallback...")
        selected_url = "https://www.douyin.com/video/7431832422867537189"

    print(f"Selected URL to process: {selected_url}")
    return download_video(selected_url)

def extract_id(url):
    m = re.search(r'/video/(\d+)', url)
    if m:
        return m.group(1)
    m2 = re.search(r'clientCacheKey=([a-zA-Z0-9_-]+)', url)
    if m2:
        return m2.group(1)
    m3 = re.search(r'/short-video/([a-zA-Z0-9_-]+)', url)
    if m3:
        return m3.group(1)
    return None

def download_video(url, output_path="source_raw.mp4"):
    vid_id = extract_id(url) or str(int(time.time()))
    title = "China Crazy Gadget Invention"
    download_url = None

    if "kwaicdn.com" in url or url.endswith(".mp4"):
        download_url = url
    elif "douyin.com" in url or (vid_id and vid_id.isdigit()):
        print(f"Fetching unwatermarked stream for Douyin ID: {vid_id}...")
        s = requests.Session()
        try:
            r0 = s.get("https://api.douyin.wtf/api/v1/auth/demo", timeout=10)
            cred = r0.json().get("data", {})
            s.post("https://api.douyin.wtf/api/v1/auth/login", json={"username": cred.get("username", "demo"), "password": cred.get("password")}, timeout=10)
            r = s.get(f"https://api.douyin.wtf/api/v1/douyin/video?aweme_id={vid_id}&wait=10", timeout=20)
            if r.status_code == 200:
                data = r.json().get("data", {})
                title = data.get("title") or title
                download_url = data.get("media", {}).get("video", {}).get("url")
        except Exception as e:
            print(f"Douyin parser notice: {e}")

    if not download_url:
        download_url = url

    print(f"Downloading stream from CDN...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Referer": "https://www.douyin.com/"
    }
    resp = requests.get(download_url, headers=headers, stream=True, timeout=40)
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Video downloaded: {size_mb:.2f} MB -> {output_path}")

    return {
        "video_path": output_path,
        "video_id": vid_id,
        "title": title,
        "url": url
    }
