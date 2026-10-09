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


def upload_short(video_source=None, title=None, desc=None, tags=None, publish_at=None):
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
        # Search locally
        files = glob.glob("viral_short_*.mp4") or glob.glob("viral_short.mp4")
        if files:
            video_path = files[0]
        else:
            # Fallback to current Uguu live backup stream
            backup_url = "https://n.uguu.se/ssEHaavH.mp4"
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

    if not title:
        title = "Gary's Tactical Barnyard Prison Break! 🐔🍷 #Shorts"

    if not desc:
        desc = (
            "Gary attempts the ultimate tactical escape from Brenda's strict barnyard lockdown! 😂\n\n"
            "From an undercover wine shuttle to green laser distress SOS signals and a covert phone recycling heist, "
            "watch the unbelievable escape unfold! 🐔🍷\n\n"
            "🎙️ Narrated with British comedic flair by Liam.\n\n"
            "🔔 Like, Share and Subscribe for Gary's next legendary escape mission!\n\n"
            "#Shorts #Comedy #Funny #Escape #Rooster #Viral #Storytelling #Humor #Relatable #ShortsFeed #Trending"
        )

    tags = [
        "Shorts", "Comedy", "Funny", "Viral", "Humor", "Storytime",
        "Barnyard", "Escape", "Meme", "Trending", "Rooster", "BritishNarrator"
    ]

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
            "tags": tags,
            "categoryId": "23"  # Comedy category
        },
        "status": status_dict
    }

    print(f"\n📺 Publishing YouTube Short:")
    print(f"   📌 Title: {title}")
    print(f"   📂 Category: Comedy (23)")
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

    # Write summary for GitHub Actions if available
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
    parser.add_argument("--publish-at", default=None, help="Scheduled publish time in ISO-8601 UTC")
    args = parser.parse_args()

    upload_short(video_source=args.video, title=args.title, desc=args.desc, publish_at=args.publish_at)
