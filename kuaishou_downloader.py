import os
import sys
import re
import json
import subprocess
import urllib.request
import requests
import time
from bs4 import BeautifulSoup

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

FFMPEG_BIN = r"C:\Users\ladu\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = "ffmpeg"
SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"


def extract_photo_id(url: str) -> str:
    """Extract photoId from various Kuaishou URL formats directly without network calls."""
    m = re.search(r'(?:short-video|photo|fw/photo)/([a-zA-Z0-9_\-]+)', url)
    if m:
        return m.group(1)
    
    m_pid = re.search(r'photoId=([a-zA-Z0-9_\-]+)', url)
    if m_pid:
        return m_pid.group(1)

    m2 = re.search(r'fid=([a-zA-Z0-9_\-]+)', url)
    if m2:
        return m2.group(1)
        
    return ""


def resolve_short_link_if_needed(raw_url: str) -> str:
    """Only resolve if it is a short link like v.kuaishou.com by inspecting 302 Location."""
    if "v.kuaishou.com" in raw_url:
        try:
            r = requests.head(raw_url, headers={"User-Agent": IPHONE_UA}, allow_redirects=False, timeout=8)
            loc = r.headers.get("Location")
            if loc:
                return loc
        except Exception:
            pass
        try:
            r = requests.get(raw_url, headers={"User-Agent": IPHONE_UA}, allow_redirects=False, timeout=8)
            loc = r.headers.get("Location")
            if loc:
                return loc
        except Exception:
            pass
    return raw_url


def fetch_kuaishou_video_info(url_or_id: str) -> dict:
    """
    Fetch unwatermarked CDN MP4 and metadata by querying mobile endpoint.
    Bypasses desktop captchas completely.
    """
    photo_id = extract_photo_id(url_or_id)
    if not photo_id:
        resolved = resolve_short_link_if_needed(url_or_id)
        photo_id = extract_photo_id(resolved)

    if not photo_id and not "http" in url_or_id:
        photo_id = url_or_id.strip()

    if not photo_id:
        raise ValueError(f"Could not extract photoId from: {url_or_id}")

    # Mobile endpoint directly returns unwatermarked MP4 URL in HTML
    mobile_url = f"https://c.kuaishou.com/fw/photo/{photo_id}"
    req = urllib.request.Request(mobile_url, headers={"User-Agent": IPHONE_UA})
    
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", "ignore")

    soup = BeautifulSoup(html, "html.parser")
    page_title = soup.title.string.strip() if soup.title and soup.title.string else ""

    clean_html = html.replace(r'\/', '/').replace(r'\u002F', '/')

    # Find unwatermarked CDN video URL (filter out 8s remux preview snippets)
    mp4_urls = list(set(re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', clean_html)))
    if not mp4_urls:
        for alt_url in [f"https://www.kuaishou.com/short-video/{photo_id}", f"https://m.kuaishou.com/fw/photo/{photo_id}"]:
            try:
                req_alt = urllib.request.Request(alt_url, headers={"User-Agent": IPHONE_UA})
                with urllib.request.urlopen(req_alt, timeout=10) as r_alt:
                    alt_html = r_alt.read().decode("utf-8", "ignore").replace(r'\/', '/').replace(r'\u002F', '/')
                    found = list(set(re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', alt_html)))
                    if found:
                        mp4_urls = found
                        break
            except Exception:
                pass

    full_candidates = [u for u in mp4_urls if "/upic/" in u or ("vod-rt-remux" not in u and ("kwimgs.com" in u or "yximgs.com" in u))]
    if not full_candidates:
        full_candidates = [u for u in mp4_urls if "vod-rt-remux" not in u]
    if not full_candidates:
        full_candidates = mp4_urls

    if not full_candidates:
        raise RuntimeError("No direct MP4 CDN URL found in mobile response!")

    cdn_url = full_candidates[0]
    for c in full_candidates:
        if "/upic/" in c:
            cdn_url = c
            break

    cdn_url = cdn_url.replace(r"\/", "/")

    # Extract author and caption
    caption = ""
    author = ""
    scripts = soup.find_all("script")
    for s in scripts:
        t = s.string or ""
        if not caption:
            c = re.findall(r'"caption":\s*"([^"]+)"', t)
            if c:
                caption = c[0]
        if not author:
            a = re.findall(r'"userName":\s*"([^"]+)"', t)
            if a:
                author = a[0]

    return {
        "photo_id": photo_id,
        "title": page_title,
        "author": author or "川哥哥 (Creator)",
        "caption": caption or page_title,
        "cdn_url": cdn_url
    }


def download_and_transcode(video_info: dict, output_dir: str = SCRATCH_DIR) -> str:
    """
    Downloads CDN MP4 with chunked streaming and transcodes HEVC to standard H.264.
    """
    photo_id = video_info["photo_id"]
    playable_path = os.path.join(output_dir, f"playable_{photo_id}.mp4")

    if os.path.exists(playable_path) and os.path.getsize(playable_path) > 1000:
        print(f"[Downloader] Found cached playable H.264 video: {playable_path}")
        return playable_path

    raw_path = os.path.join(output_dir, f"raw_{photo_id}.mp4")

    # 1. Download in chunks with robust retry & CDN headers
    if not os.path.exists(raw_path) or os.path.getsize(raw_path) < 1000:
        print(f"[Downloader] Downloading {photo_id} from CDN...")
        cdn_headers = {
            "User-Agent": IPHONE_UA,
            "Referer": "https://c.kuaishou.com/",
            "Accept": "*/*",
            "Connection": "keep-alive"
        }
        download_ok = False
        for attempt in range(3):
            try:
                with requests.get(video_info["cdn_url"], headers=cdn_headers, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(raw_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024*1024):
                            if chunk:
                                f.write(chunk)
                if os.path.exists(raw_path) and os.path.getsize(raw_path) > 10000:
                    download_ok = True
                    break
            except Exception as e:
                print(f"[Downloader] Stream attempt {attempt+1} failed: {e}")
                time.sleep(2)

        if not download_ok:
            print("[Downloader] Falling back to curl...")
            cmd_curl = [
                "curl", "-L", "-s",
                "-H", f"User-Agent: {IPHONE_UA}",
                "-H", "Referer: https://c.kuaishou.com/",
                video_info["cdn_url"],
                "-o", raw_path
            ]
            subprocess.run(cmd_curl, check=True)

        print(f"[Downloader] Downloaded raw video: {os.path.getsize(raw_path) / (1024*1024):.2f} MB")

    # 2. Transcode HEVC -> H.264
    print(f"[Downloader] Transcoding HEVC to H.264 for universal compatibility...")
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", raw_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "19",
        "-c:a", "aac",
        "-b:a", "192k",
        playable_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[Downloader] Transcoding complete: {playable_path}")
    return playable_path


if __name__ == "__main__":
    test_url = "https://www.kuaishou.com/short-video/3xnhw787utiscgu"
    info = fetch_kuaishou_video_info(test_url)
    print("Success! Photo ID:", info["photo_id"])
    print("Author:", info["author"])
    print("CDN URL:", info["cdn_url"][:60] + "...")
    p = download_and_transcode(info)
    print("Playable File:", p)
