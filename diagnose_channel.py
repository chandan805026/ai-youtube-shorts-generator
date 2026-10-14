import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

client_id = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()

creds = Credentials(
    token=None,
    refresh_token=refresh_token,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=client_id,
    client_secret=client_secret
)
creds.refresh(Request())
yt = build("youtube", "v3", credentials=creds)

print("=" * 70)
print("  FORENSIC YOUTUBE CHANNEL & VIDEO INVESTIGATION")
print("=" * 70)

# 1. Channel Details & Status
ch_resp = yt.channels().list(part="snippet,statistics,status,contentDetails", mine=True).execute()
for ch in ch_resp.get("items", []):
    print("\n[CHANNEL STATUS]:")
    print(json.dumps({
        "id": ch.get("id"),
        "title": ch.get("snippet", {}).get("title"),
        "status": ch.get("status"),
        "statistics": ch.get("statistics")
    }, indent=2))

# 2. Query target videos: Su6i4eFRV5E, AtqtNMnL-xo, 14XiUbqjqvw, dAnG1SZQFbc
vids_to_check = ["Su6i4eFRV5E", "AtqtNMnL-xo", "14XiUbqjqvw", "dAnG1SZQFbc", "8NXyPlkPtVY"]
v_resp = yt.videos().list(
    part="snippet,status,statistics,contentDetails,processingDetails",
    id=",".join(vids_to_check)
).execute()

print("\n[VIDEO DETAILED STATUSES]:")
for v in v_resp.get("items", []):
    print("\n------------------------------------------------------------")
    print(f"VIDEO ID: {v.get('id')} | Title: {v.get('snippet', {}).get('title')}")
    print(f"Status: {json.dumps(v.get('status'), indent=2)}")
    print(f"Processing Details: {json.dumps(v.get('processingDetails'), indent=2)}")
    print(f"Statistics: {json.dumps(v.get('statistics'), indent=2)}")
