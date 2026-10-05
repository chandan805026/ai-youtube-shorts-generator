import os
import sys
import json
import time

def upload_short_to_youtube(video_path, metadata):
    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip()

    if not (client_id and client_secret and refresh_token):
        print("YouTube API credentials not found in environment. Skipping upload.")
        return None

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        print("google-api-python-client not installed. Skipping upload.")
        return None

    print("Connecting to YouTube Data API via OAuth 2.0...")
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    youtube = build("youtube", "v3", credentials=creds)

    title = metadata.get("title", "China Ka Sabse Khatarnak Gadget 😱 #shorts")
    if len(title) > 95:
        title = title[:90] + " #shorts"
    if "#shorts" not in title.lower():
        title = f"{title[:85]} #shorts"

    description = metadata.get("description", "China Crazy Viral Gadget Short! #shorts #gadgets #viral")
    tags = metadata.get("tags", ["shorts", "gadgets", "viral", "funny"])

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "28",
            "defaultLanguage": "hi",
            "defaultAudioLanguage": "hi"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    print(f"Uploading: {title}...")
    media = MediaFileUpload(video_path, chunksize=1024*1024*5, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading progress: {int(status.progress() * 100)}%")

    uploaded_id = response.get("id")
    print(f"SUCCESS! Video uploaded to YouTube Shorts!")
    print(f"🔗 https://www.youtube.com/shorts/{uploaded_id}")
    return uploaded_id
