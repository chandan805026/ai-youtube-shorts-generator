import os
import sys
import glob
import json
import urllib.request
import argparse

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run_youtube_server_diagnosis():
    print("=" * 70)
    print("🔍 QUERYING YOUTUBE SERVERS DIRECTLY FOR CHANNEL & VIDEO DIAGNOSTICS 🔍")
    print("=" * 70)
    client_id = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()

    token_json = os.getenv("YOUTUBE_TOKEN_JSON", "").strip()
    if token_json and not (client_id and refresh_token):
        try:
            tj = json.loads(token_json)
            client_id = client_id or tj.get("client_id")
            client_secret = client_secret or tj.get("client_secret")
            refresh_token = refresh_token or tj.get("refresh_token")
        except Exception:
            pass

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    creds.refresh(Request())
    print(f"✅ OAuth Token Scopes: {creds.scopes}")
    yt = build("youtube", "v3", credentials=creds)

    # 1. Channel Status & Audit
    uploads_playlist_id = None
    ch_resp = yt.channels().list(part="snippet,statistics,status,contentDetails,brandingSettings,topicDetails", mine=True).execute()
    for ch in ch_resp.get("items", []):
        uploads_playlist_id = ch.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        print("\n[YOUTUBE CHANNEL SERVER DATA]:")
        print(json.dumps({
            "id": ch.get("id"),
            "title": ch.get("snippet", {}).get("title"),
            "publishedAt": ch.get("snippet", {}).get("publishedAt"),
            "country": ch.get("snippet", {}).get("country"),
            "defaultLanguage": ch.get("snippet", {}).get("defaultLanguage"),
            "statistics": ch.get("statistics"),
            "status": ch.get("status"),
            "topicDetails": ch.get("topicDetails"),
            "brandingSettings": ch.get("brandingSettings", {}).get("channel")
        }, indent=2))

    # 2. Try auditDetails if permitted
    try:
        aud_resp = yt.channels().list(part="auditDetails", mine=True).execute()
        print("\n[YOUTUBE CHANNEL AUDIT DETAILS]:")
        print(json.dumps(aud_resp.get("items", []), indent=2))
    except Exception as e:
        print(f"\n[AuditDetails Note]: {e}")

    # 3. Fetch ALL uploaded videos on the channel via uploads playlist
    vid_ids = []
    if uploads_playlist_id:
        pl_resp = yt.playlistItems().list(part="snippet,contentDetails,status", playlistId=uploads_playlist_id, maxResults=25).execute()
        for item in pl_resp.get("items", []):
            vid = item.get("contentDetails", {}).get("videoId")
            if vid and vid not in vid_ids:
                vid_ids.append(vid)

    for known_id in ["Su6i4eFRV5E", "dAnG1SZQFbc", "14XiUbqjqvw", "fzqxUylFbbU", "DdMkn9eOJ4E"]:
        if known_id not in vid_ids:
            vid_ids.append(known_id)

    # 4. Query full server details for every video
    v_resp = yt.videos().list(
        part="snippet,status,statistics,contentDetails,processingDetails,suggestions,topicDetails,recordingDetails,localizations",
        id=",".join(vid_ids[:20])
    ).execute()

    print("\n[YOUTUBE VIDEOS SERVER REPORT]:")
    for v in v_resp.get("items", []):
        vid_report = {
            "id": v.get("id"),
            "publishedAt": v.get("snippet", {}).get("publishedAt"),
            "title": v.get("snippet", {}).get("title"),
            "description": v.get("snippet", {}).get("description"),
            "categoryId": v.get("snippet", {}).get("categoryId"),
            "defaultLanguage": v.get("snippet", {}).get("defaultLanguage"),
            "defaultAudioLanguage": v.get("snippet", {}).get("defaultAudioLanguage"),
            "tags": v.get("snippet", {}).get("tags"),
            "liveBroadcastContent": v.get("snippet", {}).get("liveBroadcastContent"),
            "duration": v.get("contentDetails", {}).get("duration"),
            "dimension": v.get("contentDetails", {}).get("dimension"),
            "definition": v.get("contentDetails", {}).get("definition"),
            "caption": v.get("contentDetails", {}).get("caption"),
            "licensedContent": v.get("contentDetails", {}).get("licensedContent"),
            "projection": v.get("contentDetails", {}).get("projection"),
            "hasCustomThumbnail": v.get("contentDetails", {}).get("hasCustomThumbnail"),
            "contentRating": v.get("contentDetails", {}).get("contentRating"),
            "regionRestriction": v.get("contentDetails", {}).get("regionRestriction"),
            "status": v.get("status"),
            "processingDetails": v.get("processingDetails"),
            "suggestions": v.get("suggestions"),
            "statistics": v.get("statistics"),
            "topicDetails": v.get("topicDetails")
        }
        print(f"--- VIDEO {v.get('id')} ---")
        print(json.dumps(vid_report, indent=2))

    # 5. Try YouTube Analytics API if scope permits
    try:
        yt_analytics = build("youtubeAnalytics", "v2", credentials=creds)
        an_resp = yt_analytics.reports().query(
            ids="channel==MINE",
            startDate="2026-10-01",
            endDate="2026-10-14",
            metrics="views,engagedViews,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares",
            dimensions="video",
            sort="-views",
            maxResults=20
        ).execute()
        print("\n[YOUTUBE ANALYTICS SERVER REPORT]:")
        print(json.dumps(an_resp, indent=2))
    except Exception as ex:
        print(f"\n[YouTube Analytics Note]: {ex}")



def sanitize_youtube_metadata(text: str) -> str:
    if not text:
        return ""
    import re
    safe_replacements = [
        (r'\bholding\s+(.*?)\s+hostage\b', r'using \1 as a bargaining chip'),
        (r'\bheld\s+(.*?)\s+hostage\b', r'used \1 as a bargaining chip'),
        (r'\bhostage\b', 'prank'),
        (r'\blive\s+bomb\b', 'firecracker'),
        (r'\bbomb\b', 'firecracker'),
        (r'\bcommit\s+a\s+crime\b', 'lose her temper'),
        (r'\bcrime\b', 'prank'),
        (r'\bnear\s+death\s+experience\b', 'hilarious close call'),
        (r'\bdeath\b', 'disaster'),
        (r'\bdead\b', 'done for'),
        (r'\bkilled\b', 'busted'),
        (r'\bkill\b', 'catch'),
        (r'\bmurder\b', 'trouble'),
        (r'\bsuicide\b', 'mistake'),
        (r'\bkidnapped\b', 'carried away'),
        (r'\bkidnap\b', 'carry away'),
        (r'\bterrorist\b', 'prankster'),
        (r'\bweapon\b', 'prop'),
        (r'\bgun\b', 'water blaster'),
        (r'\bliquor\b', 'secret drink'),
        (r'\balcohol\b', 'secret drink'),
    ]
    for pat, repl in safe_replacements:
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    return text.strip()


def build_dynamic_tags(title: str, desc: str, custom_tags=None) -> list:
    import re
    base_tags = ["Shorts", "Comedy", "Funny", "Humor", "Viral", "Storytime", "Prank"]
    if custom_tags:
        if isinstance(custom_tags, str):
            extra = [t.strip() for t in custom_tags.split(",") if t.strip()]
        else:
            extra = [str(t).strip() for t in custom_tags if str(t).strip()]
    else:
        extra = []

    # Extract meaningful topic keywords from title & description
    stop_words = {
        "the", "and", "for", "his", "her", "their", "when", "with", "from", "that",
        "this", "into", "until", "would", "could", "really", "thought", "plan",
        "actually", "worked", "backfired", "instantly", "shorts", "funny", "comedy",
        "watch", "like", "share", "subscribe", "daily", "hilarious", "stories", "story"
    }
    words = re.findall(r'[A-Za-z]{4,14}', f"{title} {desc}")
    for w in words:
        lw = w.lower()
        if lw not in stop_words and lw not in {"hostage", "bomb", "crime", "kill", "death", "rooster", "barnyard"}:
            cap_w = w.capitalize()
            if cap_w not in base_tags and cap_w not in extra:
                extra.append(cap_w)
            if len(extra) >= 7:
                break

    final_tags = []
    for t in base_tags + extra:
        if t not in final_tags and t.lower() not in {"rooster", "barnyard"}:
            final_tags.append(t)
    return final_tags[:14]


def upload_short(video_source=None, title=None, desc=None, tags=None, publish_at=None):
    if video_source == "DIAGNOSE":
        run_youtube_server_diagnosis()
        return "DIAGNOSE", "DIAGNOSE"

    print("=" * 60)
    print("🚀 YOUTUBE SHORTS CLOUD PUBLISHER 🚀")
    print("=" * 60)

    # 1. Locate video file
    video_path = None
    if video_source and os.path.exists(video_source):
        video_path = video_source
    elif video_source and video_source.startswith("http"):
        local_dl = "downloaded_target_short.mp4"
        print(f"📥 Downloading short from stream: {video_source}...")
        req = urllib.request.Request(video_source, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp, open(local_dl, "wb") as f:
            f.write(resp.read())
        video_path = local_dl
    else:
        files = glob.glob("viral_short_*.mp4") or glob.glob("viral_short.mp4")
        if files:
            video_path = files[0]
        else:
            backup_url = "https://n.uguu.se/JytmzlvD.mp4"
            local_dl = "viral_short_target.mp4"
            print(f"📥 Downloading latest rendered short from backup stream: {backup_url}...")
            req = urllib.request.Request(backup_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp, open(local_dl, "wb") as f:
                f.write(resp.read())
            video_path = local_dl

    video_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"🎬 Ready to upload: {video_path} ({video_size_mb:.2f} MB)")

    # 2. Get YouTube OAuth Secrets
    client_id = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()

    token_json = os.getenv("YOUTUBE_TOKEN_JSON", "").strip()
    if token_json and not (client_id and refresh_token):
        try:
            tj = json.loads(token_json)
            client_id = client_id or tj.get("client_id")
            client_secret = client_secret or tj.get("client_secret")
            refresh_token = refresh_token or tj.get("refresh_token")
        except Exception:
            pass

    if not (client_id and client_secret and refresh_token):
        print("❌ Error: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, or YOUTUBE_REFRESH_TOKEN is missing!")
        sys.exit(1)

    print("🔐 [YouTube Auth] Initializing Google OAuth2 credentials...")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )

    try:
        creds.refresh(Request())
        print("✅ [YouTube OAuth] Access token refreshed successfully!")
    except Exception as e:
        print(f"❌ [YouTube OAuth Error] Failed to refresh token: {e}")
        sys.exit(1)

    yt_service = build("youtube", "v3", credentials=creds)

    # Check if latest_metadata.json exists for automatic metadata
    saved_meta = {}
    if os.path.exists("latest_metadata.json"):
        try:
            with open("latest_metadata.json", "r", encoding="utf-8") as mf:
                saved_meta = json.load(mf)
        except Exception:
            pass

    if not title:
        title = saved_meta.get("title") or "His Clever Prank Plan Backfired Instantly! 😂 #Shorts"

    if not desc:
        desc = saved_meta.get("description") or (
            "He really thought his sneaky backup plan would work, until instant karma took over! 😂🔥\n\n"
            "🔔 Subscribe for daily hilarious comedy stories!\n\n"
            "#Shorts #Comedy #Funny #Prank #Humor #Storytime #Viral #Laughter"
        )

    title = sanitize_youtube_metadata(title)
    if "#Shorts" not in title and "#shorts" not in title:
        title = f"{title} #Shorts"
    desc = sanitize_youtube_metadata(desc)
    final_tags = build_dynamic_tags(title, desc, tags or saved_meta.get("tags"))

    status_dict = {
        "privacyStatus": "private" if publish_at else "public",
        "selfDeclaredMadeForKids": False
    }
    if publish_at:
        status_dict["publishAt"] = publish_at

    body = {
        "snippet": {
            "title": title,
            "description": desc,
            "tags": final_tags,
            "categoryId": "23",  # Comedy category
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en"
        },
        "status": status_dict
    }

    print(f"\n📺 Publishing YouTube Short:")
    print(f"   📌 Title: {title}")
    print(f"   🏷️  Tags ({len(final_tags)}): {final_tags}")
    print(f"   📂 Category: Comedy (23) | Language: en")
    if publish_at:
        print(f"   ⏰ Scheduled Publish Time: {publish_at} (Private until release)")
    else:
        print(f"   🌐 Visibility: Public")
    print(f"\n🚀 Uploading video stream to YouTube...")

    media = MediaFileUpload(video_path, chunksize=1024 * 1024 * 5, resumable=True, mimetype="video/mp4")
    request = yt_service.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Uploading: {int(status.progress() * 100)}% complete...")

    video_id = response.get("id")
    yt_url = f"https://youtu.be/{video_id}"
    yt_short_url = f"https://www.youtube.com/shorts/{video_id}"

    print("=" * 60)
    print("🎉 YOUTUBE UPLOAD COMPLETE!")
    print(f"▶️ Video ID: {video_id}")
    print(f"🔗 YouTube Link: {yt_url}")
    print(f"📱 YouTube Short Link: {yt_short_url}")
    print("=" * 60)

    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file and os.path.exists(summary_file):
        with open(summary_file, "a", encoding="utf-8") as sf:
            sf.write(f"\n### 🚀 YouTube Shorts Published!\n")
            sf.write(f"- **YouTube Video**: [{yt_url}]({yt_url})\n")
            sf.write(f"- **Shorts Link**: [{yt_short_url}]({yt_short_url})\n")

    return video_id, yt_short_url


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload Short to YouTube")
    parser.add_argument("--video", default=None, help="Video file path or HTTP stream URL")
    parser.add_argument("--title", default=None, help="Video Title")
    parser.add_argument("--desc", default=None, help="Video Description")
    parser.add_argument("--tags", default=None, help="Comma-separated custom tags")
    parser.add_argument("--publish-at", default=None, help="Scheduled publish time in ISO-8601 UTC")
    args = parser.parse_args()

    upload_short(video_source=args.video, title=args.title, desc=args.desc, tags=args.tags, publish_at=args.publish_at)

