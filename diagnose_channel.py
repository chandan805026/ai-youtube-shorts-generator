import os
import json
import requests

api_key = os.getenv("GEMINI_API_KEY", "").strip()

print("=" * 70)
print("  FORENSIC YOUTUBE VIDEO INVESTIGATION (API KEY METHOD)")
print("=" * 70)

vids_to_check = ["Su6i4eFRV5E", "AtqtNMnL-xo", "14XiUbqjqvw", "dAnG1SZQFbc", "8NXyPlkPtVY"]
url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,status,contentDetails,statistics&id={','.join(vids_to_check)}&key={api_key}"

r = requests.get(url)
print(f"API Response Code: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    items = data.get("items", [])
    print(f"Total videos returned by YouTube API: {len(items)}")
    found_ids = [item["id"] for item in items]
    print(f"Found IDs: {found_ids}")
    
    for v in items:
        print("\n------------------------------------------------------------")
        print(f"VIDEO ID: {v.get('id')}")
        print(f"Title: {v.get('snippet', {}).get('title')}")
        print(f"Status: {json.dumps(v.get('status'), indent=2)}")
        print(f"Statistics: {json.dumps(v.get('statistics'), indent=2)}")
        
    for vid in vids_to_check:
        if vid not in found_ids:
            print(f"\n⚠️ CRITICAL: Video {vid} was COMPLETELY EXPUNGED / DELETED from YouTube database!")
else:
    print("API Error Response:", r.text[:500])
