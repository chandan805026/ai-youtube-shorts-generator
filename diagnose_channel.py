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
print("  FORENSIC YOUTUBE VIDEO INVESTIGATION")
print("=" * 70)

vids_to_check = ["Su6i4eFRV5E", "AtqtNMnL-xo", "14XiUbqjqvw", "dAnG1SZQFbc", "8NXyPlkPtVY"]
v_resp = yt.videos().list(
    part="snippet,status,statistics,contentDetails",
    id=",".join(vids_to_check)
).execute()

print(f"Found {len(v_resp.get('items', []))} videos:")
for v in v_resp.get("items", []):
    print("\n------------------------------------------------------------")
    print(f"VIDEO ID: {v.get('id')}")
    print(f"Title: {v.get('snippet', {}).get('title')}")
    print(f"Status: {json.dumps(v.get('status'), indent=2)}")
    print(f"Statistics: {json.dumps(v.get('statistics'), indent=2)}")
