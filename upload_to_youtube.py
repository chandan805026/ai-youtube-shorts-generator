import os
import sys
import json
import argparse
import time

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"❌ Missing required Google API libraries: {e}")
    print("Please install: pip install google-api-python-client google-auth-oauthlib")
    sys.exit(1)

def get_authenticated_service(client_id, client_secret, refresh_token):
    """Initializes YouTube Data API client using OAuth 2.0 Refresh Token"""
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    return build("youtube", "v3", credentials=creds)

def upload_video_to_youtube(video_path, thumb_path, meta_path, privacy_status="public"):
    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip()

    if not (client_id and client_secret and refresh_token):
        print("⚠️ Warning: YouTube OAuth secrets are not fully configured in environment.")
        print("Required: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN")
        return None

    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found at {video_path}")
        return None

    # Load metadata if available
    metadata = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load {meta_path}: {e}")

    raw_title = metadata.get("title", "The Unexplained Cosmic Enigma 🌌 #shorts")
    # YouTube titles are capped at 100 characters
    if len(raw_title) > 95:
        title = raw_title[:90].strip() + "... #shorts"
    else:
        title = raw_title

    description = metadata.get("description", "")
    description += "\n\n🌌 Welcome to Cosmic Vault.\nWe explore the deepest mysteries of space, ancient wonders, and the unexplained.\n\nSubscribe for daily mind-bending documentary Shorts!\n#shorts #cosmicvault #mystery #space #science #history #unexplained"

    tags = metadata.get("tags", ["shorts", "mystery", "science", "deep space", "cosmic vault"])
    if "Cosmic Vault" not in tags:
        tags.append("Cosmic Vault")

    print(f"🚀 Initializing YouTube Uploader for Cosmic Vault...")
    youtube = get_authenticated_service(client_id, client_secret, refresh_token)

    body = {
        "snippet": {
            "title": title,
            "description": description.strip(),
            "tags": tags,
            "categoryId": "28"  # Science & Technology
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    print(f"📤 Uploading video ({privacy_status}): {title}...")
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=1024*1024*4)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    retry_count = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"   ⏳ Upload Progress: {int(status.progress() * 100)}%")
        except HttpError as ex:
            if ex.resp.status in [500, 502, 503, 504] and retry_count < 5:
                retry_count += 1
                wait_time = retry_count * 2
                print(f"   ⚠️ Temporary server error ({ex.resp.status}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ YouTube API Error: {ex}")
                raise ex

    video_id = response.get("id")
    shorts_url = f"https://youtube.com/shorts/{video_id}"
    print(f"\n🎉 VIDEO SUCCESSFULLY UPLOADED TO YOUTUBE!")
    print(f"🔗 YouTube Shorts URL: {shorts_url}")
    print(f"🆔 Video ID: {video_id}")

    # Set Custom Thumbnail if exists
    if thumb_path and os.path.exists(thumb_path):
        print(f"🖼️ Setting custom thumbnail: {thumb_path}...")
        try:
            thumb_media = MediaFileUpload(thumb_path, mimetype="image/jpeg")
            youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
            print("✅ Custom thumbnail attached successfully!")
        except HttpError as ex:
            print(f"ℹ️ Note on thumbnail: {ex}")
            print("If Intermediate features/phone verification is still pending on YouTube, thumbnail can be set from YouTube Studio.")
        except Exception as e:
            print(f"⚠️ Thumbnail upload skipped: {e}")

    # Write summary for GitHub Actions
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        try:
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n## 📺 Live on YouTube (Cosmic Vault)!\n")
                f.write(f"- **Title:** {title}\n")
                f.write(f"- **Privacy:** `{privacy_status}`\n")
                f.write(f"- **Watch Live:** [Click to Open Shorts on YouTube]({shorts_url})\n")
        except Exception:
            pass

    return shorts_url

def main():
    parser = argparse.ArgumentParser(description="Upload generated Short to YouTube")
    parser.add_argument("--video", default="output/final_video.mp4", help="Path to video file")
    parser.add_argument("--thumb", default="output/thumbnail.jpg", help="Path to thumbnail image")
    parser.add_argument("--meta", default="output/metadata.json", help="Path to metadata json")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"], help="Privacy status")
    args = parser.parse_args()

    upload_video_to_youtube(args.video, args.thumb, args.meta, args.privacy)

if __name__ == "__main__":
    main()
